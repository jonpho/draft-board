import '@testing-library/jest-dom'

// Mock window.confirm
global.confirm = vi.fn(() => true)

// Mock window.prompt
global.prompt = vi.fn()
