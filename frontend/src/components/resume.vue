<template>
  <div class="rp-root">
    <input ref="fileInputRef" type="file" accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.webp" style="display:none" @change="onFileChange" />

    <Transition name="phase-fade">
      <div v-if="phase === 'upload'" class="rp-upload">

        <div class="rp-upload-inner" :class="{ 'rp-precise-layout': mode === 'precise' }">
         
          <div class="rp-left-col">
         
          <div class="rp-mode-tabs">
            <button :class="['rp-mode-tab', { active: mode === 'comprehensive' }]" @click="mode = 'comprehensive'">
              <div class="rp-mode-info">
                <span class="rp-mode-title">综合分析</span>
                <span class="rp-mode-desc">8 维度深度评估</span>
              </div>
            </button>
            <button :class="['rp-mode-tab', { active: mode === 'precise' }]" @click="mode = 'precise'">
              <div class="rp-mode-info">
                <span class="rp-mode-title">精确分析</span>
                <span class="rp-mode-desc">对比 JD，精准命中率</span>
              </div>
            </button>
          </div>

         
          <div
            class="rp-dropzone"
            :class="{ active: dragOver, filled: !!uploadFile }"
            @dragover.prevent="dragOver = true"
            @dragleave.prevent="dragOver = false"
            @drop.prevent="onDrop"
          >
            <div v-if="!uploadFile" class="rp-drop-inner" @click="triggerPick">
              <div class="rp-drop-icon-wrap">
               
                <svg class="rp-drop-main-icon" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="10" y="6" width="36" height="46" rx="4" fill="#EEF4F2" stroke="#2C5749" stroke-width="2.2"/>
                  <rect x="10" y="6" width="36" height="46" rx="4" fill="url(#inkFill)" stroke="#1A3C34" stroke-width="2"/>
                  <line x1="18" y1="22" x2="38" y2="22" stroke="#4A7C68" stroke-width="2" stroke-linecap="round"/>
                  <line x1="18" y1="29" x2="38" y2="29" stroke="#4A7C68" stroke-width="2" stroke-linecap="round"/>
                  <line x1="18" y1="36" x2="30" y2="36" stroke="#4A7C68" stroke-width="2" stroke-linecap="round"/>
                  <circle cx="50" cy="46" r="12" fill="#1A3C34"/>
                  <polyline points="50,40 50,52" stroke="#EEF4F2" stroke-width="2.2" stroke-linecap="round"/>
                  <polyline points="45,45 50,40 55,45" stroke="#EEF4F2" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                  <defs>
                    <linearGradient id="inkFill" x1="10" y1="6" x2="46" y2="52" gradientUnits="userSpaceOnUse">
                      <stop offset="0%" stop-color="#F5FAF8"/>
                      <stop offset="100%" stop-color="#EEF4F2"/>
                    </linearGradient>
                  </defs>
                </svg>
               
                <span class="rp-drop-float rp-drop-f1">📄</span>
                <span class="rp-drop-float rp-drop-f2">✦</span>
                <span class="rp-drop-float rp-drop-f3">◈</span>
              </div>
              <p class="rp-drop-title">拖拽简历至此，或<span class="rp-drop-link">点击选择</span></p>
              <div class="rp-fmts">
                <span>PDF</span><span>DOC</span><span>DOCX</span><span>JPG</span><span>PNG</span>
              </div>
            </div>
            <div v-else class="rp-file-preview">
              <div class="rp-file-info">
                <p class="rp-file-name">{{ uploadFile.name }}</p>
                <p class="rp-file-size">{{ fmtSize(uploadFile.size) }}</p>
              </div>
              <button class="rp-btn-change" @click.stop="triggerPick">更换</button>
            </div>
          </div>

          <p v-if="uploadError" class="rp-err">⚠️ {{ uploadError }}</p>

         
          <button class="rp-btn-start" :disabled="!uploadFile || (mode === 'precise' && !jdText.trim())" @click="startEval">
            <span class="rp-btn-start-inner">
              <span>{{ mode === 'precise' ? '开始精确分析' : '开始深度评估' }}</span>
            </span>
            <span class="rp-btn-glow" />
          </button>
          </div>
          <transition name="jd-slide">
            <div v-if="mode === 'precise'" class="rp-right-col">
              <div class="rp-jd-section rp-jd-section--right">
                <div class="rp-jd-header">
                  <div>
                    <p class="rp-jd-title">粘贴目标岗位 JD</p>
                    <p class="rp-jd-hint">逐条对照简历进行精准匹配分析</p>
                  </div>
                </div>
                <textarea
                  v-model="jdText"
                  class="rp-jd-textarea rp-jd-textarea--full"
                  placeholder="在此粘贴岗位描述（JD）内容...&#10;&#10;例如：&#10;【岗位职责】&#10;1. 负责后端系统架构设计与研发...&#10;【任职要求】&#10;1. 本科及以上学历，3年以上后端开发经验..."
                />
                <div class="rp-jd-count">{{ jdText.length }} 字</div>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </Transition>

    
    <Transition name="phase-fade">
      <div v-if="phase === 'processing'" class="rp-proc">
        <div class="rp-proc-card">
          <div class="iv-spinner-wrap">
            <div class="rp-spinner">
              <div class="rp-ring rp-ring-1"></div>
              <div class="rp-ring rp-ring-2"></div>
              <div class="rp-ring rp-ring-3"></div>
              <div class="rp-ring-core">评</div>
            </div>
          </div>
          <p class="rp-proc-msg">{{ currentMsg }}</p>
          <p class="rp-elapsed">已处理 {{ elapsedSec }}s</p>

          <div class="rp-steps">
            <div v-for="(label, i) in STEPS" :key="i" :class="['rp-step', getStepCls(i)]">
              <div class="rp-step-dot">
                <template v-if="currentStep > i + 1">
                  <span class="rp-step-check">✓</span>
                </template>
                <template v-else-if="currentStep === i + 1">
                  <span class="rp-step-pulse"></span>
                </template>
                <template v-else>
                  <span>{{ i + 1 }}</span>
                </template>
              </div>
              <span class="rp-step-lbl">{{ label }}</span>
              <div v-if="i < STEPS.length - 1" class="rp-step-line"></div>
            </div>
          </div>

          <div class="rp-pbar-wrap">
            <div class="rp-pbar-fill" :style="{ width: progress + '%' }">
              <div class="rp-pbar-shine"></div>
            </div>
          </div>
          <span class="rp-pct">{{ progress }}%</span>
        </div>
      </div>
    </Transition>

    
    <Transition name="phase-fade">
      <div v-if="phase === 'done'" class="rp-report">

        <div class="rp-topbar">
          <div class="rp-topbar-l">
            <span class="rp-topbar-file">{{ uploadFile?.name }}</span>
            <span class="rp-topbar-meta">{{ report.char_count.toLocaleString() }} 字符</span>
          </div>
          <button class="rp-btn-reset" @click="reset">↩ 重新评估</button>
        </div>

        
        <div class="rp-card rp-overview">
          <div class="rp-gauge-wrap">
            <EChartsCard :options="gaugeOpts" height="220px" />
            <p class="rp-gauge-label">综合评分</p>
          </div>
          <div class="rp-overview-info">
            <div :class="['rp-rating-badge', ratingCls(evaluation.overall_score)]">
              {{ evaluation.overall_rating }}
            </div>
            <p class="rp-score-num">{{ evaluation.overall_score }} <small>/ 100</small></p>
            <p class="rp-summary">{{ evaluation.summary }}</p>
          </div>
        </div>

        <div class="rp-card">
          <h2 class="rp-card-title">维度综合评估</h2>
          <div class="rp-dims">
            <div class="rp-dim rp-radar-cell">
              <p class="rp-radar-cell-label">能力雷达</p>
              <EChartsCard :options="radarOpts" height="260px" />
            </div>
            
            <div
              v-for="([key, dim]) in dimEntries"
              :key="key"
              class="rp-dim"
            >
              <div class="rp-dim-top">
                <span class="rp-dim-icon">{{ dim.icon }}</span>
                <span class="rp-dim-lbl">{{ dim.label }}</span>
                <span class="rp-dim-score" :style="{ color: scoreClr(dim.score) }">{{ dim.score }}</span>
              </div>
              <div class="rp-dim-bar">
                <div
                  class="rp-dim-fill"
                  :style="{ width: dim.score + '%', background: scoreClr(dim.score) }"
                ></div>
              </div>
              <div class="rp-dim-footer">
                <span class="rp-dim-rating" :style="{ color: scoreClr(dim.score) }">{{ dim.rating }}</span>
                <span class="rp-dim-weight">权重 {{ dim.weight }}%</span>
              </div>
              <p v-if="dim.detail" class="rp-dim-desc">{{ dim.detail }}</p>
            </div>
          </div>
        </div>

        
        <div class="rp-card">
          <h2 class="rp-card-title">各维度详细分析</h2>
          <el-collapse accordion>
            <el-collapse-item v-for="([key, dim]) in dimEntries" :key="key" :name="key">
              <template #title>
                <div class="rp-acc-title">
                  <span>{{ dim.icon }} {{ dim.label }}</span>
                  <span class="rp-acc-score" :style="{ color: scoreClr(dim.score) }">
                    {{ dim.score }} 分 · {{ dim.rating }}
                  </span>
                </div>
              </template>
              <div class="rp-dim-detail">
                <p class="rp-detail-p">{{ dim.detail }}</p>
                <div v-if="dim.highlights?.length" class="rp-highlights">
                  <div class="rp-detail-label rp-detail-label--green">亮点优势</div>
                  <ul><li v-for="(h, hi) in dim.highlights" :key="hi">{{ h }}</li></ul>
                </div>
                <div v-if="dim.issues?.length" class="rp-issues">
                  <div class="rp-detail-label rp-detail-label--red">问题短板</div>
                  <ul><li v-for="(iss, ii) in dim.issues" :key="ii">{{ iss }}</li></ul>
                </div>
                <div v-if="dim.suggestions?.length" class="rp-sug">
                  <div class="rp-detail-label rp-detail-label--blue">改进建议</div>
                  <ul><li v-for="(sg, si) in dim.suggestions" :key="si">{{ sg }}</li></ul>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>

        
        <template v-if="mode === 'comprehensive'">

        
        <div class="rp-card rp-sw">
          <div class="rp-sw-col rp-strengths">
            <h3>核心优势</h3>
            <ul>
              <li v-for="(s, i) in evaluation.strengths" :key="i">{{ s }}</li>
            </ul>
          </div>
          <div class="rp-sw-col rp-weaknesses">
            <h3>待改进项</h3>
            <ul>
              <li v-for="(w, i) in evaluation.weaknesses" :key="i">{{ w }}</li>
            </ul>
          </div>
        </div>

       
        <div class="rp-card">
          <h2 class="rp-card-title">优先优化建议</h2>
          <div class="rp-recs">
            <div
              v-for="(rec, i) in evaluation.key_recommendations"
              :key="i"
              :class="['rp-rec', rec.priority === '高' ? 'rp-rec-high' : rec.priority === '中' ? 'rp-rec-mid' : 'rp-rec-low']"
            >
              <div class="rp-rec-hd">
                <span class="rp-rec-badge">
              {{ rec.priority === '高' ? '高优先级' : rec.priority === '中' ? '中优先级' : '低优先级' }}
                </span>
                <span class="rp-rec-cat">{{ rec.category }}</span>
              </div>
              <p class="rp-rec-action"><strong>{{ rec.action }}</strong></p>
              <p class="rp-rec-eg"><em>{{ rec.example }}</em></p>
              <p class="rp-rec-impact">{{ rec.impact }}</p>
            </div>
          </div>
        </div>

        
        <div class="rp-card">
          <h2 class="rp-card-title">职业发展建议</h2>
          <div class="rp-career">
            <div v-if="evaluation.career_path?.suitable_positions?.length" class="rp-career-sect">
              <h4>适合岗位方向</h4>
              <div class="rp-pos-tags">
                <span v-for="(p, i) in evaluation.career_path.suitable_positions" :key="i">{{ p }}</span>
              </div>
            </div>
            <div class="rp-career-sect">
              <h4>目标公司建议</h4>
              <div v-if="evaluation.career_path?.target_companies?.tier1?.length" class="rp-tier">
                <span class="rp-tier-tag rp-t1">冲击</span>
                <span v-for="c in evaluation.career_path.target_companies.tier1" :key="c" class="rp-co">{{ c }}</span>
              </div>
              <div v-if="evaluation.career_path?.target_companies?.tier2?.length" class="rp-tier">
                <span class="rp-tier-tag rp-t2">稳妥</span>
                <span v-for="c in evaluation.career_path.target_companies.tier2" :key="c" class="rp-co">{{ c }}</span>
              </div>
              <div v-if="evaluation.career_path?.target_companies?.tier3?.length" class="rp-tier">
                <span class="rp-tier-tag rp-t3">保底</span>
                <span v-for="c in evaluation.career_path.target_companies.tier3" :key="c" class="rp-co">{{ c }}</span>
              </div>
            </div>
            <div class="rp-career-plan">
              <div class="rp-plan-blk">
                <h4>近期（3—6 个月）</h4>
                <p>{{ evaluation.career_path?.short_term }}</p>
              </div>
              <div class="rp-plan-blk">
                <h4>中期（1—2 年）</h4>
                <p>{{ evaluation.career_path?.medium_term }}</p>
              </div>
            </div>
          </div>
        </div>

        
        <div v-if="evaluation.interview_tips?.length" class="rp-card">
          <h2 class="rp-card-title">面试准备建议</h2>
          <ol class="rp-tips">
            <li v-for="(tip, i) in evaluation.interview_tips" :key="i">{{ tip }}</li>
          </ol>
        </div>

        
        <div class="rp-card">
          <el-collapse>
            <el-collapse-item title="原始解析数据（JSON）" name="raw">
              <pre class="rp-json">{{ JSON.stringify(report.resume_data, null, 2) }}</pre>
            </el-collapse-item>
          </el-collapse>
        </div>

        </template>
               <div v-if="jdMatch" class="rp-card">
          <h2 class="rp-card-title">JD 精确匹配报告</h2>

         
          <div class="rp-jdm-overview">
            <div :class="['rp-jdm-badge', jdMatch.overall_match === 'High' ? 'jdm-high' : jdMatch.overall_match === 'Medium' ? 'jdm-mid' : 'jdm-low']">
              {{ jdMatch.overall_match === 'High' ? '高度匹配' : jdMatch.overall_match === 'Medium' ? '中度匹配' : '匹配较低' }}
            </div>
            <div class="rp-jdm-pct">{{ jdMatch.match_percentage }}<small>%</small></div>
            <p class="rp-jdm-summary">{{ jdMatch.summary }}</p>
          </div>

          
          <div class="rp-jdm-section">
            <h3 class="rp-jdm-subtitle">岗位要求逐条匹配</h3>
            <div
              v-for="(req, i) in jdMatch.requirements_analysis"
              :key="i"
              :class="['rp-req-item', req.match_level === 'High Match' ? 'req-high' : req.match_level === 'Potential Match' ? 'req-potential' : 'req-gap']"
            >
              <div class="rp-req-hd">
                <span :class="['rp-req-badge', req.match_level === 'High Match' ? 'badge-high' : req.match_level === 'Potential Match' ? 'badge-potential' : 'badge-gap']">
                  {{ req.match_level }}
                </span>
                <span class="rp-req-text">{{ req.requirement }}</span>
              </div>
              <p class="rp-req-evidence">{{ req.evidence }}</p>
              <p v-if="req.rewrite_suggestion" class="rp-req-suggest">建议改写：{{ req.rewrite_suggestion }}</p>
            </div>
          </div>

          
          <div class="rp-sw" style="margin-bottom:20px">
            <div class="rp-sw-col rp-strengths">
              <h3>相对 JD 的优势</h3>
              <ul><li v-for="(s, i) in jdMatch.strengths" :key="i">{{ s }}</li></ul>
            </div>
            <div class="rp-sw-col rp-weaknesses">
              <h3>核心缺口</h3>
              <ul><li v-for="(g, i) in jdMatch.gaps" :key="i">{{ g }}</li></ul>
            </div>
          </div>

          
          <div v-if="jdMatch.rewrite_priority?.length" class="rp-jdm-section">
            <h3 class="rp-jdm-subtitle">简历改写优先级</h3>
            <div
              v-for="(rw, i) in jdMatch.rewrite_priority"
              :key="i"
              :class="['rp-rec', rw.priority === '高' ? 'rp-rec-high' : rw.priority === '中' ? 'rp-rec-mid' : 'rp-rec-low']"
            >
              <div class="rp-rec-hd">
                <span class="rp-rec-badge">{{ rw.priority === '高' ? '高优先级' : rw.priority === '中' ? '中优先级' : '低优先级' }}</span>
                <span class="rp-rec-cat">{{ rw.section }}</span>
              </div>
              <p class="rp-rec-action"><strong>{{ rw.action }}</strong></p>
              <p class="rp-rec-eg"><em>{{ rw.example }}</em></p>
            </div>
          </div>

          
          <div v-if="jdMatch.interview_prediction" class="rp-jdm-section">
            <h3 class="rp-jdm-subtitle">面试通过预测</h3>
            <div class="rp-jdm-passrate">
              面试通过率：
              <span :class="['rp-jdm-rate', jdMatch.interview_prediction.pass_rate === '高' ? 'rate-high' : jdMatch.interview_prediction.pass_rate === '中' ? 'rate-mid' : 'rate-low']">
                {{ jdMatch.interview_prediction.pass_rate }}
              </span>
            </div>
            <div v-if="jdMatch.interview_prediction.likely_questions?.length" class="rp-jdm-questions">
              <p class="rp-jdm-q-title">可能被追问的问题：</p>
              <ol><li v-for="(q, i) in jdMatch.interview_prediction.likely_questions" :key="i">{{ q }}</li></ol>
            </div>
            <div v-if="jdMatch.interview_prediction.red_flags?.length" class="rp-jdm-redflags">
              <p class="rp-jdm-q-title">面试官可能质疑的点：</p>
              <ul><li v-for="(rf, i) in jdMatch.interview_prediction.red_flags" :key="i">{{ rf }}</li></ul>
            </div>
          </div>

          
          <div class="rp-jdm-verdict">
            <p>{{ jdMatch.final_verdict }}</p>
          </div>
        </div>

      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import EChartsCard from './EChartsCard.vue'
