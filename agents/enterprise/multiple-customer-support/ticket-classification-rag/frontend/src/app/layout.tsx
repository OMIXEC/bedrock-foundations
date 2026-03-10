import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'CloudSync Pro Support',
  description: 'AI-powered customer support for CloudSync Pro',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
