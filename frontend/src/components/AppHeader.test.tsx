import { render, screen } from '@testing-library/react'
import { AppHeader } from './AppHeader'

describe('AppHeader', () => {
  it('renders the app title', () => {
    render(<AppHeader />)
    expect(screen.getByText('VA Claims Copilot')).toBeInTheDocument()
  })

  it('renders the educational disclaimer badge', () => {
    render(<AppHeader />)
    expect(screen.getByText(/educational tool/i)).toBeInTheDocument()
    expect(screen.getByText(/not legal advice/i)).toBeInTheDocument()
  })

  it('renders a banner landmark', () => {
    render(<AppHeader />)
    expect(screen.getByRole('banner')).toBeInTheDocument()
  })
})
