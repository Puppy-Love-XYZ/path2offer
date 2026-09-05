<template>
  <div class="panorama-root">
    <section class="panorama-toolbar" aria-label="岗位技能筛选器">
      <div class="panorama-toolbar__intro">
        <div class="panorama-toolbar__title-row">
          <div>
            <h3>岗位‑技能趋势演变图</h3>
          </div>
          <div class="panorama-summary-pills">
            <span><strong>4</strong> 季度</span>
            <span v-if="quarterData.length > 0"><strong>{{ quarterData.length }}</strong> 个技能</span>
          </div>
        </div>
      </div>
      <div v-if="stat.total > 0" class="stat-card-row">
        <div class="stat-card">
          <div class="stat-card-label">上升技能</div>
          <div class="stat-val rise">{{ stat.rise }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-card-label">下降技能</div>
          <div class="stat-val drop">{{ stat.drop }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-card-label">平稳技能</div>
          <div class="stat-val stable">{{ stat.stable }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-card-label">单点技能</div>
          <div class="stat-val single">{{ stat.single }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-card-label">全部技能</div>
          <div class="stat-val">{{ stat.total }}</div>
        </div>
        <div class="panorama-filter-grid">
          <label class="panorama-control">
            <span class="panorama-control__label">选择岗位</span>
            <div class="panorama-select-shell">
              <el-select
                v-model="selectedPost"
                class="panorama-tech-select"
                popper-class="panorama-premium-popper"
                placeholder="请选择岗位"
                style="width:100%"
              >
                <el-option
                  v-for="post in postList"
                  :key="post"
                  :label="post"
                  :value="post"
                />
              </el-select>
            </div>
          </label>
        </div>
      </div>
      <div class="panorama-toolbar__footer">
        <div></div>
        <div class="panorama-legend">
          <span><span style="color:#2554b7">●</span> 上升</span>
          <span><span style="color:#d47b28">●</span> 下降</span>
          <span><span style="color:#277c67">●</span> 平稳</span>
          <span><span style="color:#94A3B8">●</span> 单点</span>
        </div>
        <button type="button" class="panorama-reset-filter" @click="resetPage">
          <el-icon><RefreshLeft /></el-icon>重置
        </button>
      </div>
    </section>
    <div class="panorama-scroll-body">
      <div ref="scrollRef" class="panorama-stage">
        <div class="panorama-stage__backdrop" aria-hidden="true">
          <span class="panorama-orbit panorama-orbit--a"></span>
          <span class="panorama-orbit panorama-orbit--b"></span>
          <span class="panorama-grid-glow"></span>
        </div>
        <div v-if="!selectedPost" class="empty-wrap">
          <div class="empty-text">请在上方筛选栏选择岗位</div>
        </div>
        <div v-else class="single-post-cloud">
          <div v-if="quarterData.length===0" class="empty-wrap">
            <div class="empty-text">该岗位无有效技能数据</div>
          </div>
          <div class="cloud-grid" v-else>
            <div class="skill-card" v-for="(skill, idx) in quarterData" :key="idx">
              <div class="skill-card-left">
                <div class="skill-name-row">
                  <span class="skill-name">{{ skill.技能 }}</span>
                  <span class="skill-trend" :class="getTrendClass(skill.趋势)">
                    {{ skill.趋势 }}
                  </span>
                </div>
              </div>
              <div class="skill-card-right">
                <div class="trend-chart-box" :ref="el => setChartRef(el, idx)"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="showTrendModal" class="trend-modal-mask" @click.self="closeTrendModal">
      <div class="trend-modal">
        <div class="trend-modal-header">
          <h4>{{ currentSkillMeta?.技能 }}</h4>
          <button class="trend-close-btn" @click="closeTrendModal">×</button>
        </div>
        <div class="trend-meta-info">
          <div><b>趋势类型：</b>{{ currentSkillMeta?.趋势 }}</div>
          <div v-if="currentSkillMeta?.提示"><b>提示：</b>{{ currentSkillMeta?.提示 }}</div>
        </div>
        <div ref="trendChartRef" class="trend-mini-chart"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { RefreshLeft } from '@element-plus/icons-vue'

const props = defineProps({
  filterParams: {
    type: Object,
    default: () => ({})
  },
  triggerJobName: {
    type: String,
    default: ''
  }
})

const COLOR_TREND = {
  rise: '#2554b7',
  drop: '#d47b28',
  stable: '#277c67',
  single: '#94A3B8'
}

// 判断是否为上升趋势（包含所有上升相关关键词）
function isRiseTrend(trend) {
  if (!trend) return false
  const riseKeywords = ['上升', '持续上升', '整体上升', '稳步上升', '快速增长', '持续增长']
  return riseKeywords.some(keyword => trend.includes(keyword))
}

// 判断是否为下降趋势
function isDropTrend(trend) {
  if (!trend) return false
  const dropKeywords = ['下降', '持续下降', '整体下降', '稳步下降']
  return dropKeywords.some(keyword => trend.includes(keyword))
}

// 判断是否为平稳趋势
function isStableTrend(trend) {
  if (!trend) return false
  return trend === '平稳' || trend.includes('平稳')
}

// 判断是否为单点趋势
function isSingleTrend(trend) {
  if (!trend) return false
  return trend === '单点' || trend.includes('单点')
}

const scrollRef = ref(null)
const jsonData = ref({})
const jsonReady = ref(false)
const pendingJob = ref('')
const selectedPost = ref('')
const quarterData = ref([])
const chartInstances = ref([])
const chartRefs = ref([])

const showTrendModal = ref(false)
const currentSkillMeta = ref(null)
const trendChartRef = ref(null)
let trendChartIns = null

const stat = computed(() => {
  if (!selectedPost.value || !jsonData.value['岗位技能演变']) {
    return { rise: 0, drop: 0, stable: 0, single: 0, total: 0 }
  }
  const jobObj = jsonData.value['岗位技能演变'][selectedPost.value]
  const skillList = Array.isArray(jobObj?.技能序列) ? jobObj.技能序列 : []
  let rise = 0, drop = 0, stable = 0, single = 0
  skillList.forEach(sk => {
    const t = sk.趋势 || ''
    if (isRiseTrend(t)) {
      rise++
    } else if (isDropTrend(t)) {
      drop++
    } else if (isStableTrend(t)) {
      stable++
    } else if (isSingleTrend(t)) {
      single++
    } else {
      // 如果无法归类，默认算平稳
      stable++
    }
  })
  return { rise, drop, stable, single, total: skillList.length }
})

function getTrendClass(trend) {
  if (isRiseTrend(trend)) return 'trend-rise'
  if (isDropTrend(trend)) return 'trend-drop'
  if (isStableTrend(trend)) return 'trend-stable'
  if (isSingleTrend(trend)) return 'trend-single'
  return 'trend-stable'
}

function getTrendColor(trend) {
  if (isRiseTrend(trend)) return COLOR_TREND.rise
  if (isDropTrend(trend)) return COLOR_TREND.drop
  if (isStableTrend(trend)) return COLOR_TREND.stable
  if (isSingleTrend(trend)) return COLOR_TREND.single
  return COLOR_TREND.stable
}

function setChartRef(el, index) {
  if (el) {
    chartRefs.value[index] = el
  }
}

function resetPage() {
  selectedPost.value = ''
  quarterData.value = []
  chartRefs.value = []
  chartInstances.value.forEach(ins => ins?.dispose())
  chartInstances.value = []
  loadData()
  closeTrendModal()
}

async function loadData() {
  jsonReady.value = false
  selectedPost.value = ''
  quarterData.value = []
  chartRefs.value = []
  chartInstances.value.forEach(ins => ins?.dispose())
  chartInstances.value = []

  try {
    let data = null
    
    if (window.__SKILL_DATA__) {
      data = window.__SKILL_DATA__
      console.log('[LOAD] 从 window 加载数据成功')
    }
    
    if (!data) {
      try {
        const response = await fetch('/position_skill_evolution_fixed.json')
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        data = await response.json()
        console.log('[LOAD] 从 position_skill_evolution_fixed.json 加载数据成功')
      } catch (fetchError) {
        console.error('[LOAD] 加载 JSON 文件失败:', fetchError)
        try {
          const response = await fetch('./position_skill_evolution_fixed.json')
          if (response.ok) {
            data = await response.json()
            console.log('[LOAD] 从备用路径加载数据成功')
          }
        } catch (backupError) {
          console.error('[LOAD] 备用路径也失败:', backupError)
        }
      }
    }
    
    if (!data || !data['岗位技能演变'] || Object.keys(data['岗位技能演变']).length === 0) {
      console.error('[LOAD] 无法加载数据，请确保 position_skill_evolution_fixed.json 文件存在')
      jsonData.value = { '岗位技能演变': {} }
      jsonReady.value = true
      return
    }
    
    jsonData.value = data
    jsonReady.value = true
    
    const allJobs = jsonData.value['岗位技能演变'] || {}
    const allKeys = Object.keys(allJobs)
    
    if (pendingJob.value && allKeys.includes(pendingJob.value)) {
      selectedPost.value = pendingJob.value
      pendingJob.value = ''
    } else if (props.triggerJobName && allKeys.includes(props.triggerJobName)) {
      selectedPost.value = props.triggerJobName
    } else if (allKeys.length > 0) {
      selectedPost.value = allKeys[0]
    }
    
  } catch (err) {
    console.error('[数据加载异常]', err)
    jsonData.value = { '岗位技能演变': {} }
    jsonReady.value = true
  }
}

const postList = computed(() => {
  const jobs = jsonData.value['岗位技能演变']
  if (!jobs) return []
  return Object.keys(jobs)
})

watch(() => props.triggerJobName, (newVal) => {
  if (!newVal || !newVal.trim()) return
  const target = newVal.trim()
  const allJobs = jsonData.value['岗位技能演变'] || {}
  const allKeys = Object.keys(allJobs)
  if (!jsonReady.value) {
    pendingJob.value = target
    return
  }
  if (allKeys.includes(target)) {
    selectedPost.value = target
  } else {
    console.warn(`[组件] 传入岗位【${target}】不在岗位列表中`)
  }
})

function buildSkillTrendData(jobObj) {
  const skillSequence = jobObj?.['技能序列']
  if (!Array.isArray(skillSequence)) {
    console.warn('[buildSkillTrendData] skillSequence 不是数组')
    return []
  }
  
  const quarters = ['Q1', 'Q2', 'Q3', 'Q4']
  
  const result = skillSequence.map(skill => {
    const rateObj = skill['各季度出现率'] || {}
    const values = quarters.map(q => {
      const val = rateObj[q]
      return val !== null && val !== undefined ? Number(val) : null
    })
    
    return {
      技能: skill.技能,
      趋势: skill.趋势 || '平稳',
      整体变化幅度: skill.整体变化幅度,
      'Q1~Q2变化幅度': skill['Q1~Q2变化幅度'],
      'Q2~Q3变化幅度': skill['Q2~Q3变化幅度'],
      'Q3~Q4变化幅度': skill['Q3~Q4变化幅度'],
      峰值季度: skill.峰值季度,
      峰值出现率: skill.峰值出现率,
      提示: skill.提示,
      各季度出现率: rateObj,
      values: values
    }
  })
  
  // 按最新季度出现率从高到低排序
  const sorted = result.sort((a, b) => {
    const aLatest = a.values[a.values.length - 1] || 0
    const bLatest = b.values[b.values.length - 1] || 0
    return bLatest - aLatest
  })
  
  return sorted
}

function getChartOption(values, skillName, trend) {
  const quarters = ['Q1', 'Q2', 'Q3', 'Q4']
  const color = getTrendColor(trend)

  const validPoints = values.map((v, i) => ({ v, i })).filter(item => item.v !== null)
  let markPointData = []
  if (validPoints.length > 0) {
    const max = Math.max(...validPoints.map(item => item.v))
    markPointData = validPoints.filter(item => item.v === max).map(item => ({
      coord: [item.i, item.v],
      value: item.v,
      symbol: 'pin',
      symbolSize: 28,
      itemStyle: { color: color },
      label: {
        show: true,
        formatter: function(params) {
          return params.value
        },
        fontSize: 9,
        color: '#fff'
      }
    }))
  }

  return {
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        const p = params[0]
        if (p.value === null) return `${p.axisValue}<br/>无数据`
        return `${p.axisValue}<br/>${skillName}: ${p.value}`
      }
    },
    grid: {
      left: 35,
      right: 6,
      top: 8,
      bottom: 12
    },
    xAxis: {
      type: 'category',
      data: quarters,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        fontSize: 10,
        color: '#94A3B8'
      }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 1,
      splitLine: {
        lineStyle: {
          color: '#e8eff8',
          type: 'dashed',
          lineWidth: 0.5
        }
      },
      axisLabel: {
        fontSize: 9,
        color: '#94A3B8',
        formatter: function(value) {
          return value
        }
      }
    },
    series: [{
      type: 'line',
      data: values,
      connectNulls: false,
      smooth: false,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        color: color,
        width: 2
      },
      itemStyle: {
        color: color
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: color + '40' },
          { offset: 1, color: color + '05' }
        ])
      },
      markPoint: {
        data: markPointData
      }
    }]
  }
}

