<!-- PATH2OFFER-JOBPERSONA-EMERGING-PANORAMA-20260904 -->
<template>
    <div class="jp-page">
        <div class="jp-greeting-wrap">
            <PageGreeting tip="探索你的目标岗位画像，找准求职方向！" />
        </div>

        <div class="jp-top-area">
            <div class="jp-hero">
                <div class="jp-categories">
                    <span class="jp-cat-tag" :class="{ active: activeCategory === '' }"
                        @click="selectCategory('')">全部</span>
                    <span v-for="cat in categories.filter(cat=>['人工智能','智能系统','物联网','大数据'].includes(cat.name))" :key="cat.name" class="jp-cat-tag"
                        :class="{ active: activeCategory === cat.name }"
                        :style="!(activeCategory === cat.name) ? { '--cat-color': cat.color } : {}"
                        @click="selectCategory(cat.name)">
                        {{ cat.name }}
                        <em>{{ cat.count }}</em>
                    </span>
                </div>

                <div class="jp-search-bar">
                    <el-input v-model="searchKeyword" placeholder="搜索岗位名称或公司名称..." size="default" clearable
                        @input="onSearchInput" @clear="handleClear" @keyup.enter="doSearch">
                        <template #prefix><el-icon>
                                <Search />
                            </el-icon></template>
                    </el-input>
                    <button
                        class="jp-search-submit"
                        type="button"
                        :disabled="searching"
                        style="background:radial-gradient(circle at 18% -35%,rgba(97,194,202,.28),transparent 46%),linear-gradient(135deg,#17283a 0%,#1c4653 56%,#26656b 100%) !important;color:#f7ffff !important;border-color:rgba(58,126,134,.72) !important;"
                        @click="doSearch"
                    >
                        <span class="jp-search-submit__edge jp-search-submit__edge--top" aria-hidden="true"></span>
                        <span class="jp-search-submit__edge jp-search-submit__edge--corner" aria-hidden="true"></span>
                        <el-icon class="jp-search-submit__icon" :class="{ 'is-spinning': searching }">
                            <Loading v-if="searching" />
                            <Search v-else />
                        </el-icon>
                        <span class="jp-search-submit__text">{{ searching ? '搜索中' : '搜索' }}</span>
                    </button>
                </div>
            </div>

            <transition name="slide-down">
                <div v-if="showResults" class="jp-results-panel">
                    <div v-if="searchKeyword.trim()" class="jp-stats-bar">
                        <div class="jp-stat">
                            <span class="jp-stat__num">{{ resultSummary.total_jobs.toLocaleString() }}</span>
                            <span class="jp-stat__label">个岗位</span>
                        </div>
                        <div class="jp-stat-divider"></div>
                        <div class="jp-stat">
                            <span class="jp-stat__num">{{ resultSummary.total_cities }}</span>
                            <span class="jp-stat__label">个城市在招</span>
                        </div>
                        <div class="jp-stat-divider"></div>
                        <div class="jp-stat">
                            <span class="jp-stat__num">{{ resultSummary.total_companies.toLocaleString() }}</span>
                            <span class="jp-stat__label">家公司在招</span>
                        </div>
                        <div class="jp-stats-keyword">
                            关键词：<strong>{{ resultSummary.keyword }}</strong>
                        </div>
                        <el-button size="small" text @click="handleReset">清除筛选</el-button>
                    </div>

                    <div v-if="selectedJobName" class="jp-selected-tip">
                        <el-icon>
                            <InfoFilled />
                        </el-icon>
                        图表正在显示：<strong>{{ selectedJobName }}</strong> 的数据
                        <el-button size="small" text type="primary" @click="clearSelectedJob">查看全部搜索结果</el-button>
                    </div>

                    <div class="jp-group-list">
                        <div v-for="group in searchGroups" :key="group.job_name" class="jp-group"
                            :class="{ 'is-selected': selectedJobName === group.job_name }"
                            @click="selectJobForChart(group.job_name)">
                            <div class="jp-group__header">
                                <div class="jp-group__left">
                                    <span class="jp-group__name">{{ group.job_name }}</span>
                                    <el-tag size="small" effect="plain">{{ group.count }} 个岗位</el-tag>
                                    <span class="jp-group__meta">{{ group.city_count }} 城市 · {{ group.company_count }}
                                        公司</span>
                                    <span v-if="group.avg_salary > 0" class="jp-group__salary">
                                        均薪 {{ group.avg_salary }}K
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </transition>
        </div>

        <div class="jp-charts-section" :class="{ 'is-panorama': viewMode === 'panorama' }">
        <div class="jp-charts-section" :class="{ 'is-panorama': viewMode === 'panorama' }">
            <div class="jp-charts-header">
                <div class="jp-charts-header__left">
            <div class="jp-charts-view">
                <button class="jp-charts-switch" :class="{ active: viewMode === 'overview' }" @click="viewMode = 'overview'">
                        {{ activeCategory ? '分类画像' : '综合画像' }}
                    </button>
                    <button class="jp-charts-switch" :class="{ active: viewMode === secondaryViewMode }" @click="switchGraphView">
                        {{ isDomainCategory ? '领域视图' : '全景图谱' }}
                    </button>
                </div>
                </div>
                <el-button v-if="currentFilter.job_name || currentFilter.keyword || currentFilter.category" size="small"
                    @click="handleReset">
                    重置为全部数据
                </el-button>
            </div>

            <div v-if="viewMode === 'panorama'" class="jp-panorama-wrapper">
                <PanoramaGraph :key="panoramaViewKey" :emerging-threshold="PANORAMA_EMERGING_THRESHOLD" />
            </div>

            <div v-else-if="viewMode === 'domain'" class="jp-domain-wrapper">
                <DomainViewGraph :domain-name="activeCategory" />
            </div>

            <div v-else-if="chartsLoading" class="jp-charts-skeleton">
                <div v-for="i in 5" :key="i" class="jp-skeleton-card"></div>
            </div>

            <div v-else class="jp-charts-grid">
                <div class="jp-chart-card jp-chart-card--bar">
                    <div class="jp-card-header">
                        <span class="jp-card-title">
                            {{ aggregateData.bar_type === 'industry' ? '行业分布 Top 15' : '岗位数量排名 Top 15' }}
                        </span>
                    </div>
                    <EChartsCard :options="barChartOptions" height="100%" />
                </div>

                <div class="jp-chart-card jp-chart-card--pie">
                    <div class="jp-card-header">
                        <span class="jp-card-title">学历要求分布</span>
                    </div>
                    <EChartsCard :options="pieChartOptions" height="100%" />
                </div>

                <div class="jp-chart-card jp-chart-card--map">
                    <div class="jp-card-header">
                        <span class="jp-card-title">地理热力分布</span>
                        <el-button size="small" text type="primary" style="margin-left:auto;font-size:12px;"
                            @click="resetToNational">重置全国</el-button>
                    </div>
                    <EChartsCard :options="mapChartOptions" height="100%" @chart-click="onMapClick" />
                </div>

                <div class="jp-chart-card jp-chart-card--box">
                    <div class="jp-card-header">
                        <span class="jp-card-title">薪资分布（按学历）</span>
                    </div>
                    <EChartsCard :options="boxChartOptions" height="100%" />
                </div>

                <div class="jp-chart-card jp-chart-card--cloud">
                    <div class="jp-card-header">
                        <span class="jp-card-title">技能关键词云</span>
                        <span v-if="wordCloudLoading" style="margin-left:8px;font-size:12px;color:#9ca3af">
                            <el-icon class="is-loading">
                                <Loading />
                            </el-icon> 提取关键词中...
                        </span>
                        <span v-else-if="(aggregateData.word_cloud_data || []).length"
                            style="margin-left:8px;font-size:12px;color:#67c23a">
                            ✓ {{ (aggregateData.word_cloud_data || []).length }} 个关键词
                        </span>
                    </div>
                    <EChartsCard :options="wordCloudOptions" height="100%" />
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ref, computed, onMounted, watch } from 'vue'
import EChartsCard from '../components/EChartsCard.vue'
import PanoramaGraph from '../components/PanoramaGraph.vue'
import DomainViewGraph from '../components/DomainViewGraph.vue'
import PanoramaGraph from '../components/PanoramaGraph.vue'
import DomainViewGraph from '../components/DomainViewGraph.vue'
import PageGreeting from '@/components/PageGreeting.vue'
import {
    fetchPersonaCategories,
    fetchPersonaSearch,
    fetchPersonaAggregate,
    fetchPersonaWordcloud,
} from '../api/analysis'
import { Search, Loading, InfoFilled } from '@element-plus/icons-vue'
import { Search, Loading, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import chinaJson from '../assets/china-full.json'
echarts.registerMap('china', chinaJson as any)

const categories = ref<any[]>([])
const activeCategory = ref('')

const searchKeyword = ref('')
const searching = ref(false)
const showResults = ref(false)
const searchGroups = ref<any[]>([])
const resultSummary = ref({ total_jobs: 0, total_cities: 0, total_companies: 0, keyword: '' })
const selectedJobName = ref('')
let searchDebounce: number | null = null

const chartsLoading = ref(false)
const wordCloudLoading = ref(false)
const aggregateData = ref<any>({
    job_name: '全部岗位', bar_data: [], bar_type: 'job', pie_data: [], box_data: [], word_cloud_data: [], map_data: [], province_data: [],
})
const mapProvinceData = ref<any[]>([])
const mapCityData = ref<any[]>([])
const selectedCityName = ref('')
const currentFilter = ref<{ job_name?: string; keyword?: string; category?: string; city?: string }>({})
const PANORAMA_EMERGING_THRESHOLD = 20
const viewMode = ref<'overview' | 'panorama' | 'domain'>('overview')
const panoramaViewKey = ref(0)
const DOMAIN_SET = new Set(['人工智能', '智能系统', '物联网', '大数据'])
const isDomainCategory = computed(() => DOMAIN_SET.has(activeCategory.value))
const secondaryViewMode = computed(() => (isDomainCategory.value ? 'domain' : 'panorama'))

const switchGraphView = () => {
    const nextView = secondaryViewMode.value
    if (nextView === 'panorama') panoramaViewKey.value += 1
    viewMode.value = nextView
}

const selectCategory = async (name: string) => {
    activeCategory.value = name
    viewMode.value = 'overview'
    searchKeyword.value = ''
    showResults.value = false
    searchGroups.value = []
    selectedJobName.value = ''
    currentFilter.value = name ? { category: name } : {}
    await loadCharts(currentFilter.value)
}

const normalizeViewMode = () => {
    if (!isDomainCategory.value && viewMode.value === 'domain') {
        viewMode.value = 'panorama'
    }
}

const normalizeViewMode = () => {
    if (!isDomainCategory.value && viewMode.value === 'domain') {
        viewMode.value = 'panorama'
    }
}

const onSearchInput = () => {
    if (searchDebounce) clearTimeout(searchDebounce)
    searchDebounce = window.setTimeout(() => {
        if (searchKeyword.value.trim()) doSearch()
        else handleClear()
    }, 400)
}

const doSearch = async () => {
    const kw = searchKeyword.value.trim()
    if (!kw) return
    searching.value = true
    activeCategory.value = ''
    selectedJobName.value = ''
    try {
        const result = await fetchPersonaSearch(kw, 50)
        searchGroups.value = (result.groups || []).map((g: any) => ({
            ...g, _expanded: false, _loading: false, _jobs: [],
        }))
        resultSummary.value = {
            total_jobs: result.total_jobs || 0,
            total_cities: result.total_cities || 0,
            total_companies: result.total_companies || 0,
            keyword: kw,
        }
        showResults.value = true
        currentFilter.value = { keyword: kw }
        await loadCharts({ keyword: kw })
    } catch {
        ElMessage.error('搜索失败，请重试')
    } finally {
        searching.value = false
    }
}

const handleClear = () => {
    searchKeyword.value = ''
    showResults.value = false
    searchGroups.value = []
    selectedJobName.value = ''
    activeCategory.value = ''
    currentFilter.value = {}
    normalizeViewMode()
    normalizeViewMode()
    loadCharts({})
}

const handleReset = () => {
    handleClear()
}

const selectJobForChart = async (jobName: string) => {
    selectedJobName.value = jobName
    currentFilter.value = { job_name: jobName }
    showResults.value = false
    await loadCharts({ job_name: jobName })
}

const selectCity = async (cityName: string) => {
    selectedCityName.value = cityName
    const params = { ...currentFilter.value, city: cityName }
    currentFilter.value = params
    await loadCharts(params, false)
}

const resetToNational = () => {
    selectedCityName.value = ''
    searchKeyword.value = ''
    showResults.value = false
    activeCategory.value = ''
    currentFilter.value = {}
    normalizeViewMode()
    normalizeViewMode()
    loadCharts({}, true)
}

const onMapClick = (params: any) => {
    if (params.seriesType === 'effectScatter' && params.name) {
        selectCity(params.name)
    }
}

const clearSelectedJob = async () => {
    selectedJobName.value = ''
    const kw = searchKeyword.value.trim()
    currentFilter.value = kw ? { keyword: kw } : {}
    await loadCharts(currentFilter.value)
}

const loadCharts = async (
    params: { job_name?: string; keyword?: string; category?: string; city?: string },
    updateMap = true,
) => {
    chartsLoading.value = true
    try {
        const data = await fetchPersonaAggregate(params)
        aggregateData.value = data
        if (updateMap) {
            mapProvinceData.value = data.province_data || []
            mapCityData.value = data.map_data || []
        }
    } catch {
        ElMessage.error('加载图表数据失败')
    } finally {
        chartsLoading.value = false
    }
    wordCloudLoading.value = true
    fetchPersonaWordcloud(params as any)
        .then(wc => { aggregateData.value = { ...aggregateData.value, word_cloud_data: wc.word_cloud_data || [] } })
        .finally(() => { wordCloudLoading.value = false })
}

const COLORS = ['#4A7DC8', '#5B9FB8', '#4B9A8E', '#8B7AB8', '#7E9872', '#8B9EB8', '#A8946A', '#6A8A9E']

const barChartOptions = computed(() => {
    const data = aggregateData.value.bar_data || []
    const isIndustry = aggregateData.value.bar_type === 'industry'
    return {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, confine: true },
        grid: { left: 8, right: 24, bottom: 8, top: 8, containLabel: true },
        xAxis: {
            type: 'value',
            name: '数量',
            nameTextStyle: { color: '#7A8EA8', fontSize: 10 },
            splitLine: { lineStyle: { type: 'dashed', color: '#E2ECF5' } },
            axisLabel: { fontSize: 10, color: '#7A8EA8' },
        },
        yAxis: {
            type: 'category',
            data: data.map((d: any) => d.name),
            axisLabel: { fontSize: 11, color: '#2A4268', width: isIndustry ? 100 : 80, overflow: 'truncate' },
            axisLine: { lineStyle: { color: '#D8E5F0' } },
            inverse: true,
        },
        series: [{
            type: 'bar',
            data: data.map((d: any, i: number) => ({
                value: d.value,
                itemStyle: { color: COLORS[i % COLORS.length], borderRadius: [0, 4, 4, 0] },
            })),
            barMaxWidth: 24,
            label: { show: true, position: 'right', fontSize: 10, color: '#4A6280' },
        }],
    }
})

