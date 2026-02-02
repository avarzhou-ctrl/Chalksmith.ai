// src/app/layout.tsx
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "ClassKit",
  description: "Built with Next.js and FastAPI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}