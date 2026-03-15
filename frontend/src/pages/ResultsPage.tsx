import type { FinalPacket } from '../App'
import './ResultsPage.css'

interface ResultsPageProps {
  packet: FinalPacket
  onStartOver: () => void
}

export function ResultsPage({ packet, onStartOver }: ResultsPageProps) {
  const topSources = getTopSources(packet, 4)
  const fullSources = getTopSources(packet, Number.MAX_SAFE_INTEGER)
  const shortReasonSummary = getShortReasonSummary(packet)
  const topNextSteps = getTopNextSteps(packet, 3)
  const keyMissingEvidence = packet.possible_missing_evidence.slice(0, 5)
  const safetyNote = sanitizeRuleRefs(packet.safety_note)
  const summaryText = buildSummary(packet)

  function handleCopy() {
    navigator.clipboard.writeText(summaryText).catch(() => {
      // ignore copy errors in MVP
    })
  }

  function handleDownload() {
    const blob = new Blob([summaryText], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'va-claims-copilot-summary.txt'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <main className="results">
      <header className="results-header">
        <h1>Journey summary</h1>
        <p>
          This is an educational packet based on a small set of official VA rules. It is not legal
          advice and does not replace accredited help.
        </p>
      </header>

      <section className="results-grid">
        <div className="results-main">
          <h2>Likely path</h2>
          <p className="route-pill">{toFriendlyRouteName(packet.case_type)}</p>

          <section className="result-card">
            <h3>Reason summary</h3>
            <p>{shortReasonSummary}</p>
          </section>

          <section className="result-card">
            <h3>Top 3 next steps</h3>
            <ul>
              {topNextSteps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ul>
          </section>

          <section className="result-card">
            <h3>Key missing evidence</h3>
            {keyMissingEvidence.length > 0 ? (
              <ul>
                {keyMissingEvidence.map((item) => (
                  <li key={item}>{sanitizeRuleRefs(item)}</li>
                ))}
              </ul>
            ) : (
              <p>No key evidence gaps were identified from current information.</p>
            )}
          </section>

          <details className="result-details">
            <summary>Why not other paths</summary>
            {packet.why_not_other_paths.length > 0 ? (
              <ul>
                {packet.why_not_other_paths.map((reason) => (
                  <li key={reason}>{sanitizeRuleRefs(reason)}</li>
                ))}
              </ul>
            ) : (
              <p>No additional exclusions were provided.</p>
            )}
          </details>

          <details className="result-details">
            <summary>Full evidence details</summary>
            {packet.possible_forms.length > 0 && (
              <>
                <h4>Possible forms</h4>
                <ul>
                  {packet.possible_forms.map((f) => (
                    <li key={f}>{sanitizeRuleRefs(f)}</li>
                  ))}
                </ul>
              </>
            )}

            {packet.possible_missing_evidence.length > 0 && (
              <>
                <h4>All possible missing evidence</h4>
                <ul>
                  {packet.possible_missing_evidence.map((e) => (
                    <li key={e}>{sanitizeRuleRefs(e)}</li>
                  ))}
                </ul>
              </>
            )}

            {packet.known_facts && Object.keys(packet.known_facts).length > 0 && (
              <>
                <h4>Known facts used</h4>
                <ul>
                  {Object.entries(packet.known_facts).map(([key, val]) => {
                    let strVal = val
                    if (typeof val === 'object') {
                      if (val.issues && Array.isArray(val.issues)) {
                        strVal = `Issues: ${val.issues.join(', ')}`
                      } else {
                        strVal = JSON.stringify(val)
                      }
                    }
                    return (
                      <li key={key}>
                        <strong>{key.replace(/_/g, ' ')}:</strong> {String(strVal)}
                      </li>
                    )
                  })}
                </ul>
              </>
            )}
          </details>
        </div>

        <aside className="results-sidebar">
          <h2>Official sources (top links)</h2>
          <ul className="source-list">
            {topSources.map((c) => (
              <li key={`${c.source_url}-${c.source_title}`}>
                <a href={c.source_url} target="_blank" rel="noreferrer">
                  {friendlySourceLabel(c.source_title)}
                </a>
              </li>
            ))}
          </ul>

          <h3>Safety note</h3>
          <p>{safetyNote}</p>
          {packet.needs_accredited_help && (
            <p className="escalation" style={{ fontWeight: 600, color: 'var(--va-warm-dark)' }}>
              VA says accredited attorneys, claims agents, and VSO representatives can help file
              claims or request decision reviews, and accredited VSO services on VA benefit claims
              are free. Consider accredited help if your case is complex, involves the Board, or has
              been denied multiple times.
            </p>
          )}

          <details className="result-details sidebar-details">
            <summary>Full source list</summary>
            <ul className="source-list">
              {fullSources.map((c) => (
                <li key={`${c.source_url}-${c.source_title}`}>
                  <a href={c.source_url} target="_blank" rel="noreferrer">
                    {friendlySourceLabel(c.source_title)}
                  </a>
                </li>
              ))}
            </ul>
          </details>

          {packet.warnings.length > 0 && (
            <details className="result-details sidebar-details">
              <summary>Warnings and reminders</summary>
              <ul>
                {packet.warnings.map((w) => (
                  <li key={w}>{sanitizeRuleRefs(w)}</li>
                ))}
              </ul>
            </details>
          )}

          <div className="export-panel">
            <h3>Export</h3>
            <button type="button" className="primary-button" onClick={handleCopy}>
              Copy summary
            </button>
            <button type="button" className="secondary-button" onClick={handleDownload}>
              Download .txt
            </button>
          </div>

          <button type="button" className="link-button" onClick={onStartOver}>
            Start over
          </button>
        </aside>
      </section>
    </main>
  )
}

function buildSummary(packet: FinalPacket): string {
  const topSources = getTopSources(packet, 4)
  const fullSources = getTopSources(packet, Number.MAX_SAFE_INTEGER)
  const topNextSteps = getTopNextSteps(packet, 3)
  const shortReasonSummary = getShortReasonSummary(packet)
  const parts: string[] = []
  parts.push(`# Veteran Disability Claims Journey Copilot summary`)
  parts.push('')
  parts.push(`Likely path: ${toFriendlyRouteName(packet.case_type)}`)
  parts.push('')
  parts.push(`Reason summary:`)
  parts.push(`- ${shortReasonSummary}`)
  parts.push('')

  parts.push(`Top 3 next steps:`)
  for (const step of topNextSteps) {
    parts.push(`- ${step}`)
  }
  parts.push('')

  parts.push(`Why this path:`)
  for (const reason of packet.why_this_path) {
    parts.push(`- ${sanitizeRuleRefs(reason)}`)
  }
  parts.push('')

  if (packet.why_not_other_paths && packet.why_not_other_paths.length > 0) {
    parts.push(`Why not other paths:`)
    for (const reason of packet.why_not_other_paths) {
      parts.push(`- ${sanitizeRuleRefs(reason)}`)
    }
    parts.push('')
  }

  if (packet.known_facts && Object.keys(packet.known_facts).length > 0) {
    parts.push('Known facts used:')
    for (const [key, val] of Object.entries(packet.known_facts)) {
      let strVal = val
      if (typeof val === 'object') {
        if (val.issues && Array.isArray(val.issues)) {
          strVal = `Issues: ${val.issues.join(', ')}`
        } else {
          strVal = JSON.stringify(val)
        }
      }
      parts.push(`- ${key.replace(/_/g, ' ')}: ${sanitizeRuleRefs(String(strVal))}`)
    }
    parts.push('')
  }

  if (packet.possible_forms.length > 0) {
    parts.push('Possible forms mentioned in rules:')
    for (const f of packet.possible_forms) {
      parts.push(`- ${sanitizeRuleRefs(f)}`)
    }
    parts.push('')
  }

  if (packet.possible_missing_evidence.length > 0) {
    parts.push('Possible missing evidence to review:')
    for (const e of packet.possible_missing_evidence) {
      parts.push(`- ${sanitizeRuleRefs(e)}`)
    }
    parts.push('')
  }

  if (packet.follow_up_questions.length > 0) {
    parts.push('Follow-up questions:')
    for (const q of packet.follow_up_questions) {
      parts.push(`- ${sanitizeRuleRefs(q)}`)
    }
    parts.push('')
  }

  if (packet.warnings.length > 0) {
    parts.push('Warnings and reminders:')
    for (const w of packet.warnings) {
      parts.push(`- ${sanitizeRuleRefs(w)}`)
    }
    parts.push('')
  }

  if (topSources.length > 0) {
    parts.push('Top official sources:')
    for (const c of topSources) {
      parts.push(`- ${sanitizeRuleRefs(c.source_title)} (${c.source_url})`)
    }
    parts.push('')
  }

  if (fullSources.length > 0) {
    parts.push('Full source list:')
    for (const c of fullSources) {
      parts.push(`- ${sanitizeRuleRefs(c.source_title)} (${c.source_url})`)
    }
    parts.push('')
  }

  if (packet.needs_accredited_help) {
    parts.push('Accredited help recommended for this case complexity.')
    parts.push('')
  }

  parts.push('Safety note:')
  parts.push(sanitizeRuleRefs(packet.safety_note))

  return parts.join('\n')
}

function toFriendlyRouteName(route: string): string {
  const map: Record<string, string> = {
    initial_claim: 'Initial Claim',
    supplemental_claim: 'Supplemental Claim',
    hlr: 'Higher-Level Review',
    board_explainer: 'Board Appeal',
    unclear: 'Needs clarification',
  }
  return map[route] || route.replace(/_/g, ' ')
}

function sanitizeRuleRefs(text: string): string {
  return text
    .replace(/\(\s*RULE_[A-Z0-9_]+\s*\)/g, '')
    .replace(/\bRULE_[A-Z0-9_]+\b/g, '')
    .replace(/\s{2,}/g, ' ')
    .replace(/\s+([,.;:])/g, '$1')
    .trim()
}

function friendlySourceLabel(title: string): string {
  return title.replace(/\bVA Form\b/g, 'VA page')
}

function getTopSources(packet: FinalPacket, maxCount: number) {
  const seen = new Set<string>()
  const deduped = []
  for (const citation of packet.citations) {
    const key = citation.source_url || citation.rule_id
    if (!key || seen.has(key)) continue
    seen.add(key)
    deduped.push(citation)
    if (deduped.length >= maxCount) break
  }
  return deduped
}

function getShortReasonSummary(packet: FinalPacket): string {
  if (packet.why_this_path.length === 0) {
    return 'This path was selected based on the details provided so far.'
  }
  const topReasons = packet.why_this_path.slice(0, 2).map((r) => sanitizeRuleRefs(r))
  return topReasons.join(' ')
}

function getTopNextSteps(packet: FinalPacket, maxCount: number): string[] {
  const steps: string[] = []
  if (packet.possible_forms[0]) {
    steps.push(`Review and prepare ${sanitizeRuleRefs(packet.possible_forms[0])}.`)
  }
  if (packet.possible_missing_evidence[0]) {
    steps.push(`Gather: ${sanitizeRuleRefs(packet.possible_missing_evidence[0])}.`)
  }
  if (packet.possible_missing_evidence[1]) {
    steps.push(`Also gather: ${sanitizeRuleRefs(packet.possible_missing_evidence[1])}.`)
  }
  if (packet.follow_up_questions[0]) {
    steps.push(`Answer this first: ${sanitizeRuleRefs(packet.follow_up_questions[0])}`)
  }
  if (steps.length === 0 && packet.why_this_path[0]) {
    steps.push(sanitizeRuleRefs(packet.why_this_path[0]))
  }
  return Array.from(new Set(steps)).slice(0, maxCount)
}

