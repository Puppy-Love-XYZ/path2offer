<template>
  <div class="jm-page">
    <div class="jm-greeting-wrap">
      <PageGreeting tip="看看哪些岗位最适合你，精准投递事半功倍！" />
    </div>

    <div class="jm-status-strip">
      <template v-if="indexStatus.status === 'ready'">
        <el-icon color="#67c23a"><SuccessFilled /></el-icon>
        <span>向量库就绪 · {{ indexStatus.total.toLocaleString() }} 个岗位</span>
      </template>
      <template v-else-if="indexStatus.status === 'indexing'">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>向量库构建中（{{ indexedPct }}%）...</span>
        <el-progress :percentage="indexedPct" :show-text="false" style="width:120px;margin-left:8px" />
      </template>
      <template v-else-if="indexStatus.status === 'not_started'">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>向量库初始化中...</span>
      </template>
      <template v-else-if="indexStatus.status === 'error'">
        <el-icon color="#F56C6C"><WarningFilled /></el-icon>
        <span>向量库错误：{{ indexStatus.error }}</span>
      </template>
    </div>

    <div class="jm-body">
      <div class="jm-mode-bar">
        <button :class="['jm-mode-btn', activeTab === 'filter' && 'is-active']" @click="activeTab = 'filter'; onTabChange()">
          <span class="jm-mode-icon">⊟</span>
          <span class="jm-mode-label">岗位筛选</span>
          <span class="jm-mode-sub">多条件精准过滤</span>
        </button>
        <button :class="['jm-mode-btn', activeTab === 'smart' && 'is-active']" @click="activeTab = 'smart'; onTabChange()">
          <span class="jm-mode-icon">⚡</span>
          <span class="jm-mode-label">智能人岗匹配</span>
          <span class="jm-mode-sub">AI 简历向量推荐</span>
        </button>
      </div>

      <div v-if="activeTab === 'filter'" class="jm-panel">
        <div class="jm-filter-card">
          <div class="filter-row">
            <div class="filter-label">城市</div>
            <div class="filter-tags-wrap">
              <span
                v-for="city in citiesDisplayList"
                :key="city"
                :class="['filter-tag', filterReq.cities.includes(city) && 'is-active']"
                @click="toggleArr(filterReq.cities, city)"
              >{{ city }}</span>
              <span
                v-if="filterOptions.cities.length > CITY_LIMIT"
                class="filter-tag-more"
                @click="citiesExpanded = !citiesExpanded"
              >{{ citiesExpanded ? '收起' : `+${filterOptions.cities.length - CITY_LIMIT} 更多` }}</span>
            </div>
          </div>

          <div class="filter-row filter-row--split">
            <div class="filter-row-half">
              <div class="filter-label">工作类型</div>
              <div class="filter-tags-wrap">
                <span
                  v-for="wt in filterOptions.work_types"
                  :key="wt"
                  :class="['filter-tag', filterReq.work_types.includes(wt) && 'is-active']"
                  @click="toggleArr(filterReq.work_types, wt)"
                >{{ wt }}</span>
              </div>
            </div>
            <div class="filter-row-sep"></div>
            <div class="filter-row-half">
              <div class="filter-label">薪资区间</div>
              <div class="filter-salary-row">
                <el-input-number
                  v-model="filterReq.salary_min"
                  :min="0" :max="999" :step="1" placeholder="最低"
                  controls-position="right" size="small" style="width:110px"
                />
                <span class="salary-sep">–</span>
                <el-input-number
                  v-model="filterReq.salary_max"
                  :min="0" :max="999" :step="1" placeholder="最高"
                  controls-position="right" size="small" style="width:110px"
                />
                <span class="salary-unit">K / 月</span>
              </div>
            </div>
          </div>

          <div class="filter-row">
            <div class="filter-label">学历要求</div>
            <div class="filter-tags-wrap">
              <span
                v-for="edu in EDU_OPTIONS"
                :key="edu"
                :class="['filter-tag', filterReq.education === edu && 'is-active']"
                @click="filterReq.education = edu"
              >{{ edu }}</span>
            </div>
          </div>

          <div class="filter-row">
            <div class="filter-label">工作经验</div>
            <div class="filter-tags-wrap">
              <span
                v-for="exp in normalizedWorkExps"
                :key="exp"
                :class="['filter-tag', filterReq.working_exps.includes(exp) && 'is-active']"
                @click="toggleArr(filterReq.working_exps, exp)"
              >{{ exp }}</span>
            </div>
          </div>

          <div class="filter-row">
            <div class="filter-label">公司规模</div>
            <div class="filter-tags-wrap">
              <span
                v-for="sz in filterOptions.company_sizes"
                :key="sz"
                :class="['filter-tag', filterReq.company_sizes.includes(sz) && 'is-active']"
                @click="toggleArr(filterReq.company_sizes, sz)"
              >{{ sz }}</span>
            </div>
          </div>

          <div class="filter-row">
            <div class="filter-label">公司福利</div>
            <div class="filter-tags-wrap filter-tags-wrap--benefit">
              <span
                v-for="kw in benefitDisplayList"
                :key="kw"
                :class="['filter-tag filter-tag--sm', filterReq.benefit_keywords.includes(kw) && 'is-active']"
                @click="toggleArr(filterReq.benefit_keywords, kw)"
              >{{ kw }}</span>
              <span
                v-if="filterOptions.benefit_keywords.length > BENEFIT_LIMIT"
                class="filter-tag-more"
                @click="benefitExpanded = !benefitExpanded"
              >{{ benefitExpanded ? '收起' : `+${filterOptions.benefit_keywords.length - BENEFIT_LIMIT} 更多` }}</span>
            </div>
          </div>

          <div class="filter-row">
            <div class="filter-label">专业关键词</div>
            <el-input
              v-model="filterReq.major_keyword"
              placeholder="如：计算机、金融、机械（模糊匹配）"
              clearable
              size="small"
              style="max-width:320px"
            />
          </div>

          <div class="filter-actions">
            <el-button size="default" plain @click="clearFilter">清空筛选</el-button>
            <el-button
              type="primary" size="default"
              :loading="filterLoading"
              @click="doFilter(1)"
            >
              寻找岗位
            </el-button>
          </div>
        </div>

        <transition name="fade-up">
          <div v-if="filterSearched" class="jm-filter-results">
            <div v-if="filterLoading" class="jm-loading-tip">
              <el-icon class="is-loading"><Loading /></el-icon> 搜索中...
            </div>
            <template v-else>
              <div class="jm-results-header">
                <span v-if="filterTotal > 0">
                  共找到 <b>{{ filterTotal.toLocaleString() }}</b> 个岗位
                </span>
                <span v-if="filterTotal > 0 && !currentResumeFile" class="jm-match-tip">
                  提示：在「智能人岗匹配」Tab 上传简历后，可对岗位进行深度匹配分析
                </span>
                <el-empty v-else-if="filterTotal === 0" description="未找到满足条件的岗位，请调整筛选条件" :image-size="80" />
              </div>
              <div v-if="filterTotal > 0" class="jm-job-grid">
                <div
                  v-for="job in filterResults"
                  :key="job.id"
                  class="jm-job-card"
                  @click="viewJobDetail(job.id)"
                >
                  <div class="jm-job-card-top">
                    <div class="jm-job-info">
                      <div class="jm-job-name">{{ job.job_name }}</div>
                      <div class="jm-job-company">{{ job.company_name }}</div>
                    </div>
                    <div class="jm-card-btns">
                      <button
                        class="match-icon-btn"
                        title="去匹配"
                        @click.stop="openDeepAnalysis(job.id, job.job_name, job.company_name)"
                      >⚡</button>
                      <button
                        class="fav-btn"
                        :class="{ 'is-faved': isFavorited(job.id) }"
                        :disabled="!!favLoading[job.id]"
                        @click.stop="toggleFavorite(job.id)"
                        title="收藏岗位"
                      >
                        <span v-if="favLoading[job.id]">...</span>
                        <span v-else>{{ isFavorited(job.id) ? '♥' : '♡' }}</span>
                      </button>
                    </div>
                  </div>
                  <div class="jm-job-meta">
                    <el-tag size="small" type="info" effect="plain">{{ job.work_city || '–' }}</el-tag>
                    <el-tag size="small" type="success" effect="plain">
                      {{ job.job_salary || formatSalary(job.salary_min, job.salary_max) }}
                    </el-tag>
                    <el-tag v-if="job.your_education" size="small" effect="plain">{{ job.your_education }}</el-tag>
                    <el-tag v-if="job.working_exp" size="small" effect="plain">{{ job.working_exp }}</el-tag>
                    <el-tag v-if="job.work_type" size="small" :type="job.work_type === '实习' ? 'warning' : 'primary'" effect="plain">{{ job.work_type }}</el-tag>
                    <el-tag v-if="job.company_size" size="small" type="info" effect="plain">{{ job.company_size }}</el-tag>
                  </div>
                  <p v-if="job.job_summary" class="jm-job-desc">{{ job.job_summary.slice(0, 80) }}{{ job.job_summary.length > 80 ? '...' : '' }}</p>
                </div>
              </div>

              <div v-if="filterTotal > filterReq.page_size" class="jm-pagination">
                <el-pagination
                  v-model:current-page="filterReq.page"
                  :page-size="filterReq.page_size"
                  :total="filterTotal"
                  layout="prev, pager, next"
                  @current-change="doFilter($event)"
                />
              </div>
            </template>
          </div>
        </transition>
      </div>

      <div v-if="activeTab === 'smart'" class="jm-panel jm-smart">
        <div class="jm-smart-left">
          <div class="jm-smart-section-label">上传简历</div>
          <div
            class="jm-drop-zone"
            :class="{ 'is-over': isDraggingSmart, 'has-file': !!currentResumeFile }"
            @dragover.prevent="isDraggingSmart = true"
            @dragleave="isDraggingSmart = false"
            @drop.prevent="onDropSmart"
            @click="($refs.smartFileInput as HTMLInputElement).click()"
          >
            <input ref="smartFileInput" type="file" accept=".pdf,.docx,.txt,.jpg,.jpeg,.png,.webp" hidden @change="onSmartFileChange" />
            <template v-if="!currentResumeFile">
              <el-icon class="jm-drop-icon"><Upload /></el-icon>
              <p class="jm-drop-text">拖放或点击上传简历</p>
              <p class="jm-drop-hint">支持 PDF · DOCX · TXT · JPG · PNG</p>
            </template>
            <template v-else>
              <el-icon style="font-size:22px;color:#1A3C34"><Document /></el-icon>
              <p class="jm-file-name">{{ currentResumeFile.name }}</p>
              <button class="jm-remove-btn" @click.stop="clearSmartResume">移除</button>
            </template>
          </div>

          <div v-if="indexStatus.status !== 'ready' && indexStatus.status !== 'not_started'" class="jm-index-warn">
            向量库尚未就绪，无法使用智能推荐
          </div>

          <button
            class="jm-ink-btn"
            :class="{ 'is-loading': autoLoading }"
            :disabled="!currentResumeFile || indexStatus.status !== 'ready' || autoLoading"
            @click="doAutoRecommend"
          >
            <span v-if="autoLoading" class="jm-btn-spinner"></span>
            {{ autoLoading ? '分析中...' : '⚡ 智能推荐岗位' }}
          </button>

          <div class="jm-smart-tips">
            <div class="jm-tip-item">
              <span class="jm-tip-dot"></span>基于 SBERT 语义向量匹配
            </div>
            <div class="jm-tip-item">
              <span class="jm-tip-dot"></span>从 {{ indexStatus.total.toLocaleString() || '88,538' }} 个岗位中筛选
            </div>
            <div class="jm-tip-item">
              <span class="jm-tip-dot"></span>返回 Top 5 最匹配岗位
            </div>
          </div>
        </div>

        <div class="jm-smart-right">
          <transition name="fade-up" mode="out-in">
            <div v-if="autoLoading" class="jm-smart-loading">
              <div class="jm-loading-rings">
                <div class="jm-ring jm-ring-1"></div>
                <div class="jm-ring jm-ring-2"></div>
                <div class="jm-ring jm-ring-3"></div>
                <span class="jm-ring-core">AI</span>
              </div>
              <p class="jm-loading-msg">语义向量匹配中...</p>
              <p class="jm-loading-sub">正在从 {{ indexStatus.total.toLocaleString() }} 个岗位中寻找最佳匹配</p>
            </div>
            <JobMatchingList
              v-else-if="recommendJobs.length"
              :jobs="mappedRecommendJobs"
              :favorite-ids="favoriteIds"
              @select="job => viewJobDetail(job.id)"
              @match="job => openDeepAnalysis(job.id, job.job_summary, job.job_name || '')"
              @favorite="job => toggleFavorite(job.id)"
            />
            <div v-else class="jm-smart-placeholder">
              <div class="jm-placeholder-icon">◈</div>
              <p class="jm-placeholder-title">Top 5 语义匹配岗位</p>
              <p class="jm-placeholder-sub">上传简历后，系统将基于语义向量为你精准推荐最匹配的 5 个岗位，并展示匹配得分</p>
            </div>
          </transition>
        </div>
      </div>
    </div>

    <el-drawer v-model="drawerVisible" size="500px" direction="rtl" :with-header="false">
      <div v-if="drawerJob" class="jm-drawer-content">
        <div class="jm-drawer-head">
          <div class="jm-drawer-head-info">
            <h2 class="jm-drawer-title">{{ drawerJob.job_name }}</h2>
            <p class="jm-drawer-company">{{ drawerJob.company_name }}</p>
          </div>
          <button
            class="fav-btn fav-btn--lg"
            :class="{ 'is-faved': isFavorited(drawerJob.id) }"
            :disabled="!!favLoading[drawerJob.id]"
            @click="toggleFavorite(drawerJob.id)"
          >
            {{ favLoading[drawerJob.id] ? '...' : (isFavorited(drawerJob.id) ? '♥ 已收藏' : '♡ 收藏') }}
          </button>
        </div>
        <div class="jm-drawer-tags">
          <el-tag>{{ drawerJob.work_city }}</el-tag>
          <el-tag type="success">{{ drawerJob.job_salary || '薪资面议' }}</el-tag>
          <el-tag v-if="drawerJob.your_education" type="info">{{ drawerJob.your_education }}</el-tag>
          <el-tag v-if="drawerJob.working_exp">{{ drawerJob.working_exp }}</el-tag>
          <el-tag v-if="drawerJob.company_size" type="warning">{{ drawerJob.company_size }}</el-tag>
          <el-tag v-if="drawerJob.work_type" :type="drawerJob.work_type === '实习' ? 'warning' : 'primary'">{{ drawerJob.work_type }}</el-tag>
        </div>
        <div class="jm-drawer-actions">
          <button
            class="match-btn match-btn--primary"
            @click="openDeepAnalysis(drawerJob.id, drawerJob.job_name, drawerJob.company_name); drawerVisible = false"
          >⚡ 去匹配</button>
        </div>
        <div class="jm-drawer-section">
          <div class="jm-drawer-label">岗位描述</div>
          <p class="jm-drawer-text">{{ drawerJob.job_summary || '暂无描述' }}</p>
        </div>
        <template v-if="drawerJob.company_benefits">
          <div class="jm-drawer-section">
            <div class="jm-drawer-label">福利待遇</div>
            <p class="jm-drawer-text">{{ drawerJob.company_benefits }}</p>
          </div>
        </template>
        <template v-if="drawerJob.work_major">
          <div class="jm-drawer-section">
            <div class="jm-drawer-label">专业要求</div>
            <p class="jm-drawer-text">{{ drawerJob.work_major }}</p>
          </div>
        </template>
      </div>
      <div v-else class="jm-drawer-loading">
        <el-icon class="is-loading"><Loading /></el-icon> 加载中...
      </div>
    </el-drawer>

    <el-dialog
      v-model="analysisDialogVisible"
      :title="analysisTargetName ? `深度匹配分析 · ${analysisTargetName}` : '深度匹配分析'"
      width="680px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div v-if="!currentResumeFile" class="da-no-resume">
        <el-icon style="font-size:40px;color:#9ca3af"><Document /></el-icon>
        <p>请先上传简历才能进行深度匹配分析</p>
        <div
          class="jm-drop-zone da-upload-zone"
          :class="{ 'is-over': isDraggingDialog }"
          @dragover.prevent="isDraggingDialog = true"
          @dragleave="isDraggingDialog = false"
          @drop.prevent="onDropDialog"
          @click="($refs.dialogFileInput as HTMLInputElement).click()"
        >
          <input ref="dialogFileInput" type="file" accept=".pdf,.docx,.txt,.jpg,.jpeg,.png,.webp" hidden @change="onDialogFileChange" />
          <el-icon class="jm-drop-icon"><Upload /></el-icon>
          <p class="jm-drop-text">拖放或点击上传简历</p>
          <p class="jm-drop-hint">支持 PDF · DOCX · TXT · JPG · PNG</p>
        </div>
      </div>

      <template v-else>
        <div v-if="analysisLoading" class="da-loading">
          <div class="da-loading-icon">
            <el-icon class="is-loading" style="font-size:40px;color:#6366f1"><Loading /></el-icon>
          </div>
          <p class="da-loading-text">大模型深度解析中...</p>
          <p class="da-loading-sub">正在分析简历与岗位的匹配情况，约需 10-20 秒</p>
        </div>

        <div v-else-if="analysisResult" class="da-result">
          <div class="da-score-row">
            <div class="da-score-big" :class="daScoreClass(analysisResult.match_score)">
              {{ analysisResult.match_score.toFixed(2) }}
            </div>
            <div class="da-score-info">
              <div class="da-job-name">{{ analysisResult.job?.job_name || analysisTargetName }}</div>
              <div v-if="analysisResult.job?.company_name" class="da-company">{{ analysisResult.job.company_name }}</div>
              <div class="da-score-hint" :class="hintClass(analysisResult.match_score)">
                {{ hintText(analysisResult.match_score) }}
              </div>
            </div>
          </div>

          <div v-if="analysisResult.report?.dimensions" class="da-dims">
            <div
              v-for="(dim, key) in analysisResult.report.dimensions"
              :key="key"
              class="da-dim-row"
            >
              <span class="da-dim-label">{{ dim.label }}</span>
              <div class="da-dim-bar-wrap">
                <div class="da-dim-bar-fill" :style="{ width: dim.score + '%', background: rdScoreClr(dim.score) }"></div>
              </div>
              <span class="da-dim-score" :style="{ color: rdScoreClr(dim.score) }">{{ Math.round(dim.score) }}</span>
              <span v-if="dim.match" class="da-dim-match">{{ dim.match }}</span>
              <span v-else-if="dim.matched_skills?.length" class="da-dim-match">{{ dim.matched_skills.slice(0, 5).join(' · ') }}</span>
            </div>
          </div>

          <div class="da-llm-section">
            <div v-if="analysisResult.deep_analysis?.strengths?.length" class="da-block da-block--green">
              <div class="da-block-title">✅ 优势亮点</div>
              <ul class="da-list">
                <li v-for="(s, i) in analysisResult.deep_analysis.strengths" :key="i">{{ s }}</li>
              </ul>
            </div>
            <div v-if="analysisResult.deep_analysis?.weaknesses?.length" class="da-block da-block--orange">
              <div class="da-block-title">⚠️ 差距不足</div>
              <ul class="da-list">
                <li v-for="(w, i) in analysisResult.deep_analysis.weaknesses" :key="i">{{ w }}</li>
              </ul>
            </div>
            <div v-if="analysisResult.deep_analysis?.advice?.length" class="da-block da-block--blue">
              <div class="da-block-title">💡 投递建议</div>
              <ul class="da-list">
                <li v-for="(a, i) in analysisResult.deep_analysis.advice" :key="i">{{ a }}</li>
              </ul>
            </div>
            <div
              v-if="!analysisResult.deep_analysis?.strengths?.length && !analysisResult.deep_analysis?.weaknesses?.length"
              class="da-fallback"
            >
              大模型分析暂不可用，以下为算法评估结果
            </div>
          </div>
        </div>

        <div v-else-if="analysisError" class="da-error">
          <el-icon color="#f56c6c" style="font-size:32px"><WarningFilled /></el-icon>
          <p>{{ analysisError }}</p>
        </div>
      </template>

      <template #footer>
        <div class="da-footer">
          <span v-if="currentResumeFile" class="da-resume-name">简历：{{ currentResumeFile.name }}</span>
          <el-button @click="analysisDialogVisible = false">关闭</el-button>
          <el-button
            v-if="currentResumeFile && !analysisLoading"
            type="primary"
            :disabled="!analysisTargetJobId"
            @click="doDeepAnalysis"
          >
            {{ analysisResult ? '重新分析' : '开始分析' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import PageGreeting from '@/components/PageGreeting.vue'
import JobMatchingList, { type MatchedJob as PPJobEntry } from '@/components/design/JobMatchingList.vue'
import { Upload, Document, Loading, WarningFilled, SuccessFilled } from '@element-plus/icons-vue'
import {
  fetchMatchingStatus, fetchAutoRecommend, fetchJobDetail,
  fetchFilterOptions, fetchFilteredJobs, fetchFavoriteIds, addFavorite, removeFavorite,
  fetchDeepAnalysis,
  type IndexStatus, type MatchedJob,
  type FilterOptions, type FilteredJob, type DeepAnalysisResult,
} from '../api/matching'
import { apiSaveMatchingHistory } from '@/api/history'
import { apiGetProfile } from '@/api/auth'
import { useAuth } from '@/composables/useAuth'

useAuth()

const EDU_OPTIONS = ['不限', '专科及以上', '本科及以上', '硕士及以上', '博士']
const BENEFIT_LIMIT = 25
const CITY_LIMIT = 20

const indexStatus = ref<IndexStatus>({ status: 'not_started', total: 0, indexed: 0, error: null })
let statusTimer: number | null = null

const indexedPct = computed(() =>
  indexStatus.value.total
    ? Math.floor(indexStatus.value.indexed / indexStatus.value.total * 100)
    : 0,
)

async function pollStatus() {
  try { indexStatus.value = await fetchMatchingStatus() } catch { }
  if (indexStatus.value.status === 'indexing' || indexStatus.value.status === 'not_started') {
    statusTimer = window.setTimeout(pollStatus, 5000)
  }
}

const activeTab = ref<'filter' | 'smart'>('filter')

function onTabChange() {
}

const currentResumeFile = ref<File | null>(null)

function clearSmartResume() {
  currentResumeFile.value = null
  recommendJobs.value = []
}

function onSmartFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) { currentResumeFile.value = file; recommendJobs.value = [] }
}

