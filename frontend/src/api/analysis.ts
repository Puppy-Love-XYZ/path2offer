const BASE = 'http://localhost:8000'

export async function fetchPersonaSummary(jobName: string) {
	try {
		const res = await fetch(`${BASE}/api/persona/summary?job_name=${encodeURIComponent(jobName)}`)
		if (!res.ok) throw new Error(`HTTP ${res.status}`)
		return await res.json()
	} catch (e) {
		console.error('fetchPersonaSummary error', e)
		return {}
	}
}

export async function fetchSalaryBoxplot(params: any) {
	try {
		const queryParams = new URLSearchParams()
		if (params.job_name) queryParams.append('job_name', params.job_name)
		if (params.group_by) queryParams.append('group_by', params.group_by)
		if (params.work_city) queryParams.append('work_city', params.work_city)
		if (params.major) queryParams.append('major', params.major)
		if (params.work_type) queryParams.append('work_type', params.work_type)

		const res = await fetch(`${BASE}/api/analysis/salary-boxplot?${queryParams.toString()}`)
		if (!res.ok) throw new Error(`HTTP ${res.status}`)
		return await res.json()
	} catch (e) {
		console.error('fetchSalaryBoxplot error', e)
		return []
	}
}

export async function fetchJobStats(jobName: string) {
	try {
		const res = await fetch(`${BASE}/jobs/stats/by-job-name?job_name=${encodeURIComponent(jobName)}`)
		if (!res.ok) throw new Error(`HTTP ${res.status}`)
		return await res.json()
	} catch (e) {
		console.error('fetchJobStats error', e)
		return {}
	}
}

export async function fetchJobNameSuggestions(prefix: string) {
	try {
		const res = await fetch(`${BASE}/jobs/names/suggestions?prefix=${encodeURIComponent(prefix)}`)
		if (!res.ok) throw new Error(`HTTP ${res.status}`)
		return await res.json()
	} catch (e) {
		console.error('fetchJobNameSuggestions error', e)
		return []
	}
}

export async function uploadResume(file: File) {
	try {
		const formData = new FormData()
		formData.append('file', file)
		const res = await fetch(`${BASE}/api/resume/analyze`, { method: 'POST', body: formData })
		if (!res.ok) throw new Error(`HTTP ${res.status}`)
		return await res.json()
	} catch (e) {
		console.error('uploadResume error', e)
		throw e
	}
}

export async function fetchTopJobCategories() {
	try {
		const res = await fetch(`${BASE}/jobs/names/top-categories`)
		if (!res.ok) throw new Error(`HTTP ${res.status}`)
		return await res.json()
	} catch (e) {
		console.error('fetchTopJobCategories error', e)
		return []
	}
}

export async function fetchJobGeoDistribution(jobName: string, city?: string, district?: string) {
	try {
		const queryParams = new URLSearchParams()
		queryParams.append('job_name', jobName)
		if (city) queryParams.append('city', city)
		if (district) queryParams.append('district', district)
		const res = await fetch(`${BASE}/api/persona/geo-distribution?${queryParams.toString()}`)
		if (!res.ok) throw new Error(`HTTP ${res.status}`)
		return await res.json()
	} catch (e) {
		console.error('fetchJobGeoDistribution error', e)
		return { job_name: jobName, city_data: [], geo_data: [], total_cities: 0, filter: {} }
	}
}

// ======================
// 岗位分类接口
// ======================
export async function fetchPersonaCategories() {
	try {
		const res = await fetch(`${BASE}/api/persona/categories`)
		if (!res.ok) throw new Error(`HTTP ${res.status}`)
		return await res.json()
	} catch (e) {
		console.error('fetchPersonaCategories error', e)
		return { categories: [], total: 0 }
	}
}

export async function fetchPersonaSearch(keyword: string = '', limit: number = 50) {
	try {
		const queryParams = new URLSearchParams()
		if (keyword) queryParams.append('keyword', keyword)
		queryParams.append('limit', limit.toString())
		const res = await fetch(`${BASE}/api/persona/search?${queryParams.toString()}`)
		if (!res.ok) throw new Error(`HTTP ${res.status}`)
		return await res.json()
	} catch (e) {
		console.error('fetchPersonaSearch error', e)
		return { total_jobs: 0, total_cities: 0, total_companies: 0, groups: [] }
	}
}


export async function fetchPersonaSearchJobs(
	jobName: string,
	keyword: string = '',
	limit: number = 20,
	offset: number = 0,
) {
	try {
		const queryParams = new URLSearchParams()
		queryParams.append('job_name', jobName)
		if (keyword) queryParams.append('keyword', keyword)
		queryParams.append('limit', limit.toString())
		queryParams.append('offset', offset.toString())
		const res = await fetch(`${BASE}/api/persona/search/jobs?${queryParams.toString()}`)
		if (!res.ok) throw new Error(`HTTP ${res.status}`)
		return await res.json()
	} catch (e) {
		console.error('fetchPersonaSearchJobs error', e)
		return { jobs: [] }
	}
}


export async function fetchPersonaWordcloud(params?: {
	job_name?: string
	keyword?: string
	category?: string
}) {
	try {
		const queryParams = new URLSearchParams()
		if (params?.job_name) queryParams.append('job_name', params.job_name)
		if (params?.keyword) queryParams.append('keyword', params.keyword)
		if (params?.category) queryParams.append('category', params.category)
		const res = await fetch(`${BASE}/api/persona/wordcloud?${queryParams.toString()}`)
		if (!res.ok) throw new Error(`HTTP ${res.status}`)
		return await res.json()
	} catch (e) {
		console.error('fetchPersonaWordcloud error', e)
		return { word_cloud_data: [] }
	}
}


export async function fetchPersonaAggregate(params?: {
	job_name?: string
	keyword?: string
	category?: string
	city?: string
}) {
	try {
		const queryParams = new URLSearchParams()
		if (params?.job_name) queryParams.append('job_name', params.job_name)
		if (params?.keyword) queryParams.append('keyword', params.keyword)
		if (params?.category) queryParams.append('category', params.category)
		if (params?.city) queryParams.append('city', params.city)
		const res = await fetch(`${BASE}/api/persona/aggregate?${queryParams.toString()}`)
		if (!res.ok) throw new Error(`HTTP ${res.status}`)
		return await res.json()
	} catch (e) {
		console.error('fetchPersonaAggregate error', e)
		return { job_name: '全部岗位', bar_data: [], bar_type: 'job', pie_data: [], box_data: [], word_cloud_data: [], map_data: [], province_data: [] }
	}
}