import { apiSaveResumeAnalysis } from '@/api/history'


interface Dimension {
  score: number
  rating: string
  weight: number
  icon: string
  label: string
  level?: string
  highlights: string[]
  issues: string[]
  suggestions: string[]
  detail: string
}
interface Evaluation {
  overall_score: number
  overall_rating: string
  summary: string
  dimensions: Record<string, Dimension>
  strengths: string[]
  weaknesses: string[]
  key_recommendations: { priority: string; category: string; action: string; example: string; impact: string }[]
  career_path: {
    suitable_positions: string[]
    target_companies: { tier1: string[]; tier2: string[]; tier3: string[] }
    short_term: string
    medium_term: string
  }
  interview_tips: string[]
  format_issues: string[]
}
interface Report {
  resume_data: any
  evaluation: Evaluation
  jd_match?: JdMatchReport
  filename: string
  char_count: number
  elapsed_seconds: number
}
interface RequirementAnalysis {
  requirement: string
  match_level: 'High Match' | 'Potential Match' | 'Gap'
  evidence: string
  rewrite_suggestion: string
}
interface JdMatchReport {
  overall_match: 'High' | 'Medium' | 'Low'
  match_percentage: number
  summary: string
  requirements_analysis: RequirementAnalysis[]
  strengths: string[]
  gaps: string[]
  rewrite_priority: { priority: string; section: string; action: string; example: string }[]
  interview_prediction: {
    pass_rate: string
    likely_questions: string[]
    red_flags: string[]
  }
  final_verdict: string
}

