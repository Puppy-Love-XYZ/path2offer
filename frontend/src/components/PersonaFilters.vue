<template>
    <div class="persona-page">
        <div class="search-bar">
            <el-input v-model="searchQuery" placeholder="搜索岗位名称或公司名称" size="large" clearable @keyup.enter="loadAll"
                style="flex: 1">
                <template #prefix>
                    <el-icon class="search-icon">
                        <Search />
                    </el-icon>
                </template>
            </el-input>

            <el-select v-model="groupBy" size="large" style="width: 180px" clearable>
                <el-option label="按学历分组" value="your_education" />
                <el-option label="按经验分组" value="working_exp" />
                <el-option label="按公司规模分组" value="company_size" />
                <el-option label="按城市分组" value="work_city" />
            </el-select>

            <el-button type="primary" size="large" @click="loadAll" class="search-btn">
                <el-icon>
                    <Search />
                </el-icon>
                搜索
            </el-button>
        </div>

        <div class="dashboard">
            <div class="card">
                <div class="card-title">薪资分布（箱线图）</div>
                <div ref="boxRef" class="chart"></div>
            </div>

            <div class="card map-card">
                <div class="card-title">岗位地域分布</div>
                <div ref="mapRef" class="map"></div>
            </div>

            <div class="card">
                <div class="card-title">公司规模/性质分布</div>
                <div ref="pieRef" class="chart"></div>
                <div v-if="selectedCompanySize" class="company-list">
                    <div class="company-list-title">公司列表</div>
                    <ul>
                        <li v-for="company in companyList" :key="company.id">
                            {{ company.name }}
                        </li>
                    </ul>
                </div>
            </div>

            <div class="card">
                <div class="card-title">技能热点词云</div>
                <div ref="wordCloudRef" class="chart"></div>
            </div>

            <div class="card stat-card">
                <div class="stat-title">岗位总量</div>
                <div class="stat-value">{{ summary.total_jobs ?? '-' }}</div>
            </div>

            <div class="card stat-card">
                <div class="stat-title">平均薪资</div>
                <div class="stat-value">
                    {{ summary.avg_salary ? summary.avg_salary + ' 元' : '-' }}
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'
import { Search } from '@element-plus/icons-vue'
import chinaJson from '@/assets/china.json'

const searchQuery = ref('')
const groupBy = ref('your_education')
const selectedCompanySize = ref('')
const companyList = ref<any[]>([])
const summary = ref<any>({})

const mapRef = ref<HTMLDivElement>()
const boxRef = ref<HTMLDivElement>()
const pieRef = ref<HTMLDivElement>()
const wordCloudRef = ref<HTMLDivElement>()
let mapChart: echarts.ECharts
let boxChart: echarts.ECharts
let pieChart: echarts.ECharts
let wordCloudChart: echarts.ECharts

const loadSummary = async () => {
    const res = await axios.get('/api/persona/summary', {
        params: { search_query: searchQuery.value }
    })
    summary.value = res.data
}

const loadMap = async () => {
    const res = await axios.get('/api/persona/location', {
        params: { search_query: searchQuery.value }
    })

    const data = res.data.map((i: any) => ({
        name: i.city,
        value: i.count
    }))

    mapChart.setOption({
        tooltip: { trigger: 'item' },
        visualMap: {
            min: 0,
            max: Math.max(...data.map((i: any) => i.value), 10),
            left: 'left',
            bottom: 20,
            calculable: true
        },
        series: [{
            type: 'map',
            map: 'china',
            roam: true,
            data,
            emphasis: {
                label: {
                    show: true
                },
                itemStyle: {
                    areaColor: '#387908'
                }
            },
            select: {
                itemStyle: {
                    areaColor: '#2c3e50'
                },
                label: {
                    show: true,
                    color: '#fff'
                }
            }
        }]
    })
}

const loadBox = async () => {
    const res = await axios.get('/api/analysis/salary-boxplot', {
        params: {
            search_query: searchQuery.value,
            group_by: groupBy.value || 'your_education'
        }
    })

    const categories = res.data.map((i: any) => i.category)
    const values = res.data.map((i: any) => [
        i.min, i.q1, i.median, i.q3, i.max
    ])

    boxChart.setOption({
        tooltip: {
            trigger: 'item',
            formatter: function (params: any) {
                const data = params.data
                return `${params.name}<br/>` +
                    `最小值: ${data[0]}k<br/>` +
                    `下四分位: ${data[1]}k<br/>` +
                    `中位数: ${data[2]}k<br/>` +
                    `上四分位: ${data[3]}k<br/>` +
                    `最大值: ${data[4]}k`
            }
        },
        grid: {
            left: '10%',
            right: '10%',
            bottom: '15%',
            top: '10%'
        },
        xAxis: {
            type: 'category',
            data: categories,
            axisLabel: {
                rotate: 45,
                interval: 0
            }
        },
        yAxis: {
            type: 'value',
            name: '薪资（k）',
            min: 0
        },
        series: [{
            type: 'boxplot',
            data: values,
            itemStyle: {
                color: '#409eff',
                borderColor: '#409eff'
            },
            emphasis: {
                itemStyle: {
                    color: '#66b1ff'
                }
            }
        }]
    })
}

