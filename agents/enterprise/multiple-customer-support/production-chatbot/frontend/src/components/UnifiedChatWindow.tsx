/**
 * Unified chat window supporting both WebSocket (streaming) and REST (polling) modes.
 */

'use client';

import React, { useState, useEffect, useRef } from 'react';
import { WebSocketClient, Message } from '../lib/websocket-client';
import { RestChatClient } from '../lib/rest-client';
import { MessageBubble } from './MessageBubble';

type ConnectionMode = 'websocket' | 'rest';

interface UnifiedChatWindowProps {
  wsUrl?: string;
  restUrl?: string;
  mode?: ConnectionMode;
}

export const UnifiedChatWindow: React.FC<UnifiedChatWindowProps> = ({
  wsUrl,
  restUrl,
  mode = 'websocket',
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [streamingContent, setStreamingContent] = useState('');
  const [currentMode, setCurrentMode] = useState<ConnectionMode>(mode);

  const wsClient = useRef<WebSocketClient | null>(null);
  const restClient = useRef<RestChatClient | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  // Initialize clients
  useEffect(() => {
    if (currentMode === 'websocket' && wsUrl) {
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
        setIsProcessing(false);
      });

      client.connect().catch((err) => {
        console.error('WebSocket connection failed:', err);
        setError('WebSocket connection failed');
      });

      wsClient.current = client;

      return () => {
        client.disconnect();
      };
    } else if (currentMode === 'rest' && restUrl) {
      restClient.current = new RestChatClient(restUrl);
      setIsConnected(true);
    }
  }, [currentMode, wsUrl, restUrl]);

  const handleSendMessageWebSocket = () => {
    if (!inputMessage.trim() || !wsClient.current || !isConnected) {
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setIsProcessing(true);
    setStreamingContent('');

    wsClient.current.sendMessage(inputMessage);
  };

  const handleSendMessageRest = async () => {
    if (!inputMessage.trim() || !restClient.current) {
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setIsProcessing(true);
    setError(null);

    try {
      const response = await restClient.current.sendMessage(inputMessage);

      const assistantMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSendMessage = () => {
    if (currentMode === 'websocket') {
      handleSendMessageWebSocket();
    } else {
      handleSendMessageRest();
    }
  };

  // Handle streaming completion for WebSocket
  useEffect(() => {
    if (currentMode === 'websocket' && isProcessing && streamingContent.length > 0) {
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
          setIsProcessing(false);
        }
      }, 500);

      return () => clearTimeout(timer);
    }
  }, [streamingContent, isProcessing, currentMode]);

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleMode = () => {
    const newMode = currentMode === 'websocket' ? 'rest' : 'websocket';
    setCurrentMode(newMode);
    setMessages([]);
    setStreamingContent('');
    setIsProcessing(false);
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto bg-white shadow-lg">
      {/* Header */}
      <div className="bg-primary-600 text-white px-6 py-4">
        <div className="flex justify-between items-center">
          <h1 className="text-xl font-semibold">Insurance Customer Support</h1>
          <button
            onClick={toggleMode}
            className="px-3 py-1 text-sm bg-white/20 hover:bg-white/30 rounded transition-colors"
          >
            Mode: {currentMode === 'websocket' ? '⚡ Streaming' : '📡 REST'}
          </button>
        </div>
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
            <p className="text-xs mt-2 text-gray-400">
              Using {currentMode === 'websocket' ? 'WebSocket streaming' : 'REST API'}
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

        {/* Streaming message (WebSocket only) */}
        {currentMode === 'websocket' && isProcessing && streamingContent && (
          <div className="flex justify-start mb-4">
            <div className="max-w-[70%] rounded-lg px-4 py-2 bg-gray-100 text-gray-900 border border-gray-200">
              <p className="text-sm whitespace-pre-wrap break-words">
                {streamingContent}
                <span className="animate-pulse">▊</span>
              </p>
            </div>
          </div>
        )}

        {/* Processing indicator (REST only) */}
        {currentMode === 'rest' && isProcessing && (
          <div className="flex justify-start mb-4">
            <div className="max-w-[70%] rounded-lg px-4 py-2 bg-gray-100 text-gray-900 border border-gray-200">
              <p className="text-sm text-gray-500">Processing...</p>
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
            disabled={!isConnected || isProcessing}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            onClick={handleSendMessage}
            disabled={!isConnected || !inputMessage.trim() || isProcessing}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};