const BASE = 'http://localhost:8000'


const mode = ref<'comprehensive' | 'precise'>('comprehensive')
const jdText = ref('')
const jdMatch = ref<JdMatchReport | null>(null)

const phase = ref<'upload' | 'processing' | 'done'>('upload')
const uploadFile = ref<File | null>(null)
const dragOver = ref(false)
const uploadError = ref('')
const currentStep = ref(0)
const currentMsg = ref('准备中...')
const progress = ref(0)
const elapsedSec = ref(0)
const report = ref<Report>({ resume_data: {}, evaluation: {} as Evaluation, filename: '', char_count: 0, elapsed_seconds: 0 })
const fileInputRef = ref<HTMLInputElement>()


const sseProgress = ref(0)
let progressTimer: ReturnType<typeof setInterval> | null = null
let elapsedTimer: ReturnType<typeof setInterval> | null = null
let evalStartTime = 0

function startTimers() {
  evalStartTime = Date.now()
  elapsedTimer = setInterval(() => {
    elapsedSec.value = Math.floor((Date.now() - evalStartTime) / 1000)
  }, 1000)
  progressTimer = setInterval(() => {
    const diff = sseProgress.value - progress.value
    if (Math.abs(diff) < 0.5) {
      progress.value = sseProgress.value
    } else {
      progress.value = Math.round(progress.value + diff * 0.18)
    }
  }, 80)
}

