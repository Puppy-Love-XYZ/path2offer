
const BASE = 'http://localhost:8000'

function getToken() {
  return localStorage.getItem('token') || ''
}

export interface MatchDimension {
  score: number
  weight?: number
  label: string
  
  match?: string
  matched_skills?: string[]
  matched_count?: number
  total_count?: number
  w2v_used?: boolean
}

export interface MatchReport {
  total_score: number
  sbert_score: number
  w2v_score: number | null
  w2v_available: boolean
  dimensions: Record<string, MatchDimension>
  highlights: string[]
  suggestions: string[]
}

export interface MatchedJob {
  job_id: number
  job_name: string
  company_name: string
  work_city: string
  salary_min: number
  salary_max: number
  job_salary: string
  your_education: string
  working_exp: string
  industry_name: string
  company_size: string
  match_score: number
  report?: {
    dimensions: Record<string, MatchDimension>
  }
}

export interface IndexStatus {
  status: 'not_started' | 'indexing' | 'ready' | 'error'
  total: number
  indexed: number
  error: string | null
}

export interface JobSearchResult {
  id: number
  job_name: string
  company_name: string
  work_city: string
  job_salary: string
  your_education: string
  working_exp: string
  jd_preview: string
}

export async function fetchMatchingStatus(): Promise<IndexStatus> {
  const res = await fetch(`${BASE}/api/matching/status`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  })
  return res.json()
}

export async function fetchAutoRecommend(
  file: File,
  topK = 20,
): Promise<{ matches: MatchedJob[]; resume_preview: string; w2v_available: boolean }> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/api/matching/auto?top_k=${topK}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${getToken()}` },
    body: form,
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || '匹配失败')
  return data
}

export async function fetchSpecificMatch(
  file: File,
  jobId: number,
): Promise<{ match_score: number; report: MatchReport; job: any; resume_preview: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/api/matching/specific?job_id=${jobId}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${getToken()}` },
    body: form,
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || '匹配失败')
  return data
}

export async function fetchJobSearch(keyword: string, limit = 30): Promise<{ jobs: JobSearchResult[] }> {
  const res = await fetch(
    `${BASE}/api/matching/jobs/search?keyword=${encodeURIComponent(keyword)}&limit=${limit}`,
    { headers: { Authorization: `Bearer ${getToken()}` } },
  )
  return res.json()
}

export async function fetchJobDetail(jobId: number): Promise<any> {
  const res = await fetch(`${BASE}/api/matching/jobs/${jobId}`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  })
  return res.json()
}



export interface ParsedEdu {
  school?: string
  degree?: string
  major?: string
  start_year?: string
  end_year?: string
  awards?: string[]
  courses?: string[]
  gpa?: string
}

export interface ParsedExp {
  company?: string
  position?: string
  start_date?: string
  end_date?: string
  description?: string
  achievements?: string[]
}

export interface ParsedProject {
  name?: string
  role?: string
  tech_stack?: string[]
  description?: string
  achievements?: string[]
  github?: string
}

export interface ParsedCampus {
  organization?: string
  role?: string
  start_date?: string
  end_date?: string
  description?: string
  scale?: string
}

export interface ParsedResume {
  basic_info?: { name?: string; target_position?: string; location?: string }
  education?: ParsedEdu[]
  work_experience?: ParsedExp[]
  internships?: ParsedExp[]
  campus_experience?: ParsedCampus[]
  projects?: ParsedProject[]
  skills?: {
    technical?: string[]
    tools?: string[]
    languages?: string[]
    certifications?: string[]
    other?: string[]
  }
  awards?: string[]
}

export async function parseResume(
  file: File,
): Promise<{ parsed: ParsedResume; resume_preview: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/api/matching/parse-resume`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${getToken()}` },
    body: form,
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || '简历解析失败')
  return data
}



export interface FilterOptions {
  cities: string[]
  education_raw: string[]
  company_sizes: string[]
  work_types: string[]
  working_exps: string[]
  benefit_keywords: string[]
}

export interface FilterRequest {
  cities?: string[]
  work_types?: string[]
  salary_min?: number | null
  salary_max?: number | null
  education?: string | null
  major_keyword?: string | null
  company_sizes?: string[]
  benefit_keywords?: string[]
  working_exps?: string[]
  page?: number
  page_size?: number
}

export interface FilteredJob {
  id: number
  job_name: string
  company_name: string
  work_city: string
  job_salary: string
  salary_min: number
  salary_max: number
  your_education: string
  working_exp: string
  company_size: string
  work_type: string
  work_major: string
  industry_name: string
  job_summary: string
  company_benefits: string
}

export async function fetchFilterOptions(): Promise<FilterOptions> {
  const res = await fetch(`${BASE}/api/jobs/filter-options`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  })
  return res.json()
}

export async function fetchFilteredJobs(
  req: FilterRequest,
): Promise<{ total: number; page: number; page_size: number; jobs: FilteredJob[] }> {
  const res = await fetch(`${BASE}/api/jobs/filter`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
    body: JSON.stringify(req),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || '筛选失败')
  return data
}



export interface DeepAnalysis {
  strengths: string[]
  weaknesses: string[]
  advice: string[]
}

export interface DeepAnalysisResult {
  match_score: number
  report: MatchReport
  deep_analysis: DeepAnalysis
  job: any
  resume_preview: string
}

export async function fetchDeepAnalysis(
  file: File,
  jobId: number,
): Promise<DeepAnalysisResult> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/api/matching/deep-analysis?job_id=${jobId}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${getToken()}` },
    body: form,
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || '深度分析失败')
  return data
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

export async function fetchFavorites(
  page = 1,
  limit = 20,
): Promise<{ total: number; page: number; items: FavoriteJobItem[] }> {
  const res = await fetch(`${BASE}/api/favorites?page=${page}&limit=${limit}`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || '获取收藏失败')
  return data
}

export async function fetchFavoriteIds(): Promise<number[]> {
  const res = await fetch(`${BASE}/api/favorites/ids`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  })
  const data = await res.json()
  return data.ids ?? []
}

export async function addFavorite(jobId: number): Promise<void> {
  await fetch(`${BASE}/api/favorites/${jobId}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${getToken()}` },
  })
}

export async function removeFavorite(jobId: number): Promise<void> {
  await fetch(`${BASE}/api/favorites/${jobId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${getToken()}` },
  })
}