async function renderAllCharts() {
  await nextTick()

  chartInstances.value.forEach(ins => ins?.dispose())
  chartInstances.value = []

  await nextTick()
  
  quarterData.value.forEach((item, idx) => {
    const dom = chartRefs.value[idx]
    if (!dom) {
      return
    }
    try {
      const ins = echarts.init(dom)
      ins.setOption(getChartOption(item.values, item.技能, item.趋势))
      ins.on('click', () => {
        openTrendModal(item)
      })
      chartInstances.value[idx] = ins
    } catch (err) {
      console.error(`[renderAllCharts] 渲染第 ${idx} 个图表失败：`, err)
    }
  })
}

async function openTrendModal(metaObj) {
  currentSkillMeta.value = metaObj
  showTrendModal.value = true
  await nextTick()
  if (trendChartIns) trendChartIns.dispose()
  trendChartIns = echarts.init(trendChartRef.value)
  const quarters = ['Q1', 'Q2', 'Q3', 'Q4']
  const rateObj = metaObj['各季度出现率'] || {}
  const seriesData = quarters.map(q => {
    const val = rateObj[q]
    return val !== null && val !== undefined ? Number(val) : null
  })
  const color = getTrendColor(metaObj.趋势)
  const opt = {
    tooltip: { 
      trigger: 'axis',
      formatter: function(params) {
        const p = params[0]
        if (p.value === null) return `${p.axisValue}<br/>无数据`
        return `${p.axisValue}<br/>出现率: ${p.value}`
      }
    },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: quarters },
    yAxis: { 
      type: 'value', 
      name: '出现率',
      min: 0, 
      max: 1,
      axisLabel: {
        formatter: function(value) {
          return value
        }
      }
    },
    series: [{
      name: '出现率',
      type: 'line',
      connectNulls: false,
      data: seriesData,
      itemStyle: { color: color },
      lineStyle: { color: color, width: 2 },
      symbol: 'circle',
      symbolSize: 8,
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: color + '40' },
          { offset: 1, color: color + '05' }
        ])
      }
    }]
  }
  trendChartIns.setOption(opt)
}