function onDropSmart(e: DragEvent) {
  isDraggingSmart.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) { currentResumeFile.value = file; recommendJobs.value = [] }
}

const filterOptions = ref<FilterOptions>({
  cities: [], education_raw: [], company_sizes: [], work_types: [], working_exps: [], benefit_keywords: [],
})
const benefitExpanded = ref(false)
const benefitDisplayList = computed(() =>
  benefitExpanded.value
    ? filterOptions.value.benefit_keywords
    : filterOptions.value.benefit_keywords.slice(0, BENEFIT_LIMIT),
)

const citiesExpanded = ref(false)
const citiesDisplayList = computed(() =>
  citiesExpanded.value
    ? filterOptions.value.cities
    : filterOptions.value.cities.slice(0, CITY_LIMIT),
)

const EXCLUDED_EXPS = new Set(['应届生', '在校生', '应届毕业生', '在校学生'])
const normalizedWorkExps = computed(() => {
  const seen = new Set<string>()
  return filterOptions.value.working_exps
    .map(e => (e === '经验不限' ? '不限' : e))
    .filter(e => !EXCLUDED_EXPS.has(e))
    .filter(e => { if (seen.has(e)) return false; seen.add(e); return true })
})

async function loadFilterOptions() {
  try {
    filterOptions.value = await fetchFilterOptions()
  } catch { }
}

