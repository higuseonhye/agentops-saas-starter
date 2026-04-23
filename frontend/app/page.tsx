import Link from "next/link"

export default function HomePage() {
  return (
    <section className="grid gap-3 md:grid-cols-2">
      <Link href="/usage" className="rounded-xl bg-white p-5 shadow-sm hover:bg-slate-50">
        <h2 className="font-semibold">Usage</h2>
        <p className="text-sm text-slate-600">Track cost, requests, and token trends.</p>
      </Link>
      <Link href="/performance" className="rounded-xl bg-white p-5 shadow-sm hover:bg-slate-50">
        <h2 className="font-semibold">Performance</h2>
        <p className="text-sm text-slate-600">Monitor accuracy and error rates.</p>
      </Link>
      <Link href="/failures" className="rounded-xl bg-white p-5 shadow-sm hover:bg-slate-50">
        <h2 className="font-semibold">Failures</h2>
        <p className="text-sm text-slate-600">Inspect failed answers and replay cases.</p>
      </Link>
      <Link href="/system" className="rounded-xl bg-white p-5 shadow-sm hover:bg-slate-50">
        <h2 className="font-semibold">System</h2>
        <p className="text-sm text-slate-600">View config and trigger operations.</p>
      </Link>
    </section>
  )
}
