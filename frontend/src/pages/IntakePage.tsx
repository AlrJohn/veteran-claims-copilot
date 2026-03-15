import { useEffect, useState } from 'react'
import type { SessionState, AnalyzeResponse } from '../App'
import { analyzeSession, getSampleCases, uploadDecisionLetter } from '../lib/api'
import './IntakePage.css'

interface IntakePageProps {
  sessionState: SessionState
  onBack: () => void
  onAnalyzeSuccess: (newState: SessionState, res: AnalyzeResponse) => void
}

export function IntakePage({ sessionState, onBack, onAnalyzeSuccess }: IntakePageProps) {
  const [userText, setUserText] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [routePreview, setRoutePreview] = useState<string | null>(null)
  const [sampleCases, setSampleCases] = useState<any[]>([])

  useEffect(() => {
    ;(async () => {
      try {
        const data = await getSampleCases()
        setSampleCases(data?.cases ?? [])
      } catch {
        // Non-fatal for intake UI
      }
    })()
  }, [])

  async function handleAnalyze() {
    setLoading(true)
    setError(null)
    try {
      let newState = { ...sessionState }

      if (file) {
        const result = await uploadDecisionLetter(file, userText)
        const res = result.session_response as AnalyzeResponse
        newState.initial_user_text = userText
        newState.uploaded_letter_present = true
        // The endpoint already called analyze_session, so we just use its response!
        onAnalyzeSuccess(newState, res)
        return
      }

      // Instead of manual routing & explanation, build session state and call analyzeSession
      newState.initial_user_text = userText
      
      const res = await analyzeSession(newState)
      setRoutePreview(res.preliminary_route)
      
      onAnalyzeSuccess(newState, res)
    } catch (e: any) {
      console.error('Analyze failed:', e)
      setError(e?.message ?? 'Something went wrong while analyzing your information.')
    } finally {
      setLoading(false)
    }
  }

  function handleSampleClick(sample: any) {
    setUserText(sample.summary ?? '')
  }

  return (
    <main className="intake">
      <header className="intake-header">
        <button type="button" className="link-button" onClick={onBack}>
          ← Back
        </button>
        <h1>Describe your situation</h1>
        <p>
          Use plain language. You can mention if this is a new claim, a denial, new evidence, or a
          request for review.
        </p>
      </header>

      <section className="intake-grid">
        <div className="intake-main">
          <label className="field-label" htmlFor="user-text">
            Your description
          </label>
          <textarea
            id="user-text"
            value={userText}
            onChange={(e) => setUserText(e.target.value)}
            rows={8}
            placeholder='For example: "I filed a claim last year, was denied, and now I have new medical records."'
          />

          <label className="field-label" htmlFor="letter-upload">
            Optional: upload a VA decision letter (PDF)
          </label>
          <input
            id="letter-upload"
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />

          <button className="primary-button" type="button" onClick={handleAnalyze} disabled={loading || !userText}>
            {loading ? 'Analyzing…' : 'Analyze'}
          </button>

          {routePreview && !file && (
            <p className="route-preview">
              Preliminary route from your text:{' '}
              <strong>
                {routePreview}
              </strong>
            </p>
          )}

          {error && <p className="error-text">{error}</p>}
        </div>

        <aside className="intake-sidebar">
          <h2>Sample scenarios</h2>
          <p>Use these for quick demos without real personal information.</p>
          <ul>
            {sampleCases.map((c) => (
              <li key={c.id}>
                <button type="button" className="link-button" onClick={() => handleSampleClick(c)}>
                  {c.title} <span className="route-tag">{c.route}</span>
                </button>
              </li>
            ))}
          </ul>
        </aside>
      </section>
    </main>
  )
}