function closeTrendModal() {
  showTrendModal.value = false
  currentSkillMeta.value = null
  if (trendChartIns) {
    trendChartIns.dispose()
    trendChartIns = null
  }
}

async function refresh() {
  const allJobs = jsonData.value['岗位技能演变']
  if (!allJobs || !selectedPost.value) {
    quarterData.value = []
    return
  }
  const jobItem = allJobs[selectedPost.value]

  const newData = buildSkillTrendData(jobItem || { 技能序列: [] })
  quarterData.value = newData
  chartRefs.value = new Array(newData.length).fill(null)

  await renderAllCharts()
}

watch(selectedPost, refresh)

onMounted(() => {
  loadData()
  window.addEventListener('resize', () => {
    chartInstances.value.forEach(ins => ins?.resize())
    if (trendChartIns) trendChartIns.resize()
  })
})
</script>

<style scoped>
.panorama-root {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f3f6fa;
  color: #1F2933;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
  font-size: 9px;
  overflow: hidden;
}

.panorama-toolbar {
  padding: 2px 22px;
  background: #FFFFFF;
  border-bottom: 1px solid #d8e1ec;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  flex-shrink: 0;
  z-index: 10;
}

.panorama-toolbar__title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
  flex-wrap: wrap;
}

.panorama-toolbar__title-row h3 {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 800;
  color: #14233b;
}

