from collections import defaultdict
from unittest.mock import AsyncMock

import pytest

from app.core.models import Draft, DraftPlayer, Match
from app.core.utils.drafts import generate_matches, generate_rounds, rotate_players, sort_to_inside


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


class TestRounds:
    @pytest.mark.asyncio
    async def test_no_players(self, base_draft: Draft, mock_db: AsyncMock) -> None:
        base_draft.draft_players = []
        player_ids = [player_id for player_id in base_draft.draft_players]

        rounds = await generate_rounds(base_draft, player_ids, mock_db)

        assert len(rounds) == 0

    @pytest.mark.asyncio
    async def test_one_player(self, base_draft: Draft, mock_db: AsyncMock) -> None:
        base_draft.draft_players = [DraftPlayer(player_id=1, order=1)]
        player_ids = [player_id for player_id in base_draft.draft_players]

        rounds = await generate_rounds(base_draft, player_ids, mock_db)

        assert len(rounds) == 0

    @pytest.mark.asyncio
    async def test_even_number_of_players(self, draft_even_players: Draft, mock_db: AsyncMock) -> None:
        player_ids = [player.player_id for player in draft_even_players.draft_players]

        rounds = await generate_rounds(draft_even_players, player_ids, mock_db)

        assert len(rounds) == 3

    @pytest.mark.asyncio
    async def test_odd_number_of_players(self, draft_odd_players: Draft, mock_db: AsyncMock) -> None:
        player_ids = [player.player_id for player in draft_odd_players.draft_players]
        player_ids.append(None)

        rounds = await generate_rounds(draft_odd_players, player_ids, mock_db)

        assert len(rounds) == 5


class TestMatches:
    def group_matches_by_round(self, matches: list[Match]) -> dict[int, list[Match]]:
        grouped_matches = defaultdict(list)
        for match in matches:
            grouped_matches[match.round_id].append(match)
        return grouped_matches

    @pytest.mark.asyncio
    async def test_even_rounds_even_players(self, draft_even_players_with_rounds: Draft, mock_db: AsyncMock) -> None:
        player_ids = [player.player_id for player in draft_even_players_with_rounds.draft_players]

        matches = await generate_matches(draft_even_players_with_rounds.rounds, player_ids, mock_db)
        grouped_matches = self.group_matches_by_round(matches)

        # Round 1
        assert grouped_matches[1][0].player_1_id == 1
        assert grouped_matches[1][0].player_2_id == 2
        assert grouped_matches[1][1].player_1_id == 3
        assert grouped_matches[1][1].player_2_id == 4

        # Round 2
        assert grouped_matches[2][0].player_1_id == 1
        assert grouped_matches[2][0].player_2_id == 4
        assert grouped_matches[2][1].player_1_id == 2
        assert grouped_matches[2][1].player_2_id == 3

        # Round 3
        assert grouped_matches[3][0].player_1_id == 1
        assert grouped_matches[3][0].player_2_id == 3
        assert grouped_matches[3][1].player_1_id == 4
        assert grouped_matches[3][1].player_2_id == 2

        assert len(grouped_matches) == 3
        assert len(grouped_matches[1]) == 2
        assert len(grouped_matches[2]) == 2
        assert len(grouped_matches[3]) == 2

    @pytest.mark.asyncio
    async def test_even_rounds_odd_players(self, draft_odd_players_with_rounds: Draft, mock_db: AsyncMock) -> None:
        player_ids = [player.player_id for player in draft_odd_players_with_rounds.draft_players]
        player_ids.append(None)

        matches = await generate_matches(draft_odd_players_with_rounds.rounds, player_ids, mock_db)
        grouped_matches = self.group_matches_by_round(matches)

        # Round 1
        assert grouped_matches[1][0].player_1_id == 1
        assert grouped_matches[1][0].player_2_id == 2
        assert grouped_matches[1][1].player_1_id == 3
        assert grouped_matches[1][1].player_2_id == 4

        # Round 2
        assert grouped_matches[2][0].player_1_id == 1
        assert grouped_matches[2][0].player_2_id == 4
        assert grouped_matches[2][1].player_1_id == 3
        assert grouped_matches[2][1].player_2_id == 5

        # Round 3
        assert grouped_matches[3][0].player_1_id == 4
        assert grouped_matches[3][0].player_2_id == 5
        assert grouped_matches[3][1].player_1_id == 2
        assert grouped_matches[3][1].player_2_id == 3

        # Round 4
        assert grouped_matches[4][0].player_1_id == 1
        assert grouped_matches[4][0].player_2_id == 5
        assert grouped_matches[4][1].player_1_id == 4
        assert grouped_matches[4][1].player_2_id == 2

        # Round 5
        assert grouped_matches[5][0].player_1_id == 1
        assert grouped_matches[5][0].player_2_id == 3
        assert grouped_matches[5][1].player_1_id == 5
        assert grouped_matches[5][1].player_2_id == 2

        assert len(grouped_matches) == 5
        assert len(grouped_matches[1]) == 2
        assert len(grouped_matches[2]) == 2
        assert len(grouped_matches[3]) == 2
        assert len(grouped_matches[4]) == 2
        assert len(grouped_matches[5]) == 2
