import type { SessionState, AnalyzeResponse } from '../App'

const BACKEND_BASE = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'

async function parseError(res: Response, fallback: string): Promise<never> {
  let message = fallback

  try {
    const data = await res.json()
    message =
      data?.detail ||
      data?.error ||
      data?.message ||
      JSON.stringify(data)
  } catch {
    try {
      const text = await res.text()
      if (text) message = text
    } catch {
      // ignore
    }
  }

  throw new Error(message)
}

export async function classifyRoute(userText: string) {
  const res = await fetch(`${BACKEND_BASE}/api/classify/route/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_text: userText }),
  })

  if (!res.ok) {
    await parseError(res, 'Failed to classify route')
  }

  return (await res.json()) as {
    route: string
    confidence: number
    rule_hits: string[]
    notes?: string
  }
}

export async function analyzeSession(state: SessionState): Promise<AnalyzeResponse> {
  const res = await fetch(`${BACKEND_BASE}/api/session/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(state),
  })

  if (!res.ok) {
    await parseError(res, 'Failed to analyze session state')
  }

  return (await res.json()) as AnalyzeResponse
}

export async function uploadDecisionLetter(file: File, userText: string) {
  const form = new FormData()
  form.append('file', file)
  form.append('user_text', userText)

  const res = await fetch(`${BACKEND_BASE}/api/decision-letter/`, {
    method: 'POST',
    body: form,
  })

  if (!res.ok) {
    await parseError(res, 'Failed to process decision letter')
  }

  return res.json()
}

export async function getSampleCases() {
  const res = await fetch(`${BACKEND_BASE}/api/sample-cases/`)

  if (!res.ok) {
    await parseError(res, 'Failed to load sample cases')
  }

  return res.json()
}