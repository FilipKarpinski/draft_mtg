from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import POINTS_MAP, Draft, DraftPlayer, Match, MatchResult, Round


def rotate_players(players: List[int]) -> List[int]:
    """
    Rotate players for round-robin tournament.
    First player stays fixed, others rotate clockwise.
    """
    if len(players) <= 1:
        return players
    return players[0:1] + [players[-1]] + players[1:-1]


def sort_to_inside(players: List[int]) -> List[int]:
    """
    Sort players to inside out pattern.
    Example: [1,2,3,4,5,6] -> [1,3,5,6,4,2]
    """
    return players[::2] + players[1::2][::-1]


async def calculate_points(draft: Draft, db: AsyncSession) -> None:
    """
    Calculate points for all players in a draft based on match results.
    Set final_place based on points and head-to-head matches.
    If points and head-to-head are equal, it's a tie.
    """
    # Load draft with all relationships
    stmt = (
        select(Draft)
        .options(
            selectinload(Draft.rounds).selectinload(Round.matches),
            selectinload(Draft.draft_players),
        )
        .filter(Draft.id == draft.id)
    )
    result = await db.execute(stmt)
    draft_with_relations: Draft | None = result.scalar()

    if not draft_with_relations:
        return

    # Initialize points for all players
    player_points: Dict[int, int] = {}
    for draft_player in draft_with_relations.draft_players:
        player_points[draft_player.player_id] = 0

    # Calculate points from all matches
    for round_obj in draft_with_relations.rounds:
        for match in round_obj.matches:
            if match.score in POINTS_MAP:
                player_1_points: int
                player_2_points: int
                player_1_points, player_2_points = POINTS_MAP[MatchResult(match.score)]

                if match.player_1_id in player_points:
                    player_points[match.player_1_id] += player_1_points
                if match.player_2_id in player_points:
                    player_points[match.player_2_id] += player_2_points

    # Update points in database
    for draft_player in draft_with_relations.draft_players:
        draft_player.points = player_points[draft_player.player_id]

    # Create head-to-head record for tiebreaking
    head_to_head: Dict[int, Dict[int, int]] = {}
    for round_obj in draft_with_relations.rounds:
        for match in round_obj.matches:
            if match.score in POINTS_MAP:
                p1_id: int = match.player_1_id
                p2_id: int = match.player_2_id

                # Initialize head-to-head records
                if p1_id not in head_to_head:
                    head_to_head[p1_id] = {}
                if p2_id not in head_to_head:
                    head_to_head[p2_id] = {}

                # Record head-to-head result
                p1_points: int
                p2_points: int
                p1_points, p2_points = POINTS_MAP[MatchResult(match.score)]

                if p2_id not in head_to_head[p1_id]:
                    head_to_head[p1_id][p2_id] = 0
                if p1_id not in head_to_head[p2_id]:
                    head_to_head[p2_id][p1_id] = 0

                head_to_head[p1_id][p2_id] += p1_points
                head_to_head[p2_id][p1_id] += p2_points

    # Sort players by points and resolve ties with head-to-head
    draft_players_list: List[DraftPlayer] = list(draft_with_relations.draft_players)

    def compare_players(p1: DraftPlayer, p2: DraftPlayer) -> int:
        """Compare two players for ranking. Return -1 if p1 > p2, 1 if p2 > p1, 0 if tie."""
        # First compare by points
        if p1.points != p2.points:
            return -1 if p1.points > p2.points else 1

        # If points are equal, check head-to-head
        p1_id: int = p1.player_id
        p2_id: int = p2.player_id
        if p1_id in head_to_head and p2_id in head_to_head[p1_id]:
            p1_h2h: int = head_to_head[p1_id].get(p2_id, 0)
            p2_h2h: int = head_to_head[p2_id].get(p1_id, 0)

            if p1_h2h != p2_h2h:
                return -1 if p1_h2h > p2_h2h else 1

        # If both points and head-to-head are equal, it's a tie
        return 0

    # Sort players using bubble sort with custom comparison to handle ties properly
    for i in range(len(draft_players_list)):
        for j in range(len(draft_players_list) - 1 - i):
            if compare_players(draft_players_list[j], draft_players_list[j + 1]) > 0:
                draft_players_list[j], draft_players_list[j + 1] = draft_players_list[j + 1], draft_players_list[j]

    # Assign final places, handling ties
    current_place: int = 1
    for i, player in enumerate(draft_players_list):
        if i > 0:
            prev_player: DraftPlayer = draft_players_list[i - 1]
            if compare_players(prev_player, player) != 0:
                # Not a tie, move to next place
                current_place = i + 1
            # If it's a tie, keep the same place

        player.final_place = current_place

    # Commit all changes
    await db.commit()


async def generate_matches(draft: Draft, db: AsyncSession) -> None:
    """Generate matches for a draft using a round-robin tournament algorithm."""
    # Get players sorted by order
    draft_players = sorted(draft.draft_players, key=lambda x: x.order or float("inf"))
    player_ids = [dp.player_id for dp in draft_players]

    # Calculate number of rounds needed
    num_players = len(player_ids)
    if num_players % 2 != 0:
        # Add a dummy player for bye if odd number of players
        player_ids.append(None)
        num_players += 1

    num_rounds = num_players - 1

    # Apply inside-out sorting for first round to get 1v2, 3v4 pairing
    sorted_players = sort_to_inside(player_ids.copy())

    for round_num in range(1, num_rounds + 1):
        # Create round
        db_round = Round(
            number=round_num,
            draft_id=draft.id,
        )
        db.add(db_round)
        await db.flush()  # Flush to get the round ID

        # Use sorted players for first round, regular rotation for subsequent rounds
        current_players = sorted_players if round_num == 1 else player_ids

        for i in range(num_players // 2):
            player1_id = current_players[i]
            player2_id = current_players[num_players - 1 - i]

            # Skip matches with dummy player (bye)
            if player1_id is not None and player2_id is not None:
                match = Match(
                    round_id=db_round.id,
                    player_1_id=player1_id,
                    player_2_id=player2_id,
                    score=MatchResult.BASE,
                )
                db.add(match)

        # Rotate players for next round (first player stays fixed)
        player_ids = rotate_players(player_ids)

    await db.commit()

    # Refresh the draft to get the rounds and matches with their IDs
    await db.refresh(draft)
