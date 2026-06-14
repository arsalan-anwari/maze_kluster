from __future__ import annotations

from maze_kluster.bots import BOTS


def test_all_registered_bots_are_callable() -> None:
    for constructor in BOTS.values():
        assert callable(constructor)


def test_registered_bot_names() -> None:
    assert set(BOTS.keys()) == {"baseline", "rf", "gbt", "gp"}


def test_adding_mock_bot_appears_in_registry() -> None:
    class MockBot:
        pass

    BOTS["mock"] = MockBot  # type: ignore[assignment]
    assert "mock" in BOTS
    del BOTS["mock"]


def test_registry_is_single_dict() -> None:
    assert isinstance(BOTS, dict)