const pieChartOptions = computed(() => {
    const data = aggregateData.value.pie_data || []
    return {
        tooltip: {
            trigger: 'item',
            confine: true,
            formatter: (p: any) => `${p.name}<br/>岗位数：${p.value}（${p.percent}%）`,
        },
        legend: {
            orient: 'vertical',
            left: '2%',
            top: 'center',
            itemWidth: 10,
            itemHeight: 10,
            textStyle: { fontSize: 11, color: '#2A4268' },
        },
        series: [{
            type: 'pie',
            radius: ['42%', '72%'],
            center: ['65%', '50%'],
            data: data.map((d: any, i: number) => ({
                name: d.name, value: d.value,
                itemStyle: { color: COLORS[i % COLORS.length] },
            })),
            label: { show: false },
            emphasis: { label: { show: true, fontSize: 12, fontWeight: 'bold' } },
        }],
    }
})

const boxChartOptions = computed(() => {
    const data = aggregateData.value.box_data || []
    return {
        tooltip: {
            trigger: 'item',
            confine: true,
            padding: [6, 10],
            textStyle: { fontSize: 12 },
            formatter: (p: any) => {
                const v = p.data
                return `<b>${p.name}</b><br/>最低 ${v[1]}K&nbsp;&nbsp;Q1 ${v[2]}K<br/>中位 ${v[3]}K&nbsp;&nbsp;Q3 ${v[4]}K<br/>最高 ${v[5]}K`
            },
        },
        grid: { left: 8, right: 16, bottom: 8, top: 8, containLabel: true },
        xAxis: {
            type: 'category',
            data: data.map((d: any) => d.name),
            axisLabel: { fontSize: 10, color: '#2A4268', interval: 0, width: 46, overflow: 'truncate', margin: 8 },
        },
        yAxis: { type: 'value', name: '薪资 (K)', nameTextStyle: { fontSize: 10, color: '#7A8EA8' }, splitLine: { lineStyle: { type: 'dashed', color: '#E2ECF5' } } },
        series: [{
            type: 'boxplot',
            data: data.map((d: any) => [d.min, d.q1, d.median, d.q3, d.max]),
            itemStyle: { color: 'rgba(74,125,200,0.10)', borderColor: '#4A7DC8', borderWidth: 2 },
        }],
    }
})

