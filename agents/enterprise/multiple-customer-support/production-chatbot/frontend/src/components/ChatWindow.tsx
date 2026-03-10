/**
 * Chat window component with WebSocket integration.
 */

'use client';

import React, { useState, useEffect, useRef } from 'react';
import { WebSocketClient, Message } from '../lib/websocket-client';
import { MessageBubble } from './MessageBubble';

interface ChatWindowProps {
  wsUrl: string;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ wsUrl }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [streamingContent, setStreamingContent] = useState('');

  const wsClient = useRef<WebSocketClient | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  // Initialize WebSocket connection
  useEffect(() => {
    const client = new WebSocketClient(wsUrl);

    client.onConnect(() => {
      setIsConnected(true);
      setError(null);
    });

    client.onDisconnect(() => {
      setIsConnected(false);
    });

    client.onStreamChunk((chunk: string) => {
      setStreamingContent((prev) => prev + chunk);
    });

    client.onError((errorMessage: string) => {
      setError(errorMessage);
      setIsStreaming(false);
    });

    // Connect
    client.connect().catch((err) => {
      console.error('Failed to connect:', err);
      setError('Failed to connect to chat server');
    });

    wsClient.current = client;

    // Cleanup on unmount
    return () => {
      client.disconnect();
    };
  }, [wsUrl]);

  const handleSendMessage = () => {
    if (!inputMessage.trim() || !wsClient.current || !isConnected) {
      return;
    }

    // Add user message to UI
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setIsStreaming(true);
    setStreamingContent('');

    // Send to server
    wsClient.current.sendMessage(inputMessage);
  };

  // When streaming ends, add assistant message
  useEffect(() => {
    if (isStreaming && streamingContent.length > 0) {
      // Check if stream has ended (no new chunks for 500ms)
      const timer = setTimeout(() => {
        if (streamingContent.trim()) {
          const assistantMessage: Message = {
            id: Date.now().toString(),
            role: 'assistant',
            content: streamingContent,
            timestamp: new Date(),
          };

          setMessages((prev) => [...prev, assistantMessage]);
          setStreamingContent('');
          setIsStreaming(false);
        }
      }, 500);

      return () => clearTimeout(timer);
    }
  }, [streamingContent, isStreaming]);

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto bg-white shadow-lg">
      {/* Header */}
      <div className="bg-primary-600 text-white px-6 py-4">
        <h1 className="text-xl font-semibold">Insurance Customer Support</h1>
        <div className="flex items-center gap-2 mt-1">
          <div
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-300' : 'bg-red-300'
            }`}
          />
          <span className="text-sm">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 px-4 py-3">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg mb-2">Welcome to Insurance Support Chat</p>
            <p className="text-sm">
              Ask me anything about your insurance policy, claims, or coverage.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            role={message.role}
            content={message.content}
            timestamp={message.timestamp}
          />
        ))}

        {/* Streaming message */}
        {isStreaming && streamingContent && (
          <div className="flex justify-start mb-4">
            <div className="max-w-[70%] rounded-lg px-4 py-2 bg-gray-100 text-gray-900 border border-gray-200">
              <div className="flex items-start gap-2">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                  <svg
                    className="w-5 h-5 text-primary-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                    />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="text-sm whitespace-pre-wrap break-words">
                    {streamingContent}
                    <span className="animate-pulse">▊</span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 px-6 py-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={!isConnected || isStreaming}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            onClick={handleSendMessage}
            disabled={!isConnected || !inputMessage.trim() || isStreaming}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};
