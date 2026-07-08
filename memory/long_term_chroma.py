import os
import asyncio
from typing import Optional, List
from datetime import datetime, timezone
import chromadb
from chromadb.config import Settings
from core.schemas import MemoryEntry
import logging

logger = logging.getLogger(__name__)

class LongTermMemoryChroma:
    def __init__(self, db_path: str = 'data/chroma_db'):
        self.db_path = db_path
        self._client = None
        self._collection = None

    async def initialize(self) -> None:
        def _init():
            os.makedirs(self.db_path, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.db_path, settings=Settings(anonymized_telemetry=False))
            self._collection = self._client.get_or_create_collection(name="localmind_memories")
        await asyncio.to_thread(_init)

    async def save(self, content: str, category: str = 'general') -> int:
        def _save():
            count = self._collection.count()
            new_id = count + 1
            now_iso = datetime.now(timezone.utc).isoformat()
            
            self._collection.add(
                documents=[content],
                metadatas=[{"category": category, "int_id": new_id, "created_at": now_iso, "updated_at": now_iso}],
                ids=[str(new_id)]
            )
            return new_id
            
        return await asyncio.to_thread(_save)

    async def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        def _search():
            if self._collection.count() == 0:
                return []
            # Chroma query will error if collection is empty or n_results > count sometimes
            actual_limit = min(limit, self._collection.count())
            if actual_limit == 0: return []
            
            results = self._collection.query(
                query_texts=[query],
                n_results=actual_limit
            )
            entries = []
            if results and results.get('documents') and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    doc = results['documents'][0][i]
                    meta = results['metadatas'][0][i]
                    created = meta.get('created_at', None)
                    updated = meta.get('updated_at', None)
                    
                    entries.append(MemoryEntry(
                        id=meta.get('int_id', int(results['ids'][0][i])),
                        content=doc,
                        category=meta.get('category', 'general'),
                        created_at=created if created else datetime.now().isoformat(),
                        updated_at=updated if updated else datetime.now().isoformat()
                    ))
            return entries
        return await asyncio.to_thread(_search)

    async def list_all(self, category: Optional[str] = None) -> List[MemoryEntry]:
        def _list():
            where = {"category": category} if category else None
            results = self._collection.get(where=where)
            entries = []
            if results and results.get('documents'):
                for i in range(len(results['documents'])):
                    doc = results['documents'][i]
                    meta = results['metadatas'][i]
                    created = meta.get('created_at', None)
                    updated = meta.get('updated_at', None)
                    entries.append(MemoryEntry(
                        id=meta.get('int_id', int(results['ids'][i])),
                        content=doc,
                        category=meta.get('category', 'general'),
                        created_at=created if created else datetime.now().isoformat(),
                        updated_at=updated if updated else datetime.now().isoformat()
                    ))
            return sorted(entries, key=lambda x: getattr(x, 'updated_at', datetime.now()), reverse=True)
        return await asyncio.to_thread(_list)

    async def get(self, memory_id: int) -> Optional[MemoryEntry]:
        def _get():
            results = self._collection.get(ids=[str(memory_id)])
            if results and results.get('documents') and len(results['documents']) > 0:
                doc = results['documents'][0]
                meta = results['metadatas'][0]
                created = meta.get('created_at', None)
                updated = meta.get('updated_at', None)
                return MemoryEntry(
                    id=meta.get('int_id', int(results['ids'][0])),
                    content=doc,
                    category=meta.get('category', 'general'),
                    created_at=created if created else datetime.now().isoformat(),
                    updated_at=updated if updated else datetime.now().isoformat()
                )
            return None
        return await asyncio.to_thread(_get)

    async def update(self, memory_id: int, content: str) -> bool:
        def _update():
            res = self._collection.get(ids=[str(memory_id)])
            if not res or not res.get('documents'):
                return False
            meta = res['metadatas'][0]
            meta['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            self._collection.update(
                ids=[str(memory_id)],
                documents=[content],
                metadatas=[meta]
            )
            return True
        return await asyncio.to_thread(_update)

    async def delete(self, memory_id: int) -> bool:
        def _delete():
            res = self._collection.get(ids=[str(memory_id)])
            if not res or not res.get('documents'):
                return False
            self._collection.delete(ids=[str(memory_id)])
            return True
        return await asyncio.to_thread(_delete)

    async def get_relevant_context(self, query: str, limit: int = 3) -> str:
        if not query.strip():
            return "No relevant memories."
        try:
            memories = await self.search(query, limit)
            if not memories:
                return "No relevant memories found."
            return "\n".join([f"- {m.content}" for m in memories])
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return "No relevant memories found."

    async def close(self) -> None:
        pass