const filterReq = reactive({
  cities: [] as string[],
  work_types: [] as string[],
  salary_min: undefined as number | undefined,
  salary_max: undefined as number | undefined,
  education: '不限',
  working_exps: [] as string[],
  company_sizes: [] as string[],
  benefit_keywords: [] as string[],
  major_keyword: '',
  page: 1,
  page_size: 20,
})

const filterResults = ref<FilteredJob[]>([])
const filterTotal = ref(0)
const filterLoading = ref(false)
const filterSearched = ref(false)

function toggleArr(arr: string[], val: string) {
  const idx = arr.indexOf(val)
  if (idx >= 0) arr.splice(idx, 1)
  else arr.push(val)
}

function clearFilter() {
  filterReq.cities = []
  filterReq.work_types = []
  filterReq.salary_min = undefined
  filterReq.salary_max = undefined
  filterReq.education = '不限'
  filterReq.working_exps = []
  filterReq.company_sizes = []
  filterReq.benefit_keywords = []
  filterReq.major_keyword = ''
  filterReq.page = 1
}

async function doFilter(page = 1) {
  filterReq.page = page
  filterLoading.value = true
  filterSearched.value = true
  filterResults.value = []
  try {
    const res = await fetchFilteredJobs({
      cities: filterReq.cities.length ? [...filterReq.cities] : undefined,
      work_types: filterReq.work_types.length ? [...filterReq.work_types] : undefined,
      salary_min: filterReq.salary_min ?? null,
      salary_max: filterReq.salary_max ?? null,
      education: filterReq.education !== '不限' ? filterReq.education : null,
      working_exps: filterReq.working_exps.length ? [...filterReq.working_exps] : undefined,
      company_sizes: filterReq.company_sizes.length ? [...filterReq.company_sizes] : undefined,
      benefit_keywords: filterReq.benefit_keywords.length ? [...filterReq.benefit_keywords] : undefined,
      major_keyword: filterReq.major_keyword || null,
      page: filterReq.page,
      page_size: filterReq.page_size,
    })
    filterResults.value = res.jobs
    filterTotal.value = res.total
  } catch (e: any) {
    ElMessage.error(e.message || '筛选失败')
  } finally {
    filterLoading.value = false
  }
}

