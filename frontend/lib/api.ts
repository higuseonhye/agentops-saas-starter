const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000"

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: {
      "x-api-key": process.env.NEXT_PUBLIC_API_KEY || ""
    },
    cache: "no-store"
  })
  if (!res.ok) {
    throw new Error(`${path} failed: ${res.status}`)
  }
  return res.json()
}

export async function apiPost<T>(path: string, body: Record<string, unknown> = {}): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": process.env.NEXT_PUBLIC_API_KEY || ""
    },
    body: JSON.stringify(body)
  })
  if (!res.ok) {
    throw new Error(`${path} failed: ${res.status}`)
  }
  return res.json()
}