function stopTimers() {
  if (progressTimer) { clearInterval(progressTimer); progressTimer = null }
  if (elapsedTimer) { clearInterval(elapsedTimer); elapsedTimer = null }
}

// ─── Computed ─────────────────────────────────────────────────────────────────
const STEPS = computed(() =>
  mode.value === 'precise'
    ? ['读取文件', '解析结构', '综合评估', 'JD精确匹配', '生成报告', '完成']
    : ['读取文件', '解析结构', '多维评估', '生成报告', '完成']
)

const evaluation = computed(() => report.value.evaluation || ({} as Evaluation))
const dimEntries = computed(() => Object.entries(evaluation.value.dimensions || {}))

const gaugeOpts = computed(() => {
  const score = evaluation.value.overall_score || 0
  return {
    animation: true,
    series: [{
      type: 'gauge',
      startAngle: 205,
      endAngle: -25,
      min: 0,
      max: 100,
      radius: '90%',
      splitNumber: 5,
      axisLine: {
        lineStyle: {
          width: 18,
          color: [[0.4, '#EF4444'], [0.6, '#F59E0B'], [0.75, '#3B82F6'], [1, '#10B981']],
        },
      },
      pointer: { length: '65%', width: 6, itemStyle: { color: '#3B6FA8' } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      detail: {
        valueAnimation: true,
        formatter: '{value}',
        fontSize: 44,
        fontWeight: 'bold',
        color: '#142038',
        offsetCenter: [0, '68%'],
      },
      title: { show: false },
      data: [{ value: score }],
    }],
  }
})

const radarOpts = computed(() => {
  const dims = evaluation.value.dimensions
  if (!dims) return {}
  const list = Object.values(dims) as Dimension[]
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item' },
    radar: {
      indicator: list.map(d => ({ name: d.label, max: 100 })),
      radius: '60%',
      center: ['50%', '54%'],
      splitNumber: 5,
      axisName: { color: '#2A4268', fontSize: 13, fontWeight: '500' },
      splitArea: { areaStyle: { color: ['rgba(59,111,168,0.02)', 'rgba(59,111,168,0.05)', 'rgba(59,111,168,0.02)', 'rgba(59,111,168,0.05)'] } },
      axisLine: { lineStyle: { color: 'rgba(59,111,168,0.15)' } },
      splitLine: { lineStyle: { color: 'rgba(59,111,168,0.1)' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: list.map(d => d.score),
        name: '能力评分',
        symbol: 'circle',
        symbolSize: 7,
        lineStyle: { color: '#3B6FA8', width: 2.5 },
        areaStyle: {
          color: { type: 'radial', x: 0.5, y: 0.5, r: 0.5,
            colorStops: [{ offset: 0, color: 'rgba(59,111,168,0.45)' }, { offset: 1, color: 'rgba(59,111,168,0.04)' }] },
        },
        itemStyle: { color: '#3B6FA8', borderColor: '#fff', borderWidth: 2 },
        label: {
          show: true,
          formatter: (p: any) => p.value,
          fontSize: 11,
          color: '#3B6FA8',
          fontWeight: 'bold',
        },
      }],
    }],
  }
})


const fmtSize = (b: number) => b < 1048576 ? (b / 1024).toFixed(1) + ' KB' : (b / 1048576).toFixed(1) + ' MB'

const scoreClr = (s: number) => s >= 80 ? '#4A9A6E' : s >= 65 ? '#3B6FA8' : s >= 50 ? '#B07D4A' : '#9B4A4A'

const ratingCls = (s: number) => s >= 80 ? 'badge-excellent' : s >= 65 ? 'badge-good' : s >= 50 ? 'badge-avg' : 'badge-poor'

const getStepCls = (i: number) => currentStep.value > i + 1 ? 'done' : currentStep.value === i + 1 ? 'active' : 'pending'


const triggerPick = () => fileInputRef.value?.click()

const onFileChange = (e: Event) => {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (f) setFile(f)
  ;(e.target as HTMLInputElement).value = ''
}

const onDrop = (e: DragEvent) => {
  dragOver.value = false
  const f = e.dataTransfer?.files?.[0]
  if (f) setFile(f)
}

const setFile = (f: File) => {
  if (!/\.(pdf|doc|docx|jpg|jpeg|png|webp)$/i.test(f.name)) { uploadError.value = '仅支持 PDF / DOC / DOCX / JPG / PNG / WEBP 格式'; return }
  if (f.size > 10 * 1024 * 1024) { uploadError.value = '文件大小不能超过 10 MB'; return }
  uploadError.value = ''
  uploadFile.value = f
}


const reset = () => {
  stopTimers()
  phase.value = 'upload'
  progress.value = 0
  sseProgress.value = 0
  elapsedSec.value = 0
  currentStep.value = 0
  currentMsg.value = '准备中...'
  jdMatch.value = null
  report.value = { resume_data: {}, evaluation: {} as Evaluation, filename: '', char_count: 0, elapsed_seconds: 0 }
}

const startEval = async () => {
  if (!uploadFile.value) return
  if (mode.value === 'precise' && !jdText.value.trim()) return

  phase.value = 'processing'
  progress.value = 0
  sseProgress.value = 0
  elapsedSec.value = 0
  currentStep.value = 1
  currentMsg.value = '正在准备评估...'
  uploadError.value = ''
  jdMatch.value = null
  startTimers()

  const fd = new FormData()
  fd.append('file', uploadFile.value)

  const url = mode.value === 'precise'
    ? `${BASE}/api/resume/evaluate-jd`
    : `${BASE}/api/resume/evaluate`

  if (mode.value === 'precise') {
    fd.append('jd_text', jdText.value.trim())
  }

  try {
    const res = await fetch(url, { method: 'POST', body: fd })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    if (!res.body) throw new Error('No response body')

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buf = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const lines = buf.split('\n')
      buf = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const ev = JSON.parse(line.slice(6))
          if (ev.message) currentMsg.value = ev.message
          if (ev.progress !== undefined) sseProgress.value = ev.progress
          if (ev.step) currentStep.value = ev.step

          if (ev.error) {
            stopTimers()
            uploadError.value = ev.message || '评估失败'
            phase.value = 'upload'
            return
          }
          if (ev.stage === 'done' && ev.result) {
            stopTimers()
            sseProgress.value = 100
            progress.value = 100
            report.value = ev.result
            if (ev.result.jd_match) jdMatch.value = ev.result.jd_match
            phase.value = 'done'
            
            apiSaveResumeAnalysis({
              filename: ev.result.filename,
              overall_score: ev.result.evaluation?.overall_score,
              overall_rating: ev.result.evaluation?.overall_rating,
              char_count: ev.result.char_count,
              elapsed_seconds: ev.result.elapsed_seconds,
              result_json: JSON.stringify(ev.result),
            }).catch(() => {/* 保存失败不影响主流程 */})
          }
        } catch { /* ignore */ }
      }
    }
  } catch (err) {
    stopTimers()
    uploadError.value = err instanceof Error ? err.message : '评估请求失败，请重试'
    phase.value = 'upload'
  }
}
</script>

