import type { Metadata } from "next";
import { Instrument_Serif, JetBrains_Mono, Geist } from "next/font/google";
import "./globals.css";

const instrumentSerif = Instrument_Serif({
  subsets: ["latin"],
  weight: ["400"],
  style: ["normal", "italic"],
  variable: "--font-display",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-mono",
});

const geistSans = Geist({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "Lumint — AI-Powered Fraud Intelligence Platform",
  description:
    "Illuminate the threat. Before it strikes. Lumint is a unified multimodal fraud intelligence platform for India's digital payment ecosystem — detecting fraud across documents, URLs, UPI screenshots, and fraud campaign networks.",
  keywords: [
    "fraud detection",
    "AI",
    "UPI fraud",
    "phishing",
    "document forensics",
    "India",
    "fintech",
  ],
  authors: [{ name: "Lumint Research" }],
  openGraph: {
    title: "Lumint — AI Fraud Intelligence",
    description: "Illuminate the threat. Before it strikes.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${instrumentSerif.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-canvas text-text-primary font-sans flex flex-col">
        {children}
      </body>
    </html>
  );
}
