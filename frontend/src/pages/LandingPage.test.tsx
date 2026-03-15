import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LandingPage } from './LandingPage'

describe('LandingPage', () => {
  it('renders the page heading', () => {
    render(<LandingPage onStart={() => {}} />)
    expect(
      screen.getByRole('heading', { name: /veteran disability claims journey copilot/i }),
    ).toBeInTheDocument()
  })

  it('renders the tagline', () => {
    render(<LandingPage onStart={() => {}} />)
    expect(screen.getByText(/educational assistant/i)).toBeInTheDocument()
  })

  it('renders the "What this tool does" card', () => {
    render(<LandingPage onStart={() => {}} />)
    expect(screen.getByText(/what this tool does/i)).toBeInTheDocument()
  })

  it('renders the "Important limits" card', () => {
    render(<LandingPage onStart={() => {}} />)
    expect(screen.getByText(/important limits/i)).toBeInTheDocument()
  })

  it('renders the Start button', () => {
    render(<LandingPage onStart={() => {}} />)
    expect(screen.getByRole('button', { name: /start journey check/i })).toBeInTheDocument()
  })

  it('calls onStart when the Start button is clicked', async () => {
    const user = userEvent.setup()
    const onStart = vi.fn()
    render(<LandingPage onStart={onStart} />)
    await user.click(screen.getByRole('button', { name: /start journey check/i }))
    expect(onStart).toHaveBeenCalledTimes(1)
  })

  it('renders the safety note in the footer', () => {
    render(<LandingPage onStart={() => {}} />)
    expect(screen.getByText(/accredited representatives/i)).toBeInTheDocument()
  })
})
