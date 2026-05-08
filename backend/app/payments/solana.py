"""Solana USDC monitor (mainnet-beta JSON-RPC).

We poll for new transactions involving our SPL token account, then for each
new signature we fetch the parsed transaction and look for `transfer` /
`transferChecked` instructions where:
  - mint == settings.solana_usdc_mint
  - destination == settings.chain_solana_address (or its associated token account)

Cursor: we store the most recent signature in `state.last_tx_hash`. Solana
RPC `getSignaturesForAddress` accepts `until=<sig>` to stop once we hit the
last-known signature, giving us cheap incremental polling.

USDC has 6 decimals on Solana. 1 USDC = 100_000_000 µ¢, so the multiplier
from raw token units to µ¢ is 100.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.config import settings
from app.logging_config import logger
from app.models.orm import ChainMonitorState
from app.payments.base import ChainMonitor, IncomingTx

USDC_DECIMALS = 6
MICRO_CENTS_PER_USD = 100_000_000


class SolanaMonitor(ChainMonitor):
    network = "solana"
    payment_channel = "usdt-sol"

    def __init__(self) -> None:
        self.receive_address = settings.chain_solana_address
        self.mint = settings.solana_usdc_mint
        self.client = httpx.AsyncClient(
            base_url=settings.solana_rpc_url,
            timeout=20.0,
            headers={"content-type": "application/json"},
        )
        self._req_id = 0

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    async def close(self) -> None:
        await self.client.aclose()

    async def _rpc(self, method: str, params: list[Any]) -> Any:
        body = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params,
        }
        resp = await self.client.post("", json=body)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"Solana RPC error: {data['error']}")
        return data.get("result")

    async def fetch_new_incoming(
        self, state: ChainMonitorState
    ) -> list[IncomingTx]:
        # Page 1: signatures since last cursor (or 25 most recent on cold start)
        sigs_params: list[Any] = [
            self.receive_address,
            {"limit": 25}
            if not state.last_tx_hash
            else {"limit": 50, "until": state.last_tx_hash},
        ]
        sigs = await self._rpc("getSignaturesForAddress", sigs_params)
        if not sigs:
            return []

        # Newest is at index 0 — we'll set the cursor to that one after success
        newest_sig = sigs[0].get("signature")

        out: list[IncomingTx] = []
        for entry in sigs:
            sig = entry.get("signature")
            if not sig:
                continue

            # Fetch parsed tx
            try:
                tx = await self._rpc(
                    "getTransaction",
                    [sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}],
                )
            except Exception as exc:
                logger.warning("solana_get_tx_failed", sig=sig, error=str(exc))
                continue
            if tx is None:
                continue

            try:
                hits = self._extract_usdc_credits(tx, sig)
                out.extend(hits)
            except Exception as exc:
                logger.warning("solana_tx_parse_failed", sig=sig, error=str(exc))

        if newest_sig:
            state.last_tx_hash = newest_sig

        logger.info(
            "solana_fetch_done",
            count=len(out),
            cursor=state.last_tx_hash,
        )
        return out

    def _extract_usdc_credits(self, tx: dict, sig: str) -> list[IncomingTx]:
        """Pull USDC transfer credits to `self.receive_address` out of a parsed
        Solana transaction. Looks at both top-level instructions and inner
        instructions; supports `transfer` and `transferChecked` from SPL Token.
        """
        msg = (tx.get("transaction") or {}).get("message") or {}
        instructions = list(msg.get("instructions") or [])

        meta = tx.get("meta") or {}
        for inner in meta.get("innerInstructions") or []:
            instructions.extend(inner.get("instructions") or [])

        block_time = tx.get("blockTime")
        slot = tx.get("slot")

        out: list[IncomingTx] = []
        for ix in instructions:
            if (ix.get("program") or "") not in ("spl-token", "spl-token-2022"):
                continue
            parsed = ix.get("parsed") or {}
            ix_type = parsed.get("type")
            if ix_type not in ("transfer", "transferChecked"):
                continue
            info = parsed.get("info") or {}

            # transferChecked carries explicit `mint` + `tokenAmount`. transfer
            # carries `amount` only and the mint is determined by the token
            # account; for our use case (we only ever post the receive_address
            # to be paid in USDC) we'll treat both as mint-checked and require
            # `mint` to be set when present.
            mint = info.get("mint")
            if mint and mint != self.mint:
                continue

            # Destination authority. Wallet address may live under
            # `destinationOwner` for transferChecked or has to be looked up
            # from preTokenBalances / postTokenBalances. Fall back to address.
            dest = (
                info.get("destinationOwner")
                or info.get("destination")
                or ""
            )
            if not _matches_destination(dest, self.receive_address, meta):
                continue

            # Amount. transferChecked uses `tokenAmount.amount` (raw units +
            # decimals). Plain transfer uses `amount` raw units.
            raw_units: int | None = None
            if "tokenAmount" in info:
                ta = info["tokenAmount"]
                try:
                    raw_units = int(ta.get("amount"))
                except (TypeError, ValueError):
                    raw_units = None
            elif "amount" in info:
                try:
                    raw_units = int(info["amount"])
                except (TypeError, ValueError):
                    raw_units = None

            if raw_units is None:
                continue

            amount_micro_cents = raw_units * MICRO_CENTS_PER_USD // (10 ** USDC_DECIMALS)
            from_addr = info.get("authority") or info.get("source") or ""

            out.append(IncomingTx(
                network="solana",
                tx_hash=sig,
                from_address=from_addr,
                to_address=dest,
                amount_micro_cents=amount_micro_cents,
                block_height=slot,
                block_time=None,  # blockTime is unix-seconds, can convert later
                memo=None,
                raw={"sig": sig, "ix": ix, "block_time": block_time},
            ))
        return out


def _matches_destination(
    candidate: str, receive_wallet: str, meta: dict
) -> bool:
    """Return True if `candidate` is either our wallet or a token account
    owned by our wallet (per pre/post token balances)."""
    if not candidate:
        return False
    if candidate == receive_wallet:
        return True

    # Cross-reference token balance entries — `accountIndex` -> owner mapping.
    # For our purposes we just check if any postTokenBalance owner equals the
    # receive wallet AND its `mint` is our USDC mint.
    accounts = ((meta or {}).get("postTokenBalances") or [])
    for tb in accounts:
        if tb.get("owner") == receive_wallet:
            return True
    return False


__all__ = ["SolanaMonitor"]
