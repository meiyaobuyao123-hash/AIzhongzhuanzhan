"""USDT chain monitors (v0.3).

Each chain has a `ChainMonitor` subclass that polls its public RPC / API,
fetches new incoming USDT transfers to our receive address, and matches them
against pending `payment_intents` to credit user balances.

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
