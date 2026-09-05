const BASE = 'http://localhost:8000'

export interface EmergenceSignals {
	岗位新兴技能占比: string | null
	新兴职位占比: string | null
	招聘次数环比增幅: string | null
	命名新颖性: string | null
}

export interface ContainedJobs {
	职位列表: string[]
	职位总数: number
}

export interface PositionDefinition {
	岗位名称: string
	核心职责: string[]
	必备技能: string[]
	加分技能: string[]
	典型行业应用场景: string[]
	所属领域: string
	新兴程度: string
	是否是新兴岗位: string
	新兴度判定信号?: EmergenceSignals
	所含职位?: ContainedJobs
}

export interface JobRecord {
	id: number
	job_name: string | null
	company_name: string | null
	job_salary: string | null
	salary_min: number | null
	salary_max: number | null
	work_city: string | null
	company_size: string | null
	your_education: string | null
	working_exp: string | null
	company_benefits: string | null
	job_summary: string | null
}

export async function fetchPositionDefinitions(params: {
	keyword?: string
	domain?: string
	emerging_only?: boolean
} = {}) {
	const queryParams = new URLSearchParams()
	if (params.keyword) queryParams.append('keyword', params.keyword)
	if (params.domain) queryParams.append('domain', params.domain)
	if (params.emerging_only !== undefined) queryParams.append('emerging_only', String(params.emerging_only))

	const res = await fetch(`${BASE}/api/position-definitions?${queryParams.toString()}`)
	if (!res.ok) throw new Error(`HTTP ${res.status}`)
	return await res.json() as { total: number; positions: PositionDefinition[] }
}

export async function fetchJobsByName(jobName: string, limit = 20) {
	const queryParams = new URLSearchParams()
	queryParams.append('position_name', jobName)
	queryParams.append('limit', String(limit))
	const res = await fetch(`${BASE}/api/jobs/by-position-name?${queryParams.toString()}`)
	if (!res.ok) throw new Error(`HTTP ${res.status}`)
	return await res.json() as { total: number; jobs: JobRecord[] }
}
