import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import LoadingSpinner from '@/shared/components/LoadingSpinner.vue'
import ToastContainer from '@/shared/components/ToastContainer.vue'
import { useToast } from '@/shared/composables/useToast'

describe('EmptyState', () => {
  it('renders the required title', () => {
    render(EmptyState, { props: { title: 'No patients found' } })
    expect(screen.getByText('No patients found')).toBeTruthy()
  })

  it('renders the optional message when provided', () => {
    render(EmptyState, { props: { title: 'No results', message: 'Try a different search term.' } })
    expect(screen.getByText('Try a different search term.')).toBeTruthy()
  })

  it('omits the message paragraph when none is provided', () => {
    const { container } = render(EmptyState, { props: { title: 'No results' } })
    expect(container.querySelectorAll('p').length).toBe(0)
  })

  it('renders slot content below the message (e.g. a call-to-action button)', () => {
    render(EmptyState, {
      props: { title: 'No assessments yet' },
      slots: { default: '<button>Start first assessment</button>' },
    })
    expect(screen.getByText('Start first assessment')).toBeTruthy()
  })
})

describe('LoadingSpinner', () => {
  it('renders a spinning indicator', () => {
    const { container } = render(LoadingSpinner)
    expect(container.querySelector('svg.animate-spin')).toBeTruthy()
  })

  it('renders an optional loading message', () => {
    render(LoadingSpinner, { props: { message: 'Loading patients…' } })
    expect(screen.getByText('Loading patients…')).toBeTruthy()
  })

  it('omits the message when none is provided', () => {
    const { container } = render(LoadingSpinner)
    expect(container.querySelector('p')).toBeNull()
  })
})

describe('ToastContainer — error/status states', () => {
  beforeEach(() => {
    // useToast's `toasts` ref is a module-level singleton — drain it between tests.
    const { toasts } = useToast()
    toasts.value.splice(0, toasts.value.length)
  })

  it('renders nothing when there are no active toasts', () => {
    const { container } = render(ToastContainer)
    expect(container.querySelectorAll('[class*="rounded-xl"]').length).toBe(0)
  })

  it('shows an error toast message pushed via showToast', async () => {
    render(ToastContainer)
    const { showToast } = useToast()
    showToast('Could not save changes — storage may be full.', 'error')
    expect(await screen.findByText('Could not save changes — storage may be full.')).toBeTruthy()
  })

  it('dismisses a toast when clicked', async () => {
    render(ToastContainer)
    const { showToast } = useToast()
    showToast('Something went wrong', 'error')
    const toast = await screen.findByText('Something went wrong')
    await fireEvent.click(toast)
    expect(screen.queryByText('Something went wrong')).toBeNull()
  })

  it('auto-dismisses a toast after its duration elapses', async () => {
    vi.useFakeTimers()
    render(ToastContainer)
    const { showToast } = useToast()
    showToast('Saved!', 'success', 1000)
    expect(await screen.findByText('Saved!')).toBeTruthy()
    await vi.advanceTimersByTimeAsync(1100)
    expect(screen.queryByText('Saved!')).toBeNull()
    vi.useRealTimers()
  })
})