.panorama-summary-pills {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.panorama-summary-pills span {
  padding: 4px 10px;
  background: #e8eff8;
  border: 1px solid #d8e1ec;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  color: #38547b;
}

.panorama-summary-pills span strong {
  font-size: 14px;
  font-weight: 700;
  color: #2554b7;
}

.stat-card-row {
  display: flex;
  gap: 10px;
  margin: 14px 0 0;
  flex-wrap: wrap;
}

.stat-card {
  background: #FFFFFF;
  border: 1px solid #d8e1ec;
  border-radius: 10px;
  padding: 8px 12px;
  min-width: 88px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(20, 35, 59, 0.05);
}

.stat-card-label {
  font-size: 11px;
  color: #546988;
  margin-bottom: 4px;
}

.stat-val {
  font-size: 18px;
  font-weight: 800;
  color: #14233b;
}

.stat-val.rise {
  color: #2554b7;
}
.stat-val.drop {
  color: #d47b28;
}
.stat-val.stable {
  color: #277c67;
}
.stat-val.single {
  color: #94A3B8;
}

.panorama-filter-grid {
  margin-top: 14px;
}

.panorama-control__label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: #2c4266;
  margin-bottom: 6px;
}

:deep(.panorama-tech-select .el-input__inner) {
  font-size: 13px;
  font-weight: 500;
  color: #1F2933;
  background: #FFFFFF;
  border: 1px solid #b8c8dd;
  border-radius: 8px;
}

