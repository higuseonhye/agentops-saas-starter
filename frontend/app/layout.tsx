import "./globals.css"
import type { Metadata } from "next"
import { Suspense, type ReactNode } from "react"
import TopNav from "@/components/TopNav"

export const metadata: Metadata = {
  title: "AgentOps Dashboard",
  description: "Usage, quality, failures and system operations"
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <main className="mx-auto max-w-6xl p-6">
          <h1 className="mb-4 text-3xl font-bold">AgentOps Dashboard</h1>
          <Suspense fallback={<div className="mb-6 h-10 rounded-lg bg-white" />}>
            <TopNav />
          </Suspense>
          {children}
        </main>
      </body>
    </html>
  )
}
