import aiosqlite
from typing import Optional, List
from core.schemas import MemoryEntry

class LongTermMemory:
    def __init__(self, db_path: str = 'data/memory.db'):
        self.db_path = db_path
        self._conn = None

    async def initialize(self) -> None:
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        
        await self._conn.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await self._conn.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                content, category, content='memories', content_rowid='id'
            )
        ''')
        
        # Triggers to keep FTS in sync
        await self._conn.executescript('''
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, content, category) VALUES (new.id, new.content, new.category);
            END;
            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, content, category) VALUES('delete', old.id, old.content, old.category);
            END;
            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, content, category) VALUES('delete', old.id, old.content, old.category);
                INSERT INTO memories_fts(rowid, content, category) VALUES (new.id, new.content, new.category);
            END;
        ''')
        await self._conn.commit()

    async def save(self, content: str, category: str = 'general') -> int:
        cursor = await self._conn.execute(
            'INSERT INTO memories (content, category) VALUES (?, ?)',
            (content, category)
        )
        await self._conn.commit()
        return cursor.lastrowid

    async def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        cursor = await self._conn.execute('''
            SELECT m.id, m.content, m.category, m.created_at, m.updated_at
            FROM memories m
            JOIN memories_fts fts ON m.id = fts.rowid
            WHERE memories_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        ''', (query, limit))
        rows = await cursor.fetchall()
        return [MemoryEntry(**dict(row)) for row in rows]

    async def list_all(self, category: Optional[str] = None) -> List[MemoryEntry]:
        if category:
            cursor = await self._conn.execute('SELECT * FROM memories WHERE category = ? ORDER BY updated_at DESC', (category,))
        else:
            cursor = await self._conn.execute('SELECT * FROM memories ORDER BY updated_at DESC')
        rows = await cursor.fetchall()
        return [MemoryEntry(**dict(row)) for row in rows]

    async def get(self, memory_id: int) -> Optional[MemoryEntry]:
        cursor = await self._conn.execute('SELECT * FROM memories WHERE id = ?', (memory_id,))
        row = await cursor.fetchone()
        return MemoryEntry(**dict(row)) if row else None

    async def update(self, memory_id: int, content: str) -> bool:
        cursor = await self._conn.execute(
            "UPDATE memories SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (content, memory_id)
        )
        await self._conn.commit()
        return cursor.rowcount > 0

    async def delete(self, memory_id: int) -> bool:
        cursor = await self._conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        await self._conn.commit()
        return cursor.rowcount > 0

    async def get_relevant_context(self, query: str, limit: int = 3) -> str:
        if not query.strip():
            return "No relevant memories."
        # Simple extraction of keywords for FTS match
        keywords = " OR ".join(query.split()[:5]) 
        try:
            memories = await self.search(keywords, limit)
            if not memories:
                return "No relevant memories found."
            return "\n".join([f"- {m.content}" for m in memories])
        except Exception:
            return "No relevant memories found."

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
