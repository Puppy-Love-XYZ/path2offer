/**
 * 认证状态管理 composable
 * 模块级响应式状态，持久化到 localStorage，无需 Pinia
 */
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

interface AuthUser {
  id: number
  username: string
}


const _token = ref<string>(localStorage.getItem('token') || '')
const _user = ref<AuthUser | null>(
  JSON.parse(localStorage.getItem('user') || 'null')
)
const _displayName = ref<string>(localStorage.getItem('displayName') || '')

export function useAuth() {
  const router = useRouter()
  const isLoggedIn = computed(() => !!_token.value)

  function login(token: string, user: AuthUser) {
    _token.value = token
    _user.value = user
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(user))
  }

  function logout() {
    _token.value = ''
    _user.value = null
    _displayName.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('displayName')
    router.push('/login')
  }

  function setDisplayName(name: string) {
    _displayName.value = name
    if (name) localStorage.setItem('displayName', name)
    else localStorage.removeItem('displayName')
  }

  return {
    token: _token,
    user: _user,
    displayName: _displayName,
    isLoggedIn,
    login,
    logout,
    setDisplayName,
  }
}
