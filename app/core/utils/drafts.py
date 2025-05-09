from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Draft, Match, MatchResult
from app.db.database import get_db


def rotate_players(players: list[int]) -> list[int]:
    """
    Rotate players for round-robin tournament.
    First player stays fixed, others rotate clockwise.
    """
    if len(players) <= 1:
        return players
    return players[0:1] + [players[-1]] + players[1:-1]


def sort_to_inside(players: list[int]) -> list[int]:
    """
    Sort players to inside out pattern.
    Example: [1,2,3,4,5,6] -> [1,3,5,6,4,2]
    """
    return players[::2] + players[1::2][::-1]


async def generate_matches(draft: Draft, db: AsyncSession = Depends(get_db)) -> list[Match]:
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
    matches = []

    for round_num in range(1, num_rounds + 1):
        for i in range(num_players // 2):
            player1_id = player_ids[i]
            player2_id = player_ids[num_players - 1 - i]

            # Skip matches with dummy player (bye)
            if player1_id is not None and player2_id is not None:
                match = Match(
                    draft_id=draft.id,
                    round=round_num,
                    player_1_id=player1_id,
                    player_2_id=player2_id,
                )
                db.add(match)
                matches.append(match)

        # Rotate players for next round (first player stays fixed)
        player_ids = rotate_players(player_ids)

    await db.commit()

    # Refresh the draft to get the matches with their IDs
    await db.refresh(draft)
    return draft.matches


async def calculate_final_places(draft: Draft, db: AsyncSession) -> None:
    """Calculate final places for players in a draft based on points and head-to-head results."""

    # Sort players by points in descending order
    sorted_players = sorted(draft.draft_players, key=lambda p: p.points, reverse=True)

    current_place = 1
    i = 0

    while i < len(sorted_players):
        # Find all players with the same number of points
        tied_players = [sorted_players[i]]
        j = i + 1
        while j < len(sorted_players) and sorted_players[j].points == sorted_players[i].points:
            tied_players.append(sorted_players[j])
            j += 1

        if len(tied_players) == 1:
            # No tie - assign place directly
            tied_players[0].final_place = current_place
            current_place += 1
        elif len(tied_players) == 2:
            # Two players tied - check head to head
            p1, p2 = tied_players
            # Find matches between these players
            head_to_head = next(
                (
                    m
                    for m in draft.matches
                    if (m.player_1_id == p1.player_id and m.player_2_id == p2.player_id)
                    or (m.player_1_id == p2.player_id and m.player_2_id == p1.player_id)
                    and m.score is not None
                ),
                None,
            )

            if head_to_head and head_to_head.score:
                # Determine winner based on match result
                if head_to_head.player_1_id == p1.player_id:
                    if head_to_head.score in (MatchResult.PLAYER_1_FULL_WIN, MatchResult.PLAYER_1_WIN):
                        p1.final_place = current_place
                        p2.final_place = current_place + 1
                    else:
                        p2.final_place = current_place
                        p1.final_place = current_place + 1
                else:  # head_to_head.player_1_id == p2.player_id
                    if head_to_head.score in (MatchResult.PLAYER_2_FULL_WIN, MatchResult.PLAYER_2_WIN):
                        p1.final_place = current_place
                        p2.final_place = current_place + 1
                    else:
                        p2.final_place = current_place
                        p1.final_place = current_place + 1
            else:
                # No head to head result or match not played - mark as tie
                p1.final_place = current_place
                p2.final_place = current_place
            current_place += len(tied_players)
        else:
            # Three or more players tied - all get same place
            for player in tied_players:
                player.final_place = current_place
            current_place += len(tied_players)

        i = j

    await db.commit()
