import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';
import { vi } from 'vitest';

vi.mock('./hooks/useChat', () => ({
  useChat: () => ({ messages: [], sendMessage: vi.fn(), isConnecting: false, isThinking: false, clearChat: vi.fn() })
}));

vi.mock('./services/api', () => ({
  api: { 
    getMemories: vi.fn().mockResolvedValue([]), 
    getContext: vi.fn().mockResolvedValue(null) 
  },
  createChatSocket: vi.fn()
}));

test('renders app header and tabs', async () => {
  render(<App />);
  expect(screen.getByText('LocalMind')).toBeInTheDocument();
  expect(screen.getByTitle('Chat')).toBeInTheDocument();
  expect(screen.getByTitle('Memory')).toBeInTheDocument();
  expect(screen.getByTitle('Context')).toBeInTheDocument();
});

test('switches tabs', async () => {
  render(<App />);
  const memoryTab = screen.getByTitle('Memory');
  fireEvent.click(memoryTab);
  expect(await screen.findByText('Long-Term Memory')).toBeInTheDocument();
  
  const contextTab = screen.getByTitle('Context');
  fireEvent.click(contextTab);
  expect(await screen.findByText('Loading context window...')).toBeInTheDocument();
});
