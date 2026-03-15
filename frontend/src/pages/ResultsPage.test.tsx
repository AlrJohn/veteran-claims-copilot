import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ResultsPage } from './ResultsPage'
import type { FinalPacket } from '../App'

const mockPacket: FinalPacket = {
  case_type: 'supplemental_claim',
  confidence: 0.88,
  why_this_path: ['You have new and relevant evidence', 'Prior claim was denied'],
  why_not_other_paths: ['HLR requires no new evidence'],
  possible_forms: ['VA Form 20-0995'],
  possible_missing_evidence: ['Medical nexus letter'],
  known_facts: { denial_date: '2023-01-15', condition: 'tinnitus' },
  follow_up_questions: ['Have you seen a doctor since the denial?'],
  warnings: ['File within one year of the decision date'],
  citations: [
    {
      rule_id: 'RULE_SC_001',
      source_title: 'VA Supplemental Claims',
      source_url: 'https://www.va.gov/decision-reviews/supplemental-claim/',
    },
  ],
  safety_note: 'This is an educational tool.',
  needs_accredited_help: false,
}

describe('ResultsPage', () => {
  it('renders the Journey summary heading', () => {
    render(<ResultsPage packet={mockPacket} onStartOver={() => {}} />)
    expect(screen.getByRole('heading', { name: /journey summary/i })).toBeInTheDocument()
  })

  it('displays the likely route', () => {
    render(<ResultsPage packet={mockPacket} onStartOver={() => {}} />)
    expect(screen.getByText(/supplemental_claim/i)).toBeInTheDocument()
  })

  it('renders why-this-path items', () => {
    render(<ResultsPage packet={mockPacket} onStartOver={() => {}} />)
    expect(screen.getByText('You have new and relevant evidence')).toBeInTheDocument()
    expect(screen.getByText('Prior claim was denied')).toBeInTheDocument()
  })

  it('renders possible forms', () => {
    render(<ResultsPage packet={mockPacket} onStartOver={() => {}} />)
    expect(screen.getByText('VA Form 20-0995')).toBeInTheDocument()
  })

  it('renders warnings', () => {
    render(<ResultsPage packet={mockPacket} onStartOver={() => {}} />)
    expect(screen.getByText('File within one year of the decision date')).toBeInTheDocument()
  })

  it('renders citations with links', () => {
    render(<ResultsPage packet={mockPacket} onStartOver={() => {}} />)
    const link = screen.getByRole('link', { name: /va supplemental claims/i })
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', 'https://www.va.gov/decision-reviews/supplemental-claim/')
  })

  it('renders the safety note', () => {
    render(<ResultsPage packet={mockPacket} onStartOver={() => {}} />)
    expect(screen.getByText('This is an educational tool.')).toBeInTheDocument()
  })

  it('renders accredited help notice when needs_accredited_help is true', () => {
    const packetWithHelp = { ...mockPacket, needs_accredited_help: true }
    render(<ResultsPage packet={packetWithHelp} onStartOver={() => {}} />)
    expect(screen.getByText(/accredited attorneys/i)).toBeInTheDocument()
  })

  it('does not render accredited help notice when needs_accredited_help is false', () => {
    render(<ResultsPage packet={mockPacket} onStartOver={() => {}} />)
    expect(screen.queryByText(/accredited attorneys/i)).not.toBeInTheDocument()
  })

  it('renders Copy summary and Download buttons', () => {
    render(<ResultsPage packet={mockPacket} onStartOver={() => {}} />)
    expect(screen.getByRole('button', { name: /copy summary/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /download/i })).toBeInTheDocument()
  })

  it('calls onStartOver when Start over is clicked', async () => {
    const user = userEvent.setup()
    const onStartOver = vi.fn()
    render(<ResultsPage packet={mockPacket} onStartOver={onStartOver} />)
    await user.click(screen.getByRole('button', { name: /start over/i }))
    expect(onStartOver).toHaveBeenCalledTimes(1)
  })
})