const loadPie = async () => {
    const res = await axios.get('/api/analysis/company-distribution', {
        params: {
            search_query: searchQuery.value
        }
    })

    pieChart.setOption({
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            left: 'left',
            top: 'center',
            data: res.data.map((i: any) => i.name),
            textStyle: {
                fontSize: 12
            }
        },
        series: [{
            name: '公司分布',
            type: 'pie',
            radius: '45%',
            center: ['65%', '50%'],
            data: res.data.map((i: any) => ({
                value: i.value,
                name: i.name
            })),
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            },
            label: {
                show: true,
                formatter: '{b}: {d}%'
            },
            labelLine: {
                show: true
            }
        }]
    })
}

const loadCompanyList = async (companySize: string) => {
    const res = await axios.get('/api/analysis/company-list', {
        params: {
            search_query: searchQuery.value,
            company_size: companySize
        }
    })
    companyList.value = res.data
}

const loadWordCloud = async () => {
    const res = await axios.get('/api/analysis/skill-wordcloud', {
        params: {
            search_query: searchQuery.value
        }
    })

    const sortedData = res.data.sort((a: any, b: any) => b.value - a.value)

    wordCloudChart.setOption({
        tooltip: {
            trigger: 'item',
            formatter: function (params: any) {
                return `${params.name}<br/>需求度: ${params.value}`
            }
        },
        series: [{
            type: 'wordCloud',
            shape: 'circle',
            left: 'center',
            top: 'center',
            width: '80%',
            height: '80%',
            right: null,
            bottom: null,
            sizeRange: [12, 80],
            rotationRange: [-45, 45],
            rotationStep: 45,
            gridSize: 10,
            drawOutOfBound: false,
            textStyle: {
                fontFamily: 'sans-serif',
                fontWeight: 'bold',
                color: function () {
                    return 'rgb(' + [
                        Math.round(Math.random() * 160 + 50),
                        Math.round(Math.random() * 160 + 50),
                        Math.round(Math.random() * 160 + 50)
                    ].join(',') + ')';
                }
            },
            emphasis: {
                focus: 'self',
                textStyle: {
                    shadowBlur: 10,
                    shadowColor: '#333'
                }
            },
            data: sortedData.map((i: any) => ({
                name: i.word,
                value: i.value
            }))
        }]
    })
}

const loadAll = async () => {
    await Promise.all([
        loadSummary(),
        loadMap(),
        loadBox(),
        loadPie(),
        loadWordCloud()
    ])
}

onMounted(async () => {
    mapChart = echarts.init(mapRef.value!)
    boxChart = echarts.init(boxRef.value!)
    pieChart = echarts.init(pieRef.value!)
    wordCloudChart = echarts.init(wordCloudRef.value!)

    echarts.registerMap('china', chinaJson as any)

    mapChart.on('click', (params: any) => {
        if (params.value > 5) {
            console.log('点击城市:', params.name, '岗位数:', params.value)
            Promise.all([
                loadBox(),
                loadPie(),
                loadWordCloud()
            ])
        }
    })

    pieChart.on('click', (params: any) => {
        console.log('点击饼图:', params.name, 'value:', params.value)
        selectedCompanySize.value = params.name
        loadCompanyList(params.name)
    })

    loadAll()
})

watch(groupBy, loadAll)
</script>

<style scoped>
.persona-page {
    padding: 20px;
    background: #f5f7fa;
}

.search-bar {
    display: flex;
    gap: 12px;
    background: #fff;
    padding: 16px;
    border-radius: 16px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    align-items: center;
}

.search-icon {
    color: #909399;
}

.search-btn {
    border-radius: 8px;
    font-weight: 600;
}

.dashboard {
    display: grid;
    grid-template-columns: 1fr 2fr 1fr;
    grid-template-rows: 300px 300px;
    gap: 16px;
}

.card {
    background: #fff;
    border-radius: 16px;
    padding: 16px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    transition: all 0.3s ease;
    display: flex;
    flex-direction: column;
}

.card:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
    transform: translateY(-2px);
}

.map-card {
    grid-row: span 2;
}

.map {
    width: 100%;
    height: 100%;
    border-radius: 8px;
    overflow: hidden;
}

.chart {
    width: 100%;
    height: calc(100% - 32px);
    border-radius: 8px;
    flex-grow: 1;
}

.company-list {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #f0f0f0;
}

.company-list-title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
    color: #606266;
}

.company-list ul {
    list-style: none;
    padding: 0;
    margin: 0;
    max-height: 120px;
    overflow-y: auto;
}

.company-list li {
    font-size: 13px;
    padding: 4px 0;
    color: #909399;
    cursor: pointer;
    transition: color 0.3s ease;
}

.company-list li:hover {
    color: #409eff;
}

.stat-card {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
}

.stat-title {
    color: rgba(255, 255, 255, 0.8);
    font-size: 14px;
}

.stat-value {
    font-size: 28px;
    font-weight: bold;
    margin-top: 8px;
    color: #fff;
}

.card-title {
    font-weight: 600;
    margin-bottom: 12px;
    font-size: 16px;
    color: #303133;
}

@media screen and (max-width: 1200px) {
    .dashboard {
        grid-template-columns: 1fr;
        grid-template-rows: auto;
    }

    .map-card {
        grid-row: auto;
        height: 400px;
    }

    .stat-card {
        height: 150px;
    }

    .chart {
        height: 300px;
    }
}
</style>