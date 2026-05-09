"""USDC chain monitors (v0.3, USDT→USDC token swap done in v0.4).

Each chain has a `ChainMonitor` subclass that polls its public RPC / API,
fetches new incoming USDC transfers to our receive address, and matches them
against pending `payment_intents` to credit user balances.

Note: internal `payment_intent.channel` keys still use `usdt-*` prefixes
(`usdt-trc20`, `usdt-sol`, `usdt-evm`) for DB CHECK-constraint compatibility,
even though we now accept USDC tokens — the contract addresses in
`config.py` point at USDC, not USDT.

Public surface:
  - `ChainMonitor` (abstract base)
  - `IncomingTx` (dataclass)
  - `match_and_credit(intent, tx, db)` — common credit logic
  - `monitor_loop(monitor)` — async polling loop
  - `start_all_monitors()` — fans out tasks based on settings.chain_monitors
"""

from app.payments.base import (
    ChainMonitor,
    IncomingTx,
    match_and_credit,
)
from app.payments.monitor import (
    build_monitor,
    monitor_loop,
    start_all_monitors,
)

__all__ = [
    "ChainMonitor",
    "IncomingTx",
    "match_and_credit",
    "monitor_loop",
    "build_monitor",
    "start_all_monitors",
]
