import type { Metadata } from "next";
import { Instrument_Serif, DM_Mono, Geist } from "next/font/google";
import "./globals.css";

const instrumentSerif = Instrument_Serif({
  subsets: ["latin"],
  weight: ["400"],
  style: ["normal", "italic"],
  variable: "--font-display",
});

const dmMono = DM_Mono({
  subsets: ["latin"],
  weight: ["300", "400", "500"],
  variable: "--font-mono",
});

const geistSans = Geist({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "SentinelX - Premium Fraud Intelligence Platform",
  description: "AI-Powered Banking Fraud Intelligence Operating System. Digital forensics and threat mapping.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${instrumentSerif.variable} ${dmMono.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-bg-base text-text-primary font-sans flex flex-col">
        {children}
      </body>
    </html>
  );
}
