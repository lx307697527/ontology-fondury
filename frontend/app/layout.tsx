import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ontology-fondry",
  description: "LLM 原生的企业知识图谱平台",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
