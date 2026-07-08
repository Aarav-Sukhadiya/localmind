import { useState, useRef, useEffect } from 'react';
import { Send, TerminalSquare, BrainCircuit, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useChat } from '../hooks/useChat';

export default function ChatPanel() {
  const { messages, sendMessage, isConnecting, isThinking } = useChat();
  const [input, setInput] = useState('');
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    sendMessage(input);
    setInput('');
  };

  return (
    <div className="flex flex-col h-full bg-slate-800/20">
      <div className="h-12 border-b border-slate-700/50 flex items-center justify-between px-4">
        <h2 className="font-semibold text-slate-200 flex items-center gap-2">
          <BrainCircuit size={18} className="text-blue-400" />
          Chat Session
        </h2>
        {isConnecting && (
          <span className="text-xs text-orange-400 flex items-center gap-1">
            <Loader2 size={12} className="animate-spin" /> Connecting...
          </span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-slate-500">
            <BrainCircuit size={48} className="mb-4 opacity-50" />
            <p>Welcome to LocalMind.</p>
            <p className="text-sm">Send a message to start.</p>
          </div>
        )}
        
        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div 
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-lg ${
                msg.role === 'user' ? 'bg-blue-600' : 
                msg.role === 'tool' ? 'bg-purple-600' : 'bg-slate-700'
              }`}>
                {msg.role === 'user' ? 'U' : msg.role === 'tool' ? 'T' : 'LM'}
              </div>
              
              <div className={`flex flex-col max-w-[85%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                {msg.role === 'tool' ? (
                  <div className="bg-slate-900/80 rounded-xl overflow-hidden border border-slate-700 w-full shadow-lg backdrop-blur-sm">
                    <div className="flex items-center gap-2 bg-slate-800/90 px-3 py-2 text-xs font-mono text-slate-300 border-b border-slate-700">
                      <TerminalSquare size={14} className="text-yellow-400" />
                      <span>{msg.text}</span>
                    </div>
                    {msg.toolResult && (
                      <div className="p-3 text-xs font-mono bg-black/50">
                        {msg.toolResult.error ? (
                          <div className="text-red-400 whitespace-pre-wrap">{msg.toolResult.error}</div>
                        ) : (
                          <div className="text-green-400 whitespace-pre-wrap">
                            {msg.toolResult.output.length > 500 
                              ? msg.toolResult.output.substring(0, 500) + '... (truncated)' 
                              : msg.toolResult.output}
                          </div>
                        )}
                      </div>
                    )}
                    {!msg.toolResult && (
                      <div className="p-3 text-xs font-mono text-slate-500 flex items-center gap-2">
                        <Loader2 size={12} className="animate-spin" /> Running...
                      </div>
                    )}
                  </div>
                ) : (
                  <div className={`p-3 rounded-2xl shadow-md ${
                    msg.role === 'user' 
                      ? 'bg-blue-600/90 text-white rounded-tr-sm backdrop-blur-sm' 
                      : 'bg-slate-700/80 text-slate-200 rounded-tl-sm border border-slate-600/50 backdrop-blur-sm'
                  }`}>
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                    {msg.isStreaming && (
                      <span className="inline-block w-1.5 h-3 ml-1 bg-blue-400 animate-pulse" />
                    )}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
          
          {isThinking && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex gap-4"
            >
               <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center shrink-0">
                <Loader2 size={16} className="text-slate-400 animate-spin" />
              </div>
              <div className="p-3 rounded-2xl bg-slate-800/50 text-slate-400 rounded-tl-sm border border-slate-700/50 flex items-center gap-2">
                <span className="text-sm italic">Thinking...</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={endOfMessagesRef} />
      </div>

      <div className="p-4 border-t border-slate-700/50 bg-slate-900/50 backdrop-blur-md">
        <form onSubmit={handleSend} className="relative max-w-4xl mx-auto">
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isConnecting}
            placeholder={isConnecting ? "Connecting to server..." : "Message LocalMind..."}
            className="w-full bg-slate-800/80 border border-slate-600/50 rounded-xl pl-4 pr-12 py-3.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-slate-200 placeholder-slate-500 shadow-inner"
          />
          <button 
            type="submit"
            disabled={isConnecting || !input.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-blue-500 hover:bg-blue-600 disabled:bg-slate-700 disabled:text-slate-500 rounded-lg transition-colors text-white shadow-lg"
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
