import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ChatProvider } from "@/lib/context/chat-context";
import { ThemeProvider } from "@/lib/context/theme-context";
import { SettingsProvider } from "@/lib/context/settings-context";
import { ToastProvider } from "@/lib/context/toast-context"; // Import ToastProvider

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TcyberChatbot - Local First AI Assistant",
  description: "A comprehensive multi-modal chatbot with local AI processing. Upload documents, ask questions, get RAG-enhanced answers with citations.",
  keywords: "AI chatbot, local AI, RAG, document analysis, multimodal chat, privacy-focused",
  authors: [{ name: "TcyberChatbot Team" }],
  icons: {
    icon: "/favicon.ico",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning={true}>
      <body
        suppressHydrationWarning={true}
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen flex flex-col`}
      >
        <SettingsProvider>
          <ThemeProvider>
            <ToastProvider> {/* Wrap with ToastProvider */}
              <ChatProvider>
                {children}
              </ChatProvider>
            </ToastProvider>
          </ThemeProvider>
        </SettingsProvider>
      </body>
    </html>
  );
}
