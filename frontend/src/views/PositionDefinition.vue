<template>
  <div class="pd-page">
    <!-- 页头 -->
    <div class="pd-header">
      <div class="pd-header__title-row">
        <div class="pd-header__icon">
          <el-icon :size="22"><Compass /></el-icon>
        </div>
        <div>
          <h1 class="pd-header__title">新兴岗位动态</h1>
          <p class="pd-header__subtitle">基于多源异构数据驱动的新兴岗位图谱 · 定义 · 演化分析</p>
        </div>
      </div>
    </div>

    <!-- 顶部视图切换：新兴岗位定义 / 岗位技能演变趋势图 -->
    <div class="pd-view-switch">
      <button
        class="pd-view-switch__btn"
        :class="{ 'is-active': mainView === 'definition' }"
        @click="mainView = 'definition'"
      >
        <el-icon :size="15"><Compass /></el-icon>
        新兴岗位定义
      </button>
      <button
        class="pd-view-switch__btn"
        :class="{ 'is-active': mainView === 'evolution' }"
        @click="mainView = 'evolution'"
      >
        <el-icon :size="15"><DataLine /></el-icon>
        岗位技能演变趋势图
      </button>
    </div>

    <!-- 视图一：新兴岗位定义（搜索 + 统计 + 卡片列表） -->
    <template v-if="mainView === 'definition'">
    <!-- 搜索 & 筛选 -->
    <div class="pd-filter-card">
      <div class="pd-filter-row">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索岗位名称，如：AI算法工程师"
          class="pd-search"
          clearable
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select v-model="filterDomain" placeholder="所属领域" clearable class="pd-filter-select">
          <el-option v-for="d in domainOptions" :key="d" :label="d" :value="d" />
        </el-select>

        <el-select v-model="filterEmerging" placeholder="新兴岗位" clearable class="pd-filter-select">
          <el-option label="仅新兴岗位" :value="true" />
          <el-option label="仅传统岗位" :value="false" />
        </el-select>

        <el-button type="primary" @click="handleSearch" class="pd-search-btn">
          <el-icon class="pd-btn-icon"><Search /></el-icon>
          检索
        </el-button>

        <el-button @click="handleReset" class="pd-reset-btn">
          <el-icon class="pd-btn-icon"><RefreshRight /></el-icon>
          重置
        </el-button>
      </div>

      <!-- 操作提示 -->
      <div class="pd-tip">
        <el-icon :size="14"><InfoFilled /></el-icon>
        <span>点击新兴岗位名称，查看具体岗位信息（所含职位及招聘详情）</span>
      </div>

      <!-- 热门标签 -->
      <div class="pd-hot-tags" v-if="hotTags.length">
        <span class="pd-hot-label">热门岗位</span>
        <span
          v-for="tag in hotTags"
          :key="tag"
          class="pd-hot-tag"
          @click="searchKeyword = tag; handleSearch()"
        >{{ tag }}</span>
      </div>
    </div>

    <!-- 统计栏 -->
    <div class="pd-stats">
      <div class="pd-stat-item">
        <span class="pd-stat-num">{{ stats.total }}</span>
        <span class="pd-stat-label">岗位总数</span>
      </div>
      <div class="pd-stat-item">
        <span class="pd-stat-num pd-stat-num--emerging">{{ stats.emerging }}</span>
        <span class="pd-stat-label">新兴岗位</span>
      </div>
      <div class="pd-stat-item">
        <span class="pd-stat-num">{{ stats.domains }}</span>
        <span class="pd-stat-label">覆盖领域</span>
      </div>
      <div class="pd-stat-item">
        <span class="pd-stat-num">{{ stats.avgEmergence }}%</span>
        <span class="pd-stat-label">平均新兴度</span>
      </div>
    </div>

    <!-- 岗位卡片列表 -->
    <div v-loading="loading" class="pd-card-grid">
      <div
        v-for="pos in positions"
        :key="pos.岗位名称"
        class="pd-card"
      >
        <!-- 卡片头部 -->
        <div class="pd-card__header">
          <div class="pd-card__title-row">
            <h3
              class="pd-card__title pd-card__title--link"
              title="点击查看所含职位"
              @click="openPositionDialog(pos)"
            >
              {{ pos.岗位名称 }}
              <el-icon :size="13" class="pd-card__title-icon"><Search /></el-icon>
            </h3>
            <div class="pd-card__badges">
              <span v-if="pos.是否是新兴岗位 === '是'" class="pd-badge pd-badge--emerging">新兴岗位</span>
              <span v-else class="pd-badge pd-badge--normal">传统岗位</span>
              <span class="pd-badge pd-badge--domain">{{ pos.所属领域 }}</span>
            </div>
          </div>
        </div>

        <!-- 新兴程度进度条 -->
        <div class="pd-emergence">
          <div class="pd-emergence__header">
            <span class="pd-emergence__label">新兴程度</span>
            <span class="pd-emergence__value" :class="getEmergenceClass(pos.新兴程度)">{{ pos.新兴程度 }}</span>
          </div>
          <div class="pd-emergence__bar">
            <div
              class="pd-emergence__fill"
              :class="getEmergenceClass(pos.新兴程度)"
              :style="{ width: pos.新兴程度 }"
            />
          </div>
        </div>

        <!-- 新兴度判定信号 -->
        <div class="pd-signals" v-if="pos.新兴度判定信号">
          <div class="pd-signals__title">
            <el-icon :size="14"><DataLine /></el-icon>
            <span>新兴度判定信号</span>
          </div>
          <div
            v-for="key in signalKeys"
            :key="key"
            class="pd-signal-item"
          >
            <div class="pd-signal-row">
              <span class="pd-signal-label">{{ signalLabels[key] }}</span>
              <span class="pd-signal-value">{{ formatSignal(pos.新兴度判定信号[key]) }}</span>
            </div>
            <div class="pd-signal-bar">
              <div
                class="pd-signal-fill"
                :style="{ width: formatSignal(pos.新兴度判定信号[key]) }"
              />
            </div>
          </div>
        </div>

        <!-- 核心职责 -->
        <div class="pd-section">
          <div class="pd-section__title">
            <el-icon :size="14"><List /></el-icon>
            <span>核心职责</span>
          </div>
          <ol class="pd-duty-list">
            <li v-for="(duty, i) in pos.核心职责" :key="i" class="pd-duty-item">{{ duty }}</li>
          </ol>
        </div>

        <!-- 必备技能 -->
        <div class="pd-section">
          <div class="pd-section__title">
            <el-icon :size="14"><Star /></el-icon>
            <span>必备技能</span>
          </div>
          <div class="pd-tag-wrap">
            <span v-for="skill in pos.必备技能" :key="skill" class="pd-skill-tag pd-skill-tag--required">{{ skill }}</span>
          </div>
        </div>

        <!-- 加分技能 -->
        <div class="pd-section" v-if="pos.加分技能 && pos.加分技能.length">
          <div class="pd-section__title">
            <el-icon :size="14"><Plus /></el-icon>
            <span>加分技能</span>
          </div>
          <div class="pd-tag-wrap">
            <span v-for="skill in pos.加分技能" :key="skill" class="pd-skill-tag pd-skill-tag--bonus">{{ skill }}</span>
          </div>
        </div>

        <!-- 典型行业应用场景 -->
        <div class="pd-section" v-if="pos.典型行业应用场景 && pos.典型行业应用场景.length">
          <div class="pd-section__title">
            <el-icon :size="14"><Location /></el-icon>
            <span>典型应用场景</span>
          </div>
          <div class="pd-tag-wrap">
            <span v-for="scene in pos.典型行业应用场景" :key="scene" class="pd-scene-tag">{{ scene }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && positions.length === 0" class="pd-empty">
      <el-icon :size="48" color="#c0c4cc"><Search /></el-icon>
      <p>未找到匹配的岗位定义</p>
    </div>
    </template>

    <!-- 视图二：岗位技能演变趋势图 -->
    <template v-else>
      <div class="pd-evolution">
        <WordCloudFlow :trigger-job-name="evolutionJobName" />
      </div>
    </template>

    <!-- 岗位联动弹窗：展示所含职位，点击职位查看详情 -->
    <el-dialog
      v-model="dialogVisible"
      :title="activePosition?.岗位名称 || '岗位详情'"
      width="760px"
      top="6vh"
      class="pd-dialog"
    >
      <div v-if="activePosition" class="pd-dialog__body">
        <!-- 岗位概要 -->
        <div class="pd-dialog__summary">
          <div class="pd-dialog__badges">
            <span v-if="activePosition.是否是新兴岗位 === '是'" class="pd-badge pd-badge--emerging">新兴岗位</span>
            <span v-else class="pd-badge pd-badge--normal">传统岗位</span>
            <span class="pd-badge pd-badge--domain">{{ activePosition.所属领域 }}</span>
          </div>
          <div class="pd-dialog__actions">
            <span class="pd-dialog__emergence">
              新兴程度 <b :class="getEmergenceClass(activePosition.新兴程度)">{{ activePosition.新兴程度 }}</b>
            </span>
            <button class="pd-jump-evolution" @click="jumpToEvolution">
              <el-icon :size="14"><DataLine /></el-icon>
              查看技能演变趋势
            </button>
          </div>
        </div>

        <!-- 所含职位列表 -->
        <div class="pd-jobs">
          <div class="pd-jobs__header">
            <span>所含职位</span>
            <span class="pd-jobs__count">
              共 {{ activePosition.所含职位?.职位总数 ?? activePosition.所含职位?.职位列表?.length ?? 0 }} 条
            </span>
          </div>
          <p class="pd-jobs__hint">点击职位名称可展开该职位在库中的招聘详情</p>

          <template v-if="activePosition.所含职位?.职位列表?.length">
            <div
              v-for="job in activePosition.所含职位.职位列表"
              :key="job"
              class="pd-job-item"
            >
              <button class="pd-job-item__name" @click="toggleJobDetail(job)">
                <el-icon :size="12" class="pd-job-item__arrow" :class="{ 'is-open': expandedJob === job }">
                  <ArrowRight />
                </el-icon>
                <span>{{ job }}</span>
              </button>

              <!-- 展开的岗位详情 -->
              <div v-if="expandedJob === job" class="pd-job-detail">
                <div v-if="jobLoading" class="pd-job-detail__loading">
                  <el-icon class="is-loading"><Loading /></el-icon> 加载中...
                </div>
                <template v-else-if="jobDetails.length">
                  <div v-for="rec in jobDetails" :key="rec.id" class="pd-job-card">
                    <div class="pd-job-card__row">
                      <span class="pd-job-card__company">{{ rec.company_name || '—' }}</span>
                      <span class="pd-job-card__salary">{{ rec.job_salary || '面议' }}</span>
                    </div>
                    <div class="pd-job-card__meta">
                      <template v-if="rec.work_city">{{ rec.work_city }}</template>
                      <template v-if="rec.work_city && rec.your_education"> · </template>
                      <template v-if="rec.your_education">{{ rec.your_education }}</template>
                      <template v-if="(rec.work_city || rec.your_education) && rec.working_exp"> · </template>
                      <template v-if="rec.working_exp">{{ rec.working_exp }}</template>
                      <template v-if="(rec.work_city || rec.your_education || rec.working_exp) && rec.company_size"> · </template>
                      <template v-if="rec.company_size">{{ rec.company_size }}</template>
                    </div>
                    <div v-if="rec.company_benefits" class="pd-job-card__benefits">{{ rec.company_benefits }}</div>
                    <details v-if="rec.job_summary" class="pd-job-card__summary">
                      <summary>岗位描述</summary>
                      <p>{{ rec.job_summary }}</p>
                    </details>
                  </div>
                  <p v-if="jobTotal > jobDetails.length" class="pd-job-detail__more">
                    库中另有 {{ jobTotal - jobDetails.length }} 条相似记录，仅展示前 {{ jobDetails.length }} 条
                  </p>
                </template>
                <div v-else class="pd-job-detail__empty">
                  <el-icon :size="16"><Search /></el-icon>
                  数据库中未找到该职位名称的招聘记录
                </div>
              </div>
            </div>
          </template>
          <div v-else class="pd-job-detail__empty">
            <el-icon :size="16"><Search /></el-icon>
            该岗位暂无关联职位数据
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Search, Star, Plus, Location, List, Compass, DataLine, ArrowRight, Loading, RefreshRight, InfoFilled } from '@element-plus/icons-vue'
import WordCloudFlow from '../components/WordCloudFlow.vue'
import {
  fetchPositionDefinitions,
  fetchJobsByName,
  type PositionDefinition,
  type JobRecord,
} from '../api/position'