const wordCloudOptions = computed(() => {
    const data = aggregateData.value.word_cloud_data || []
    if (!data.length) {
        return {
            graphic: [{
                type: 'text',
                left: 'center', top: 'middle',
                style: { text: wordCloudLoading.value ? '正在提取技能关键词...' : '暂无数据', fill: '#9ca3af', fontSize: 14 }
            }]
        }
    }

    const PALETTE = [
        '#4A7DC8', '#5B9FB8', '#4B9A8E', '#8B7AB8',
        '#7E9872', '#6A8A9E', '#A8946A', '#5B7A9E',
        '#7E6B9E', '#4A7E8A', '#6A9070', '#9E8A5B',
    ]
    let colorIdx = 0
    const colorMap: Record<string, string> = {}

    const sorted = [...data].sort((a: any, b: any) => b.value - a.value)
    sorted.forEach((d: any, i: number) => {
        colorMap[d.name as string] = i < 5
            ? (['#0C1A2D', '#152845', '#1C3456', '#2B5382', '#3B6FA8'] as string[])[i] ?? '#4A7DC8'
            : PALETTE[colorIdx++ % PALETTE.length] ?? '#4A7DC8'
    })

    return {
        tooltip: {
            show: true,
            formatter: (params: any) => {
                const pct = Math.round(params.value / 10)
                return `<b>${params.name}</b><br/>技能权重：${pct}%`
            }
        },
        series: [{
            type: 'wordCloud',
            shape: 'circle',
            left: 'center',
            top: 'center',
            width: '95%',
            height: '90%',
            sizeRange: [11, 52],
            rotationRange: [-45, 45],
            rotationStep: 15,
            gridSize: 6,
            drawOutOfBound: false,
            layoutAnimation: true,
            textStyle: {
                fontFamily: "'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif",
                fontWeight: 'bold',
                color: (params: any) => colorMap[params.name] || PALETTE[0],
            },
            emphasis: {
                focus: 'self',
                textStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.25)' },
            },
            data: data.map((d: any) => ({ name: d.name, value: d.value })),
        }],
    }
})

