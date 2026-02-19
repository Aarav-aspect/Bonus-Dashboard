import type { Metadata } from "next";
import "./globals.css";
import Navbar from "./Navbar";

import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "Aspect Dashboard",
  description: "Simple authentication dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`antialiased bg-gray-50`}>
        <Navbar />
        {children}
        <Toaster />
      </body>
    </html>
  );
}
