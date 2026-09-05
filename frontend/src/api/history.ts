const BASE = 'http://localhost:8000'

function authHeader(): Record<string, string> {
  const token = localStorage.getItem('token') || ''
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  if (method === 'DELETE') return undefined as T
  return res.json()
}



export interface ResumeHistorySavePayload {
  filename?: string
  overall_score?: number
  overall_rating?: string
  char_count?: number
  elapsed_seconds?: number
  result_json?: string
}

export interface MatchingHistorySavePayload {
  mode: 'auto' | 'specific'
  filename?: string
  resume_preview?: string
  match_score?: number
  job_name?: string
  company_name?: string
  top_k?: number
  result_json?: string
}

export interface ResumeHistoryItem {
  id: number
  filename: string | null
  overall_score: number | null
  overall_rating: string | null
  char_count: number | null
  elapsed_seconds: number | null
  created_at: string
}

export interface ResumeHistoryDetail extends ResumeHistoryItem {
  result_json: string | null
}

export interface MatchingHistoryItem {
  id: number
  mode: 'auto' | 'specific'
  filename: string | null
  resume_preview: string | null
  match_score: number | null
  job_name: string | null
  company_name: string | null
  top_k: number | null
  result_json: string | null
  created_at: string
}

export interface InterviewHistoryItem {
  id: number
  session_id: string | null
  style: string | null
  style_name: string | null
  job_name: string | null
  turns: number
  duration_seconds: number | null
  created_at: string
}

export interface InterviewRecordDetail extends InterviewHistoryItem {
  history: Array<{ role: string; content: string }>
  summary: string | null
}

export interface HistoryList<T> {
  total: number
  page: number
  items: T[]
}



export function apiSaveResumeAnalysis(payload: ResumeHistorySavePayload) {
  return req<{ id: number; created_at: string }>('POST', '/api/history/resume/save', payload)
}

export function apiSaveMatchingHistory(payload: MatchingHistorySavePayload) {
  return req<{ id: number; created_at: string }>('POST', '/api/history/matching/save', payload)
}



export function apiGetResumeHistory(page = 1, limit = 10) {
  return req<HistoryList<ResumeHistoryItem>>('GET', `/api/history/resume?page=${page}&limit=${limit}`)
}

export function apiGetMatchingHistory(page = 1, limit = 10) {
  return req<HistoryList<MatchingHistoryItem>>('GET', `/api/history/matching?page=${page}&limit=${limit}`)
}

export function apiGetInterviewHistory(page = 1, limit = 10) {
  return req<HistoryList<InterviewHistoryItem>>('GET', `/api/history/interview?page=${page}&limit=${limit}`)
}



export function apiGetResumeDetail(id: number) {
  return req<ResumeHistoryDetail>('GET', `/api/history/resume/${id}`)
}

export function apiGetInterviewDetail(id: number) {
  return req<InterviewRecordDetail>('GET', `/api/history/interview/${id}`)
}



export function apiDeleteHistory(type: 'resume' | 'matching' | 'interview', id: number) {
  return req<void>('DELETE', `/api/history/${type}/${id}`)
}

export interface FavoriteJobItem {
  fav_id: number
  job_id: number
  favorited_at: string
  job_name: string | null
  company_name: string | null
  work_city: string | null
  job_salary: string | null
  your_education: string | null
  working_exp: string | null
  company_size: string | null
  work_type: string | null
  job_summary: string | null
}

export function apiGetFavorites(page = 1, limit = 20) {
  return req<{ total: number; page: number; items: FavoriteJobItem[] }>('GET', `/api/favorites?page=${page}&limit=${limit}`)
}

