import { useState, useEffect } from 'react';
import { Cpu, AlertTriangle, RefreshCw } from 'lucide-react';
import { api, type ContextSnapshot } from '../services/api';

export default function ContextPanel() {
  const [snapshot, setSnapshot] = useState<ContextSnapshot | null>(null);

  const fetchContext = async () => {
    const data = await api.getContext();
    if (data) setSnapshot(data);
  };

  // Poll for context updates (simple implementation)
  useEffect(() => {
    fetchContext();
    const interval = setInterval(fetchContext, 2000);
    return () => clearInterval(interval);
  }, []);

  if (!snapshot) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-slate-500">
        <RefreshCw className="animate-spin mb-2" />
        <p>Loading context window...</p>
      </div>
    );
  }

  const { max_tokens, total_tokens, usage_percent, per_message_tokens } = snapshot;

  return (
    <div className="flex flex-col h-full bg-slate-800/20">
      <div className="h-12 border-b border-slate-700/50 flex items-center px-4">
        <h2 className="font-semibold text-slate-200 flex items-center gap-2">
          <Cpu size={18} className="text-emerald-400" />
          Context Window
        </h2>
      </div>

      <div className="p-6 border-b border-slate-700/50 flex flex-col gap-4 bg-slate-900/40">
        <div className="flex justify-between items-end">
          <div>
            <p className="text-xs text-slate-400 uppercase tracking-wider mb-1 font-semibold">Token Usage</p>
            <p className="text-3xl font-light text-slate-200 tracking-tight">
              {total_tokens.toLocaleString()} <span className="text-sm text-slate-500 font-normal">/ {max_tokens.toLocaleString()}</span>
            </p>
          </div>
          <span className={`text-xl font-bold ${usage_percent > 80 ? 'text-orange-400' : 'text-emerald-400'}`}>
            {usage_percent.toFixed(1)}%
          </span>
        </div>

        {/* Progress Bar */}
        <div className="h-4 w-full bg-slate-800/80 rounded-full overflow-hidden border border-slate-700 shadow-inner">
          <div 
            className={`h-full transition-all duration-500 ${usage_percent > 80 ? 'bg-orange-500' : 'bg-gradient-to-r from-emerald-600 to-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.5)]'}`}
            style={{ width: `${usage_percent}%` }}
          />
        </div>
        
        {usage_percent > 80 && (
          <div className="flex items-start gap-2 mt-2 text-orange-400/90 bg-orange-500/10 p-3 rounded-xl border border-orange-500/20 shadow-lg">
            <AlertTriangle size={18} className="shrink-0 mt-0.5" />
            <p className="text-sm leading-relaxed">
              Context is getting full. Older messages will be pruned automatically during the next turn.
            </p>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 px-2">Message Breakdown</h3>
        <div className="space-y-2">
          {per_message_tokens.map((msg, idx) => (
            <div key={idx} className="flex items-center justify-between p-3 bg-slate-800/60 backdrop-blur-sm border border-slate-700/50 rounded-xl shadow-sm hover:border-slate-600 transition-colors">
              <div className="flex items-center gap-3 w-[70%]">
                <span className={`w-2.5 h-2.5 rounded-full shadow-md ${
                  msg.role === 'system' ? 'bg-purple-500' :
                  msg.role === 'user' ? 'bg-blue-500' :
                  msg.role === 'assistant' ? 'bg-emerald-500' : 'bg-yellow-500'
                }`} />
                <span className="text-sm font-medium text-slate-300 capitalize">{msg.role}</span>
                <span className="text-xs text-slate-500 truncate" title={msg.preview}>{msg.preview}</span>
              </div>
              <span className="text-xs font-mono text-slate-300 bg-slate-900/80 border border-slate-700 px-2.5 py-1 rounded-md shadow-inner">
                {msg.tokens} tkns
              </span>
            </div>
          ))}
          {per_message_tokens.length === 0 && (
            <div className="text-center text-slate-500 text-sm p-4">
              Context is empty.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
