"use client"

import { Suspense, useState } from "react"
import { useSearchParams } from "next/navigation"
import useSWR from "swr"

import { apiGet, apiPost } from "@/lib/api"

type FailureCase = {
  id: string
  question: string
  answer: string
  ground_truth: string
  context: string
}

function FailuresPageContent() {
  const searchParams = useSearchParams()
  const selectedOrgId = searchParams.get("org_id") || ""
  const query = selectedOrgId ? `?org_id=${encodeURIComponent(selectedOrgId)}` : ""
  const path = `/failures${query}`

  const { data, error, isLoading, mutate } = useSWR(path, (p) => apiGet<FailureCase[]>(p))
  const [message, setMessage] = useState("")

  async function onReplay(id: string) {
    const res = await apiPost<{ answer: string }>(`/replay${query}`, { id })
    setMessage(`Replayed: ${res.answer}`)
    mutate()
  }

  if (isLoading) return <p>Loading failures...</p>
  if (error || !data) return <p>Unable to load failures.</p>

  return (
    <section className="space-y-3">
      {message ? <p className="rounded bg-emerald-50 p-2 text-sm text-emerald-700">{message}</p> : null}
      {data.map((f) => (
        <article key={f.id} className="rounded-xl bg-white p-4 shadow-sm">
          <h2 className="font-semibold">{f.question}</h2>
          <p className="mt-1 text-sm text-red-600">Answer: {f.answer}</p>
          <p className="mt-1 text-sm text-emerald-700">Ground truth: {f.ground_truth}</p>
          <p className="mt-1 text-xs text-slate-600">Context: {f.context}</p>
          <button
            type="button"
            className="mt-3 rounded bg-black px-3 py-1 text-sm text-white hover:bg-slate-800"
            onClick={() => onReplay(f.id)}
          >
            Replay
          </button>
        </article>
      ))}
    </section>
  )
}

export default function FailuresPage() {
  return (
    <Suspense fallback={<p>Loading failures...</p>}>
      <FailuresPageContent />
    </Suspense>
  )
}
