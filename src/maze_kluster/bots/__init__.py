from __future__ import annotations

from collections.abc import Callable

from maze_kluster.bots.base import BotProtocol
from maze_kluster.bots.baseline import BaselineBot
from maze_kluster.bots.smart import SmartBotBase
from maze_kluster.models.gbt import GBTScorer
from maze_kluster.models.gp import GPUCBScorer
from maze_kluster.models.rf import RFScorer

BOTS: dict[str, Callable[..., BotProtocol]] = {
    "baseline": BaselineBot,
    "rf":  lambda client: SmartBotBase(client=client, scorer=RFScorer.load()),
    "gbt": lambda client: SmartBotBase(client=client, scorer=GBTScorer.load()),
    "gp":  lambda client: SmartBotBase(client=client, scorer=GPUCBScorer.load()),
}

__all__ = ["BOTS", "BaselineBot", "BotProtocol", "SmartBotBase"]
