import { useState } from 'react'
import './App.css'
import { LandingPage } from './pages/LandingPage'
import { IntakePage } from './pages/IntakePage'
import { FollowUpPage } from './pages/FollowUpPage'
import { ResultsPage } from './pages/ResultsPage'

export type RouteView = 'landing' | 'intake' | 'followup' | 'results'

export interface SessionState {
  conversation_history: { role: string; content: string }[]
  initial_user_text: string
  uploaded_letter_present: boolean
  current_route: string | null
  route_confidence: number | null
  known_facts: Record<string, any>
  missing_facts: string[]
  follow_up_questions: string[]
  candidate_routes: string[]
  final_packet_ready: boolean
}

export interface Citation {
  rule_id: string
  source_title: string
  source_url: string
  source_excerpt?: string
}

export interface FinalPacket {
  case_type: string
  confidence: number
  why_this_path: string[]
  why_not_other_paths: string[]
  possible_forms: string[]
  possible_missing_evidence: string[]
  known_facts: Record<string, any>
  follow_up_questions: string[]
  warnings: string[]
  citations: Citation[]
  safety_note: string
  needs_accredited_help: boolean
}

export interface AnalyzeResponse {
  needs_follow_up: boolean
  follow_up_questions: string[]
  preliminary_route: string
  preliminary_confidence: number
  known_facts: Record<string, any>
  missing_facts: string[]
  citations: Citation[]
  warnings: string[]
  final_packet?: FinalPacket
}

export const emptySessionState: SessionState = {
  conversation_history: [],
  initial_user_text: '',
  uploaded_letter_present: false,
  current_route: null,
  route_confidence: null,
  known_facts: {},
  missing_facts: [],
  follow_up_questions: [],
  candidate_routes: [],
  final_packet_ready: false,
}

function App() {
  const [view, setView] = useState<RouteView>('landing')
  const [sessionState, setSessionState] = useState<SessionState>(emptySessionState)
  const [lastResponse, setLastResponse] = useState<AnalyzeResponse | null>(null)

  return (
    <div className="app-shell">
      {view === 'landing' && (
        <LandingPage
          onStart={() => {
            setSessionState(emptySessionState)
            setView('intake')
          }}
        />
      )}
      {view === 'intake' && (
        <IntakePage
          sessionState={sessionState}
          onBack={() => setView('landing')}
          onAnalyzeSuccess={(newState: SessionState, res: AnalyzeResponse) => {
            setSessionState(newState)
            setLastResponse(res)
            if (res.needs_follow_up) {
              setView('followup')
            } else {
              setView('results')
            }
          }}
        />
      )}
      {view === 'followup' && lastResponse && (
        <FollowUpPage
          sessionState={sessionState}
          analyzeResponse={lastResponse}
          onBack={() => setView('intake')}
          onAnalyzeSuccess={(newState: SessionState, res: AnalyzeResponse) => {
            setSessionState(newState)
            setLastResponse(res)
            if (res.needs_follow_up) {
              setView('followup')
            } else {
              setView('results')
            }
          }}
        />
      )}
      {view === 'results' && lastResponse?.final_packet && (
        <ResultsPage
          packet={lastResponse.final_packet}
          onStartOver={() => {
            setSessionState(emptySessionState)
            setLastResponse(null)
            setView('landing')
          }}
        />
      )}
    </div>
  )
}

export default App
