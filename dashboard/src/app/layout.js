import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

import { Space_Grotesk } from "next/font/google"

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"]
})

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "VisionIQ | AI Surveillance Platform",
  description: "Real-time AI surveillance with live monitoring, camera management, and threat alerts.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={spaceGrotesk.className}>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-[#080c0e] text-white font-sans`}
      >
        {children}
      </body>
    </html>
  );
}