const favoriteIds = ref<number[]>([])
const favLoading = ref<Record<number, boolean>>({})

function isFavorited(jobId: number) {
  return favoriteIds.value.includes(jobId)
}

async function loadFavoriteIds() {
  try {
    favoriteIds.value = await fetchFavoriteIds()
  } catch { }
}

async function toggleFavorite(jobId: number) {
  if (favLoading.value[jobId]) return
  favLoading.value[jobId] = true
  try {
    if (isFavorited(jobId)) {
      await removeFavorite(jobId)
      favoriteIds.value = favoriteIds.value.filter(id => id !== jobId)
      ElMessage.success('已取消收藏')
    } else {
      await addFavorite(jobId)
      favoriteIds.value = [...favoriteIds.value, jobId]
      ElMessage.success('收藏成功')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    delete favLoading.value[jobId]
  }
}

const drawerVisible = ref(false)
const drawerJob = ref<any>(null)

async function viewJobDetail(jobId: number) {
  drawerVisible.value = true
  drawerJob.value = null
  try {
    drawerJob.value = await fetchJobDetail(jobId)
  } catch {
    ElMessage.error('获取岗位详情失败')
    drawerVisible.value = false
  }
}

const isDraggingSmart = ref(false)
const autoLoading = ref(false)
const recommendJobs = ref<MatchedJob[]>([])

const mappedRecommendJobs = computed<PPJobEntry[]>(() =>
  recommendJobs.value.map(j => ({
    id:              j.job_id,
    job_summary:     j.job_name,
    job_name:        j.company_name,
    work_city:       j.work_city,
    salary_min:      j.salary_min,
    salary_max:      j.salary_max,
    working_exp:     j.working_exp,
    your_education:  j.your_education,
    company_size:    j.company_size,
    score:           (j.match_score ?? 0) / 100,
    score_semantic:  j.report?.dimensions?.['semantic']   ? Math.round(j.report.dimensions['semantic'].score)   : Math.round(j.match_score ?? 0),
    score_skill:     j.report?.dimensions?.['skills']     ? Math.round(j.report.dimensions['skills'].score)     : undefined,
    score_exp:       j.report?.dimensions?.['experience'] ? Math.round(j.report.dimensions['experience'].score) : undefined,
    dimensions: j.report?.dimensions ? {
      semantic:   j.report.dimensions['semantic'],
      skills:     j.report.dimensions['skills'],
      experience: j.report.dimensions['experience'],
    } : undefined,
  }))
)

async function doAutoRecommend() {
  if (!currentResumeFile.value) return
  autoLoading.value = true
  recommendJobs.value = []
  try {
    const res = await fetchAutoRecommend(currentResumeFile.value, 5)
    recommendJobs.value = res.matches.slice(0, 5)
    apiSaveMatchingHistory({
      mode: 'auto',
      filename: currentResumeFile.value.name,
      top_k: recommendJobs.value.length,
      result_json: JSON.stringify(recommendJobs.value),
    }).catch(() => {})
  } catch (e: any) {
    ElMessage.error(e.message || '推荐失败')
  } finally {
    autoLoading.value = false
  }
}

const analysisDialogVisible = ref(false)
const analysisTargetJobId = ref<number | null>(null)
const analysisTargetName = ref('')
const analysisLoading = ref(false)
const analysisResult = ref<DeepAnalysisResult | null>(null)
const analysisError = ref('')
const isDraggingDialog = ref(false)

function openDeepAnalysis(jobId: number, jobName: string, companyName: string) {
  analysisTargetJobId.value = jobId
  analysisTargetName.value = `${jobName} · ${companyName}`
  analysisResult.value = null
  analysisError.value = ''
  analysisDialogVisible.value = true
  if (currentResumeFile.value) {
    doDeepAnalysis()
  }
}

async function doDeepAnalysis() {
  if (!currentResumeFile.value || !analysisTargetJobId.value) return
  analysisLoading.value = true
  analysisResult.value = null
  analysisError.value = ''
  try {
    const res = await fetchDeepAnalysis(currentResumeFile.value, analysisTargetJobId.value)
    analysisResult.value = res
    apiSaveMatchingHistory({
      mode: 'specific',
      filename: currentResumeFile.value.name,
      match_score: res.match_score,
      job_name: res.job?.job_name,
      company_name: res.job?.company_name,
      result_json: JSON.stringify(res),
    }).catch(() => {})
  } catch (e: any) {
    analysisError.value = e.message || '深度分析失败，请重试'
  } finally {
    analysisLoading.value = false
  }
}

function onDialogFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) {
    currentResumeFile.value = file
    doDeepAnalysis()
  }
}