const loading = ref(false)
const positions = ref<PositionDefinition[]>([])
const searchKeyword = ref('')
const filterDomain = ref('')
const filterEmerging = ref<boolean | ''>('')

/* ── 技能动态演变联动：点击岗位名称时传入 ── */
const evolutionJobName = ref('')

/* ── 顶部视图切换：definition=新兴岗位定义 / evolution=岗位技能演变趋势图 ── */
const mainView = ref<'definition' | 'evolution'>('definition')

function jumpToEvolution() {
  if (activePosition.value) {
    evolutionJobName.value = activePosition.value.岗位名称
  }
  dialogVisible.value = false
  mainView.value = 'evolution'
  // 切到视图后滚回页面顶部，确保看到趋势图标题
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

/* ── 岗位联动弹窗 ── */
const dialogVisible = ref(false)
const activePosition = ref<PositionDefinition | null>(null)
const expandedJob = ref<string | null>(null)
const jobLoading = ref(false)
const jobDetails = ref<JobRecord[]>([])
const jobTotal = ref(0)

function openPositionDialog(pos: PositionDefinition) {
  activePosition.value = pos
  expandedJob.value = null
  jobDetails.value = []
  jobTotal.value = 0
  dialogVisible.value = true
  // 记录当前岗位，供技能演变趋势图联动
  evolutionJobName.value = pos.岗位名称
}

async function toggleJobDetail(jobName: string) {
  if (expandedJob.value === jobName) {
    expandedJob.value = null
    return
  }
  expandedJob.value = jobName
  jobLoading.value = true
  jobDetails.value = []
  jobTotal.value = 0
  try {
    const res = await fetchJobsByName(jobName, 20)
    jobDetails.value = res.jobs
    jobTotal.value = res.total
  } catch (e) {
    console.error('查询职位详情失败', e)
  } finally {
    jobLoading.value = false
  }
}

const domainOptions = computed(() => {
  const set = new Set(positions.value.map(p => p.所属领域))
  return Array.from(set)
})

const hotTags = [
  'AI算法工程师', 'AI产品经理', 'AI全栈工程师',
  'AI机器人工程师', 'AI自动驾驶工程师', 'AI安全工程师',
]

const stats = computed(() => {
  const total = positions.value.length
  const emerging = positions.value.filter(p => p.是否是新兴岗位 === '是').length
  const domains = new Set(positions.value.map(p => p.所属领域)).size
  const avgEmergence = total > 0
    ? Math.round(positions.value.reduce((sum, p) => sum + parseInt(p.新兴程度) || 0, 0) / total)
    : 0
  return { total, emerging, domains, avgEmergence }
})

function getEmergenceClass(percent: string): string {
  const n = parseInt(percent) || 0
  if (n >= 60) return 'pd-emergence--high'
  if (n >= 30) return 'pd-emergence--mid'
  return 'pd-emergence--low'
}

/* ── 新兴度判定信号 ── */
const signalKeys = ['岗位新兴技能占比', '新兴职位占比', '招聘次数环比增幅', '命名新颖性'] as const
const signalLabels: Record<string, string> = {
  岗位新兴技能占比: '岗位新兴技能占比',
  新兴职位占比: '新兴职位占比',
  招聘次数环比增幅: '招聘次数环比增幅',
  命名新颖性: '命名新颖性',
}
function formatSignal(val: string | null | undefined): string {
  if (val === null || val === undefined) return '—'
  return val
}

async function loadData() {
  loading.value = true
  try {
    const params: { keyword?: string; domain?: string; emerging_only?: boolean } = {}
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (filterDomain.value) params.domain = filterDomain.value
    if (filterEmerging.value !== '') params.emerging_only = filterEmerging.value as boolean
    const res = await fetchPositionDefinitions(params)
    positions.value = res.positions
  } catch (e) {
    console.error('加载岗位定义失败', e)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  loadData()
}

function handleReset() {
  searchKeyword.value = ''
  filterDomain.value = ''
  filterEmerging.value = ''
  loadData()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.pd-page {
  padding: 28px 32px 48px;
  width: 100%;
  max-width: 100%;
  margin: 0;
  box-sizing: border-box;
}

/* ── 页头 ── */
.pd-header {
  margin-bottom: 20px;
}

.pd-header__title-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.pd-header__icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

.pd-header__title {
  font-size: 22px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
  line-height: 1.2;
}

.pd-header__subtitle {
  font-size: 13px;
  color: #8c8c9a;
  margin: 4px 0 0;
}

/* ── 筛选卡片 ── */
.pd-filter-card {
  background: #fff;
  border-radius: 16px;
  padding: 20px 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  margin-bottom: 16px;
}

.pd-filter-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.pd-search {
  flex: 1;
}

.pd-filter-select {
  width: 160px;
}

.pd-search-btn {
  flex-shrink: 0;
  background: linear-gradient(135deg, #6366f1 0%, #818cf8 100%);
  border: none;
}

.pd-reset-btn {
  flex-shrink: 0;
}

/* 操作提示 */
.pd-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 14px;
  font-size: 12px;
  color: #8a6d1a;
  background: #fdf6e3;
  border: 1px solid #faecd8;
  border-radius: 8px;
  padding: 8px 14px;
}

.pd-tip .el-icon {
  color: #e6a23c;
  flex-shrink: 0;
}

.pd-btn-icon {
  margin-right: 4px;
}

/* 热门标签 */
.pd-hot-tags {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  flex-wrap: wrap;
}

.pd-hot-label {
  font-size: 12px;
  color: #a0a0b0;
  font-weight: 600;
}

.pd-hot-tag {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 12px;
  background: #f0f0ff;
  color: #6366f1;
  cursor: pointer;
  transition: all 150ms ease;
}

.pd-hot-tag:hover {
  background: #6366f1;
  color: #fff;
}

/* ── 统计栏 ── */
.pd-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.pd-stat-item {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  padding: 16px 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}

.pd-stat-num {
  display: block;
  font-size: 28px;
  font-weight: 800;
  color: #1a1a2e;
  line-height: 1;
}

.pd-stat-num--emerging {
  color: #8b5cf6;
}

.pd-stat-label {
  display: block;
  font-size: 12px;
  color: #a0a0b0;
  margin-top: 6px;
}

/* ── 卡片网格 ── */
.pd-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
}

.pd-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  border: 1px solid #f0f0f5;
  transition: box-shadow 200ms ease, transform 200ms ease;
}

.pd-card:hover {
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

/* 卡片头部 */
.pd-card__header {
  margin-bottom: 16px;
}

.pd-card__title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.pd-card__title {
  font-size: 17px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
  line-height: 1.4;
}

/* 可点击标题 */
.pd-card__title--link {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #4338ca;
  transition: color 150ms ease;
  border-bottom: 1px dashed transparent;
}

.pd-card__title--link:hover {
  color: #6366f1;
  border-bottom-color: #a5b4fc;
}

.pd-card__title-icon {
  opacity: 0;
  transition: opacity 150ms ease;
}

.pd-card__title--link:hover .pd-card__title-icon {
  opacity: 0.7;
}

.pd-card__badges {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.pd-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
  white-space: nowrap;
}

.pd-badge--emerging {
  background: #ede9fe;
  color: #7c3aed;
}

.pd-badge--normal {
  background: #f3f4f6;
  color: #6b7280;
}

.pd-badge--domain {
  background: #e0f2fe;
  color: #0284c7;
}

/* ── 新兴程度 ── */
.pd-emergence {
  margin-bottom: 18px;
}

.pd-emergence__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.pd-emergence__label {
  font-size: 12px;
  color: #8c8c9a;
  font-weight: 600;
}

.pd-emergence__value {
  font-size: 14px;
  font-weight: 800;
}

.pd-emergence__bar {
  width: 100%;
  height: 8px;
  background: #f0f0f5;
  border-radius: 4px;
  overflow: hidden;
}

.pd-emergence__fill {
  height: 100%;
  border-radius: 4px;
  transition: width 400ms ease;
}

.pd-emergence--high.pd-emergence__value {
  color: #8b5cf6;
}
.pd-emergence__fill.pd-emergence--high {
  background: linear-gradient(90deg, #8b5cf6, #a78bfa);
}

.pd-emergence--mid.pd-emergence__value {
  color: #3b82f6;
}
.pd-emergence__fill.pd-emergence--mid {
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
}

.pd-emergence--low.pd-emergence__value {
  color: #94a3b8;
}
.pd-emergence__fill.pd-emergence--low {
  background: linear-gradient(90deg, #94a3b8, #cbd5e1);
}

/* ── 新兴度判定信号 ── */
.pd-signals {
  background: #f8faff;
  border: 1px solid #e8edff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 18px;
}

.pd-signals__title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
  color: #4a4a5e;
  margin-bottom: 14px;
}

.pd-signals__title .el-icon {
  color: #6366f1;
}

.pd-signal-item {
  margin-bottom: 12px;
}

.pd-signal-item:last-child {
  margin-bottom: 0;
}

.pd-signal-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.pd-signal-label {
  font-size: 12px;
  color: #5a5a6e;
  font-weight: 500;
}

.pd-signal-value {
  font-size: 13px;
  font-weight: 700;
  color: #1a1a2e;
}

.pd-signal-bar {
  width: 100%;
  height: 6px;
  background: #e8edf5;
  border-radius: 3px;
  overflow: hidden;
}

.pd-signal-fill {
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, #14b8a6, #2dd4bf);
  transition: width 400ms ease;
}

/* ── 通用区块 ── */
.pd-section {
  margin-bottom: 16px;
}

.pd-section__title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
  color: #4a4a5e;
  margin-bottom: 8px;
}

.pd-section__title .el-icon {
  color: #818cf8;
}

/* 核心职责列表 */
.pd-duty-list {
  margin: 0;
  padding-left: 0;
  list-style: none;
  counter-reset: duty-counter;
}

.pd-duty-item {
  font-size: 13px;
  color: #5a5a6e;
  line-height: 1.7;
  padding-left: 22px;
  position: relative;
  margin-bottom: 4px;
  counter-increment: duty-counter;
}

.pd-duty-item::before {
  content: counter(duty-counter);
  position: absolute;
  left: 0;
  top: 1px;
  width: 16px;
  height: 16px;
  border-radius: 4px;
  background: #eef2ff;
  color: #6366f1;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 技能标签 */
.pd-tag-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.pd-skill-tag {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 6px;
  font-weight: 500;
}

.pd-skill-tag--required {
  background: #eef2ff;
  color: #4338ca;
  border: 1px solid #c7d2fe;
}

.pd-skill-tag--bonus {
  background: #f0fdf4;
  color: #15803d;
  border: 1px solid #bbf7d0;
}

.pd-scene-tag {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 12px;
  background: #f0f9ff;
  color: #0284c7;
  border: 1px solid #bae6fd;
}

/* ── 顶部视图切换 ── */
.pd-view-switch {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.pd-view-switch__btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 11px 26px;
  border-radius: 12px;
  border: 1px solid #e4e4ee;
  background: #fff;
  color: #5a5a6e;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 180ms ease;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
}

.pd-view-switch__btn:hover {
  border-color: #a5b4fc;
  color: #4338ca;
}

.pd-view-switch__btn.is-active {
  background: linear-gradient(135deg, #6366f1 0%, #818cf8 100%);
  border-color: transparent;
  color: #fff;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

/* ── 岗位技能演变趋势图视图容器 ── */
.pd-evolution {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  border: 1px solid #f0f0f5;
  padding: 18px 20px;
  overflow: hidden;
}

/* ── 弹窗内操作区 ── */
.pd-dialog__actions {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}

.pd-jump-evolution {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 10px;
  border: 1px solid #14b8a6;
  background: #f0fdfa;
  color: #0f766e;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 180ms ease;
}

.pd-jump-evolution:hover {
  background: #14b8a6;
  color: #fff;
}

/* ── 空状态 ── */
.pd-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: #c0c4cc;
}

.pd-empty p {
  margin-top: 12px;
  font-size: 14px;
}

/* ── 岗位联动弹窗 ── */
.pd-dialog__body {
  padding: 4px 2px 8px;
}

.pd-dialog__summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  background: #f8faff;
  border: 1px solid #e8edff;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 18px;
}

.pd-dialog__badges {
  display: flex;
  gap: 6px;
}

.pd-dialog__badges .pd-badge {
  font-size: 13px;
  padding: 4px 12px;
}

.pd-dialog__emergence {
  font-size: 15px;
  color: #5a5a6e;
}

.pd-dialog__emergence b {
  font-size: 18px;
  font-weight: 800;
  margin-left: 4px;
}

.pd-dialog__emergence b.pd-emergence--high {
  color: #8b5cf6;
}
.pd-dialog__emergence b.pd-emergence--mid {
  color: #3b82f6;
}
.pd-dialog__emergence b.pd-emergence--low {
  color: #94a3b8;
}

/* 所含职位列表 */
.pd-jobs__header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 16px;
  font-weight: 700;
  color: #4a4a5e;
  margin-bottom: 6px;
}

.pd-jobs__count {
  margin-left: auto;
  font-size: 13px;
  font-weight: 600;
  color: #8c8c9a;
  background: #f3f4f6;
  border-radius: 10px;
  padding: 2px 10px;
}

.pd-jobs__hint {
  font-size: 13px;
  color: #6b7280;
  margin: 0 0 12px;
}

.pd-job-item {
  border: 1px solid #f0f0f5;
  border-radius: 10px;
  margin-bottom: 8px;
  overflow: hidden;
  transition: border-color 150ms ease;
}

.pd-job-item:hover {
  border-color: #c7d2fe;
}

.pd-job-item__name {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fafbff;
  border: none;
  padding: 12px 14px;
  font-size: 15px;
  font-weight: 600;
  color: #3a3a50;
  cursor: pointer;
  text-align: left;
  transition: background 150ms ease;
}

.pd-job-item__name:hover {
  background: #eef2ff;
  color: #4338ca;
}

.pd-job-item__arrow {
  color: #818cf8;
  transition: transform 200ms ease;
  flex-shrink: 0;
}

.pd-job-item__arrow.is-open {
  transform: rotate(90deg);
}

/* 展开的详情区 */
.pd-job-detail {
  border-top: 1px dashed #e5e7eb;
  padding: 10px 14px 12px;
  background: #fff;
}

.pd-job-detail__loading,
.pd-job-detail__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 14px;
  color: #6b7280;
  padding: 16px 0;
}

.pd-job-card {
  border: 1px solid #f0f0f5;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 8px;
  background: #fcfcff;
}

.pd-job-card:last-of-type {
  margin-bottom: 0;
}

.pd-job-card__row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.pd-job-card__company {
  font-size: 15px;
  font-weight: 700;
  color: #1a1a2e;
}

.pd-job-card__salary {
  font-size: 15px;
  font-weight: 700;
  color: #7c3aed;
  white-space: nowrap;
}

.pd-job-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 14px;
  color: #4b5563;
  margin-bottom: 8px;
}

.pd-job-card__benefits {
  font-size: 14px;
  color: #15803d;
  background: #f0fdf4;
  border-radius: 6px;
  padding: 6px 10px;
  margin-bottom: 8px;
  line-height: 1.6;
}

.pd-job-card__summary summary {
  font-size: 14px;
  font-weight: 600;
  color: #4338ca;
  cursor: pointer;
  user-select: none;
}

.pd-job-card__summary p {
  font-size: 14px;
  color: #5a5a6e;
  line-height: 1.8;
  margin: 8px 0 0;
  max-height: 160px;
  overflow-y: auto;
}

.pd-job-detail__more {
  font-size: 11px;
  color: #c0c4cc;
  margin: 6px 0 0;
  text-align: center;
}
</style>
