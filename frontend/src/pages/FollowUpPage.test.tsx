import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { FollowUpPage } from './FollowUpPage'
import { emptySessionState } from '../App'
import type { AnalyzeResponse } from '../App'
import * as api from '../lib/api'

vi.mock('../lib/api')

const mockAnalyzeResponse: AnalyzeResponse = {
  needs_follow_up: true,
  follow_up_questions: ['When was your claim denied?', 'Do you have new evidence?'],
  preliminary_route: 'supplemental_claim',
  preliminary_confidence: 0.8,
  known_facts: {},
  missing_facts: ['denial_date'],
  citations: [],
  warnings: [],
}

describe('FollowUpPage', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders the page heading', () => {
    render(
      <FollowUpPage
        sessionState={emptySessionState}
        analyzeResponse={mockAnalyzeResponse}
        onBack={() => {}}
        onAnalyzeSuccess={() => {}}
      />,
    )
    expect(
      screen.getByRole('heading', { name: /follow-up questions/i }),
    ).toBeInTheDocument()
  })

  it('renders all follow-up questions as inputs', () => {
    render(
      <FollowUpPage
        sessionState={emptySessionState}
        analyzeResponse={mockAnalyzeResponse}
        onBack={() => {}}
        onAnalyzeSuccess={() => {}}
      />,
    )
    expect(screen.getByText('When was your claim denied?')).toBeInTheDocument()
    expect(screen.getByText('Do you have new evidence?')).toBeInTheDocument()
    expect(screen.getAllByRole('textbox')).toHaveLength(2)
  })

  it('calls onBack when the Back button is clicked', async () => {
    const user = userEvent.setup()
    const onBack = vi.fn()
    render(
      <FollowUpPage
        sessionState={emptySessionState}
        analyzeResponse={mockAnalyzeResponse}
        onBack={onBack}
        onAnalyzeSuccess={() => {}}
      />,
    )
    await user.click(screen.getByRole('button', { name: /back/i }))
    expect(onBack).toHaveBeenCalledTimes(1)
  })

  it('shows an error when analyzeSession rejects', async () => {
    const user = userEvent.setup()
    vi.mocked(api.analyzeSession).mockRejectedValue(new Error('Network error'))
    render(
      <FollowUpPage
        sessionState={emptySessionState}
        analyzeResponse={mockAnalyzeResponse}
        onBack={() => {}}
        onAnalyzeSuccess={() => {}}
      />,
    )
    await user.click(screen.getByRole('button', { name: /continue/i }))
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument()
    })
  })

  it('calls onAnalyzeSuccess when analyzeSession resolves', async () => {
    const user = userEvent.setup()
    const successResponse: AnalyzeResponse = {
      ...mockAnalyzeResponse,
      needs_follow_up: false,
    }
    vi.mocked(api.analyzeSession).mockResolvedValue(successResponse)
    const onAnalyzeSuccess = vi.fn()
    render(
      <FollowUpPage
        sessionState={emptySessionState}
        analyzeResponse={mockAnalyzeResponse}
        onBack={() => {}}
        onAnalyzeSuccess={onAnalyzeSuccess}
      />,
    )
    await user.click(screen.getByRole('button', { name: /continue/i }))
    await waitFor(() => {
      expect(onAnalyzeSuccess).toHaveBeenCalledTimes(1)
    })
  })
})
