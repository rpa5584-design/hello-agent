"""Single local fictional profile; no clinical fields or model access."""
from datetime import datetime, timezone
from pathlib import Path
from .database import connect
from .models import ProfileUpdate


def get(path: Path) -> dict:
    with connect(path) as connection:
        return dict(connection.execute(
            "SELECT display_name,guidance_mode,updated_at FROM local_profile WHERE profile_id=1"
        ).fetchone())


def update(path: Path, request: ProfileUpdate) -> dict:
    with connect(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        if request.model_fields_set:
            # Fixed columns and bound values only; PATCH preserves omitted fields.
            connection.execute("""UPDATE local_profile SET
                display_name=CASE WHEN ? THEN ? ELSE display_name END,
                guidance_mode=CASE WHEN ? THEN ? ELSE guidance_mode END,
                updated_at=? WHERE profile_id=1""", (
                    'display_name' in request.model_fields_set, request.display_name,
                    'guidance_mode' in request.model_fields_set, request.guidance_mode,
                    datetime.now(timezone.utc).isoformat(),
                ))
        return dict(connection.execute(
            "SELECT display_name,guidance_mode,updated_at FROM local_profile WHERE profile_id=1"
        ).fetchone())
