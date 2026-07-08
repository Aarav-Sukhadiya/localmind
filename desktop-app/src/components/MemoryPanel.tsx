import { useState, useEffect } from 'react';
import { Database, Search, Edit3, Trash2, Plus, Loader2 } from 'lucide-react';
import { api, type Memory } from '../services/api';

export default function MemoryPanel() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchMemories();
  }, []);

  const fetchMemories = async () => {
    setLoading(true);
    try {
      const data = await api.getMemories();
      setMemories(data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!search.trim()) {
      fetchMemories();
      return;
    }
    setLoading(true);
    try {
      const data = await api.searchMemories(search);
      setMemories(data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const handleDelete = async (id: number) => {
    await api.deleteMemory(id);
    setMemories(memories.filter(m => m.id !== id));
  };

  return (
    <div className="flex flex-col h-full bg-slate-800/20">
      <div className="h-12 border-b border-slate-700/50 flex items-center justify-between px-4">
        <h2 className="font-semibold text-slate-200 flex items-center gap-2">
          <Database size={18} className="text-purple-400" />
          Long-Term Memory
        </h2>
        <button 
          onClick={fetchMemories}
          className="p-1.5 bg-purple-500/20 text-purple-400 hover:bg-purple-500/30 rounded-lg transition-colors"
        >
          <Plus size={16} />
        </button>
      </div>

      <div className="p-4 border-b border-slate-700/50 bg-slate-900/30">
        <form onSubmit={handleSearch} className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input 
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search memories (Enter)"
            className="w-full bg-slate-800 border border-slate-600/50 rounded-lg pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 text-slate-200 shadow-inner"
          />
        </form>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {loading ? (
          <div className="flex justify-center p-8">
            <Loader2 size={24} className="animate-spin text-purple-500" />
          </div>
        ) : memories.length === 0 ? (
          <div className="text-center text-slate-500 p-8 text-sm">
            No memories found.
          </div>
        ) : (
          memories.map(mem => (
            <div key={mem.id} className="bg-slate-800/60 backdrop-blur-sm border border-slate-700/50 rounded-xl p-3 hover:bg-slate-700/80 transition-colors group shadow-md">
              <div className="flex justify-between items-start gap-4">
                <p className="text-sm text-slate-300 leading-relaxed break-words">
                  {mem.content}
                </p>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                  <button className="p-1 text-slate-400 hover:text-blue-400"><Edit3 size={14} /></button>
                  <button onClick={() => handleDelete(mem.id)} className="p-1 text-slate-400 hover:text-red-400"><Trash2 size={14} /></button>
                </div>
              </div>
              <div className="mt-3 flex justify-between items-center">
                <span className="inline-block px-2 py-0.5 rounded-md bg-purple-500/10 text-[10px] uppercase tracking-wider text-purple-400 border border-purple-500/20">
                  {mem.category}
                </span>
                <span className="text-[10px] text-slate-500">
                  {new Date(mem.updated_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
