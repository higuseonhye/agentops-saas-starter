"use client"

import { Suspense, useMemo, useState } from "react"
import { useSearchParams } from "next/navigation"
import useSWR from "swr"
import {
  Bar,
  BarChart,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts"

import MetricCard from "@/components/MetricCard"
import { apiGet } from "@/lib/api"

type PerformanceResponse = {
  accuracy: number
  retrieval: number
  generation: number
}

type PerformanceHistoryResponse = {
  range: {
    start_date: string
    end_date: string
    days: number
  }
  labels: string[]
  accuracy: number[]
  retrieval: number[]
  generation: number[]
}

function PerformancePageContent() {
  const searchParams = useSearchParams()
  const selectedOrgId = searchParams.get("org_id") || ""
  const [rangeType, setRangeType] = useState<"7d" | "30d" | "custom">("7d")
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")

  const query = useMemo(() => {
    const params = new URLSearchParams()
    if (selectedOrgId) {
      params.set("org_id", selectedOrgId)
    }
    if (rangeType === "custom") {
      if (!startDate || !endDate) {
        params.set("days", "7")
        return params.toString()
      }
      params.set("start_date", startDate)
      params.set("end_date", endDate)
      return params.toString()
    }
    params.set("days", rangeType === "7d" ? "7" : "30")
    return params.toString()
  }, [endDate, rangeType, selectedOrgId, startDate])

  const latestPath = `/performance?${query}`
  const historyPath = `/performance/history?${query}`

  const { data, error, isLoading } = useSWR(latestPath, (path) => apiGet<PerformanceResponse>(path))
  const { data: history } = useSWR(historyPath, (path) => apiGet<PerformanceHistoryResponse>(path))

  if (isLoading) return <p>Loading performance...</p>
  if (error || !data) return <p>Unable to load performance data.</p>

  const barData = [
    { name: "Accuracy", value: Number((data.accuracy * 100).toFixed(1)) },
    { name: "Retrieval Err", value: Number((data.retrieval * 100).toFixed(1)) },
    { name: "Generation Err", value: Number((data.generation * 100).toFixed(1)) }
  ]
  const pieData = [
    { name: "Correct", value: Number((data.accuracy * 100).toFixed(1)), color: "#10b981" },
    {
      name: "Incorrect",
      value: Number(((1 - data.accuracy) * 100).toFixed(1)),
      color: "#ef4444"
    }
  ]
  const historyData = (history?.labels ?? []).map((label, index) => ({
    day: label,
    accuracy: Number((((history?.accuracy[index] ?? 0) * 100)).toFixed(2)),
    retrieval: Number((((history?.retrieval[index] ?? 0) * 100)).toFixed(2)),
    generation: Number((((history?.generation[index] ?? 0) * 100)).toFixed(2))
  }))

  return (
    <section className="space-y-4">
      <div className="rounded-xl bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-xs text-slate-600">Range</label>
            <select
              className="rounded border px-2 py-1 text-sm"
              value={rangeType}
              onChange={(e) => setRangeType(e.target.value as "7d" | "30d" | "custom")}
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="custom">Custom</option>
            </select>
          </div>
          {rangeType === "custom" ? (
            <>
              <div>
                <label className="mb-1 block text-xs text-slate-600">Start</label>
                <input
                  type="date"
                  className="rounded border px-2 py-1 text-sm"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-slate-600">End</label>
                <input
                  type="date"
                  className="rounded border px-2 py-1 text-sm"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </div>
            </>
          ) : null}
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        <MetricCard title="Accuracy" value={`${(data.accuracy * 100).toFixed(1)}%`} />
        <MetricCard title="Retrieval Error Rate" value={`${(data.retrieval * 100).toFixed(1)}%`} />
        <MetricCard title="Generation Error Rate" value={`${(data.generation * 100).toFixed(1)}%`} />
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <h2 className="mb-3 font-semibold">Accuracy Split</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={90} label>
                  {pieData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <h2 className="mb-3 font-semibold">Quality Indicators</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#6366f1" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      <div className="rounded-xl bg-white p-4 shadow-sm">
        <h2 className="mb-3 font-semibold">Performance History</h2>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={historyData}>
              <XAxis dataKey="day" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Line type="monotone" dataKey="accuracy" stroke="#10b981" strokeWidth={2} />
              <Line type="monotone" dataKey="retrieval" stroke="#f59e0b" strokeWidth={2} />
              <Line type="monotone" dataKey="generation" stroke="#ef4444" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  )
}

export default function PerformancePage() {
  return (
    <Suspense fallback={<p>Loading performance...</p>}>
      <PerformancePageContent />
    </Suspense>
  )
}
