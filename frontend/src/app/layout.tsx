import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import { QueryProvider } from "@/lib/api/query-provider";
import { Header } from "@/components/header";
import { Footer } from "@/components/footer";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
});

export const metadata: Metadata = {
  title: "GlamNow | Quick Commerce for At-Home Beauty, Grooming & Tailoring",
  description:
    "Book verified at-home beauty, salon, massage, and custom tailoring services in 15–30 minutes across India. Compare Basic, Standard, and Premium tiers.",
  keywords: [
    "at-home salon",
    "home grooming",
    "saree draping",
    "blouse stitching",
    "doorstep tailoring",
    "quick beauty services India",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${outfit.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-gn-bg-primary text-gn-text-primary">
        <QueryProvider>
          <Header />
          <main className="flex-1">{children}</main>
          <Footer />
        </QueryProvider>
      </body>
    </html>
  );
}
