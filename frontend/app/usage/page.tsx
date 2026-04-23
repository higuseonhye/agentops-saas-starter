"use client"

import { Suspense, useMemo, useState } from "react"
import { useSearchParams } from "next/navigation"
import useSWR from "swr"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts"

import MetricCard from "@/components/MetricCard"
import { apiGet } from "@/lib/api"

type UsageResponse = {
  total_cost: number
  total_requests: number
  total_tokens: number
  period_cost: number
  labels: string[]
  daily_cost: number[]
  cumulative_cost: number[]
  range: {
    start_date: string
    end_date: string
    days: number
  }
}

type UsageCompareResponse = {
  range: {
    start_date: string
    end_date: string
    days: number
  }
  org_costs: Array<{
    org_id: string
    org_name: string
    cost: number
  }>
}

function UsagePageContent() {
  const searchParams = useSearchParams()
  const selectedOrgId = searchParams.get("org_id") || ""
  const [rangeType, setRangeType] = useState<"7d" | "30d" | "custom">("7d")
  const [mode, setMode] = useState<"daily" | "cumulative">("daily")
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
  }, [rangeType, selectedOrgId, startDate, endDate])

  const usagePath = `/usage?${query}`
  const comparePath = `/usage/compare?${query}`

  const { data, error, isLoading } = useSWR(usagePath, (path) => apiGet<UsageResponse>(path))
  const { data: compareData } = useSWR(comparePath, (path) => apiGet<UsageCompareResponse>(path))

  if (isLoading) return <p>Loading usage...</p>
  if (error || !data) return <p>Unable to load usage data.</p>

  const series = mode === "daily" ? data.daily_cost : data.cumulative_cost
  const chartData = series.map((cost, index) => ({
    day: data.labels[index] ?? `D${index + 1}`,
    cost
  }))
  const orgCompareData = compareData?.org_costs ?? []

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
          <div>
            <label className="mb-1 block text-xs text-slate-600">View</label>
            <select
              className="rounded border px-2 py-1 text-sm"
              value={mode}
              onChange={(e) => setMode(e.target.value as "daily" | "cumulative")}
            >
              <option value="daily">Daily</option>
              <option value="cumulative">Cumulative</option>
            </select>
          </div>
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        <MetricCard title="Total Cost" value={`$${data.total_cost.toFixed(4)}`} />
        <MetricCard title="Period Cost" value={`$${data.period_cost.toFixed(4)}`} />
        <MetricCard title="Requests" value={data.total_requests} />
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        <MetricCard title="Tokens" value={data.total_tokens} />
        <MetricCard title="Range Start" value={data.range.start_date} />
        <MetricCard title="Range End" value={data.range.end_date} />
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <h2 className="mb-3 font-semibold">{mode === "daily" ? "Daily" : "Cumulative"} Cost Trend</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="cost" stroke="#0284c7" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <h2 className="mb-3 font-semibold">Cost Breakdown</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="cost" fill="#0ea5e9" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      <div className="rounded-xl bg-white p-4 shadow-sm">
        <h2 className="mb-3 font-semibold">Organization Cost Comparison</h2>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={orgCompareData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="org_name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="cost" fill="#14b8a6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  )
}

export default function UsagePage() {
  return (
    <Suspense fallback={<p>Loading usage...</p>}>
      <UsagePageContent />
    </Suspense>
  )
}
