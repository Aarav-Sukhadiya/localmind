import { useState, useEffect, useRef } from 'react';
import { createChatSocket } from '../services/api';

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant' | 'system' | 'tool';
  text: string;
  isStreaming?: boolean;
  toolCall?: {
    name: string;
    arguments: any;
  };
  toolResult?: {
    output: string;
    error: string | null;
  };
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isConnecting, setIsConnecting] = useState(true);
  const [isThinking, setIsThinking] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    connect();
    return () => {
      socketRef.current?.close();
    };
  }, []);

  const connect = () => {
    const ws = createChatSocket((data) => {
      if (data.type === 'response_chunk') {
        setIsThinking(false);
        setMessages((prev) => {
          const newMessages = [...prev];
          const lastIndex = newMessages.length - 1;
          
          if (lastIndex >= 0 && newMessages[lastIndex].role === 'assistant' && newMessages[lastIndex].isStreaming) {
            newMessages[lastIndex].text += data.data.text;
          } else {
            newMessages.push({
              id: Date.now(),
              role: 'assistant',
              text: data.data.text,
              isStreaming: true
            });
          }
          return newMessages;
        });
      } else if (data.type === 'tool_call') {
        setIsThinking(false);
        setMessages((prev) => [
          ...prev, 
          {
            id: Date.now(),
            role: 'tool',
            text: `Executing ${data.data.name}...`,
            toolCall: { name: data.data.name, arguments: data.data.arguments }
          }
        ]);
      } else if (data.type === 'tool_result') {
        setMessages((prev) => {
          const newMessages = [...prev];
          const lastToolIndex = [...newMessages].reverse().findIndex(m => m.role === 'tool' && !m.toolResult);
          if (lastToolIndex !== -1) {
            const actualIndex = newMessages.length - 1 - lastToolIndex;
            newMessages[actualIndex].toolResult = {
              output: data.data.output,
              error: data.data.error
            };
          }
          return newMessages;
        });
      } else if (data.type === 'thinking') {
        setIsThinking(true);
      } else if (data.type === 'done') {
        setMessages((prev) => {
          const newMessages = [...prev];
          const lastIndex = newMessages.length - 1;
          if (lastIndex >= 0 && newMessages[lastIndex].isStreaming) {
            newMessages[lastIndex].isStreaming = false;
          }
          return newMessages;
        });
      }
    });

    ws.onopen = () => setIsConnecting(false);
    ws.onclose = () => {
      setIsConnecting(true);
      setTimeout(connect, 3000); // Reconnect
    };
    
    socketRef.current = ws;
  };

  const sendMessage = (text: string) => {
    if (!text.trim() || !socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) return;
    
    setMessages(prev => [...prev, { id: Date.now(), role: 'user', text }]);
    socketRef.current.send(JSON.stringify({ text }));
  };

  const clearChat = () => {
    setMessages([]);
  };

  return {
    messages,
    sendMessage,
    isConnecting,
    isThinking,
    clearChat
  };
}
