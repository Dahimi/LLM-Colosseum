import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Navigation } from "@/components/Navigation";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "LLM Colosseum - AI Competition Platform",
  description: "Watch and analyze competitions between different LLM models in various challenges.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="bg-gray-50">
      <body className={inter.className}>
        <Navigation />
        {children}
      </body>
    </html>
  );
}