function onDropDialog(e: DragEvent) {
  isDraggingDialog.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) {
    currentResumeFile.value = file
    doDeepAnalysis()
  }
}

function formatSalary(min: number, max: number) {
  if (!min && !max) return '薪资面议'
  const toK = (v: number) => (v / 1000).toFixed(0) + 'K'
  if (min && max) return `${toK(min)}~${toK(max)}/月`
  return min ? `${toK(min)}+/月` : `≤${toK(max)}/月`
}

function rdScoreClr(s: number): string {
  if (s >= 80) return '#10B981'
  if (s >= 65) return '#3B82F6'
  if (s >= 50) return '#F59E0B'
  return '#EF4444'
}

function daScoreClass(score: number): string {
  if (score >= 80) return 'score--high'
  if (score >= 60) return 'score--mid'
  if (score >= 40) return 'score--ok'
  return 'score--low'
}

function hintText(score: number) {
  if (score >= 85) return '非常契合！强烈建议投递'
  if (score >= 70) return '匹配度良好，值得尝试'
  if (score >= 55) return '基本匹配，可视情况投递'
  return '匹配度较低，建议优先考虑其他岗位'
}

function hintClass(score: number) {
  if (score >= 85) return 'hint-high'
  if (score >= 70) return 'hint-mid'
  if (score >= 55) return 'hint-ok'
  return 'hint-low'
}

