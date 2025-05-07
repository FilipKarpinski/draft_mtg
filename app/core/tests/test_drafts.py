from typing import Set, Tuple
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

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
    def mock_db(self) -> MagicMock:
        db = MagicMock(spec=Session)
        return db

    def test_no_players(self, mock_db: MagicMock) -> None:
        draft = Draft(id=1)
        draft.draft_players = []

        matches = generate_matches(draft, mock_db)

        assert matches == []
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_one_player(self, mock_db: MagicMock) -> None:
        draft = Draft(id=1)
        draft.draft_players = [DraftPlayer(player_id=1, order=1)]

        matches = generate_matches(draft, mock_db)

        assert matches == []
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_even_number_of_players(self, mock_db: MagicMock) -> None:
        draft = Draft(id=1)
        draft.draft_players = [
            DraftPlayer(player_id=1, order=1),
            DraftPlayer(player_id=2, order=2),
            DraftPlayer(player_id=3, order=3),
            DraftPlayer(player_id=4, order=4),
        ]

        matches = generate_matches(draft, mock_db)

        # For 4 players, we should have 3 rounds with 2 matches each = 6 matches
        assert len(matches) == 6

        # Check that all matches have the correct draft_id
        for match in matches:
            assert match.draft_id == 1

        # Check that each player plays against every other player exactly once
        player_pairs: Set[Tuple[int, int]] = set()
        for match in matches:
            # Normalize the pair to ensure (1,2) and (2,1) are considered the same
            pair = tuple(sorted([match.player_1_id, match.player_2_id]))
            player_pairs.add(pair)  # type: ignore

        expected_pairs = {(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)}
        assert player_pairs == expected_pairs

        mock_db.commit.assert_called_once()
        assert mock_db.add.call_count == 6

    def test_odd_number_of_players(self, mock_db: MagicMock) -> None:
        draft = Draft(id=1)
        draft.draft_players = [
            DraftPlayer(player_id=1, order=1),
            DraftPlayer(player_id=2, order=2),
            DraftPlayer(player_id=3, order=3),
            DraftPlayer(player_id=4, order=4),
            DraftPlayer(player_id=5, order=5),
        ]

        matches = generate_matches(draft, mock_db)

        # For 5 players with a dummy player, we should have 5 rounds
        # Each round has 2 matches (since one player sits out against dummy)
        # So total matches should be 10, but we skip matches with dummy player
        assert len(matches) == 10

        # Check that all matches have the correct draft_id
        for match in matches:
            assert match.draft_id == 1
            # Ensure no dummy player (0) in the matches
            assert match.player_1_id != 0
            assert match.player_2_id != 0

        # Check that each player plays against every other player exactly once
        player_pairs: Set[Tuple[int, int]] = set()
        for match in matches:
            # Normalize the pair to ensure (1,2) and (2,1) are considered the same
            pair = tuple(sorted([match.player_1_id, match.player_2_id]))
            player_pairs.add(pair)  # type: ignore

        expected_pairs = {(1, 2), (1, 3), (1, 4), (1, 5), (2, 3), (2, 4), (2, 5), (3, 4), (3, 5), (4, 5)}
        assert player_pairs == expected_pairs

        mock_db.commit.assert_called_once()
        assert mock_db.add.call_count == 10


class TestCalculateFinalPlaces:
    @pytest.fixture
    def mock_db(self) -> MagicMock:
        db = MagicMock(spec=Session)
        return db

    def test_no_ties(self, mock_db: MagicMock) -> None:
        draft = Draft(id=1)
        player1 = DraftPlayer(player_id=1, points=3)
        player2 = DraftPlayer(player_id=2, points=2)
        player3 = DraftPlayer(player_id=3, points=1)

        draft.draft_players = [player1, player2, player3]
        draft.matches = []

        calculate_final_places(draft, mock_db)

        assert player1.final_place == 1
        assert player2.final_place == 2
        assert player3.final_place == 3
        mock_db.commit.assert_called_once()

    def test_two_player_tie_with_head_to_head(self, mock_db: MagicMock) -> None:
        draft = Draft(id=1)
        player1 = DraftPlayer(player_id=1, points=3)
        player2 = DraftPlayer(player_id=2, points=3)
        player3 = DraftPlayer(player_id=3, points=1)

        match = Match(player_1_id=1, player_2_id=2, score=MatchResult.PLAYER_1_WIN)

        draft.draft_players = [player1, player2, player3]
        draft.matches = [match]

        calculate_final_places(draft, mock_db)

        assert player1.final_place == 1
        assert player2.final_place == 2
        assert player3.final_place == 3
        mock_db.commit.assert_called_once()

    def test_two_player_tie_with_reversed_head_to_head(self, mock_db: MagicMock) -> None:
        draft = Draft(id=1)
        player1 = DraftPlayer(player_id=1, points=3)
        player2 = DraftPlayer(player_id=2, points=3)
        player3 = DraftPlayer(player_id=3, points=1)

        match = Match(player_1_id=2, player_2_id=1, score=MatchResult.PLAYER_2_WIN)

        draft.draft_players = [player1, player2, player3]
        draft.matches = [match]

        calculate_final_places(draft, mock_db)

        # Since player1 won the head-to-head match (as player_2_id with PLAYER_2_WIN),
        # player1 should be in 1st place and player2 in 2nd place
        assert player1.final_place == 1
        assert player2.final_place == 2
        assert player3.final_place == 3
        mock_db.commit.assert_called_once()

    def test_two_player_tie_without_head_to_head(self, mock_db: MagicMock) -> None:
        draft = Draft(id=1)
        player1 = DraftPlayer(player_id=1, points=3)
        player2 = DraftPlayer(player_id=2, points=3)
        player3 = DraftPlayer(player_id=3, points=1)

        draft.draft_players = [player1, player2, player3]
        draft.matches = []

        calculate_final_places(draft, mock_db)

        assert player1.final_place == 1
        assert player2.final_place == 1
        assert player3.final_place == 3
        mock_db.commit.assert_called_once()

    def test_three_player_tie(self, mock_db: MagicMock) -> None:
        draft = Draft(id=1)
        player1 = DraftPlayer(player_id=1, points=3)
        player2 = DraftPlayer(player_id=2, points=3)
        player3 = DraftPlayer(player_id=3, points=3)
        player4 = DraftPlayer(player_id=4, points=1)

        draft.draft_players = [player1, player2, player3, player4]
        draft.matches = []

        calculate_final_places(draft, mock_db)

        assert player1.final_place == 1
        assert player2.final_place == 1
        assert player3.final_place == 1
        assert player4.final_place == 4
        mock_db.commit.assert_called_once()
