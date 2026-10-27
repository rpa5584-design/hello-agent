"""Bounded conversation writes, with a lease to serialize provider attempts."""
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import time
from .database import connect
from .reflection_provider import safe_text


class ConversationError(Exception):
    def __init__(self, status: int, message: str) -> None:
        self.status, self.message = status, message


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def load(path: Path, session_id: str) -> list[dict]:
    with connect(path) as connection:
        if not connection.execute("SELECT 1 FROM sessions WHERE session_id=?", (session_id,)).fetchone():
            raise ConversationError(404, "Session not found.")
        return [{**dict(row), "content": safe_text(row['content'])} for row in connection.execute(
            "SELECT * FROM conversation_messages WHERE session_id=? ORDER BY message_id LIMIT 5", (session_id,))]


def reserve(path: Path, session_id: str, reflection: str) -> tuple[dict, str | None]:
    content = safe_text(reflection)[:300]
    with connect(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        session = connection.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        if session is None:
            raise ConversationError(404, "Session not found.")
        if session['status'] not in ('completed', 'stopped'):
            raise ConversationError(409, "Reflection is available after a completed or stopped session.")
        user = connection.execute("SELECT content FROM conversation_messages WHERE session_id=? AND role='user'", (session_id,)).fetchone()
        if user and safe_text(user['content']) != content:
            raise ConversationError(409, "This session already has a reflection. Retry the same reflection or view Saved History.")
        request = connection.execute("SELECT * FROM reflection_requests WHERE session_id=?", (session_id,)).fetchone()
        if request and request['status'] == 'success':
            return dict(session), None
        if request and request['status'] == 'pending' and request['lease_until'] > time.time():
            raise ConversationError(409, "A reflection request is still pending. Wait before retrying.")
        if request and request['attempts'] >= 3:
            raise ConversationError(409, "This session has reached its three-attempt reflection limit.")
        if not user:
            connection.execute("INSERT INTO conversation_messages(session_id,timestamp,role,content) VALUES (?,?,'user',?)", (session_id, timestamp(), content))
        elif request and request['status'] == 'pending':
            connection.execute("INSERT INTO conversation_messages(session_id,timestamp,role,content) VALUES (?,?,'error',?)", (session_id, timestamp(), "The previous reflection request was interrupted; no saved answer is available."))
        token = str(uuid4())
        connection.execute("""INSERT INTO reflection_requests(session_id,attempts,status,token,lease_until)
            VALUES (?,1,'pending',?,?) ON CONFLICT(session_id) DO UPDATE SET
            attempts=attempts+1,status='pending',token=excluded.token,lease_until=excluded.lease_until""", (session_id, token, time.time() + 45))
        context = {key: session[key] for key in ('selected_skill', 'status', 'measured_duration_seconds', 'fewer_options')}
        context['fewer_options'] = bool(context['fewer_options'])
        context['reflection'] = content
        # No earlier turns are needed for the single-exchange use case.
        return context, token


def finish(path: Path, session_id: str, token: str, content: str, success: bool) -> None:
    with connect(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        request = connection.execute("SELECT token,status FROM reflection_requests WHERE session_id=?", (session_id,)).fetchone()
        if request is None or request['token'] != token or request['status'] != 'pending':
            raise ConversationError(409, "This reflection request is no longer current. Reload Saved History.")
        connection.execute("INSERT INTO conversation_messages(session_id,timestamp,role,content) VALUES (?,?,?,?)", (session_id, timestamp(), 'assistant' if success else 'error', content))
        connection.execute("UPDATE reflection_requests SET status=? WHERE session_id=?", ('success' if success else 'error', session_id))