onMounted(async () => {
  pollStatus()
  loadFavoriteIds()
  await loadFilterOptions()

  try {
    const prof = await apiGetProfile()
    if (prof.target_city && filterOptions.value.cities.includes(prof.target_city)) {
      filterReq.cities = [prof.target_city]
    }
    if (prof.expected_salary_min) filterReq.salary_min = prof.expected_salary_min
    if (prof.expected_salary_max) filterReq.salary_max = prof.expected_salary_max
    if (prof.work_experience) {
      const expMap: Record<string, string> = {
        '应届生': '经验不限', '1年以内': '1年以下', '1-3年': '1-3年',
        '3-5年': '3-5年', '5-10年': '5-10年', '10年以上': '10年以上',
      }
      const mapped = expMap[prof.work_experience]
      const exps = normalizedWorkExps.value
      const match = exps.find(e => e === mapped || e === prof.work_experience)
      if (match) filterReq.working_exps = [match]
    }
  } catch { }
})
onUnmounted(() => { if (statusTimer) clearTimeout(statusTimer) })
</script>

<style scoped>
.jm-page {
  background: transparent;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.jm-greeting-wrap {
  padding: 0 32px;
  flex-shrink: 0;
}

.jm-status-strip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 28px;
  background: #F8F9FA;
  border-bottom: 0.5px solid #E8E8E8;
  font-size: 12px;
  color: #9CA3AF;
  flex-shrink: 0;
}

.jm-body {
  padding: 8px 32px 20px;
  max-width: 1100px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.jm-mode-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
  flex-shrink: 0;
}

