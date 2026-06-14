from __future__ import annotations

import json
import os
import re
from typing import Any

import requests
from pydantic import BaseModel, ConfigDict, Field

from maze_kluster.enums import Direction, TileSymbol

_ENV_VAR_RE = re.compile(r"\$\{([^}]+)\}")


def _resolve(value: str) -> str:
    """Substitute ${VAR} placeholders in a string with their environment variable values."""
    def _sub(m: re.Match[str]) -> str:
        var = m.group(1)
        try:
            return os.environ[var]
        except KeyError:
            raise ValueError(
                f"connection.json references ${{{var}}} but that environment variable is not set"
            ) from None

    return _ENV_VAR_RE.sub(_sub, value)


class Neighbor(BaseModel):
    """A single adjacent tile as reported by the API's possibleActions endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    direction: Direction
    is_start: bool = Field(alias="isStart")
    allows_exit: bool = Field(alias="allowsExit")
    allows_score_collection: bool = Field(alias="allowsScoreCollection")
    has_been_visited: bool = Field(alias="hasBeenVisited")
    reward: float = Field(alias="rewardOnDestination")
    visit_count: int = Field(alias="numberOfVisitsToTile")

    @property
    def tile_type(self) -> TileSymbol:
        """Derive the tile type from the neighbor's flag fields."""
        if self.is_start:
            return TileSymbol.Start
        if self.allows_score_collection:
            return TileSymbol.Collectible
        if self.allows_exit:
            return TileSymbol.Exit
        if self.reward > 0:
            return TileSymbol.Reward
        return TileSymbol.Empty


class PossibleActionsResponse(BaseModel):
    """Full response from the possibleActions and move endpoints."""

    model_config = ConfigDict(populate_by_name=True)

    neighbors: list[Neighbor] = Field(alias="possibleMoveActions")
    can_collect_score: bool = Field(alias="canCollectScoreHere")
    can_exit: bool = Field(alias="canExitMazeHere")
    score_in_hand: float = Field(alias="currentScoreInHand")
    score_in_bag: float = Field(alias="currentScoreInBag")


class MazeInfo(BaseModel):
    """Static metadata for a maze returned by the all-mazes listing."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    total_tiles: int = Field(alias="totalTiles")
    potential_reward: float = Field(alias="potentialReward")


class MazeClient:
    """Thin wrapper around the maze API. One session per player, auth header set at construction."""

    BASE = "https://maze.kluster.htiprojects.nl"

    def __init__(self, base_url: str, api_key: str) -> None:
        self._session = requests.Session()
        self._session.headers.update({"Authorization": api_key})
        self._base = base_url.rstrip("/")

    @classmethod
    def from_config(cls, path: str = "connection.json") -> MazeClient:
        """Build a client from a connection.json file, resolving any ${ENV_VAR} references."""
        with open(path) as f:
            data: dict[str, Any] = json.load(f)
        return cls(base_url=_resolve(str(data["base_url"])), api_key=_resolve(str(data["api_key"])))

    def enter_maze(self, name: str) -> None:
        """Enter the named maze, exiting the current one first if necessary."""
        response = self._session.post(
            f"{self._base}/api/mazes/enter", params={"mazeName": name}
        )
        if response.status_code == 409:
            # 409 has two causes: (a) stuck inside another maze, exit and retry;
            # (b) maze already completed, exit returns 412, so re-raise the 409.
            try:
                self.exit_maze()
            except requests.exceptions.HTTPError:
                response.raise_for_status()
            response = self._session.post(
                f"{self._base}/api/mazes/enter", params={"mazeName": name}
            )
        response.raise_for_status()

    def possible_actions(self) -> PossibleActionsResponse:
        response = self._session.get(f"{self._base}/api/maze/possibleActions")
        response.raise_for_status()
        return PossibleActionsResponse.model_validate(response.json())

    def move(self, direction: Direction) -> PossibleActionsResponse:
        response = self._session.post(
            f"{self._base}/api/maze/move", params={"direction": direction}
        )
        response.raise_for_status()
        return PossibleActionsResponse.model_validate(response.json())

    def collect_score(self) -> None:
        response = self._session.post(f"{self._base}/api/maze/collectScore")
        response.raise_for_status()

    def exit_maze(self) -> None:
        response = self._session.post(f"{self._base}/api/maze/exit")
        response.raise_for_status()

    def all_mazes(self) -> list[MazeInfo]:
        response = self._session.get(f"{self._base}/api/mazes/all")
        response.raise_for_status()
        return [MazeInfo.model_validate(item) for item in response.json()]

    def forget(self) -> None:
        """Delete all player progress. Call register() afterwards to start fresh."""
        response = self._session.delete(f"{self._base}/api/player/forget")
        response.raise_for_status()

    def register(self, name: str) -> None:
        """Re-register the player after forget(). The auth token remains valid."""
        response = self._session.post(
            f"{self._base}/api/player/register", params={"name": name}
        )
        response.raise_for_status()
