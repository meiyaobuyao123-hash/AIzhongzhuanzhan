"""Generic EVM-USDC monitor (BSC / Polygon / Arbitrum / Ethereum).

Uses the Etherscan-style `?module=account&action=tokentx` endpoint that all
four chain explorers expose. Polls for new ERC-20 transfers of the chain's
USDC contract to our receive address since `state.last_block_height`.

USDC decimals per chain:
  - BSC (Binance-Peg USDC):  18
  - Polygon (native USDC):    6
  - Arbitrum (native USDC):   6
  - Ethereum (USDC):          6

We pick a default chain (settings.evm_default_chain) and instantiate one
EvmMonitor per evm sub-chain we want to watch. v0.3 ships only the default
chain monitor running, with the others available via config.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.config import settings
from app.logging_config import logger
from app.models.orm import ChainMonitorState
from app.payments.base import ChainMonitor, IncomingTx

MICRO_CENTS_PER_USD = 100_000_000


@dataclass(frozen=True)
class EvmChainConfig:
    name: str           # 'bsc' / 'polygon' / 'arbitrum' / 'ethereum'
    api_base: str
    api_key: str
    contract: str       # USDC contract on this chain
    decimals: int


def _build_evm_chain_configs() -> dict[str, EvmChainConfig]:
    return {
        "bsc": EvmChainConfig(
            name="bsc",
            api_base=settings.bscscan_api_base,
            api_key=settings.bscscan_api_key,
            contract=settings.bsc_usdc_contract,
            decimals=18,
        ),
        "polygon": EvmChainConfig(
            name="polygon",
            api_base=settings.polygonscan_api_base,
            api_key=settings.polygonscan_api_key,
            contract=settings.polygon_usdc_contract,
            decimals=6,
        ),
        "arbitrum": EvmChainConfig(
            name="arbitrum",
            api_base=settings.arbiscan_api_base,
            api_key=settings.arbiscan_api_key,
            contract=settings.arbitrum_usdc_contract,
            decimals=6,
        ),
        "ethereum": EvmChainConfig(
            name="ethereum",
            api_base=settings.etherscan_api_base,
            api_key=settings.etherscan_api_key,
            contract=settings.ethereum_usdc_contract,
            decimals=6,
        ),
    }


class EvmMonitor(ChainMonitor):
    payment_channel = "usdt-evm"

    def __init__(self, chain: str | None = None) -> None:
        chains = _build_evm_chain_configs()
        chain = chain or settings.evm_default_chain
        if chain not in chains:
            raise ValueError(f"Unknown EVM chain: {chain}")
        self.chain_cfg = chains[chain]
        self.network = chain
        self.receive_address = settings.chain_evm_address
        self.client = httpx.AsyncClient(
            base_url=self.chain_cfg.api_base,
            timeout=20.0,
            headers={"accept": "application/json"},
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def fetch_new_incoming(
        self, state: ChainMonitorState
    ) -> list[IncomingTx]:
        startblock = (state.last_block_height or 0) + 1
        params: dict[str, object] = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": self.chain_cfg.contract,
            "address": self.receive_address,
            "startblock": startblock,
            "endblock": 99_999_999,
            "sort": "asc",
            "page": 1,
            "offset": 100,
        }
        if self.chain_cfg.api_key:
            params["apikey"] = self.chain_cfg.api_key

        resp = await self.client.get("", params=params)
        resp.raise_for_status()
        data = resp.json()

        # Etherscan-style: status="1" if results present, "0" if none/error.
        # message="No transactions found" is the empty case — not an error.
        if data.get("status") not in ("1", 1):
            msg = data.get("message", "")
            if "No transactions" in msg:
                return []
            logger.warning(
                "evm_api_non_ok",
                chain=self.chain_cfg.name,
                status=data.get("status"),
                message=msg,
            )
            return []

        result = data.get("result") or []
        out: list[IncomingTx] = []
        max_block = state.last_block_height or 0

        for item in result:
            try:
                if (item.get("contractAddress") or "").lower() != self.chain_cfg.contract.lower():
                    continue
                if (item.get("to") or "").lower() != self.receive_address.lower():
                    continue

                tx_hash = item.get("hash") or ""
                from_addr = item.get("from") or ""
                value_units = int(item.get("value") or "0")
                amount_micro_cents = value_units * MICRO_CENTS_PER_USD // (10 ** self.chain_cfg.decimals)
                block_num = int(item.get("blockNumber") or 0)

                out.append(IncomingTx(
                    network=self.chain_cfg.name,
                    tx_hash=tx_hash,
                    from_address=from_addr,
                    to_address=self.receive_address,
                    amount_micro_cents=amount_micro_cents,
                    block_height=block_num,
                    raw=item,
                ))
                max_block = max(max_block, block_num)
            except Exception as exc:
                logger.warning(
                    "evm_tx_parse_failed",
                    chain=self.chain_cfg.name,
                    error=str(exc),
                    item=item,
                )

        if max_block > (state.last_block_height or 0):
            state.last_block_height = max_block

        logger.info(
            "evm_fetch_done",
            chain=self.chain_cfg.name,
            count=len(out),
            cursor=state.last_block_height,
        )
        return out


__all__ = ["EvmChainConfig", "EvmMonitor"]
