// src/app/layout.tsx
import './globals.css'
import { Oswald } from 'next/font/google'

const oswald = Oswald({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-oswald",
});

export const metadata = {
  title: "SocialSentiment",
  description: "Analyze and visualize Social Media Sentiment",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`dark ${oswald.variable}`}>
      <body>{children}</body>
    </html>
  );
}