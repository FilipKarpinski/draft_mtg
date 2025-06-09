from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Draft, DraftPlayer, Round


@pytest.fixture
def mock_db() -> AsyncMock:
    db = AsyncMock(spec=AsyncSession)
    return db


@pytest.fixture
def base_draft() -> Draft:
    return Draft(id=1)


@pytest.fixture
def draft_even_players() -> Draft:
    draft = Draft(id=1)
    draft.draft_players = [
        DraftPlayer(player_id=1, order=1),
        DraftPlayer(player_id=2, order=2),
        DraftPlayer(player_id=3, order=3),
        DraftPlayer(player_id=4, order=4),
    ]
    return draft


@pytest.fixture
def draft_odd_players() -> Draft:
    draft = Draft(id=1)
    draft.draft_players = [
        DraftPlayer(player_id=1, order=1),
        DraftPlayer(player_id=2, order=2),
        DraftPlayer(player_id=3, order=3),
        DraftPlayer(player_id=4, order=4),
        DraftPlayer(player_id=5, order=5),
    ]
    return draft


@pytest.fixture
def draft_even_players_with_rounds(draft_even_players: Draft) -> Draft:
    draft_even_players.rounds = [
        Round(id=1, draft_id=1, number=1),
        Round(id=2, draft_id=1, number=2),
        Round(id=3, draft_id=1, number=3),
    ]
    return draft_even_players


@pytest.fixture
def draft_odd_players_with_rounds(draft_odd_players: Draft) -> Draft:
    draft_odd_players.rounds = [
        Round(id=1, draft_id=1, number=1),
        Round(id=2, draft_id=1, number=2),
        Round(id=3, draft_id=1, number=3),
        Round(id=4, draft_id=1, number=4),
        Round(id=5, draft_id=1, number=5),
    ]
    return draft_odd_players
