"""TRC20 USDT monitor (TronGrid).

API ref:
  https://developers.tron.network/reference/get-trc20-transaction-info-by-account-address

We poll `GET /v1/accounts/{addr}/transactions/trc20`, filter by:
  - token_info.address == settings.tron_usdt_contract
  - to == settings.chain_tron_address
  - block_timestamp > state.last_scanned_at_ms

Cursor: we store the most recent block_timestamp (ms) in
`state.last_block_height` (it's a BIGINT — repurposed as ms).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import settings
from app.logging_config import logger
from app.models.orm import ChainMonitorState
from app.payments.base import ChainMonitor, IncomingTx

# 1 USDT-TRC20 = 10^6 token units. 1 USDT = 100_000_000 µ¢ in our units.
# So token_unit → µ¢ multiplier = 100.
TRC20_DECIMALS = 6
MICRO_CENTS_PER_USDT = 100_000_000


class TronMonitor(ChainMonitor):
    network = "tron"
    payment_channel = "usdt-trc20"

    def __init__(self) -> None:
        self.receive_address = settings.chain_tron_address
        self.usdt_contract = settings.tron_usdt_contract
        headers: dict[str, str] = {"accept": "application/json"}
        if settings.trongrid_api_key:
            headers["TRON-PRO-API-KEY"] = settings.trongrid_api_key
        self.client = httpx.AsyncClient(
            base_url=settings.tron_api_base,
            timeout=20.0,
            headers=headers,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def fetch_new_incoming(
        self, state: ChainMonitorState
    ) -> list[IncomingTx]:
        """Pull TRC20 transfers since the cursor.

        TronGrid returns most recent first. We page once (200 max) and stop
        when we hit a tx older than the cursor. v0.3 small volume keeps this
        well within free tier limits (5 req/s).
        """
        min_timestamp_ms = state.last_block_height or 0

        params: dict[str, Any] = {
            "limit": 50,
            "only_to": "true",
            "contract_address": self.usdt_contract,
        }
        if min_timestamp_ms:
            params["min_timestamp"] = min_timestamp_ms + 1  # exclusive

        resp = await self.client.get(
            f"/v1/accounts/{self.receive_address}/transactions/trc20",
            params=params,
        )
        resp.raise_for_status()
        body = resp.json()

        if not body.get("success", True):
            logger.warning("tron_api_unsuccessful", body=body)
            return []

        out: list[IncomingTx] = []
        max_ts = min_timestamp_ms

        for item in body.get("data", []):
            try:
                token_info = item.get("token_info") or {}
                if (token_info.get("address") or "").lower() != self.usdt_contract.lower():
                    continue
                to_addr = item.get("to") or ""
                if to_addr.lower() != self.receive_address.lower():
                    continue

                tx_hash = item.get("transaction_id") or ""
                from_addr = item.get("from") or ""
                value_str = item.get("value") or "0"  # raw token units
                ts_ms = int(item.get("block_timestamp") or 0)

                # Convert raw units → µ¢
                # value is in 10^TRC20_DECIMALS units of a USDT token
                value_units = int(value_str)
                amount_micro_cents = value_units * MICRO_CENTS_PER_USDT // (10 ** TRC20_DECIMALS)

                out.append(IncomingTx(
                    network="tron",
                    tx_hash=tx_hash,
                    from_address=from_addr,
                    to_address=to_addr,
                    amount_micro_cents=amount_micro_cents,
                    block_height=ts_ms,
                    block_time=datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc) if ts_ms else None,
                    raw=item,
                ))
                max_ts = max(max_ts, ts_ms)
            except Exception as exc:
                logger.warning("tron_tx_parse_failed", error=str(exc), item=item)

        # Advance cursor (highest seen ms)
        if max_ts > (state.last_block_height or 0):
            state.last_block_height = max_ts

        logger.info(
            "tron_fetch_done",
            count=len(out),
            cursor_ms=state.last_block_height,
        )
        return out


__all__ = ["TronMonitor"]
