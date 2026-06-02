import "./globals.css";
import { Metadata } from "next";
import { Sora, Space_Grotesk } from "next/font/google";

const sora = Sora({ subsets: ["latin"], weight: ["400", "500", "600", "700"] , variable: "--font-sora"});
const grotesk = Space_Grotesk({ subsets: ["latin"], weight: ["400", "500", "600", "700"], variable: "--font-grotesk" });

export const metadata: Metadata = {
  title: "EduSpark AI",
  description: "Монгол хэл дээрх AI STEM сургалтын туслах",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="mn">
      <body className={`${sora.variable} ${grotesk.variable} font-sans`}>{children}</body>
    </html>
  );
}