import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { IntakePage } from './IntakePage'
import { emptySessionState } from '../App'
import * as api from '../lib/api'

vi.mock('../lib/api')

const mockSampleCases = [
  { id: '1', title: 'Sample case 1', summary: 'Summary 1', route: 'initial_claim' },
]

describe('IntakePage', () => {
  beforeEach(() => {
    vi.mocked(api.getSampleCases).mockResolvedValue({ cases: mockSampleCases })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders the page heading', () => {
    render(
      <IntakePage sessionState={emptySessionState} onBack={() => {}} onAnalyzeSuccess={() => {}} />,
    )
    expect(
      screen.getByRole('heading', { name: /describe your situation/i }),
    ).toBeInTheDocument()
  })

  it('renders the description textarea', () => {
    render(
      <IntakePage sessionState={emptySessionState} onBack={() => {}} onAnalyzeSuccess={() => {}} />,
    )
    expect(screen.getByRole('textbox', { name: /your description/i })).toBeInTheDocument()
  })

  it('Analyze button is disabled when textarea is empty', () => {
    render(
      <IntakePage sessionState={emptySessionState} onBack={() => {}} onAnalyzeSuccess={() => {}} />,
    )
    expect(screen.getByRole('button', { name: /analyze/i })).toBeDisabled()
  })

  it('Analyze button becomes enabled when text is typed', async () => {
    const user = userEvent.setup()
    render(
      <IntakePage sessionState={emptySessionState} onBack={() => {}} onAnalyzeSuccess={() => {}} />,
    )
    await user.type(screen.getByRole('textbox', { name: /your description/i }), 'test text')
    expect(screen.getByRole('button', { name: /analyze/i })).not.toBeDisabled()
  })

  it('calls onBack when the Back button is clicked', async () => {
    const user = userEvent.setup()
    const onBack = vi.fn()
    render(
      <IntakePage sessionState={emptySessionState} onBack={onBack} onAnalyzeSuccess={() => {}} />,
    )
    await user.click(screen.getByRole('button', { name: /back/i }))
    expect(onBack).toHaveBeenCalledTimes(1)
  })

  it('shows an error message when analyzeSession rejects', async () => {
    const user = userEvent.setup()
    vi.mocked(api.analyzeSession).mockRejectedValue(new Error('Server error'))
    render(
      <IntakePage sessionState={emptySessionState} onBack={() => {}} onAnalyzeSuccess={() => {}} />,
    )
    await user.type(screen.getByRole('textbox', { name: /your description/i }), 'test')
    await user.click(screen.getByRole('button', { name: /analyze/i }))
    await waitFor(() => {
      expect(screen.getByText('Server error')).toBeInTheDocument()
    })
  })

  it('calls onAnalyzeSuccess when analyzeSession resolves without follow-up', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      needs_follow_up: false,
      follow_up_questions: [],
      preliminary_route: 'initial_claim',
      preliminary_confidence: 0.9,
      known_facts: {},
      missing_facts: [],
      citations: [],
      warnings: [],
    }
    vi.mocked(api.analyzeSession).mockResolvedValue(mockResponse)
    const onAnalyzeSuccess = vi.fn()
    render(
      <IntakePage
        sessionState={emptySessionState}
        onBack={() => {}}
        onAnalyzeSuccess={onAnalyzeSuccess}
      />,
    )
    await user.type(screen.getByRole('textbox', { name: /your description/i }), 'I filed a claim')
    await user.click(screen.getByRole('button', { name: /analyze/i }))
    await waitFor(() => {
      expect(onAnalyzeSuccess).toHaveBeenCalledTimes(1)
    })
  })

  it('loads and displays sample cases from the API', async () => {
    render(
      <IntakePage sessionState={emptySessionState} onBack={() => {}} onAnalyzeSuccess={() => {}} />,
    )
    await waitFor(() => {
      expect(screen.getByText('Sample case 1')).toBeInTheDocument()
    })
  })

  it('populates textarea when a sample case is clicked', async () => {
    const user = userEvent.setup()
    render(
      <IntakePage sessionState={emptySessionState} onBack={() => {}} onAnalyzeSuccess={() => {}} />,
    )
    await waitFor(() => screen.getByText('Sample case 1'))
    await user.click(screen.getByRole('button', { name: /sample case 1/i }))
    expect(screen.getByRole('textbox', { name: /your description/i })).toHaveValue('Summary 1')
  })
})