const PROV_FULL: Record<string, string> = {
    "北京": "北京市", "天津": "天津市", "上海": "上海市", "重庆": "重庆市",
    "河北": "河北省", "山西": "山西省", "辽宁": "辽宁省", "吉林": "吉林省",
    "黑龙江": "黑龙江省", "江苏": "江苏省", "浙江": "浙江省", "安徽": "安徽省",
    "福建": "福建省", "江西": "江西省", "山东": "山东省", "河南": "河南省",
    "湖北": "湖北省", "湖南": "湖南省", "广东": "广东省", "海南": "海南省",
    "四川": "四川省", "贵州": "贵州省", "云南": "云南省", "陕西": "陕西省",
    "甘肃": "甘肃省", "青海": "青海省",
    "内蒙古": "内蒙古自治区", "广西": "广西壮族自治区", "西藏": "西藏自治区",
    "宁夏": "宁夏回族自治区", "新疆": "新疆维吾尔自治区",
    "香港": "香港特别行政区", "澳门": "澳门特别行政区", "台湾": "台湾省",
}
const PROV_SHORT = Object.fromEntries(Object.entries(PROV_FULL).map(([k, v]) => [v, k]))

const mapChartOptions = computed(() => {
    const cityData = mapCityData.value
    const provData = mapProvinceData.value
    const maxVal = Math.max(...provData.map((d: any) => d.value), 1)
    const top5 = [...cityData].sort((a: any, b: any) => b.value - a.value).slice(0, 5)
    const top5MaxVal = Math.max(...top5.map((x: any) => x.value), 1)

    const provMap: Record<string, number> = {}
    provData.forEach((d: any) => { provMap[d.name] = d.value })

    const selCity = selectedCityName.value
    const normalDots = top5.filter((d: any) => d.name !== selCity)
    const selectedDots = top5.filter((d: any) => d.name === selCity)

    const dotSize = (jobCount: number) => Math.max(10, Math.min(22, jobCount / top5MaxVal * 20))

    return {
        tooltip: {
            trigger: 'item',
            confine: true,
            formatter: (p: any) => {
                if (p.seriesType === 'effectScatter') {
                    const d = p.data
                    return `<b>${d.name}</b><br/>岗位数：${d.jobCount}<br/>均薪：${d.avg_salary}K<br/><span style="color:#93c5fd;font-size:11px">点击查看该城市画像</span>`
                }
                const shortName = PROV_SHORT[p.name] || p.name
                const val = provMap[shortName]
                return val != null
                    ? `<b>${shortName}</b><br/>岗位数：${val.toLocaleString()}`
                    : (p.name || '')
            },
        },
        visualMap: {
            min: 0, max: maxVal,
            text: ['多', '少'],
            calculable: true,
            seriesIndex: 0,
            inRange: { color: ['#dbeafe', '#93c5fd', '#3b82f6', '#1d4ed8', '#1e3a8a'] },
            left: 'left', bottom: '5%',
            textStyle: { color: '#555', fontSize: 11 },
            itemHeight: 80,
        },
        geo: {
            map: 'china', roam: true, zoom: 1.2,
            center: [104, 36],
            top: '5%', bottom: '5%', left: '6%', right: '6%',
            selectedMode: false,
            label: { show: false },
            itemStyle: { areaColor: '#f0f6ff', borderColor: '#c8d6e5', borderWidth: 0.8 },
            emphasis: {
                itemStyle: { areaColor: '#bfdbfe' },
                label: { show: true, fontSize: 11, color: '#1e40af' },
            },
        },
        series: [
            {
                type: 'map',
                map: 'china',
                geoIndex: 0,
                silent: true,
                data: provData.map((d: any) => ({
                    name: PROV_FULL[d.name] || d.name,
                    value: d.value,
                })),
            },
            {
                type: 'effectScatter',
                coordinateSystem: 'geo',
                data: normalDots.map((d: any) => ({
                    name: d.name,
                    value: [d.lng, d.lat],
                    jobCount: d.value,
                    avg_salary: d.avg_salary,
                })),
                symbolSize: (_v: any, params: any) => dotSize(params.data.jobCount),
                rippleEffect: { brushType: 'stroke', scale: 3, period: 4 },
                itemStyle: { color: '#2563eb', opacity: 0.9 },
                label: {
                    show: true,
                    formatter: (p: any) => p.name,
                    fontSize: 10, color: '#1e40af', position: 'top', fontWeight: 'bold',
                },
                cursor: 'pointer', z: 10,
            },
            {
                type: 'effectScatter',
                coordinateSystem: 'geo',
                data: selectedDots.map((d: any) => ({
                    name: d.name,
                    value: [d.lng, d.lat],
                    jobCount: d.value,
                    avg_salary: d.avg_salary,
                })),
                symbolSize: (_v: any, params: any) => dotSize(params.data.jobCount) + 4,
                rippleEffect: { brushType: 'fill', scale: 4, period: 2.5 },
                itemStyle: { color: '#f59e0b', opacity: 1 },
                label: {
                    show: true,
                    formatter: (p: any) => p.name,
                    fontSize: 11, color: '#b45309', position: 'top', fontWeight: 'bold',
                },
                cursor: 'pointer', z: 15,
            },
        ],
    }
})

onMounted(async () => {
    const [,] = await Promise.all([
        fetchPersonaCategories().then(d => { categories.value = d.categories || [] }),
        loadCharts({}),
    ])
})

watch(activeCategory, () => {
    normalizeViewMode()
})

watch(activeCategory, () => {
    normalizeViewMode()
})
</script>

<style scoped>
.jp-page {
    background: transparent;
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    position: relative;
    height: calc(100vh - 42px);
    min-height: 0;
    height: calc(100vh - 42px);
    min-height: 0;
    font-family: 'Inter', 'PingFang SC', 'Helvetica Neue', system-ui, sans-serif;
    -webkit-font-smoothing: antialiased;
}

.jp-greeting-wrap {
    padding: 4px 16px 0;
    padding: 4px 16px 0;
}

