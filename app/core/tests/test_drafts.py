from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Draft, DraftPlayer, Match, MatchResult
from app.core.utils.drafts import calculate_final_places, generate_matches, rotate_players, sort_to_inside


class TestRotatePlayers:
    def test_empty_list(self) -> None:
        assert rotate_players([]) == []

    def test_single_player(self) -> None:
        assert rotate_players([1]) == [1]

    def test_two_players(self) -> None:
        assert rotate_players([1, 2]) == [1, 2]

    def test_multiple_players(self) -> None:
        assert rotate_players([1, 2, 3, 4]) == [1, 4, 2, 3]
        assert rotate_players([1, 2, 3, 4, 5]) == [1, 5, 2, 3, 4]


class TestSortToInside:
    def test_empty_list(self) -> None:
        assert sort_to_inside([]) == []

    def test_single_player(self) -> None:
        assert sort_to_inside([1]) == [1]

    def test_even_number_of_players(self) -> None:
        assert sort_to_inside([1, 2, 3, 4, 5, 6]) == [1, 3, 5, 6, 4, 2]

    def test_odd_number_of_players(self) -> None:
        assert sort_to_inside([1, 2, 3, 4, 5]) == [1, 3, 5, 4, 2]


class TestGenerateMatches:
    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.mark.asyncio
    async def test_no_players(self, mock_db: AsyncMock) -> None:
        draft = Draft(id=1)
        draft.draft_players = []

        matches = await generate_matches(draft, mock_db)

        assert matches == []

    @pytest.mark.asyncio
    async def test_one_player(self, mock_db: AsyncMock) -> None:
        draft = Draft(id=1)
        player = DraftPlayer(player_id=1, order=1)
        draft.draft_players = [player]

        matches = await generate_matches(draft, mock_db)

        assert matches == []

    @pytest.mark.asyncio
    async def test_even_number_of_players(self, mock_db: AsyncMock) -> None:
        draft = Draft(id=1)
        players = [
            DraftPlayer(player_id=1, order=1),
            DraftPlayer(player_id=2, order=2),
            DraftPlayer(player_id=3, order=3),
            DraftPlayer(player_id=4, order=4),
        ]
        draft.draft_players = players

        # Mock the matches that would be created
        matches = [Match(id=i, draft_id=1, player_1_id=1, player_2_id=2, round=1) for i in range(1, 7)]
        draft.matches = matches

        # Mock the refresh to return the draft with matches
        mock_db.refresh.return_value = None

        result = await generate_matches(draft, mock_db)

        assert len(result) == 6
        mock_db.commit.assert_awaited_once()
        assert mock_db.add.call_count == 6


class TestCalculateFinalPlaces:
    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.mark.asyncio
    async def test_no_ties(self, mock_db: AsyncMock) -> None:
        draft = Draft(id=1)
        players = [
            DraftPlayer(player_id=1, points=9),
            DraftPlayer(player_id=2, points=6),
            DraftPlayer(player_id=3, points=3),
        ]
        draft.draft_players = players
        draft.matches = []

        await calculate_final_places(draft, mock_db)

        assert players[0].final_place == 1
        assert players[1].final_place == 2
        assert players[2].final_place == 3
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_two_way_tie_with_head_to_head(self, mock_db: AsyncMock) -> None:
        draft = Draft(id=1)
        players = [
            DraftPlayer(player_id=1, points=6),
            DraftPlayer(player_id=2, points=6),
        ]
        draft.draft_players = players

        # Player 1 won against player 2
        match = Match(
            player_1_id=1,
            player_2_id=2,
            score=MatchResult.PLAYER_1_WIN,
        )
        draft.matches = [match]

        await calculate_final_places(draft, mock_db)

        assert players[0].final_place == 1
        assert players[1].final_place == 2
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_three_way_tie(self, mock_db: AsyncMock) -> None:
        draft = Draft(id=1)
        players = [
            DraftPlayer(player_id=1, points=6),
            DraftPlayer(player_id=2, points=6),
            DraftPlayer(player_id=3, points=6),
        ]
        draft.draft_players = players
        draft.matches = []

        await calculate_final_places(draft, mock_db)

        # All players should have the same place
        assert players[0].final_place == 1
        assert players[1].final_place == 1
        assert players[2].final_place == 1
        mock_db.commit.assert_awaited_once()
