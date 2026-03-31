import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import { AuthProvider } from "./context/AuthContext";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
});

export const metadata: Metadata = {
  title: "ExamESICorrector | Correction automatisée",
  description: "Pipeline de correction automatisée d'examens",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" className={outfit.variable}>
      <body className="min-h-screen bg-ink-50 text-ink-900 font-sans antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