<style scoped lang="scss">
// ─── Variables ────────────────────────────────────────────────────────────────

$ink:         #1A3C34;   
$ink-mid:     #2C5749;   
$ink-pale:    #4A7C68;   
$ink-light:   #EEF4F2;   
$ink-tint:    #F5FAF8;   
$bg:          #F8F9F8;   
$card-bg:     #FBFBFB;   
$border:      #C8D8D2;   
$border-std:  #DDE8E4;   
$text:        #1A1A1A;   
$text-muted:  #6B7280;   
$text-sub:    #3D4451;   
$radius:      4px;       
$shadow:      0 1px 6px rgba(26,60,52,0.07);
$shadow-lg:   0 4px 20px rgba(26,60,52,0.11);
$font-display: 'Georgia', 'Noto Serif SC', 'Source Han Serif SC', serif;
$font-body:    'Inter', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;


$primary:       $ink;
$primary-mid:   $ink-mid;
$primary-light: $ink-light;
$primary-ghost: $ink-tint;


.rp-root {
  flex: 1;
  background: transparent;
  position: relative;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
}


.phase-fade-enter-active, .phase-fade-leave-active { transition: all .4s ease; }
.phase-fade-enter-from { opacity: 0; transform: translateY(24px); }
.phase-fade-leave-to { opacity: 0; transform: translateY(-12px); }


.rp-upload {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow-y: auto;
  padding: 24px 32px;
  background: transparent;
}


.rp-bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  pointer-events: none;
  animation: orb-drift 12s ease-in-out infinite;
}
.rp-orb-1 {
  width: 380px; height: 380px;
  background: radial-gradient(circle, rgba(22,163,74,.18) 0%, transparent 70%);
  top: -80px; left: -80px;
  animation-delay: 0s;
}
.rp-orb-2 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, rgba(13,148,136,.16) 0%, transparent 70%);
  bottom: -60px; right: -40px;
  animation-delay: 4s;
}
.rp-orb-3 {
  width: 220px; height: 220px;
  background: radial-gradient(circle, rgba(101,163,13,.14) 0%, transparent 70%);
  top: 40%; left: 55%;
  animation-delay: 8s;
}
@keyframes orb-drift {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33%       { transform: translate(20px, -20px) scale(1.05); }
  66%       { transform: translate(-15px, 15px) scale(.95); }
}


.rp-upload-inner {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 480px;
  padding: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;

  
  &.rp-precise-layout {
    max-width: 1060px;
    flex-direction: row;
    align-items: stretch;
    gap: 28px;

    .rp-left-col {
      flex: 0 0 480px;
      width: auto;
    }
  }
}


.rp-left-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  width: 100%;
  min-width: 0;
}


.rp-right-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}


.rp-hero {
  text-align: center;
}

.rp-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  background: rgba(22,163,74,.1);
  border: 1px solid rgba(22,163,74,.2);
  color: $primary;
  padding: 4px 14px;
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 600;
  margin-bottom: 8px;
  backdrop-filter: blur(8px);
  letter-spacing: .4px;
}

.rp-badge-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: $primary;
  box-shadow: 0 0 6px rgba(22,163,74,.6);
  animation: dot-pulse 2s ease-in-out infinite;
}
@keyframes dot-pulse {
  0%, 100% { box-shadow: 0 0 4px rgba(22,163,74,.5); }
  50%       { box-shadow: 0 0 12px rgba(22,163,74,.9); }
}

.rp-hero h1 {
  font-size: 24px;
  font-weight: 800;
  margin: 0;
  background: linear-gradient(135deg, #15803D 0%, $primary 40%, #0D9488 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -.5px;
}


.rp-dropzone {
  width: 100%;
  border: 1.5px dashed rgba(26,60,52,.35);
  border-radius: 20px;
  background: rgba(255,255,255,.65);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 8px 32px rgba(26,60,52,.08), inset 0 1px 0 rgba(255,255,255,.8);
  transition: all .25s ease;
  cursor: pointer;
  overflow: hidden;

  &:hover, &.active {
    border-color: $primary;
    border-style: solid;
    background: rgba(255,255,255,.85);
    box-shadow: 0 12px 40px rgba(26,60,52,.16), inset 0 1px 0 rgba(255,255,255,.9);
    transform: translateY(-2px);
  }
  &.filled {
    cursor: default;
    border-style: solid;
    border-color: $ink;
    background: rgba(238,244,242,.85);
    box-shadow: 0 8px 32px rgba(26,60,52,.12);
    transform: translateY(-2px);
  }
}

.rp-drop-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 36px 32px 28px;
  gap: 10px;
}

.rp-drop-icon-wrap {
  position: relative;
  width: 84px; height: 84px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 6px;
  .rp-drop-main-icon {
    width: 68px;
    height: 68px;
    animation: float-bob 3s ease-in-out infinite;
    filter: drop-shadow(0 4px 10px rgba(26,60,52,0.18));
  }
}

.rp-drop-float {
  position: absolute;
  font-size: 18px;
  color: $ink-pale;
  animation: float-bob 3s ease-in-out infinite;
  &.rp-drop-f1 { top: -6px; right: -10px; animation-delay: 0s; font-size: 14px; }
  &.rp-drop-f2 { bottom: -4px; left: -14px; animation-delay: 1s; font-size: 16px; color: $ink-mid; }
  &.rp-drop-f3 { top: 6px; left: -12px; animation-delay: 2s; font-size: 12px; }
}
@keyframes float-bob {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50%       { transform: translateY(-7px) rotate(5deg); }
}

.rp-drop-title {
  font-size: 15px;
  color: $text;
  font-weight: 500;
  margin: 0;
  .rp-drop-link {
    color: $primary;
    font-weight: 700;
    text-decoration: underline;
    text-decoration-color: rgba(79,70,229,.3);
    text-underline-offset: 3px;
  }
}

.rp-fmts {
  display: flex;
  gap: 7px;
  span {
    padding: 3px 11px;
    background: rgba(26,60,52,.08);
    color: $primary;
    border-radius: 999px;
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: .8px;
    border: 1px solid rgba(26,60,52,.18);
  }
}

.rp-file-preview {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px 24px;
  .rp-file-emoji { font-size: 38px; }
  .rp-file-info { flex: 1;
    .rp-file-name { margin: 0; font-size: 14px; color: $text; font-weight: 600; word-break: break-all; }
    .rp-file-size { margin: 3px 0 0; font-size: 12px; color: $text-muted; }
  }
}

