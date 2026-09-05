
const BASE = 'http://localhost:8000'

function getToken(): string {
  return localStorage.getItem('token') || ''
}

function authHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${getToken()}`,
  }
}

function handleUnauthorized() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  window.location.href = '/login'
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: { id: number; username: string }
}

export interface UserProfile {
  id: number
  user_id: number
  real_name: string | null
  phone: string | null
  gender: string | null
  birth_year: number | null
  location: string | null
  school: string | null
  major: string | null
  degree: string | null
  graduation_year: number | null
  target_position: string | null
  target_city: string | null
  expected_salary_min: number | null
  expected_salary_max: number | null
  work_experience: string | null
  tech_skills: string | null
  about_me: string | null
  is_profile_complete: boolean
  completion: number
  username: string
}

export async function apiRegister(username: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${BASE}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || '注册失败')
  return data
}

export async function apiLogin(username: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || '登录失败')
  return data
}

export async function apiGetMe(): Promise<{ id: number; username: string }> {
  const res = await fetch(`${BASE}/api/auth/me`, { headers: authHeaders() })
  if (res.status === 401) { handleUnauthorized(); throw new Error('登录已过期') }
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || '获取用户信息失败')
  return data
}

export async function apiGetProfile(): Promise<UserProfile> {
  const res = await fetch(`${BASE}/api/profile`, { headers: authHeaders() })
  if (res.status === 401) { handleUnauthorized(); throw new Error('登录已过期') }
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || '获取档案失败')
  return data
}

export async function apiUpdateProfile(profile: Partial<UserProfile>): Promise<UserProfile> {
  const res = await fetch(`${BASE}/api/profile`, {
    method: 'PUT',
    headers: authHeaders(),
    body: JSON.stringify(profile),
  })
  if (res.status === 401) { handleUnauthorized(); throw new Error('登录已过期') }
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || '保存档案失败')
  return data
}

export async function apiChangePassword(oldPassword: string, newPassword: string): Promise<void> {
  const res = await fetch(`${BASE}/api/auth/password`, {
    method: 'PUT',
    headers: authHeaders(),
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
  })
  if (res.status === 401) { handleUnauthorized(); throw new Error('登录已过期') }
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || '修改密码失败')
}
