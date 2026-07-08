import React, { useState } from 'react';
import { MessageSquare, Database, Cpu, Settings, Trash2 } from 'lucide-react';
import ChatPanel from './components/ChatPanel';
import MemoryPanel from './components/MemoryPanel';
import ContextPanel from './components/ContextPanel';

function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'memory' | 'context'>('chat');

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-900 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-800 via-slate-900 to-black text-slate-200">
      {/* Header */}
      <header className="h-14 flex items-center justify-between px-6 border-b border-slate-700/50 bg-slate-900/50 backdrop-blur-sm z-10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center font-bold text-white shadow-[0_0_15px_rgba(59,130,246,0.5)]">
            LM
          </div>
          <h1 className="text-lg font-semibold tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-300">
            LocalMind
          </h1>
        </div>
        
        <div className="flex items-center gap-4">
          <button className="p-2 hover:bg-slate-800 rounded-full transition-colors text-slate-400 hover:text-white" title="Clear Conversation">
            <Trash2 size={18} />
          </button>
          <button className="p-2 hover:bg-slate-800 rounded-full transition-colors text-slate-400 hover:text-white" title="Settings">
            <Settings size={18} />
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex overflow-hidden p-4 gap-4">
        
        {/* Sidebar Navigation (Desktop) */}
        <div className="w-16 flex flex-col items-center py-4 gap-6 glass-panel">
          <NavButton 
            active={activeTab === 'chat'} 
            onClick={() => setActiveTab('chat')} 
            icon={<MessageSquare size={22} />} 
            label="Chat" 
          />
          <NavButton 
            active={activeTab === 'memory'} 
            onClick={() => setActiveTab('memory')} 
            icon={<Database size={22} />} 
            label="Memory" 
          />
          <NavButton 
            active={activeTab === 'context'} 
            onClick={() => setActiveTab('context')} 
            icon={<Cpu size={22} />} 
            label="Context" 
          />
        </div>

        {/* Dynamic Panel Area */}
        <div className="flex-1 flex gap-4 h-full">
          {/* Chat Panel - Always visible on desktop, or managed by tabs on smaller screens */}
          <div className={`flex-1 glass-panel flex flex-col ${activeTab !== 'chat' && 'hidden md:flex'}`}>
            <ChatPanel />
          </div>

          {/* Secondary Panel - Context or Memory */}
          <div className={`w-[400px] glass-panel flex flex-col ${activeTab === 'chat' ? 'hidden lg:flex' : 'flex'}`}>
            {activeTab === 'memory' ? <MemoryPanel /> : <ContextPanel />}
          </div>
        </div>

      </main>

      {/* Status Bar */}
      <footer className="h-8 border-t border-slate-700/50 bg-slate-900/80 px-4 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.8)] animate-pulse"></div>
          <span>Connected to llama.cpp</span>
        </div>
        <div className="flex items-center gap-4">
          <span>Model: Qwen3-8B</span>
          <span>Tools: 6 Active</span>
        </div>
      </footer>
    </div>
  );
}

function NavButton({ active, onClick, icon, label }: { active: boolean, onClick: () => void, icon: React.ReactNode, label: string }) {
  return (
    <button 
      onClick={onClick}
      className={`relative p-3 rounded-xl transition-all duration-300 group ${active ? 'bg-blue-500/20 text-blue-400' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'}`}
      title={label}
    >
      {icon}
      {active && (
        <span className="absolute inset-0 rounded-xl border border-blue-500/50 shadow-[0_0_10px_rgba(59,130,246,0.2)]"></span>
      )}
    </button>
  );
}

export default App;
