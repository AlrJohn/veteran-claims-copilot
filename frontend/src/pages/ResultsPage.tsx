import type { FinalPacket } from '../App'
import './ResultsPage.css'

interface ResultsPageProps {
  packet: FinalPacket
  onStartOver: () => void
}

export function ResultsPage({ packet, onStartOver }: ResultsPageProps) {
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
          <p>
            <strong>Route:</strong> {packet.case_type}
          </p>
          
          <div style={{ marginTop: '1rem' }}>
            <strong>Why this path:</strong>
            <ul>
              {packet.why_this_path.map((reason, idx) => (
                <li key={idx}>{reason}</li>
              ))}
            </ul>
          </div>

          {packet.why_not_other_paths && packet.why_not_other_paths.length > 0 && (
            <div style={{ marginTop: '1rem' }}>
              <strong>Why not other paths:</strong>
              <ul>
                {packet.why_not_other_paths.map((reason, idx) => (
                  <li key={idx}>{reason}</li>
                ))}
              </ul>
            </div>
          )}

          {packet.known_facts && Object.keys(packet.known_facts).length > 0 && (
            <div style={{ marginTop: '1rem' }}>
              <strong>Known facts used:</strong>
              <ul>
                {Object.entries(packet.known_facts).map(([key, val]) => {
                  let strVal = val;
                  if (typeof val === 'object') {
                    // Quick check if it's the parsed_letter
                    if (val.issues && Array.isArray(val.issues)) {
                      strVal = `Issues: ${val.issues.join(', ')}`;
                    } else {
                      strVal = JSON.stringify(val);
                    }
                  }
                  return <li key={key}><strong>{key.replace(/_/g, ' ')}:</strong> {strVal}</li>
                })}
              </ul>
            </div>
          )}

          {packet.possible_forms.length > 0 && (
            <>
              <h3>Possible forms mentioned in rules</h3>
              <ul>
                {packet.possible_forms.map((f) => (
                  <li key={f}>{f}</li>
                ))}
              </ul>
            </>
          )}

          {packet.possible_missing_evidence.length > 0 && (
            <>
              <h3>Possible missing evidence to review</h3>
              <ul>
                {packet.possible_missing_evidence.map((e) => (
                  <li key={e}>{e}</li>
                ))}
              </ul>
            </>
          )}

          {packet.follow_up_questions.length > 0 && (
            <>
              <h3>Follow-up questions you could answer</h3>
              <ul>
                {packet.follow_up_questions.map((q) => (
                  <li key={q}>{q}</li>
                ))}
              </ul>
            </>
          )}

          {packet.warnings.length > 0 && (
            <>
              <h3>Warnings and reminders</h3>
              <ul>
                {packet.warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            </>
          )}
        </div>

        <aside className="results-sidebar">
          <h2>Official sources</h2>
          <ul>
            {packet.citations.map((c) => (
              <li key={c.rule_id}>
                <a href={c.source_url} target="_blank" rel="noreferrer">
                  {c.source_title}
                </a>
              </li>
            ))}
          </ul>

          <h3>Safety note</h3>
          <p>{packet.safety_note}</p>
          {packet.needs_accredited_help && (
            <p className="escalation" style={{ fontWeight: 600, color: 'var(--va-warm-dark)' }}>
              VA says accredited attorneys, claims agents, and VSO representatives can help file
              claims or request decision reviews, and accredited VSO services on VA benefit claims
              are free. Consider accredited help if your case is complex, involves the Board, or has
              been denied multiple times.
            </p>
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
  const parts: string[] = []
  parts.push(`# Veteran Disability Claims Journey Copilot summary`)
  parts.push('')
  parts.push(`Likely path: ${packet.case_type}`)
  parts.push('')

  parts.push(`Why this path:`)
  for (const reason of packet.why_this_path) {
    parts.push(`- ${reason}`)
  }
  parts.push('')

  if (packet.why_not_other_paths && packet.why_not_other_paths.length > 0) {
    parts.push(`Why not other paths:`)
    for (const reason of packet.why_not_other_paths) {
      parts.push(`- ${reason}`)
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
      parts.push(`- ${key.replace(/_/g, ' ')}: ${strVal}`)
    }
    parts.push('')
  }

  if (packet.possible_forms.length > 0) {
    parts.push('Possible forms mentioned in rules:')
    for (const f of packet.possible_forms) {
      parts.push(`- ${f}`)
    }
    parts.push('')
  }

  if (packet.possible_missing_evidence.length > 0) {
    parts.push('Possible missing evidence to review:')
    for (const e of packet.possible_missing_evidence) {
      parts.push(`- ${e}`)
    }
    parts.push('')
  }

  if (packet.follow_up_questions.length > 0) {
    parts.push('Follow-up questions:')
    for (const q of packet.follow_up_questions) {
      parts.push(`- ${q}`)
    }
    parts.push('')
  }

  if (packet.warnings.length > 0) {
    parts.push('Warnings and reminders:')
    for (const w of packet.warnings) {
      parts.push(`- ${w}`)
    }
    parts.push('')
  }

  if (packet.citations.length > 0) {
    parts.push('Official sources used:')
    for (const c of packet.citations) {
      parts.push(`- ${c.source_title} (${c.source_url})`)
    }
    parts.push('')
  }

  if (packet.needs_accredited_help) {
    parts.push('Accredited help recommended for this case complexity.')
    parts.push('')
  }

  parts.push('Safety note:')
  parts.push(packet.safety_note)
  parts.push('')
  parts.push(
    'This packet is educational and organizational only. It does not provide legal advice, predict outcomes, or replace accredited representation.',
  )

  return parts.join('\n')
}

