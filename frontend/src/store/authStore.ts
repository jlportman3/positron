import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  username: string
  privilege_level: number
  privilege_name: string
}

interface AuthState {
  isAuthenticated: boolean
  user: User | null
  sessionId: string | null
  login: (sessionId: string, user: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      user: null,
      sessionId: null,
      login: (sessionId, user) => {
        localStorage.setItem('session_id', sessionId)
        set({ isAuthenticated: true, user, sessionId })
      },
      logout: () => {
        localStorage.removeItem('session_id')
        set({ isAuthenticated: false, user: null, sessionId: null })
      },
    }),
    {
      name: 'auth-storage',
    }
  )
)
