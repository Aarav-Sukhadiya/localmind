const API_BASE = 'http://localhost:8000/api';
const WS_BASE = 'ws://localhost:8000/ws';

export interface Memory {
  id: number;
  content: string;
  category: string;
  created_at: string;
  updated_at: string;
}

export interface ContextSnapshot {
  messages: any[];
  total_tokens: number;
  max_tokens: number;
  usage_percent: number;
  per_message_tokens: any[];
}

export const api = {
  async getMemories(category?: string): Promise<Memory[]> {
    const url = category ? `${API_BASE}/memory?category=${category}` : `${API_BASE}/memory`;
    const res = await fetch(url);
    if (!res.ok) return [];
    return res.json();
  },

  async searchMemories(q: string): Promise<Memory[]> {
    const res = await fetch(`${API_BASE}/memory/search?q=${encodeURIComponent(q)}`);
    if (!res.ok) return [];
    return res.json();
  },

  async addMemory(content: string, category: string = 'general') {
    const res = await fetch(`${API_BASE}/memory`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, category })
    });
    return res.json();
  },

  async updateMemory(id: number, content: string) {
    const res = await fetch(`${API_BASE}/memory/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    });
    return res.json();
  },

  async deleteMemory(id: number) {
    const res = await fetch(`${API_BASE}/memory/${id}`, {
      method: 'DELETE'
    });
    return res.json();
  },

  async getContext(): Promise<ContextSnapshot | null> {
    const res = await fetch(`${API_BASE}/context`);
    if (!res.ok) return null;
    return res.json();
  },

  async clearConversation() {
    const res = await fetch(`${API_BASE}/conversations/clear`, {
      method: 'POST'
    });
    return res.json();
  }
};

export function createChatSocket(onMessage: (data: any) => void) {
  const ws = new WebSocket(`${WS_BASE}/chat`);
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (e) {
      console.error("Failed to parse websocket message", e);
    }
  };
  return ws;
}