.jp-top-area {
    flex: 0 0 auto;
    flex: 0 0 auto;
    min-height: 0;
    position: relative;
    z-index: 10;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.jp-hero {
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 5px;
    padding: 0 16px;
    gap: 5px;
    padding: 0 16px;
    height: 100%;
    background: transparent;
    border-bottom: none;
}

.jp-categories {
    display: flex;
    flex-wrap: nowrap;
    gap: 5px;
    overflow-x: auto;
}

/* 分类标签 + 搜索框 同行布局 */
.jp-toolbar {
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: nowrap;
}

.jp-toolbar .jp-search-bar {
    flex: 0 1 480px;
    min-width: 300px;
    margin-left: auto;
}

.jp-categories::-webkit-scrollbar {
    display: none;
}

.jp-cat-tag {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 7px 15px;
    padding: 7px 15px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(20, 48, 80, 0.14);
    color: #2A4268;
    font-size: 12.8px;
    font-size: 12.8px;
    font-weight: 500;
    font-family: 'Inter', 'PingFang SC', system-ui, sans-serif;
    cursor: pointer;
    transition: all 0.18s cubic-bezier(0.34, 1.56, 0.64, 1);
    user-select: none;
    white-space: nowrap;
    flex-shrink: 0;
    box-shadow: 0 1px 4px rgba(12, 26, 45, 0.07);
}

.jp-cat-tag:hover {
    background: rgba(234, 242, 252, 0.98);
    border-color: rgba(20, 48, 80, 0.35);
    color: #142038;
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(12, 26, 45, 0.12);
}

.jp-cat-tag.active {
    background: linear-gradient(135deg, #17283a 0%, #28465f 100%);
    background: linear-gradient(135deg, #17283a 0%, #28465f 100%);
    color: rgba(255, 255, 255, 0.95);
    border-color: transparent;
    font-weight: 700;
    box-shadow: 0 4px 14px rgba(12, 26, 45, 0.30);
    transform: translateY(-2px);
}

.jp-cat-tag em {
    font-style: normal;
    font-size: 11px;
    opacity: 0.75;
}

.jp-search-bar {
    display: flex;
    gap: 8px;
}

.jp-search-bar .el-input {
    flex: 1;
}

.jp-search-bar :deep(.el-input__wrapper) {
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.94);
    box-shadow: none;
    border: 1px solid rgba(20, 48, 80, 0.14);
    transition: all 0.2s;
}

.jp-search-bar :deep(.el-input__wrapper:hover) {
    border-color: rgba(20, 48, 80, 0.35);
    box-shadow: 0 2px 8px rgba(12, 26, 45, 0.08);
}

.jp-search-bar :deep(.el-input__wrapper.is-focus) {
    border-color: #3B6FA8;
    box-shadow: 0 0 0 3px rgba(59, 111, 168, 0.12);
}

.jp-search-bar :deep(.el-input__prefix-inner .el-icon) {
    color: #3B6FA8;
}

.jp-search-submit {
    position: relative;
    isolation: isolate;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    min-width: 96px;
    height: 38px;
    padding: 0 18px;
    overflow: hidden;
    border: 1px solid rgba(59, 126, 134, .62);
    border-radius: 10px;
    background:
        radial-gradient(90% 130% at 20% -45%, rgba(108, 208, 210, .26) 0%, rgba(108, 208, 210, 0) 48%),
        linear-gradient(135deg, #162b3d 0%, #1a4352 52%, #235e67 100%);
    color: #f5ffff;
    font-family: 'Segoe UI Variable Display', 'Aptos', 'Segoe UI', 'Microsoft YaHei UI', 'PingFang SC', system-ui, sans-serif;
    font-size: 13.25px;
.jp-search-submit {
    position: relative;
    isolation: isolate;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    min-width: 96px;
    height: 38px;
    padding: 0 18px;
    overflow: hidden;
    border: 1px solid rgba(59, 126, 134, .62);
    border-radius: 10px;
    background:
        radial-gradient(90% 130% at 20% -45%, rgba(108, 208, 210, .26) 0%, rgba(108, 208, 210, 0) 48%),
        linear-gradient(135deg, #162b3d 0%, #1a4352 52%, #235e67 100%);
    color: #f5ffff;
    font-family: 'Segoe UI Variable Display', 'Aptos', 'Segoe UI', 'Microsoft YaHei UI', 'PingFang SC', system-ui, sans-serif;
    font-size: 13.25px;
    font-weight: 600;
    line-height: 1;
    letter-spacing: .04em;
    white-space: nowrap;
    cursor: pointer;
    box-shadow:
        0 6px 16px rgba(15, 43, 56, .19),
        inset 0 1px 0 rgba(255,255,255,.16),
        inset 0 -1px 0 rgba(5, 31, 39, .18);
    transition:
        transform .18s ease,
        box-shadow .18s ease,
        filter .18s ease,
        border-color .18s ease;
    -webkit-font-smoothing: antialiased;
    text-rendering: geometricPrecision;
}

.jp-search-submit__edge {
    position: absolute;
    z-index: 0;
    pointer-events: none;
}

.jp-search-submit__edge--top {
    top: 0;
    left: 13px;
    width: 48%;
    height: 1px;
    background: linear-gradient(
        90deg,
        transparent,
        rgba(188,239,238,.88),
        transparent
    );
    line-height: 1;
    letter-spacing: .04em;
    white-space: nowrap;
    cursor: pointer;
    box-shadow:
        0 6px 16px rgba(15, 43, 56, .19),
        inset 0 1px 0 rgba(255,255,255,.16),
        inset 0 -1px 0 rgba(5, 31, 39, .18);
    transition:
        transform .18s ease,
        box-shadow .18s ease,
        filter .18s ease,
        border-color .18s ease;
    -webkit-font-smoothing: antialiased;
    text-rendering: geometricPrecision;
}

.jp-search-submit__edge {
    position: absolute;
    z-index: 0;
    pointer-events: none;
}

.jp-search-submit__edge--top {
    top: 0;
    left: 13px;
    width: 48%;
    height: 1px;
    background: linear-gradient(
        90deg,
        transparent,
        rgba(188,239,238,.88),
        transparent
    );
}

.jp-search-submit__edge--corner {
    right: 0;
    bottom: 0;
    width: 15px;
    height: 15px;
    border-right: 2px solid rgba(105,201,197,.48);
    border-bottom: 2px solid rgba(105,201,197,.48);
    border-radius: 0 0 7px 0;
}

.jp-search-submit__text {
    position: relative;
    z-index: 2;
    color: #f7ffff;
    font-family: 'Segoe UI Variable Display', 'Aptos', 'Segoe UI', 'Microsoft YaHei UI', 'PingFang SC', system-ui, sans-serif;
    font-size: 13.25px;
    font-weight: 600;
    line-height: 1;
    letter-spacing: .105em;
    text-shadow:
        0 1px 0 rgba(0,0,0,.18),
        0 0 9px rgba(111, 218, 216, .15);
    transform: translateY(-.3px);
    text-rendering: geometricPrecision;
    -webkit-font-smoothing: antialiased;
}

.jp-search-submit__icon {
    position: relative;
    z-index: 2;
    color: rgba(226, 249, 248, .94);
    font-size: 14px;
    opacity: .94;
    filter: drop-shadow(0 0 4px rgba(101, 202, 201, .14));
}


.jp-search-submit__edge {
    position: absolute;
    z-index: 0;
    pointer-events: none;
}

.jp-search-submit__edge--top {
    top: 0;
    left: 13px;
    width: 48%;
    height: 1px;
    background: linear-gradient(
        90deg,
        transparent,
        rgba(188,239,238,.88),
        transparent
    );
}

.jp-search-submit__edge--corner {
    right: 0;
    bottom: 0;
    width: 15px;
    height: 15px;
    border-right: 2px solid rgba(105,201,197,.48);
    border-bottom: 2px solid rgba(105,201,197,.48);
    border-radius: 0 0 7px 0;
}





.jp-search-submit__text {
    position: relative;
    z-index: 1;
    font-family: inherit;
    font-weight: 500;
}

.jp-search-submit__icon {
    position: relative;
    z-index: 1;
    font-size: 15px;
    color: rgba(235, 252, 253, .98);
}



.jp-search-submit:hover:not(:disabled) {
.jp-search-submit__edge--corner {
    right: 0;
    bottom: 0;
    width: 15px;
    height: 15px;
    border-right: 2px solid rgba(105,201,197,.48);
    border-bottom: 2px solid rgba(105,201,197,.48);
    border-radius: 0 0 7px 0;
}

.jp-search-submit__text {
    position: relative;
    z-index: 2;
    color: #f7ffff;
    font-family: 'Segoe UI Variable Display', 'Aptos', 'Segoe UI', 'Microsoft YaHei UI', 'PingFang SC', system-ui, sans-serif;
    font-size: 13.25px;
    font-weight: 600;
    line-height: 1;
    letter-spacing: .105em;
    text-shadow:
        0 1px 0 rgba(0,0,0,.18),
        0 0 9px rgba(111, 218, 216, .15);
    transform: translateY(-.3px);
    text-rendering: geometricPrecision;
    -webkit-font-smoothing: antialiased;
}

.jp-search-submit__icon {
    position: relative;
    z-index: 2;
    color: rgba(226, 249, 248, .94);
    font-size: 14px;
    opacity: .94;
    filter: drop-shadow(0 0 4px rgba(101, 202, 201, .14));
}


.jp-search-submit__edge {
    position: absolute;
    z-index: 0;
    pointer-events: none;
}

.jp-search-submit__edge--top {
    top: 0;
    left: 13px;
    width: 48%;
    height: 1px;
    background: linear-gradient(
        90deg,
        transparent,
        rgba(188,239,238,.88),
        transparent
    );
}

.jp-search-submit__edge--corner {
    right: 0;
    bottom: 0;
    width: 15px;
    height: 15px;
    border-right: 2px solid rgba(105,201,197,.48);
    border-bottom: 2px solid rgba(105,201,197,.48);
    border-radius: 0 0 7px 0;
}





.jp-search-submit__text {
    position: relative;
    z-index: 1;
    font-family: inherit;
    font-weight: 500;
}

.jp-search-submit__icon {
    position: relative;
    z-index: 1;
    font-size: 15px;
    color: rgba(235, 252, 253, .98);
}



.jp-search-submit:hover:not(:disabled) {
    transform: translateY(-1px);
    border-color: rgba(73, 149, 154, .74);
    filter: brightness(1.055);
    box-shadow:
        0 9px 20px rgba(15, 43, 56, .23),
        0 0 0 1px rgba(74, 145, 151, .07),
        inset 0 1px 0 rgba(255,255,255,.19);
}

.jp-search-submit:active:not(:disabled) {
    transform: translateY(0);
    filter: brightness(.97);
    box-shadow:
        0 3px 9px rgba(14,40,52,.19),
        inset 0 1px 2px rgba(4,28,36,.22);
}

.jp-search-submit:focus-visible {
    outline: none;
    box-shadow:
        0 0 0 3px rgba(47, 127, 142, .14),
        0 8px 20px rgba(22, 66, 84, .22);
}

.jp-search-submit:disabled {
    cursor: wait;
    opacity: .78;
}

.jp-search-submit__icon {
    font-size: 15px;
}

.jp-search-submit__icon.is-spinning {
    animation: jp-search-spin .9s linear infinite;
}

@keyframes jp-search-spin {
    to { transform: rotate(360deg); }
    border-color: rgba(73, 149, 154, .74);
    filter: brightness(1.055);
    box-shadow:
        0 9px 20px rgba(15, 43, 56, .23),
        0 0 0 1px rgba(74, 145, 151, .07),
        inset 0 1px 0 rgba(255,255,255,.19);
}

.jp-search-submit:active:not(:disabled) {
    transform: translateY(0);
    filter: brightness(.97);
    box-shadow:
        0 3px 9px rgba(14,40,52,.19),
        inset 0 1px 2px rgba(4,28,36,.22);
}

.jp-search-submit:focus-visible {
    outline: none;
    box-shadow:
        0 0 0 3px rgba(47, 127, 142, .14),
        0 8px 20px rgba(22, 66, 84, .22);
}

.jp-search-submit:disabled {
    cursor: wait;
    opacity: .78;
}

.jp-search-submit__icon {
    font-size: 15px;
}

.jp-search-submit__icon.is-spinning {
    animation: jp-search-spin .9s linear infinite;
}

@keyframes jp-search-spin {
    to { transform: rotate(360deg); }
}

.jp-results-panel {
    position: absolute;
    top: 100%;
    left: 12px;
    right: 12px;
    z-index: 50;
    background: #fff;
    border-radius: 0 0 12px 12px;
    box-shadow: 0 8px 32px rgba(30, 64, 175, 0.18), 0 2px 8px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    max-height: 55vh;
    display: flex;
    flex-direction: column;
}

.jp-stats-bar {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 10px 20px;
    background: linear-gradient(90deg, #EBF2FA, #EDF5F2);
    border-bottom: 1px solid #e5e7eb;
    flex-wrap: wrap;
    flex-shrink: 0;
}

.jp-stat {
    display: flex;
    align-items: baseline;
    gap: 4px;
}

.jp-stat__num {
    font-size: 20px;
    font-weight: 700;
    color: #142038;
    font-family: 'Inter', 'PingFang SC', system-ui, sans-serif;
}

.jp-stat__label {
    font-size: 12px;
    color: #6b7280;
}

.jp-stat-divider {
    width: 1px;
    height: 20px;
    background: #d1d5db;
}

.jp-stats-keyword {
    font-size: 12px;
    color: #6b7280;
    margin-left: auto;
}

.jp-stats-keyword strong {
    color: #374151;
}

.jp-selected-tip {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 20px;
    background: #fef3c7;
    border-bottom: 1px solid #fde68a;
    font-size: 12px;
    color: #92400e;
    flex-shrink: 0;
}

.jp-selected-tip strong {
    color: #1e40af;
}

.jp-group-list {
    overflow-y: auto;
    flex: 1;
}

.jp-group-list::-webkit-scrollbar {
    width: 4px;
}

.jp-group-list::-webkit-scrollbar-thumb {
    background: #d1d5db;
    border-radius: 2px;
}

.jp-group {
    border-bottom: 1px solid #f3f4f6;
    transition: background 0.15s;
}

.jp-group:last-child {
    border-bottom: none;
}

.jp-group.is-selected {
    background: #EBF2FA;
}

.jp-group__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 9px 20px;
    cursor: pointer;
    transition: background 0.15s;
}

.jp-group__header:hover {
    background: #f9fafb;
}

.jp-group.is-selected .jp-group__header:hover {
    background: #D8E8F5;
}

.jp-group__left {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}

.jp-group__name {
    font-size: 14px;
    font-weight: 600;
    color: #111827;
}

.jp-group__meta {
    font-size: 12px;
    color: #9ca3af;
}

.jp-group__salary {
    font-size: 12px;
    color: #16a34a;
    font-weight: 600;
}

.jp-group__actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
}

.jp-group__arrow {
    font-size: 13px;
    color: #9ca3af;
    transition: transform 0.25s;
}

.jp-group__arrow.expanded {
    transform: rotate(180deg);
}

.jp-group__body {
    padding: 0 20px 8px 32px;
    background: #f9fafb;
}

.jp-group__loading {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #9ca3af;
    font-size: 12px;
    padding: 8px 0;
}

.jp-group__empty {
    font-size: 12px;
    color: #9ca3af;
    padding: 8px 0;
}

.jp-job-item {
    padding: 6px 0;
    border-bottom: 1px dashed #e5e7eb;
}

.jp-job-item:last-child {
    border-bottom: none;
}

.jp-job-item__company {
    font-size: 13px;
    font-weight: 500;
    color: #374151;
    margin-bottom: 3px;
}

.jp-job-item__info {
    display: flex;
    gap: 5px;
    flex-wrap: wrap;
}

.slide-down-enter-active,
.slide-down-leave-active {
    transition: all 0.25s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
    opacity: 0;
    transform: translateY(-8px);
}

.expand-enter-active,
.expand-leave-active {
    transition: all 0.2s ease;
    overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
    max-height: 0;
    opacity: 0;
}

.expand-enter-to,
.expand-leave-from {
    max-height: 400px;
    opacity: 1;
}

.jp-charts-section {
    flex: 1;
    padding: 3px 4px 3px;
    padding: 3px 4px 3px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    min-height: 0;
}

.jp-charts-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 3px;
    gap: 12px;
    margin-bottom: 3px;
    flex-shrink: 0;
}

.jp-charts-header__left {
.jp-charts-header__left {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
}

.jp-view-context {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
}

.jp-view-context {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: #71839a;
    font-size: 10px;
    color: #71839a;
    font-size: 10px;
    font-weight: 600;
    white-space: nowrap;
}

.jp-view-context__dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #2f7f8e;
    box-shadow: 0 0 0 4px rgba(47, 127, 142, 0.09);
}

.jp-charts-view {
    display: inline-flex;
    align-items: center;
    padding: 3px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(20, 48, 80, 0.12);
    box-shadow: 0 1px 4px rgba(12, 26, 45, 0.06);
}

.jp-charts-switch {
    appearance: none;
    border: none;
    background: transparent;
    color: #2A4268;
    font-size: 13px;
    font-weight: 600;
    white-space: nowrap;
}

.jp-view-context__dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #2f7f8e;
    box-shadow: 0 0 0 4px rgba(47, 127, 142, 0.09);
}

.jp-charts-view {
    display: inline-flex;
    align-items: center;
    padding: 3px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(20, 48, 80, 0.12);
    box-shadow: 0 1px 4px rgba(12, 26, 45, 0.06);
}

.jp-charts-switch {
    appearance: none;
    border: none;
    background: transparent;
    color: #2A4268;
    font-size: 13px;
    font-weight: 600;
    font-family: 'Inter', 'PingFang SC', system-ui, sans-serif;
    padding: 7px 14px;
    border-radius: 999px;
    cursor: pointer;
    transition: all 0.18s ease;
}

.jp-charts-switch.active {
    background: linear-gradient(135deg, #17283a 0%, #28465f 100%);
    color: rgba(255, 255, 255, 0.95);
    box-shadow: 0 5px 14px rgba(22, 40, 58, 0.16);
}

.jp-charts-section.is-panorama {
    flex: 1 1 0;
    min-height: 0;
    overflow: hidden;
    scrollbar-width: thin;
    scrollbar-color: rgba(79, 103, 133, 0.22) transparent;
}

.jp-panorama-wrapper {
    flex: 1 1 0;
    min-height: 0;
    height: auto;
    background: transparent;
    border: none;
    border-radius: 0;
    overflow: hidden;
    padding: 0;
    box-shadow: none;
}

.jp-domain-wrapper {
    flex: 1;
    min-height: 0;
    overflow: hidden;
}

.jp-panorama-layouts {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 8px;
    padding: 7px 14px;
    border-radius: 999px;
    cursor: pointer;
    transition: all 0.18s ease;
}

.jp-charts-switch.active {
    background: linear-gradient(135deg, #17283a 0%, #28465f 100%);
    color: rgba(255, 255, 255, 0.95);
    box-shadow: 0 5px 14px rgba(22, 40, 58, 0.16);
}

.jp-charts-section.is-panorama {
    flex: 1 1 0;
    min-height: 0;
    overflow: hidden;
    scrollbar-width: thin;
    scrollbar-color: rgba(79, 103, 133, 0.22) transparent;
}

.jp-panorama-wrapper {
    flex: 1 1 0;
    min-height: 0;
    height: auto;
    background: transparent;
    border: none;
    border-radius: 0;
    overflow: hidden;
    padding: 0;
    box-shadow: none;
}

.jp-domain-wrapper {
    flex: 1;
    min-height: 0;
    overflow: hidden;
}

.jp-panorama-layouts {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 8px;
}

.jp-layout-switch {
    appearance: none;
    border: 1px solid rgba(113, 136, 168, 0.2);
    background: rgba(255,255,255,0.72);
    color: #304767;
    border-radius: 999px;
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.18s ease;
}

.jp-layout-switch.active {
    background: linear-gradient(135deg, #1d4ed8 0%, #4f7cff 100%);
    border-color: transparent;
    color: #fff;
    box-shadow: 0 8px 18px rgba(79,124,255,0.22);
}

.jp-panorama-hint {
    font-size: 11px;
    color: #6d7d93;
    letter-spacing: 0.04em;
    margin: 0 0 10px;
}

.jp-panorama-shell {
    position: relative;
    height: calc(100% - 54px);
    border-radius: 14px;
    overflow: hidden;
    background: linear-gradient(180deg, rgba(255,255,255,0.28) 0%, rgba(241,246,255,0.35) 100%);
    border: 1px solid rgba(159, 177, 206, 0.24);
}

.jp-panorama-wrapper :deep(.chart-card) {
    background: transparent;
    border: none;
    box-shadow: none;
    padding: 0;
    height: 100%;
}

.jp-panorama-wrapper :deep(.chart-container) {
    min-height: 100%;
    height: 100%;
    background: transparent;
.jp-layout-switch {
    appearance: none;
    border: 1px solid rgba(113, 136, 168, 0.2);
    background: rgba(255,255,255,0.72);
    color: #304767;
    border-radius: 999px;
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.18s ease;
}

.jp-layout-switch.active {
    background: linear-gradient(135deg, #1d4ed8 0%, #4f7cff 100%);
    border-color: transparent;
    color: #fff;
    box-shadow: 0 8px 18px rgba(79,124,255,0.22);
}

.jp-panorama-hint {
    font-size: 11px;
    color: #6d7d93;
    letter-spacing: 0.04em;
    margin: 0 0 10px;
}

.jp-panorama-shell {
    position: relative;
    height: calc(100% - 54px);
    border-radius: 14px;
    overflow: hidden;
    background: linear-gradient(180deg, rgba(255,255,255,0.28) 0%, rgba(241,246,255,0.35) 100%);
    border: 1px solid rgba(159, 177, 206, 0.24);
}

.jp-panorama-wrapper :deep(.chart-card) {
    background: transparent;
    border: none;
    box-shadow: none;
    padding: 0;
    height: 100%;
}

.jp-panorama-wrapper :deep(.chart-container) {
    min-height: 100%;
    height: 100%;
    background: transparent;
}

.jp-charts-skeleton {
    flex: 1;
    display: grid;
    grid-template-columns: 1fr 45% 1fr;
    grid-template-rows: 1fr 1fr;
    gap: 6px;
    min-height: 0;
}

.jp-skeleton-card {
    background: linear-gradient(90deg, #f0f4f8 25%, #e2e8f0 50%, #f0f4f8 75%);
    background-size: 200% 100%;
    animation: shimmer 1.4s infinite;
    border-radius: 10px;
}

.jp-skeleton-card:nth-child(2) {
    grid-column: 2;
    grid-row: 1 / 3;
}

@keyframes shimmer {
    0% {
        background-position: 200% 0
    }

    100% {
        background-position: -200% 0
    }
}

.jp-charts-grid {
    flex: 1;
    display: grid;
    grid-template-columns: 1fr 45% 1fr;
    grid-template-rows: 1fr 1fr;
    gap: 6px;
    min-height: 0;
}

.jp-chart-card--bar {
    grid-column: 1;
    grid-row: 1;
}

.jp-chart-card--map {
    grid-column: 2;
    grid-row: 1 / 3;
}

.jp-chart-card--pie {
    grid-column: 3;
    grid-row: 1;
}

.jp-chart-card--box {
    grid-column: 1;
    grid-row: 2;
}

.jp-chart-card--cloud {
    grid-column: 3;
    grid-row: 2;
}

.jp-chart-card {
    background: rgba(255, 255, 255, 0.96);
    border-radius: 10px;
    padding: 10px 12px 8px;
    box-shadow: 0 1px 6px rgba(12, 26, 45, 0.06), 0 0 0 1px rgba(20, 48, 80, 0.07);
    border: none;
    transition: box-shadow 0.2s;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
}

.jp-chart-card:hover {
    box-shadow: 0 4px 18px rgba(12, 26, 45, 0.12), 0 0 0 1px rgba(20, 48, 80, 0.10);
}

.jp-chart-card :deep(.chart-card) {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    background: transparent;
    padding: 0;
    box-shadow: none;
    border: none;
    border-radius: 0;
}

.jp-chart-card :deep(.chart-container) {
    flex: 1;
    height: unset !important;
    min-height: 0;
}

.jp-card-header {
    display: flex;
    align-items: center;
    margin-bottom: 4px;
    margin-bottom: 4px;
    padding-bottom: 6px;
    border-bottom: 1px solid #E8EFF7;
    flex-shrink: 0;
}

.jp-card-title {
    font-size: 13px;
    font-weight: 600;
    color: #1A2F4A;
    font-family: 'Inter', 'PingFang SC', system-ui, sans-serif;
    letter-spacing: 0.01em;
}

@media (max-width: 1100px) {
    .jp-charts-grid {
        grid-template-columns: 1fr 1fr;
        grid-template-rows: auto;
    }

    .jp-chart-card--bar {
        grid-column: 1 / -1;
        grid-row: auto;
    }

    .jp-chart-card--map {
        grid-column: 1 / -1;
        grid-row: auto;
    }

    .jp-chart-card--pie {
        grid-column: 1;
        grid-row: auto;
    }

    .jp-chart-card--box {
        grid-column: 2;
        grid-row: auto;
    }

    .jp-chart-card--cloud {
        grid-column: 1 / -1;
        grid-row: auto;
    }

    .jp-page {
        height: auto;
        overflow: auto;
    }

    .jp-charts-section {
        overflow: visible;
    }
}

@media (max-width: 700px) {
    .jp-charts-grid {
        grid-template-columns: 1fr;
    }

    .jp-chart-card--bar,
    .jp-chart-card--map,
    .jp-chart-card--pie,
    .jp-chart-card--box,
    .jp-chart-card--cloud {
        grid-column: 1;
        grid-row: auto;
    }

    .jp-search-bar {
        flex-direction: column;
    }
}

@media (max-width: 1100px) {
    .jp-view-context { display: none; }
    .jp-panorama-wrapper {
        height: auto;
        min-height: 780px;
    }
}

@media (max-width: 1100px) {
    .jp-view-context { display: none; }
    .jp-panorama-wrapper {
        height: auto;
        min-height: 780px;
    }
}
</style>

