const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api'

export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/health`, {
    signal: AbortSignal.timeout(5000),
  })
  if (!response.ok) {
    throw new Error(`Health request failed: ${response.status}`)
  }
  return response.json()
}
