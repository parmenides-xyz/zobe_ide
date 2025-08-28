import React from 'react';
import { ColorSchemeScript } from '@mantine/core';
import { Providers } from '../components/Providers/Providers';
import '@mantine/core/styles.css';
import './globals.css';
import '../styles/glassmorphic.css';

export const metadata = {
  title: 'Kurtosis - AI Prediction Markets',
  description: 'AI-powered futarchy on Sei blockchain',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <ColorSchemeScript />
        <link rel="icon" type="image/png" href="/bg-fire.png" />
        <link rel="shortcut icon" type="image/png" href="/bg-fire.png" />
        <link rel="apple-touch-icon" href="/bg-fire.png" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link 
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap" 
          rel="stylesheet" 
        />
        <meta
          name="viewport"
          content="minimum-scale=1, initial-scale=1, width=device-width, user-scalable=no"
        />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
