from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.models import Draft, Match
from app.db.database import get_db


def generate_matches(draft: Draft, db: Session = Depends(get_db)) -> None:
    # Get draft players ordered by their order field
    draft_players = sorted(draft.draft_players, key=lambda x: x.order or float("inf"))
    players_count = len(draft_players)

    if players_count < 2:
        return

    # First round - pair players 1v2, 3v4, etc.
    round_num = 1
    for i in range(0, players_count - 1, 2):
        if i + 1 < players_count:
            match = Match(
                round=round_num,
                player_1_id=draft_players[i].player_id,
                player_2_id=draft_players[i + 1].player_id,
                draft_id=draft.id,
            )
            db.add(match)

    # Generate remaining rounds using circle method
    # Create list of player IDs excluding the first player
    player_ids = [dp.player_id for dp in draft_players]
    first_player = player_ids[0]
    rotating_players = player_ids[1:]

    for round_num in range(2, players_count):
        # Rotate players clockwise
        rotating_players = [rotating_players[-1]] + rotating_players[:-1]

        # Create matches for this round
        mid = len(rotating_players) // 2
        for i in range(mid):
            if i == 0:
                # First player vs first rotating player
                match = Match(
                    round=round_num,
                    player_1_id=first_player,
                    player_2_id=rotating_players[0],
                    draft_id=draft.id,
                )
                db.add(match)
            else:
                # Match other pairs
                match = Match(
                    round=round_num,
                    player_1_id=rotating_players[i],
                    player_2_id=rotating_players[-(i + 1)],
                    draft_id=draft.id,
                )
                db.add(match)

    db.commit()