:deep(.panorama-tech-select .el-input__inner::placeholder) {
  font-size: 13px;
  font-weight: 400;
  color: #899cb8;
}

.panorama-toolbar__footer {
  margin-top: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.panorama-legend {
  display: flex;
  gap: 18px;
  font-size: 12px;
  font-weight: 500;
  color: #38547b;
  align-items: center;
  flex-wrap: wrap;
}

.panorama-reset-filter {
  padding: 6px 12px;
  border: 1px solid #2554b7;
  background: #FFFFFF;
  color: #2554b7;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 600;
  transition: background 0.2s, color 0.2s, box-shadow 0.2s;
}

.panorama-reset-filter:hover {
  background: rgba(37, 84, 183, 0.07);
  box-shadow: 0 0 0 3px rgba(37, 84, 183, 0.12);
}

.panorama-scroll-body {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0;
  position: relative;
}

.panorama-scroll-body::-webkit-scrollbar {
  width: 6px;
}

.panorama-scroll-body::-webkit-scrollbar-track {
  background: #f0f2f5;
  border-radius: 3px;
}

.panorama-scroll-body::-webkit-scrollbar-thumb {
  background: #c1c9d6;
  border-radius: 3px;
}

.panorama-scroll-body::-webkit-scrollbar-thumb:hover {
  background: #a8b2c2;
}

.panorama-stage {
  width: 100%;
  padding: 10px 22px 70px;
  position: relative;
}

.panorama-stage__backdrop {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.panorama-orbit {
  position: absolute;
  border: 1px solid rgba(37, 84, 183, 0.07);
  border-radius: 50%;
}

.panorama-orbit--a {
  width: 65%;
  height: 65%;
  top: 15%;
  left: 17%;
}

.panorama-orbit--b {
  width: 85%;
  height: 85%;
  top: 8%;
  left: 8%;
}

.panorama-grid-glow {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at center, rgba(37, 84, 183, 0.03) 0%, transparent 65%),
    repeating-linear-gradient(0deg, transparent, transparent 24px, rgba(37, 84, 183, 0.045) 24px, rgba(37, 84, 183, 0.045) 25px),
    repeating-linear-gradient(90deg, transparent, transparent 24px, rgba(37, 84, 183, 0.045) 24px, rgba(37, 84, 183, 0.045) 25px);
  opacity: 0.55;
}

.empty-wrap {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.empty-text {
  color: #7488a6;
  font-size: 14px;
}

.cloud-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  padding-bottom: 30px;
}

.skill-card {
  display: flex;
  border: 1px solid #d8e1ec;
  border-radius: 12px;
  background: #FFFFFF;
  box-shadow: 0 2px 8px rgba(20, 35, 59, 0.06);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  overflow: hidden;
  height: 85px;
}

.skill-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(37, 84, 183, 0.12);
}

