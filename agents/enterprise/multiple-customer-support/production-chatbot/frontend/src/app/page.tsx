/**
 * Main chat page.
 */

'use client';

import { ChatWindow } from '@/components/ChatWindow';

export default function Home() {
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'wss://your-api-id.execute-api.us-east-1.amazonaws.com/dev';

  return (
    <main className="min-h-screen">
      <ChatWindow wsUrl={wsUrl} />
    </main>
  );
}
