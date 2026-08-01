import { useState, useCallback } from 'react'

interface User {
  id: string
  full_name: string
  email: string
  role: string
  company_id: string
}

export function useAuth() {
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem('token')
  )
  const [user, setUser] = useState<User | null>(() => {
    const u = localStorage.getItem('user')
    return u ? JSON.parse(u) : null
  })

  const login = useCallback((accessToken: string, userData: User) => {
    localStorage.setItem('token', accessToken)
    localStorage.setItem('user', JSON.stringify(userData))
    setToken(accessToken)
    setUser(userData)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
  }, [])

  return { token, user, login, logout }
}