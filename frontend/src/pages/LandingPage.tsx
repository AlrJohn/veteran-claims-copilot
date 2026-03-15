import './LandingPage.css'

interface LandingPageProps {
  onStart: () => void
}

export function LandingPage({ onStart }: LandingPageProps) {
  return (
    <main className="landing">
      <header className="landing-header">
        <h1>Veteran Disability Claims Journey Copilot</h1>
        <p className="tagline">
          An educational assistant to help you understand where you are in the VA disability claims
          journey and what options VA describes next.
        </p>
      </header>

      <section className="landing-body">
        <div className="card">
          <h2>What this tool does</h2>
          <ul>
            <li>Helps you describe your situation in plain language</li>
            <li>Checks it against a small set of official VA rules</li>
            <li>Suggests a likely path like initial claim or decision review</li>
            <li>Surfaces possible evidence gaps and follow-up questions</li>
          </ul>
        </div>

        <div className="card">
          <h2>Important limits</h2>
          <ul>
            <li>Does not file or submit anything to VA</li>
            <li>Is not a lawyer, claims agent, or VSO</li>
            <li>Does not give legal advice or predict outcomes</li>
            <li>Uses only a small set of official VA web pages for rules</li>
          </ul>
        </div>
      </section>

      <section className="landing-actions">
        <button className="primary-button" type="button" onClick={onStart}>
          Start journey check
        </button>
      </section>

      <footer className="landing-footer">
        <p className="safety-note">
          This tool is educational and organizational. For representation or detailed advice, VA
          says accredited representatives, claims agents, and attorneys can help with claims and
          decision reviews, and accredited VSO services for VA benefit claims are free.
        </p>
      </footer>
    </main>
  )
}

