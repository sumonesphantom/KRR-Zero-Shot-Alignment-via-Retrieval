import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { TopBar } from "@/components/layout/TopBar";
import { Toaster } from "@/components/ui/sonner";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Zero-Shot Alignment via Retrieval",
  description:
    "Retrieve a pre-trained style module from a bank and stream a 3-LLM Knowledge / Style / Judge control loop live.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      {/* h-screen + overflow-hidden on <body> locks the page to the viewport;
          only the <main> below scrolls, keeping sidebar + topbar visible. */}
      <body className="h-screen overflow-hidden bg-background text-foreground">
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <div className="flex h-full">
            <AppSidebar />
            <div className="flex min-w-0 flex-1 flex-col h-full">
              <TopBar />
              <main className="flex-1 min-h-0 min-w-0 overflow-y-auto p-4 md:p-6">
                {children}
              </main>
            </div>
          </div>
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  );
}