.rp-btn-change {
  padding: 6px 14px;
  background: transparent;
  border: 1.5px solid $ink;
  color: $ink;
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
  font-weight: 600;
  transition: all .2s;
  &:hover { background: $ink; color: #fff; }
}

.rp-err { color: #EF4444; font-size: 13px; margin: -8px 0; text-align: center; }

// 开始按钮 —— 精致发光
.rp-btn-start {
  position: relative;
  width: 100%;
  max-width: 100%;
  padding: 17px 32px;
  background: linear-gradient(135deg, $ink, $ink-mid, $ink-pale);
  background-size: 200% 200%;
  animation: btn-gradient 4s ease infinite;
  color: #fff;
  border: none;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all .25s ease;
  box-shadow: 0 6px 24px rgba(26,60,52,.4), 0 2px 8px rgba(26,60,52,.2);
  letter-spacing: .3px;
  overflow: hidden;

  &:hover:not(:disabled) {
    transform: translateY(-3px);
    box-shadow: 0 12px 36px rgba(26,60,52,.5), 0 4px 12px rgba(26,60,52,.3);
  }
  &:active:not(:disabled) { transform: translateY(-1px); }
  &:disabled {
    background: #C8D8D2;
    box-shadow: none;
    cursor: not-allowed;
    animation: none;
    color: rgba(255,255,255,.7);
    transform: none;
  }
}
@keyframes btn-gradient {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}


.rp-btn-glow {
  position: absolute;
  inset: 0;
  background: linear-gradient(105deg, transparent 40%, rgba(255,255,255,.25) 50%, transparent 60%);
  transform: translateX(-100%);
  transition: none;
}
.rp-btn-start:hover:not(:disabled) .rp-btn-glow {
  animation: btn-sweep .6s ease forwards;
}
@keyframes btn-sweep {
  to { transform: translateX(200%); }
}

.rp-btn-start-inner {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}
.rp-btn-icon { font-size: 20px; }


.rp-proc {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  background: transparent;
}

.rp-proc-card {
  background: $card-bg;
  border-radius: 24px;
  padding: 56px 48px;
  text-align: center;
  box-shadow: $shadow-lg;
  max-width: 540px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 28px;
}


.rp-spinner {
  position: relative;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.rp-ring {
  position: absolute;
  border-radius: 50%;
  border: 3px solid transparent;
  animation: spin 1.5s linear infinite;
}
.rp-ring-1 { inset: 0; border-top-color: $primary; border-right-color: rgba(26,60,52,.3); animation-duration: 1.2s; }
.rp-ring-2 { inset: 14px; border-top-color: $ink-mid; border-right-color: rgba(44,87,73,.3); animation-direction: reverse; animation-duration: 1.8s; }
.rp-ring-3 { inset: 28px; border-top-color: $ink-pale; border-right-color: rgba(74,124,104,.3); animation-duration: 2.4s; }
.rp-ring-core { font-size: 36px; position: relative; z-index: 2; animation: pulse-core 2s ease-in-out infinite; }

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes pulse-core { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.1); } }

.rp-proc-msg { font-size: 17px; font-weight: 600; color: $text; margin: 0; min-height: 24px; }
.rp-elapsed { font-size: 13px; color: $text-muted; margin: -16px 0 0; }

// Steps
.rp-steps {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  gap: 0;
  width: 100%;
}

.rp-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;

  &.done {
    .rp-step-dot { background: #10B981; border-color: #10B981; color: #fff; }
    .rp-step-lbl { color: #10B981; }
    .rp-step-line::after { width: 100%; }
  }
  &.active {
    .rp-step-dot { background: $primary; border-color: $primary; color: #fff; }
    .rp-step-lbl { color: $primary; font-weight: 700; }
  }
  &.pending {
    .rp-step-dot { background: #fff; border-color: $border-std; color: $text-muted; }
    .rp-step-lbl { color: $text-muted; }
  }
}

.rp-step-dot {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 2px solid;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  position: relative;
  z-index: 2;
  transition: all .3s ease;
}

.rp-step-check { font-size: 16px; }

.rp-step-pulse {
  display: block;
  width: 12px;
  height: 12px;
  background: #fff;
  border-radius: 50%;
  animation: pulse-dot 1s ease-in-out infinite;
}
@keyframes pulse-dot { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: .6; transform: scale(.7); } }

.rp-step-lbl { font-size: 11px; margin-top: 8px; transition: all .3s; text-align: center; }

.rp-step-line {
  position: absolute;
  top: 17px;
  left: calc(50% + 18px);
  right: calc(-50% + 18px);
  height: 2px;
  background: $border;
  z-index: 1;
  overflow: hidden;
  &::after {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 0;
    background: #10B981;
    transition: width .5s ease;
  }
}


.rp-pbar-wrap {
  width: 100%;
  height: 8px;
  background: $ink-light;
  border-radius: 999px;
  overflow: hidden;
}

.rp-pbar-fill {
  height: 100%;
  background: linear-gradient(90deg, $primary, $primary-mid);
  border-radius: 999px;
  transition: width .5s ease;
  position: relative;
  overflow: hidden;
}

.rp-pbar-shine {
  position: absolute;
  top: 0; bottom: 0;
  width: 60px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.5), transparent);
  animation: shine 1.5s linear infinite;
}
@keyframes shine { from { left: -60px; } to { left: 100%; } }

.rp-pct { font-size: 24px; font-weight: 800; color: $primary; margin: -8px 0 0; }


.rp-report {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 16px 64px;
}


.rp-topbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(240,253,244,.94);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid $border-std;
  padding: 14px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 0 -16px 24px;
  padding-left: 32px;
  padding-right: 32px;
}

