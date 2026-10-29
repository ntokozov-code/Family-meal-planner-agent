"""
memory.py - Async SQLite storage with PII sanitization and history compaction.
"""
import aiosqlite
from typing import List, Dict
from observability import redact_pii

DB_PATH = "meal_planner_memory.db"

async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS memory_summaries (
                session_id TEXT PRIMARY KEY,
                summary TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def save_message_async(session_id: str, role: str, content: str) -> None:
    """Asynchronously stores conversation turn with strict PII sanitization prior to database write."""
    sanitized_content = redact_pii(content) # Enforces PII redaction in storage pipeline
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO conversation_history (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, sanitized_content)
        )
        await db.commit()

async def get_history_async(session_id: str, limit: int = 20) -> List[Dict[str, str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT role, content FROM conversation_history WHERE session_id = ? ORDER BY id ASC LIMIT ?",
            (session_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [{"role": r[0], "content": r[1]} for r in rows]

async def compact_history_async(session_id: str, threshold: int = 10) -> str:
    history = await get_history_async(session_id, limit=100)
    if len(history) <= threshold:
        return ""
    older_turns = history[:-threshold]
    summary_text = "Compacted Past History: " + " | ".join(
        [f"{m['role']}: {m['content'][:80]}..." for m in older_turns]
    )
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO memory_summaries (session_id, summary) VALUES (?, ?)",
            (session_id, redact_pii(summary_text))
        )
        await db.commit()
    return summary_text
