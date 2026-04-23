type MetricCardProps = {
  title: string
  value: string | number
}

export default function MetricCard({ title, value }: MetricCardProps) {
  return (
    <div className="rounded-xl bg-white p-4 shadow-sm">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  )
}