.rp-topbar-l { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.rp-topbar-file { font-size: 14px; font-weight: 600; color: $text; }
.rp-topbar-meta {
  font-size: 12px;
  color: $text-muted;
  background: $primary-light;
  padding: 2px 10px;
  border-radius: 999px;
}

.rp-btn-reset {
  padding: 8px 18px;
  background: transparent;
  border: 1.5px solid $border;
  color: $text-muted;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  font-weight: 500;
  transition: all .2s;
  &:hover { border-color: $primary; color: $primary; }
}

// Card base
.rp-card {
  background: $card-bg;
  border-radius: $radius;
  padding: 28px 28px;
  box-shadow: $shadow;
  margin-bottom: 20px;
  border: 1px solid $border;
}

.rp-card-title {
  font-size: 18px;
  font-family: 'Georgia', 'Noto Serif SC', serif;
  font-weight: 600;
  color: $text;
  margin: 0 0 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid $primary-light;
}

// Overview
.rp-overview {
  display: flex;
  gap: 28px;
  align-items: center;
  background: linear-gradient(135deg, $card-bg 60%, #DCFCE7 100%);
}

.rp-gauge-wrap {
  flex-shrink: 0;
  width: 220px;
  text-align: center;
  .rp-gauge-label { font-size: 13px; color: $text-muted; margin: -8px 0 0; }
}

.rp-overview-info { flex: 1; }

.rp-rating-badge {
  display: inline-block;
  padding: 6px 20px;
  border-radius: 999px;
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 10px;
  &.badge-excellent { background: #D1FAE5; color: #065F46; }
  &.badge-good { background: #DBEAFE; color: #1E40AF; }
  &.badge-avg { background: #FEF3C7; color: #92400E; }
  &.badge-poor { background: #FEE2E2; color: #991B1B; }
}

.rp-score-num {
  font-size: 52px;
  font-weight: 900;
  color: $text;
  margin: 0 0 10px;
  line-height: 1;
  small { font-size: 18px; color: $text-muted; font-weight: 400; }
}

.rp-summary { font-size: 14px; color: $text-muted; line-height: 1.7; margin: 0; }

// Dimensions
.rp-dims {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.rp-radar-cell {
  grid-column: span 2;
  grid-row: span 2;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
  border: 1.5px solid rgba(26, 60, 52, 0.28) !important;
  box-shadow: 0 4px 20px rgba(26, 60, 52, 0.1);

  .rp-radar-cell-label {
    font-size: 13px;
    font-weight: 700;
    color: $primary;
    margin-bottom: 8px;
    letter-spacing: .02em;
  }
}

.rp-dim {
  background: $primary-ghost;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid $border-std;
  transition: box-shadow .2s, border-color .2s, background .2s;
  &:hover { box-shadow: 0 4px 16px rgba(26,60,52,.12); border-color: $border; }
}


.rp-dim-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.rp-dim-icon { font-size: 20px; }
.rp-dim-lbl { flex: 1; font-size: 13px; font-weight: 600; color: $text; }
.rp-dim-score { font-size: 22px; font-weight: 800; }

.rp-dim-bar {
  height: 6px;
  background: $border;
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 8px;
}

.rp-dim-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 1s ease;
}

.rp-dim-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.rp-dim-rating { font-size: 12px; color: $text-muted; }
.rp-dim-weight { font-size: 11px; color: $text-muted; background: $primary-light; padding: 1px 8px; border-radius: 999px; }

.rp-dim-desc {
  margin: 6px 0 0;
  font-size: 11.5px;
  color: $text-muted;
  line-height: 1.55;
}



// Accordion detail section labels
.rp-detail-label {
  font-size: 12px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 6px;
  margin-bottom: 6px;
  display: inline-block;
}

.rp-detail-label--green {
  color: #14532d;
  background: #dcfce7;
}

.rp-detail-label--red {
  color: #7f1d1d;
  background: #fee2e2;
}

.rp-detail-label--blue {
  color: #1e3a8a;
  background: #dbeafe;
}


.rp-sw {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  padding: 0;
  background: none;
  box-shadow: none;
  border: none;
  margin-bottom: 20px;
}

.rp-sw-col {
  background: $card-bg;
  border-radius: $radius;
  padding: 24px;
  border: 1px solid $border;
  box-shadow: $shadow;
  h3 { font-size: 16px; font-weight: 700; color: $text; margin: 0 0 16px; }
  ul { margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 10px; }
  li { font-size: 14px; color: $text-muted; line-height: 1.6; padding-left: 16px; position: relative;
    &::before { content: '•'; position: absolute; left: 0; font-weight: 700; }
  }
}

.rp-strengths { border-top: 3px solid #10B981;
  li::before { color: #10B981; }
}
.rp-weaknesses { border-top: 3px solid #F59E0B;
  li::before { color: #F59E0B; }
}

// Recommendations
.rp-recs { display: flex; flex-direction: column; gap: 14px; }

.rp-rec {
  border-radius: 12px;
  padding: 18px 20px;
  border-left: 4px solid;
  background: $bg;
  &.rp-rec-high { border-color: #EF4444; }
  &.rp-rec-mid { border-color: #F59E0B; }
  &.rp-rec-low { border-color: #10B981; }
}

.rp-rec-hd { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.rp-rec-badge { font-size: 13px; font-weight: 700; }
.rp-rec-cat { font-size: 12px; color: $text-muted; background: $primary-light; padding: 2px 10px; border-radius: 999px; }
.rp-rec-action { font-size: 14px; color: $text; margin: 0 0 8px; }
.rp-rec-eg { font-size: 13px; color: $text-muted; margin: 0 0 6px; background: rgba(0,0,0,.03); padding: 6px 10px; border-radius: 6px; }
.rp-rec-impact { font-size: 13px; color: #065F46; margin: 0; }


.rp-career { display: flex; flex-direction: column; gap: 20px; }
.rp-career-sect h4 { font-size: 14px; font-weight: 700; color: $text; margin: 0 0 10px; }
.rp-pos-tags { display: flex; flex-wrap: wrap; gap: 8px;
  span { padding: 6px 14px; background: $primary-light; color: $primary; border-radius: 999px; font-size: 13px; font-weight: 600; }
}

.rp-tier { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }
.rp-tier-tag {
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  &.rp-t1 { background: #FEE2E2; color: #991B1B; }
  &.rp-t2 { background: #DBEAFE; color: #1E40AF; }
  &.rp-t3 { background: #F3F4F6; color: #374151; }
}
.rp-co { padding: 4px 12px; background: #F1F5F9; color: $text; border-radius: 6px; font-size: 13px; }

.rp-career-plan { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.rp-plan-blk {
  background: $bg;
  border-radius: 10px;
  padding: 16px;
  border: 1px solid $border;
  h4 { font-size: 13px; font-weight: 700; color: $primary; margin: 0 0 8px; }
  p { font-size: 13px; color: $text-muted; margin: 0; line-height: 1.7; }
}


.rp-tips { padding-left: 20px; margin: 0; display: flex; flex-direction: column; gap: 12px;
  li { font-size: 14px; color: $text-muted; line-height: 1.7; }
}

.rp-acc-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  font-size: 14px;
  font-weight: 600;
  color: $text;
  padding-right: 12px;
}
.rp-acc-score { font-size: 13px; font-weight: 700; }

.rp-dim-detail { padding: 4px 0 8px; }
.rp-detail-p { font-size: 14px; color: $text-muted; line-height: 1.7; margin: 0 0 14px; }

.rp-highlights, .rp-issues, .rp-sug {
  margin-bottom: 12px;
  strong { display: block; font-size: 13px; color: $text; margin-bottom: 6px; }
  ul { margin: 0; padding-left: 18px; display: flex; flex-direction: column; gap: 6px; }
  li { font-size: 13px; color: $text-muted; line-height: 1.6; }
}


.rp-json {
  background: #F8FAFC;
  border-radius: 8px;
  padding: 16px;
  font-size: 12px;
  color: #475569;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  line-height: 1.6;
  overflow-x: auto;
  margin: 0;
  max-height: 400px;
  overflow-y: auto;
}


@media (max-width: 640px) {
  .rp-upload { padding: 32px 16px 48px; gap: 20px; }
  .rp-hero h1 { font-size: 26px; }
  .rp-feats { grid-template-columns: 1fr; }
  .rp-proc-card { padding: 36px 20px; }
  .rp-steps { gap: 0; }
  .rp-step-lbl { font-size: 10px; }
  .rp-report { padding: 0 8px 48px; }
  .rp-overview { flex-direction: column; }
  .rp-gauge-wrap { width: 100%; }
  .rp-sw { grid-template-columns: 1fr; }
  .rp-career-plan { grid-template-columns: 1fr; }
  .rp-dims {
    grid-template-columns: 1fr 1fr;
    .rp-radar-cell { grid-column: span 2; grid-row: span 1; }
  }
}

.rp-mode-tabs {
  display: flex;
  flex-direction: row;
  gap: 12px;
  width: 100%;
}

.rp-mode-tab {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 14px;
  border: 2px solid $border-std;
  background: rgba(255,255,255,0.75);
  cursor: pointer;
  transition: all .22s ease;
  text-align: left;
  backdrop-filter: blur(4px);

  &:hover {
    border-color: $primary;
    background: rgba(255,255,255,0.92);
    box-shadow: 0 4px 16px rgba(26,60,52,0.12);
  }
  &.active {
    border-color: $primary;
    background: #fff;
    box-shadow: 0 4px 20px rgba(26,60,52,0.18);
  }
}

.rp-mode-icon { font-size: 20px; flex-shrink: 0; }

.rp-mode-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.rp-mode-title {
  font-size: 14px;
  font-weight: 700;
  color: $text;
  display: block;
}

.rp-mode-desc {
  font-size: 11px;
  color: $text-muted;
  display: block;
  line-height: 1.4;
}

.rp-mode-tab.active .rp-mode-title { color: $primary; }


.rp-jd-section {
  width: 100%;
  max-width: 540px;
  margin-bottom: 20px;
  background: rgba(255,255,255,0.9);
  border: 1.5px solid $border-std;
  border-radius: 14px;
  overflow: hidden;
  backdrop-filter: blur(4px);
  box-shadow: 0 2px 12px rgba(26,60,52,0.05);

  
  &.rp-jd-section--right {
    max-width: 100%;
    width: 100%;
    height: 100%;
    margin-bottom: 0;
    display: flex;
    flex-direction: column;

    .rp-jd-textarea--full {
      flex: 1;
      resize: none;
      height: 100%;
      min-height: 300px;
    }
  }
}

.rp-jd-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: $primary-ghost;
  border-bottom: 1px solid $border-std;
}

.rp-jd-icon { font-size: 20px; }

.rp-jd-title {
  font-size: 13px;
  font-weight: 700;
  color: $text;
  margin: 0;
}

.rp-jd-hint {
  font-size: 11px;
  color: $text-muted;
  margin: 2px 0 0;
}

.rp-jd-textarea {
  width: 100%;
  padding: 12px 16px;
  font-size: 13px;
  color: $text;
  border: none;
  outline: none;
  resize: vertical;
  background: transparent;
  font-family: inherit;
  line-height: 1.6;
  box-sizing: border-box;

  &::placeholder { color: #94A8A0; }
  &:focus { background: rgba(26,60,52,0.02); }
}

.rp-jd-count {
  padding: 4px 16px 8px;
  font-size: 11px;
  color: $text-muted;
  text-align: right;
}


.rp-jdm-overview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px;
  background: $primary-ghost;
  border-radius: 12px;
  margin-bottom: 24px;
  text-align: center;
}

.rp-jdm-badge {
  padding: 5px 20px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 700;
  &.jdm-high  { background: #f0fdf4; color: #16a34a; border: 1.5px solid #bbf7d0; }
  &.jdm-mid   { background: #fffbeb; color: #d97706; border: 1.5px solid #fde68a; }
  &.jdm-low   { background: #fff1f2; color: #e11d48; border: 1.5px solid #fecdd3; }
}

.rp-jdm-pct {
  font-size: 48px;
  font-weight: 800;
  color: $text;
  line-height: 1;
  small { font-size: 20px; color: $text-muted; font-weight: 400; }
}

.rp-jdm-summary {
  font-size: 14px;
  color: $text-muted;
  line-height: 1.7;
  max-width: 600px;
  margin: 0;
}

.rp-jdm-section {
  margin-bottom: 24px;
}

.rp-jdm-subtitle {
  font-size: 15px;
  font-weight: 700;
  color: $text;
  margin: 0 0 14px;
  padding-bottom: 8px;
  border-bottom: 2px solid $primary-light;
}


.rp-req-item {
  padding: 14px 16px;
  border-radius: 10px;
  margin-bottom: 10px;
  border-left: 4px solid transparent;

  &.req-high     { background: #f0fdf4; border-color: #22c55e; }
  &.req-potential { background: #fffbeb; border-color: #f59e0b; }
  &.req-gap      { background: #fff1f2; border-color: #ef4444; }
}

.rp-req-hd {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.rp-req-badge {
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;

  &.badge-high     { background: #dcfce7; color: #16a34a; }
  &.badge-potential { background: #fef3c7; color: #d97706; }
  &.badge-gap      { background: #fee2e2; color: #dc2626; }
}

.rp-req-text {
  font-size: 13px;
  font-weight: 600;
  color: $text;
}

.rp-req-evidence {
  font-size: 12px;
  color: $text-muted;
  margin: 0 0 6px;
  line-height: 1.6;
}

.rp-req-suggest {
  font-size: 12px;
  color: #0D9488;
  background: #F0FDFA;
  border-radius: 6px;
  padding: 6px 10px;
  margin: 0;
  line-height: 1.6;
}

.rp-jdm-passrate {
  font-size: 14px;
  color: $text-muted;
  margin-bottom: 12px;
}

.rp-jdm-rate {
  font-weight: 700;
  padding: 2px 12px;
  border-radius: 10px;
  &.rate-high { background: #f0fdf4; color: #16a34a; }
  &.rate-mid  { background: #fffbeb; color: #d97706; }
  &.rate-low  { background: #fff1f2; color: #e11d48; }
}

.rp-jdm-questions, .rp-jdm-redflags {
  margin-bottom: 14px;
  ol, ul { margin: 6px 0 0; padding-left: 20px; }
  li { font-size: 13px; color: $text-muted; line-height: 1.7; }
}

.rp-jdm-q-title {
  font-size: 13px;
  font-weight: 600;
  color: $text;
  margin: 0;
}

.rp-jdm-redflags li { color: #dc2626; }


.rp-jdm-verdict {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%);
  border: 1.5px solid #BBF7D0;
  border-radius: 12px;
  padding: 16px 18px;
  margin-top: 20px;

  p {
    font-size: 14px;
    font-weight: 600;
    color: $text;
    line-height: 1.7;
    margin: 0;
  }
}

.rp-jdm-verdict-icon { font-size: 24px; flex-shrink: 0; }


.jd-slide-enter-active { transition: opacity .25s ease; }
.jd-slide-leave-active { transition: opacity .2s ease; }
.jd-slide-enter-from,
.jd-slide-leave-to { opacity: 0; }
</style>
