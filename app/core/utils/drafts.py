from collections import defaultdict
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


async def populate_draft(draft: Draft, db: AsyncSession) -> Draft:
    """
    Populate a draft with rounds and matches using round-robin tournament algorithm.
    This is the main function that combines round generation and match generation.
    """
    # Get players sorted by order
    draft_players = sorted(draft.draft_players, key=lambda x: x.order or float("inf"))
    player_ids = [dp.player_id for dp in draft_players]

    if len(player_ids) % 2 != 0:
        # Add a dummy player for bye if odd number of players
        player_ids.append(None)

    rounds = await generate_rounds(draft, player_ids, db)
    await generate_matches(rounds, player_ids, db)

    await db.commit()
    await db.refresh(draft)

    return draft


async def generate_rounds(draft: Draft, player_ids: List[int], db: AsyncSession) -> List[Round]:
    num_players = len(player_ids)

    if num_players < 2:
        return []
    # Calculate number of rounds needed
    num_rounds = num_players - 1

    rounds: List[Round] = []
    for round_num in range(1, num_rounds + 1):
        db_round = Round(
            number=round_num,
            draft_id=draft.id,
        )
        db.add(db_round)
        rounds.append(db_round)

    await db.flush()  # Flush to get the round IDs
    return rounds


async def generate_matches(rounds: List[Round], player_ids: List[int], db: AsyncSession) -> List[Match]:
    num_players = len(player_ids)
    all_matches: List[Match] = []
    sorted_player_ids = sort_to_inside(player_ids)

    for db_round in rounds:
        for i in range(num_players // 2):
            player1_id = sorted_player_ids[i]
            player2_id = sorted_player_ids[num_players - 1 - i]

            # Skip matches with dummy player (bye)
            if player1_id is not None and player2_id is not None:
                match = Match(
                    round_id=db_round.id,
                    player_1_id=player1_id,
                    player_2_id=player2_id,
                    score=MatchResult.BASE,
                )
                db.add(match)
                all_matches.append(match)

        # Rotate players for next round (first player stays fixed)
        sorted_player_ids = rotate_players(sorted_player_ids)

    return all_matches


def get_points_dict(draft: Draft) -> Dict[int, int]:
    player_points: Dict[int, int] = defaultdict(int)
    for round_obj in draft.rounds:
        for match in round_obj.matches:
            player_1_points, player_2_points = POINTS_MAP[MatchResult(match.score)]

            player_points[match.player_1_id] += player_1_points
            player_points[match.player_2_id] += player_2_points

    return player_points


async def calculate_points(draft: Draft, db: AsyncSession) -> None:
    """
    Calculate points for all players in a draft based on match results.
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

    player_points: Dict[int, int] = get_points_dict(draft_with_relations)

    # Update each draft player's points
    for draft_player in draft.draft_players:
        draft_player.points = player_points.get(draft_player.player_id, 0)

    # Sort players by points (descending), then handle ties
    sorted_players = sorted(draft.draft_players, key=lambda x: x.points, reverse=True)

    # Group players by points to handle ties
    groups = []
    current_group = []
    current_points = None

    for player in sorted_players:
        if current_points is None or player.points == current_points:
            current_group.append(player)
            current_points = player.points
        else:
            groups.append(current_group)
            current_group = [player]
            current_points = player.points

    if current_group:
        groups.append(current_group)

    # Assign final places, handling ties with head-to-head
    current_place = 1
    for group in groups:
        if len(group) == 1:
            # No tie, assign place directly
            group[0].final_place = current_place
            current_place += 1
        else:
            # Handle tie with head-to-head - may result in sub-groups
            ranked_subgroups = resolve_ties_with_head_to_head(group, draft)
            for subgroup in ranked_subgroups:
                # All players in a subgroup get the same place (truly tied)
                for player in subgroup:
                    player.final_place = current_place
                current_place += len(subgroup)

    await db.commit()


def resolve_ties_with_head_to_head(tied_players: List[DraftPlayer], draft: Draft) -> List[List[DraftPlayer]]:
    """
    Resolve ties between players using head-to-head results.
    Returns a list of player groups, ordered by head-to-head record.
    Players within the same group are still tied after head-to-head.
    """
    if len(tied_players) <= 1:
        return [tied_players]

    # Create head-to-head win matrix
    player_ids = [p.player_id for p in tied_players]
    h2h_wins = {pid: 0 for pid in player_ids}

    # Count head-to-head wins between tied players
    for round_obj in draft.rounds:
        for match in round_obj.matches:
            if match.player_1_id in player_ids and match.player_2_id in player_ids:
                match_result = MatchResult(match.score)
                player_1_points, player_2_points = POINTS_MAP[match_result]

                # Only count wins (3 points), not partial wins (1 point)
                if player_1_points == 3:
                    h2h_wins[match.player_1_id] += 1
                elif player_2_points == 3:
                    h2h_wins[match.player_2_id] += 1

    # Group players by their head-to-head win count
    h2h_groups: Dict[int, List[DraftPlayer]] = {}
    for player in tied_players:
        wins = h2h_wins[player.player_id]
        if wins not in h2h_groups:
            h2h_groups[wins] = []
        h2h_groups[wins].append(player)

    # Return groups ordered by head-to-head wins (descending)
    grouped_result = []
    for wins in sorted(h2h_groups.keys(), reverse=True):
        grouped_result.append(h2h_groups[wins])

    return grouped_result