.jm-mode-btn {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border: 1.5px solid #DCDCDC;
  border-radius: 3px;
  background: #FBFBFB;
  cursor: pointer;
  transition: border-color 150ms, background 150ms, box-shadow 150ms;
  text-align: left;
}
.jm-mode-btn:hover {
  border-color: #2C5749;
  background: #F5FAF8;
}
.jm-mode-btn.is-active {
  border-color: #1A3C34;
  background: #fff;
  box-shadow: 0 2px 10px rgba(26,60,52,0.12);
}
.jm-mode-icon {
  font-size: 18px;
  flex-shrink: 0;
  color: #4A7C68;
}
.jm-mode-btn.is-active .jm-mode-icon { color: #1A3C34; }
.jm-mode-label {
  font-size: 13.5px;
  font-weight: 600;
  color: #6B7280;
  display: block;
  line-height: 1.3;
}
.jm-mode-btn.is-active .jm-mode-label { color: #1A3C34; }
.jm-mode-sub {
  font-size: 11px;
  color: #B8BAC0;
  display: block;
  line-height: 1.3;
}
.jm-mode-btn.is-active .jm-mode-sub { color: #4A7C68; }
.jm-panel {
  background: #FBFBFB;
  border-radius: 3px;
  padding: 16px 20px;
  border: 0.5px solid #E8E8E8;
}
.jm-filter-results {
  margin-top: 12px;
}
.jm-filter-card {
  display: flex;
  flex-direction: column;
  gap: 0;
  flex-shrink: 0;
}
.filter-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 7px 0;
  border-bottom: 0.5px solid #EFEFEF;
}
.filter-row:last-of-type { border-bottom: none; }
.filter-label {
  flex-shrink: 0;
  width: 68px;
  font-size: 12px;
  font-weight: 500;
  color: #6B7280;
  padding-top: 5px;
  text-align: right;
  letter-spacing: 0.01em;
}
.filter-tags-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  flex: 1;
}
.filter-tags-wrap--benefit {
  max-height: 140px;
  overflow-y: auto;
}
.filter-tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 2px;
  font-size: 12.5px;
  border: 0.5px solid #DCDCDC;
  color: #4B5563;
  background: #FBFBFB;
  cursor: pointer;
  transition: border-color 140ms ease, color 140ms ease, background 140ms ease;
  user-select: none;
  line-height: 1.6;
}
.filter-tag:hover { border-color: #1A3C34; color: #1A3C34; background: #F2F6F5; }
.filter-tag.is-active { border-color: #1A3C34; background: #1A3C34; color: #FFFFFF; }
.filter-tag--sm { padding: 2px 8px; font-size: 12px; }
.filter-tag-more {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 2px;
  font-size: 12px;
  border: 1px dashed #DCDCDC;
  color: #9CA3AF;
  cursor: pointer;
  transition: border-color 140ms ease, color 140ms ease;
  user-select: none;
  line-height: 1.6;
}
.filter-tag-more:hover { border-color: #1A3C34; color: #1A3C34; }
.filter-salary-row { display: flex; align-items: center; gap: 8px; }
.salary-sep { color: #9ca3af; font-size: 16px; }
.salary-unit { font-size: 13px; color: #6b7280; white-space: nowrap; }
.filter-row--split {
  align-items: center;
  gap: 0;
}
.filter-row-half {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.filter-row-sep {
  width: 1px;
  height: 24px;
  background: #EFEFEF;
  margin: 0 16px;
  flex-shrink: 0;
}
.filter-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 10px;
  border-top: 0.5px solid #EFEFEF;
  margin-top: 4px;
  flex-shrink: 0;
}
.jm-loading-tip {
  text-align: center;
  padding: 32px;
  color: #9ca3af;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.jm-results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: #6B7280;
  margin-bottom: 16px;
  padding-bottom: 11px;
  border-bottom: 0.5px solid #EBEBEB;
  flex-wrap: wrap;
  gap: 8px;
}
.jm-match-tip {
  font-size: 11.5px;
  color: #B8BAC0;
  font-style: italic;
}
.jm-job-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}
.jm-job-card {
  border: 0.5px solid #E8E8E8;
  border-radius: 2px;
  padding: 14px 16px;
  cursor: pointer;
  transition: border-color 140ms ease, background 140ms ease;
  background: #FBFBFB;
  display: flex;
  flex-direction: column;
}
.jm-job-card:hover {
  border-color: #1A3C34;
  background: #F5FAF8;
}
.jm-job-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 8px;
  gap: 8px;
}
.jm-job-info { flex: 1; min-width: 0; }
.jm-job-name { font-family: 'Georgia', serif; font-size: 15px; font-weight: 400; color: #1A1A1A; margin-bottom: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.jm-job-company { font-size: 12px; color: #9CA3AF; }
.jm-job-meta { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }
.jm-job-desc { font-size: 12px; color: #9ca3af; line-height: 1.6; margin: 0; flex: 1; }
.jm-card-btns {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}
.match-icon-btn {
  flex-shrink: 0;
  background: none;
  border: 0.5px solid #DCDCDC;
  border-radius: 2px;
  padding: 4px 9px;
  font-size: 13px;
  cursor: pointer;
  color: #6B7280;
  transition: border-color 140ms, color 140ms, background 140ms;
  line-height: 1;
}
.match-icon-btn:hover {
  border-color: #1A3C34;
  color: #1A3C34;
  background: #F2F6F5;
}
.fav-btn {
  flex-shrink: 0;
  background: none;
  border: 0.5px solid #DCDCDC;
  border-radius: 2px;
  padding: 4px 9px;
  font-size: 15px;
  cursor: pointer;
  color: #C4C6C9;
  transition: border-color 140ms, color 140ms, background 140ms;
  line-height: 1;
}
.fav-btn:hover:not(:disabled) { border-color: #9B4A4A; color: #9B4A4A; background: #FAF0F0; }
.fav-btn.is-faved { border-color: #9B4A4A; color: #9B4A4A; }
.fav-btn--lg { padding: 5px 13px; font-size: 13px; display: flex; align-items: center; gap: 4px; }
.match-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 14px;
  border-radius: 2px;
  font-size: 12.5px;
  font-weight: 500;
  cursor: pointer;
  border: 0.5px solid #1A3C34;
  color: #1A3C34;
  background: #F5FAF8;
  transition: background 140ms, color 140ms;
  white-space: nowrap;
}
.match-btn:hover { background: #1A3C34; color: #fff; }
.match-btn--primary { background: #1A3C34; color: #fff; }
.match-btn--primary:hover { background: #132E28; }
.jm-pagination { display: flex; justify-content: center; margin-top: 20px; }
.jm-smart {
  display: flex;
  flex-direction: row;
  gap: 20px;
  min-height: 480px;
  padding: 14px 20px !important;
}
.jm-smart-left {
  flex-shrink: 0;
  width: 220px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.jm-smart-section-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #9CA3AF;
}
.jm-smart-right {
  flex: 1;
  min-width: 0;
}
.jm-drop-zone {
  width: 100%;
  min-height: 120px;
  border: 1.5px dashed #C8D8D2;
  border-radius: 3px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  cursor: pointer;
  transition: border-color 140ms, background 140ms;
  background: #F8FAF9;
  padding: 14px 10px;
  text-align: center;
  box-sizing: border-box;
}
.jm-drop-zone:hover, .jm-drop-zone.is-over { border-color: #1A3C34; background: #F0F6F4; }
.jm-drop-zone.has-file { border-color: #2C5749; background: #EEF4F2; border-style: solid; }
.jm-drop-icon { font-size: 22px; color: #4A7C68; }
.jm-drop-text { font-size: 12.5px; color: #3D4451; margin: 0; font-weight: 500; }
.jm-drop-hint { font-size: 11px; color: #B8BAC0; margin: 0; }
.jm-file-name { font-size: 12px; font-weight: 500; color: #1A3C34; margin: 0; word-break: break-all; }
.jm-remove-btn {
  font-size: 11px;
  color: #9B4A4A;
  background: none;
  border: 0.5px solid #DDB8B8;
  border-radius: 2px;
  padding: 2px 8px;
  cursor: pointer;
}
.jm-remove-btn:hover { background: #FAF0F0; }
.jm-ink-btn {
  width: 100%;
  padding: 10px 0;
  background: #1A3C34;
  color: #fff;
  border: none;
  border-radius: 3px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 150ms, opacity 150ms;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  letter-spacing: 0.02em;
}
.jm-ink-btn:hover:not(:disabled) { background: #2C5749; }
.jm-ink-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.jm-ink-btn.is-loading { opacity: 0.75; }
@keyframes jm-spin { to { transform: rotate(360deg); } }
.jm-btn-spinner {
  width: 12px; height: 12px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: jm-spin 0.8s linear infinite;
}
.jm-smart-tips {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  background: #F5FAF8;
  border-radius: 3px;
  border: 0.5px solid #C8D8D2;
}
.jm-tip-item {
  font-size: 11.5px;
  color: #4A7C68;
  display: flex;
  align-items: center;
  gap: 6px;
  line-height: 1.4;
}
.jm-tip-dot {
  width: 5px; height: 5px;
  border-radius: 50%;
  background: #2C5749;
  flex-shrink: 0;
}
.jm-index-warn {
  font-size: 11.5px;
  color: #B07D4A;
  background: #FAF5EE;
  border: 0.5px solid #E8D0A8;
  border-radius: 3px;
  padding: 6px 10px;
  text-align: center;
}
.jm-smart-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
  gap: 12px;
}
.jm-loading-rings {
  position: relative;
  width: 64px; height: 64px;
}
.jm-ring {
  position: absolute;
  inset: 0;
  border: 2.5px solid transparent;
  border-radius: 50%;
  animation: jm-spin 1.5s linear infinite;
}
.jm-ring-1 { border-top-color: #1A3C34; animation-duration: 1.2s; }
.jm-ring-2 { inset: 10px; border-top-color: #4A7C68; animation-direction: reverse; animation-duration: 1.8s; }
.jm-ring-3 { inset: 20px; border-top-color: #9AC6B8; animation-duration: 2.4s; }
.jm-ring-core {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  color: #1A3C34;
}
.jm-loading-msg { font-size: 14px; font-weight: 600; color: #1A3C34; margin: 0; }
.jm-loading-sub { font-size: 12px; color: #9CA3AF; margin: 0; }
.jm-smart-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
  text-align: center;
  gap: 10px;
  padding: 20px;
}
.jm-placeholder-icon { font-size: 32px; color: #C8D8D2; }
.jm-placeholder-title { font-family: 'Georgia', serif; font-size: 16px; color: #6B7280; font-weight: 400; margin: 0; }
.jm-placeholder-sub { font-size: 12.5px; color: #B8BAC0; line-height: 1.7; margin: 0; max-width: 320px; }
:deep(.el-button--primary) {
  background-color: #1A3C34 !important;
  border-color: #1A3C34 !important;
}
:deep(.el-button--primary:hover),
:deep(.el-button--primary:focus) {
  background-color: #2C5749 !important;
  border-color: #2C5749 !important;
}
.jm-drawer-content { padding: 16px; }
.jm-drawer-head { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 12px; gap: 12px; }
.jm-drawer-head-info { flex: 1; min-width: 0; }
.jm-drawer-title { font-family: 'Georgia', serif; font-size: 18px; font-weight: 400; margin: 0 0 4px; color: #1A1A1A; }
.jm-drawer-company { font-size: 12px; color: #9CA3AF; margin: 0; }
.jm-drawer-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.jm-drawer-actions { margin-bottom: 16px; }
.jm-drawer-section { margin-bottom: 16px; }
.jm-drawer-label { font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid #f1f5f9; }
.jm-drawer-text { font-size: 13px; color: #6b7280; line-height: 1.8; white-space: pre-wrap; margin: 0; }
.jm-drawer-loading { text-align: center; color: #9ca3af; padding: 60px 0; }
.da-no-resume {
  text-align: center;
  padding: 16px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #9ca3af;
  font-size: 14px;
}
.da-upload-zone {
  width: 100%;
  max-width: 400px;
  min-height: 100px;
}
.da-loading {
  text-align: center;
  padding: 40px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.da-loading-text { font-size: 16px; font-weight: 600; color: #374151; margin: 0; }
.da-loading-sub { font-size: 13px; color: #9ca3af; margin: 0; }
.da-result { display: flex; flex-direction: column; gap: 16px; }
.da-score-row {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px 0;
  border-bottom: 0.5px solid #EFEFEF;
}
.da-score-big {
  font-family: 'Georgia', serif;
  font-size: 42px;
  font-weight: 400;
  line-height: 1;
  flex-shrink: 0;
  letter-spacing: -0.02em;
}
.da-score-big.score--high { color: #1A3C34; }
.da-score-big.score--mid { color: #2C5749; }
.da-score-big.score--ok { color: #D97706; }
.da-score-big.score--low { color: #DC2626; }
.da-score-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.da-job-name { font-size: 16px; font-weight: 600; color: #1A1A1A; }
.da-company { font-size: 12.5px; color: #9CA3AF; }
.da-score-hint {
  font-family: 'Georgia', serif;
  font-size: 13px;
  font-style: italic;
  padding: 4px 12px;
  border-radius: 2px;
  display: inline-block;
  align-self: flex-start;
}
.hint-high { background: #EDF4EF; color: #3A6347; border: 0.5px solid #C3DFCA; }
.hint-mid { background: #FAF3EB; color: #8B6035; border: 0.5px solid #E0C9A8; }
.hint-ok { background: #EEF4F2; color: #2C5749; border: 0.5px solid #9AC6B8; }
.hint-low { background: #FAF0F0; color: #9B4A4A; border: 0.5px solid #DDB8B8; }
.da-dims { display: flex; flex-direction: column; gap: 8px; padding: 2px 0; }
.da-dim-row { display: flex; align-items: center; gap: 10px; }
.da-dim-label { width: 68px; font-size: 12px; color: #6B7280; text-align: right; flex-shrink: 0; }
.da-dim-bar-wrap { flex: 1; height: 6px; background: #F0F0F0; border-radius: 999px; overflow: hidden; }
.da-dim-bar-fill { height: 100%; border-radius: 999px; transition: width 0.4s ease; }
.da-dim-score { width: 28px; font-size: 12px; font-weight: 600; text-align: right; flex-shrink: 0; }
.da-dim-match { font-size: 11.5px; color: #9CA3AF; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.da-llm-section { display: flex; flex-direction: column; gap: 10px; }
.da-block {
  border-radius: 3px;
  padding: 12px 14px;
  border: 0.5px solid;
}
.da-block--green { background: #EDF4EF; border-color: #C3DFCA; }
.da-block--orange { background: #FAF3EB; border-color: #E0C9A8; }
.da-block--blue { background: #EEF4F2; border-color: #9AC6B8; }
.da-block-title {
  font-size: 13px;
  font-weight: 600;
  color: #3D4451;
  margin-bottom: 8px;
}
.da-list {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.da-list li {
  font-size: 13px;
  color: #374151;
  line-height: 1.6;
}
.da-fallback {
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 4px;
}
.da-error {
  text-align: center;
  padding: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #6b7280;
  font-size: 14px;
}
.da-footer {
  display: flex;
  align-items: center;
  gap: 12px;
}
.da-resume-name {
  flex: 1;
  font-size: 12px;
  color: #9ca3af;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.fade-up-enter-active, .fade-up-leave-active { transition: all 0.35s ease; }
.fade-up-enter-from, .fade-up-leave-to { opacity: 0; transform: translateY(16px); }
@media (max-width: 800px) {
  .jm-smart-upload-row { flex-direction: column; }
  .jm-smart-btn { width: 100%; height: auto; padding: 14px; }
  .filter-row { flex-direction: column; gap: 8px; }
  .filter-label { text-align: left; width: auto; }
  .jm-rec-card { flex-wrap: wrap; }
}
</style>
