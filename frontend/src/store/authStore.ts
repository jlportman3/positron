import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

interface User {
  id: string
  username: string
  email?: string
  full_name?: string
  is_active: boolean
  is_superuser: boolean
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  loading: boolean

  login: (username: string, password: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
  setToken: (token: string) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      loading: false,

      login: async (username: string, password: string) => {
        set({ loading: true })
        try {
          // OAuth2 password flow - send as form data
          const formData = new URLSearchParams()
          formData.append('username', username)
          formData.append('password', password)

          const response = await axios.post(
            `${API_URL}/api/v1/auth/login`,
            formData,
            {
              headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
              },
            }
          )

          const { access_token, user } = response.data

          // Set token in axios defaults
          axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

          set({
            token: access_token,
            user: user,
            isAuthenticated: true,
            loading: false,
          })
        } catch (error) {
          set({ loading: false })
          throw error
        }
      },

      logout: () => {
        // Clear token from axios defaults
        delete axios.defaults.headers.common['Authorization']

        set({
          user: null,
          token: null,
          isAuthenticated: false,
        })
      },

      checkAuth: async () => {
        const token = get().token
        if (!token) {
          set({ isAuthenticated: false })
          return
        }

        try {
          // Set token in axios
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`

          // Verify token with backend
          const response = await axios.get(`${API_URL}/api/v1/auth/me`)

          set({
            user: response.data,
            isAuthenticated: true,
          })
        } catch (error) {
          // Token is invalid, clear auth state
          get().logout()
        }
      },

      setToken: (token: string) => {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
        set({ token })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
      }),
    }
  )
)

// Initialize auth on app load
export const initAuth = async () => {
  const { token, checkAuth } = useAuthStore.getState()
  if (token) {
    await checkAuth()
  }
}
