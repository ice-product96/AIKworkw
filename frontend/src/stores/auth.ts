import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/client'

export interface User {
  id: string
  email: string
  role: string
  created_at: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isAuthenticated = computed(() => !!user.value)

  async function register(email: string, password: string, role: string) {
    await api.post('/auth/register', { email, password, role })
  }

  async function login(email: string, password: string) {
    const { data } = await api.post('/auth/login', { email, password })
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    await fetchMe()
  }

  async function fetchMe() {
    const { data } = await api.get('/auth/me')
    user.value = data
  }

  function logout() {
    localStorage.clear()
    user.value = null
  }

  return { user, isAuthenticated, register, login, fetchMe, logout }
})
