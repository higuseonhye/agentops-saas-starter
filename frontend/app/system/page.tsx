"use client"

import { Suspense, useState } from "react"
import { useSearchParams } from "next/navigation"
import useSWR from "swr"

import { apiGet, apiPost } from "@/lib/api"

function SystemPageContent() {
  const searchParams = useSearchParams()
  const selectedOrgId = searchParams.get("org_id") || ""
  const query = selectedOrgId ? `?org_id=${encodeURIComponent(selectedOrgId)}` : ""
  const { data, error, isLoading } = useSWR("/config", (path) => apiGet<Record<string, unknown>>(path))
  const [message, setMessage] = useState("")

  async function onOptimize() {
    await apiPost(`/optimize${query}`)
    setMessage("Optimization started.")
  }

  async function onReplayAll() {
    const failures = await apiGet<Array<{ id: string }>>(`/failures${query}`)
    for (const f of failures) {
      await apiPost(`/replay${query}`, { id: f.id })
    }
    setMessage("Replay completed.")
  }

  if (isLoading) return <p>Loading config...</p>
  if (error || !data) return <p>Unable to load config.</p>

  return (
    <section className="space-y-3">
      {message ? <p className="rounded bg-blue-50 p-2 text-sm text-blue-700">{message}</p> : null}
      <div className="rounded-xl bg-white p-4 shadow-sm">
        <h2 className="mb-2 font-semibold">Runtime Config</h2>
        <pre className="overflow-x-auto rounded bg-slate-100 p-3 text-sm">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
      <div className="flex gap-2">
        <button
          type="button"
          className="rounded bg-black px-3 py-2 text-sm text-white hover:bg-slate-800"
          onClick={onOptimize}
        >
          Run Optimize
        </button>
        <button
          type="button"
          className="rounded bg-slate-700 px-3 py-2 text-sm text-white hover:bg-slate-600"
          onClick={onReplayAll}
        >
          Replay All Failures
        </button>
      </div>
    </section>
  )
}

export default function SystemPage() {
  return (
    <Suspense fallback={<p>Loading config...</p>}>
      <SystemPageContent />
    </Suspense>
  )
}
