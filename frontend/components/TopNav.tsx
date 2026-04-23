"use client"

import Link from "next/link"
import { usePathname, useRouter, useSearchParams } from "next/navigation"
import useSWR from "swr"

import { apiGet } from "@/lib/api"

const nav = [
  { href: "/", label: "Overview" },
  { href: "/usage", label: "Usage" },
  { href: "/performance", label: "Performance" },
  { href: "/failures", label: "Failures" },
  { href: "/system", label: "System" }
]

type OrgResponse = {
  orgs: Array<{
    id: string
    name: string
    role: string
  }>
}

export default function TopNav() {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const selectedOrgId = searchParams.get("org_id") || ""

  const { data } = useSWR("/orgs", (path) => apiGet<OrgResponse>(path))
  const orgs = data?.orgs ?? []

  function hrefWithOrg(baseHref: string): string {
    if (!selectedOrgId) return baseHref
    return `${baseHref}?org_id=${encodeURIComponent(selectedOrgId)}`
  }

  function onChangeOrg(orgId: string) {
    const params = new URLSearchParams(searchParams.toString())
    if (orgId) {
      params.set("org_id", orgId)
    } else {
      params.delete("org_id")
    }
    const q = params.toString()
    router.push(q ? `${pathname}?${q}` : pathname)
  }

  return (
    <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
      <nav className="flex gap-2">
        {nav.map((item) => (
          <Link
            key={item.href}
            className="rounded-lg bg-white px-3 py-2 text-sm shadow-sm hover:bg-slate-50"
            href={hrefWithOrg(item.href)}
          >
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="flex items-center gap-2">
        <label htmlFor="org-select" className="text-sm text-slate-600">
          Org
        </label>
        <select
          id="org-select"
          className="rounded border bg-white px-2 py-1 text-sm"
          value={selectedOrgId}
          onChange={(e) => onChangeOrg(e.target.value)}
        >
          <option value="">Default</option>
          {orgs.map((org) => (
            <option key={org.id} value={org.id}>
              {org.name} ({org.role})
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
