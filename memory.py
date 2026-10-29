"""
memory.py - Async SQLite storage with conversation history compaction.
"""
import aiosqlite
import json
from typing import List, Dict, Any

DB_PATH = "meal_planner_memory.db"

async def init_db() -> None:
    """Initializes persistent storage for chat history and family profiles."""
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
    """Asynchronously stores a conversational turn into SQLite."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO conversation_history (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content)
        )
        await db.commit()

async def get_history_async(session_id: str, limit: int = 20) -> List[Dict[str, str]]:
    """Retrieves conversation history asynchronously."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT role, content FROM conversation_history WHERE session_id = ? ORDER BY id ASC LIMIT ?",
            (session_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [{"role": r[0], "content": r[1]} for r in rows]

async def compact_history_async(session_id: str, threshold: int = 10) -> str:
    """
    Compacts older conversation turns into a consolidated summary 
    to conserve context window while retaining essential constraints.
    """
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
            (session_id, summary_text)
        )
        await db.commit()

    return summary_text