.skill-card-left {
  flex: 0 0 130px;
  padding: 8px 14px;
  display: flex;
  align-items: center;
  border-right: 1px solid #e8eff8;
  background: #fafcfe;
}

.skill-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
}

.skill-name {
  font-size: 15px;
  font-weight: 700;
  color: #14233b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex-shrink: 1;
  min-width: 0;
}

.skill-trend {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 12px;
  display: inline-block;
  white-space: nowrap;
  flex-shrink: 0;
}

.skill-trend.trend-rise {
  color: #2554b7;
  background: #e8eff8;
}

.skill-trend.trend-drop {
  color: #d47b28;
  background: #fef3e8;
}

.skill-trend.trend-stable {
  color: #277c67;
  background: #e8f5f0;
}

.skill-trend.trend-single {
  color: #94A3B8;
  background: #f0f2f5;
}

.skill-card-right {
  flex: 1;
  padding: 4px 10px;
  min-width: 0;
}

.trend-chart-box {
  width: 100%;
  height: 100%;
}

.trend-modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.trend-modal {
  width: 560px;
  max-width: 92vw;
  background: #FFFFFF;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(14, 23, 40, 0.18);
}

.trend-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  background: #f3f6fa;
  border-bottom: 1px solid #d8e1ec;
}

.trend-modal-header h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
  color: #14233b;
}

.trend-close-btn {
  border: none;
  background: transparent;
  font-size: 20px;
  cursor: pointer;
  color: #546988;
  width: 26px;
  height: 26px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.trend-close-btn:hover {
  background: #e8eff8;
}

.trend-meta-info {
  padding: 14px 18px;
  font-size: 13px;
  line-height: 1.7;
  color: #2c4266;
}

.trend-mini-chart {
  width: 100%;
  height: 280px;
}

@media (max-width: 768px) {
  .cloud-grid {
    grid-template-columns: 1fr;
  }
}
.panorama-select-shell {
  width: 160px;
}
.jp-wordcloud-flow-wrapper {
  flex: 1;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
}

.jp-wordcloud-flow-wrapper > * {
  flex: 1;
  min-height: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.jp-wordcloud-empty {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #9CA3AF;
  font-size: 14px;
  text-align: center;
  pointer-events: none;
}
</style>