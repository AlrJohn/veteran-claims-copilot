import { useState } from 'react'
import type { SessionState, AnalyzeResponse } from '../App'
import { analyzeSession } from '../lib/api'
import './FollowUpPage.css'
import './IntakePage.css'

interface FollowUpPageProps {
  sessionState: SessionState
  analyzeResponse: AnalyzeResponse
  onBack: () => void
  onAnalyzeSuccess: (newState: SessionState, res: AnalyzeResponse) => void
}

export function FollowUpPage({ sessionState, analyzeResponse, onBack, onAnalyzeSuccess }: FollowUpPageProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const questions = analyzeResponse.follow_up_questions || []

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)

    // Build the user answer string
    const newContextRaw = questions
      .map((q, idx) => `Q: ${q}\nA: ${answers[idx] || 'No answer'}`)
      .join('\n\n')

    const newState: SessionState = {
      ...sessionState,
      conversation_history: [
        ...sessionState.conversation_history,
        { role: 'assistant', content: questions.join('\n') },
        { role: 'user', content: newContextRaw },
      ],
      known_facts: { ...sessionState.known_facts, ...analyzeResponse.known_facts },
      missing_facts: analyzeResponse.missing_facts || [],
      candidate_routes: [analyzeResponse.preliminary_route],
      current_route: analyzeResponse.preliminary_route,
    }

    try {
      const res = await analyzeSession(newState)
      onAnalyzeSuccess(newState, res)
    } catch (err: any) {
      console.error('Analyze failed:', err)
      setError(err?.message ?? 'Failed to process answers.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="follow-up">
      <header className="follow-up-header">
        <button type="button" className="link-button" onClick={onBack}>
          ← Back
        </button>
        <h1>A few follow-up questions</h1>
        <p>To help find the right official path, we need a bit more detail.</p>
      </header>

      <section className="intake-grid" style={{ gridTemplateColumns: 'minmax(0, 1fr)' }}>
        <div className="intake-main">
          <form onSubmit={handleSubmit} className="follow-up-form">
            {questions.map((q, idx) => (
              <div key={idx} className="follow-up-question">
                <label className="field-label">{q}</label>
                <input
                  type="text"
                  value={answers[idx] || ''}
                  onChange={(e) => setAnswers({ ...answers, [idx]: e.target.value })}
                />
              </div>
            ))}

            <button className="primary-button" type="submit" disabled={loading}>
              {loading ? 'Continuing…' : 'Continue'}
            </button>

            {error && <p className="error-text" style={{ marginTop: '1rem' }}>{error}</p>}
          </form>
        </div>
      </section>
    </main>
  )
}
