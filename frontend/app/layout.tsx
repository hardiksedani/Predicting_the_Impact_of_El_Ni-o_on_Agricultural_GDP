import type { Metadata } from "next";
import localFont from "next/font/local";
import Navbar from "@/components/Navbar";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "El Niño and Crop GSVA | State Panel",
  description:
    "IMD, NOAA, and RBI state-panel analysis of climate conditions and crop GSVA in India. Model training is manual; scenarios are not causal forecasts.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} min-h-screen bg-[#f0f4ff] antialiased`}>
        <Navbar />
        <main>{children}</main>
      </body>
    </html>
  );
}
