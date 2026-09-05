<template>
  <div class="iv-wrap">
    <PageGreeting v-if="phase === 'setup'" tip="准备好迎接面试挑战了吗？模拟练习，胸有成竹！" />

    <div v-if="phase === 'setup'" class="iv-setup">
      <div class="iv-style-grid">
        <div v-for="(cfg, key) in styles" :key="key" class="iv-style-card" :class="{ active: selectedStyle === key }"
          @click="selectedStyle = key">
          <div class="iv-style-icon">{{ cfg.icon }}</div>
          <div class="iv-style-name">{{ cfg.name }}</div>
          <div class="iv-style-desc">{{ cfg.desc }}</div>
          <div v-if="selectedStyle === key" class="iv-style-check">✓</div>
        </div>
      </div>

      <div class="iv-setup-cols">
        <div class="iv-col-card iv-col-resume" :class="{ 'is-error': showErrors && !resumeFile }">
          <div class="iv-col-label">上传简历 <span class="iv-required">*</span></div>
          <div class="iv-upload-zone" :class="{ 'has-file': resumeFile, dragging: isDragging }"
            @dragover.prevent="isDragging = true" @dragleave="isDragging = false" @drop.prevent="onDrop"
            @click="fileInput?.click()">
            <input ref="fileInput" type="file" accept=".pdf,.docx,.txt" style="display: none" @change="onFileChange" />
            <template v-if="!resumeFile">
              <div class="iv-upload-icon">📎</div>
              <div>点击或拖拽上传</div>
              <div style="font-size:11px;margin-top:2px">PDF / DOCX / TXT</div>
            </template>
            <template v-else>
              <div class="iv-upload-icon">✅</div>
              <div class="iv-upload-name">{{ resumeFile.name }}</div>
              <el-button size="small" type="danger" text @click.stop="resumeFile = null"
                style="margin-top:6px">移除</el-button>
            </template>
          </div>
        </div>

        <div class="iv-col-card iv-col-job" :class="{ 'is-error': showErrors && !selectedJob }">
          <div class="iv-col-label">应聘岗位 <span class="iv-required">*</span></div>
          <div class="iv-job-selector">
            <div class="iv-job-search-wrap">
              <input v-model="jobSearchText" class="iv-job-input" :placeholder="selectedJob ? '' : '输入岗位名称搜索…'"
                @input="onJobSearch" @focus="showJobDropdown = true" @blur="onJobInputBlur" />
              <div v-if="selectedJob" class="iv-job-selected-tag" @click="clearSelectedJob">
                <span>{{ selectedJob.job_name }}</span>
                <span class="iv-job-tag-company">· {{ selectedJob.company_name }}</span>
                <span class="iv-job-tag-city">{{ selectedJob.work_city }}</span>
                <span class="iv-job-tag-remove">✕</span>
              </div>
            </div>
            <div v-if="showJobDropdown && (jobSearchResults.length > 0 || jobSearching)" class="iv-job-dropdown">
              <div v-if="jobSearching" class="iv-job-searching">搜索中…</div>
              <template v-else>
                <div class="iv-job-dropdown-count">共 {{ jobSearchTotal }} 个，已显示 {{ jobSearchResults.length }} 个</div>
                <div v-for="job in jobSearchResults" :key="job.id" class="iv-job-item"
                  @mousedown.prevent="selectJob(job)">
                  <div class="iv-job-item-name">{{ job.job_name }}</div>
                  <div class="iv-job-item-meta">
                    <span class="iv-job-item-company">{{ job.company_name }}</span>
                    <span class="iv-job-item-city">📍 {{ job.work_city }}</span>
                    <span v-if="job.job_salary" class="iv-job-item-salary">{{ job.job_salary }}</span>
                  </div>
                  <div v-if="job.jd_preview" class="iv-job-item-preview">{{ job.jd_preview.slice(0, 60) }}…</div>
                </div>
                <div v-if="jobSearchOffset < jobSearchTotal" class="iv-job-load-more" @mousedown.prevent="loadMoreJobs">
                  {{ jobSearchLoadingMore ? '加载中…' : `加载更多（还有 ${jobSearchTotal - jobSearchOffset} 个）` }}</div>
              </template>
            </div>
          </div>
          <div v-if="selectedJob" class="iv-job-preview-card">
            <div class="iv-job-preview-name">{{ selectedJob.job_name }}</div>
            <div class="iv-job-preview-meta">
              <span>{{ selectedJob.company_name }}</span>
              <span>📍 {{ selectedJob.work_city }}</span>
              <span v-if="selectedJob.job_salary" style="color:var(--gold)">{{ selectedJob.job_salary }}</span>
            </div>
            <div v-if="fullJobDetail?.job_summary || selectedJob.jd_preview" class="iv-job-preview-jd">
              {{ fullJobDetail?.job_summary || selectedJob.jd_preview }}
            </div>
          </div>
        </div>
      </div>

      <div v-if="showErrors" class="iv-validation-tip">
        <span v-if="!resumeFile">⚠️ 请先上传简历</span>
        <span v-if="!selectedJob"> ⚠️ 请选择应聘岗位</span>
      </div>

      <div class="iv-kb-section">
        <div class="iv-kb-bar" @click="kbExpanded = !kbExpanded">
          <span class="iv-kb-dot" :class="kbStats.count > 0 ? 'ready' : 'empty'" />
          <span v-if="kbStats.count > 0" class="iv-kb-bar-text">
            面经知识库已就绪（{{ kbStats.count }} 个知识片段）— RAG 增强已开启
          </span>
          <span v-else class="iv-kb-bar-text">面经知识库为空 — 点击上传面经文档以增强回答质量</span>
          <el-icon class="iv-kb-arrow" :class="{ expanded: kbExpanded }">
            <ArrowDown />
          </el-icon>
        </div>
        <div v-if="kbExpanded" class="iv-kb-expand">
          <div class="iv-kb-expand-upload">
            <el-upload drag :auto-upload="false" :on-change="onKbFileChange" :show-file-list="true" multiple
              accept=".pdf,.docx,.txt" class="iv-kb-upload-area">
              <el-icon class="el-icon--upload" style="font-size:22px;color:var(--p-mid)">
                <UploadFilled />
              </el-icon>
              <div class="el-upload__text" style="font-size:12px">拖拽面经文件，或 <em>点击选择</em>（PDF/DOCX/TXT）</div>
            </el-upload>
            <div class="iv-kb-expand-footer">
              <div style="display:flex;gap:8px;align-items:center">
                <el-button size="small" text @click.stop="loadKbStats(); loadKbSegments()">刷新</el-button>
                <el-button size="small" type="primary" :loading="kbUploading" :disabled="kbFiles.length === 0"
                  @click.stop="uploadKbFiles">上传入库（{{ kbFiles.length }} 个）</el-button>
                <el-button v-if="kbStats.count > 0" size="small" type="danger" plain
                  @click.stop="clearKb">清空知识库</el-button>
              </div>
            </div>
            <div v-if="kbUploadResult" class="iv-kb-upload-result">{{ kbUploadResult }}</div>
          </div>

          <div v-if="kbStats.count > 0" class="iv-kb-segments">
            <div class="iv-kb-segments-header">
              <span>已入库片段（共 {{ kbStats.count }} 个）</span>
              <span v-if="kbSegmentsLoading" style="font-size:11px;color:#aaa">加载中…</span>
            </div>
            <div v-if="kbSegments.length" class="iv-kb-seg-list">
              <div v-for="seg in kbSegments" :key="seg.id" class="iv-kb-seg-item">
                <div class="iv-kb-seg-source">📄 {{ seg.source }}</div>
                <div class="iv-kb-seg-preview">{{ seg.preview }}</div>
              </div>
              <div v-if="kbSegmentOffset < kbStats.count" class="iv-kb-seg-more" @click.stop="loadMoreSegments">{{
                kbSegmentsLoading ? '加载中…' : `加载更多（还有 ${kbStats.count - kbSegmentOffset} 个）` }}</div>
            </div>
            <div v-else-if="!kbSegmentsLoading" style="font-size:12px;color:#bbb;padding:8px 0">点击刷新加载片段</div>
          </div>
        </div>
      </div>

      <el-button type="primary" size="large" class="iv-start-btn" :loading="starting" @click="startInterview">
        开始面试
      </el-button>
    </div>

    <div v-else-if="phase === 'chat'" class="iv-chat-wrap">
      <div class="iv-chat-header">
        <div class="iv-chat-title">
          <span class="iv-chat-style-badge">{{ currentStyleCfg?.icon }} {{ currentStyleCfg?.name }}</span>
          <span v-if="selectedJob" class="iv-chat-job">· {{ selectedJob.job_name }} @ {{ selectedJob.company_name
            }}</span>
        </div>
        <div class="iv-chat-meta">
          <span>第 {{ turnCount }} 轮</span>
          <span>{{ elapsedText }}</span>
        </div>
        <el-button type="danger" size="small" plain @click="confirmFinish">结束面试</el-button>
      </div>

      <div ref="msgList" class="iv-msg-list">
        <div v-for="(msg, idx) in messages" :key="idx" class="iv-msg-row" :class="msg.role">
          <div class="iv-msg-avatar">
            {{ msg.role === 'assistant' ? '🧑‍💼' : '👤' }}
          </div>
          <div class="iv-msg-bubble" v-html="renderMd(msg.content)" />
        </div>

        <div v-if="streaming" class="iv-msg-row assistant">
          <div class="iv-msg-avatar">🧑‍💼</div>
          <div class="iv-msg-bubble iv-streaming"
            v-html="renderMd(streamingText) + '<span class=\'cursor\'>|</span>'" />
        </div>
      </div>

      <div class="iv-input-area">
        <el-input v-model="userInput" type="textarea" :rows="3" placeholder="输入你的回答，或点击麦克风语音作答…" :disabled="streaming"
          resize="none" @keydown.enter.ctrl="sendMessage" />
        <div class="iv-input-actions">
          <span class="iv-input-tip">Ctrl+Enter 发送</span>
          <div class="iv-input-btns">
            <el-button :type="isRecording ? 'danger' : 'default'" circle :title="isRecording ? '点击停止录音' : '语音输入'"
              @click="toggleVoice" :class="{ 'iv-recording': isRecording }">
              <span style="font-size: 16px">{{ isRecording ? '⏹️' : '🎤' }}</span>
            </el-button>

            <el-button type="primary" :disabled="!userInput.trim() || streaming" :loading="streaming"
              @click="sendMessage">
              发送
            </el-button>
          </div>
        </div>
        <div v-if="isRecording" class="iv-voice-hint">
          <span class="iv-voice-dot" />正在录音，请说话… 再次点击停止
        </div>
        <div v-if="voiceError" class="iv-voice-error">{{ voiceError }}</div>
      </div>
    </div>

    <div v-else-if="phase === 'summary'" class="iv-summary-wrap">
      <div class="iv-summary-header">
        <div class="iv-summary-icon">📊</div>
        <h2>面试总结报告</h2>
        <div class="iv-summary-meta">
          {{ currentStyleCfg?.name }} · 共 {{ turnCount }} 轮 · 用时 {{ elapsedText }}
        </div>
      </div>

      <el-card class="iv-summary-card">
        <div v-if="summaryStreaming || summaryText" class="iv-summary-content"
          v-html="renderMd(summaryText) + (summaryStreaming ? '<span class=\'cursor\'>|</span>' : '')" />
        <div v-else class="iv-summary-loading">
          <el-icon class="is-loading">
            <Loading />
          </el-icon> 正在生成面试报告…
        </div>
      </el-card>

      <div class="iv-summary-actions">
        <el-button @click="reviewHistory">查看完整对话记录</el-button>
        <el-button type="primary" @click="restartInterview">再来一次</el-button>
      </div>
    </div>

    <el-dialog v-model="showKbUpload" title="面经知识库管理" width="480px">
      <div class="iv-kb-dialog">
        <p style="color: #666; margin-bottom: 16px; font-size: 13px">
          上传面经/攻略文档（PDF/DOCX/TXT），AI 面试官将参考这些资料生成更贴近真实的问题。
        </p>
        <el-upload drag :auto-upload="false" :on-change="onKbFileChange" :show-file-list="true" multiple
          accept=".pdf,.docx,.txt">
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">拖拽文件到此处，或 <em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip">支持 PDF、DOCX、TXT，每次上传后自动入库</div>
          </template>
        </el-upload>
        <div style="margin-top: 16px">
          <el-button type="primary" :loading="kbUploading" :disabled="kbFiles.length === 0" @click="uploadKbFiles">
            上传入库（{{ kbFiles.length }} 个文件）
          </el-button>
          <span v-if="kbUploadResult" style="margin-left: 12px; color: #67c23a; font-size: 13px">
            {{ kbUploadResult }}
          </span>
        </div>
        <el-divider />
        <div style="font-size: 13px; color: #666">
          当前知识库：<strong>{{ kbStats.count }}</strong> 个片段
          <el-button size="small" text type="primary" @click="loadKbStats" style="margin-left: 8px">刷新</el-button>
        </div>
      </div>
    </el-dialog>

    <el-drawer v-model="showHistory" title="完整对话记录" size="540px" direction="rtl">
      <div class="iv-history-drawer">
        <div v-for="(msg, idx) in messages" :key="idx" class="iv-history-item" :class="msg.role">
          <div class="iv-history-role">{{ msg.role === 'assistant' ? '🧑‍💼 面试官' : '👤 你' }}</div>
          <div class="iv-history-text" v-html="renderMd(msg.content)" />
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageGreeting from '@/components/PageGreeting.vue'
import { Loading, ArrowDown, UploadFilled } from '@element-plus/icons-vue'
import { useAuth } from '@/composables/useAuth'

const BASE = 'http://localhost:8000'

useAuth()

function getToken() {
  return localStorage.getItem('token') || ''
}

function authHeaders() {
  return { Authorization: `Bearer ${getToken()}` }
}

interface JobResult {
  id: number
  job_name: string
  company_name: string
  work_city: string
  job_salary: string
  jd_preview: string
}

const phase = ref<'setup' | 'chat' | 'summary'>('setup')
const selectedStyle = ref('technical')
const resumeFile = ref<File | null>(null)
const isDragging = ref(false)
const starting = ref(false)
const showErrors = ref(false)

const jobSearchText = ref('')
const jobSearchResults = ref<JobResult[]>([])
const selectedJob = ref<JobResult | null>(null)
const showJobDropdown = ref(false)
const jobSearching = ref(false)
const jobSearchLoadingMore = ref(false)
const jobSearchTotal = ref(0)
const jobSearchOffset = ref(0)
const JOB_SEARCH_PAGE = 50
let jobSearchTimer: ReturnType<typeof setTimeout> | null = null
let lastSearchKeyword = ''

const sessionId = ref('')
const messages = ref<{ role: string; content: string }[]>([])
const userInput = ref('')
const streaming = ref(false)
const streamingText = ref('')
const turnCount = ref(0)

const summaryStreaming = ref(false)
const summaryText = ref('')
const showHistory = ref(false)

const isRecording = ref(false)
const voiceError = ref('')
let recognition: any = null

const showKbUpload = ref(false)
const kbExpanded = ref(false)
const kbSegments = ref<{ id: string; source: string; preview: string }[]>([])
const kbSegmentsLoading = ref(false)
const kbSegmentOffset = ref(0)
const KB_SEG_PAGE = 20
const kbFiles = ref<File[]>([])
const kbUploading = ref(false)
const kbUploadResult = ref('')
const kbStats = ref({ count: 0, ready: false })
const fullJobDetail = ref<any>(null)

const styles = ref<Record<string, { name: string; icon: string; desc: string }>>({})
const msgList = ref<HTMLElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

const startTime = ref(0)
const elapsed = ref(0)
let timerInterval: ReturnType<typeof setInterval> | null = null

const elapsedText = computed(() => {
  const m = Math.floor(elapsed.value / 60)
  const s = elapsed.value % 60
  return `${m}:${String(s).padStart(2, '0')}`
})

const currentStyleCfg = computed(() => styles.value[selectedStyle.value])

onMounted(async () => {
  await Promise.all([loadStyles(), loadKbStats()])
  watch(kbExpanded, (val) => { if (val && kbSegments.value.length === 0) loadKbSegments() })
})

onUnmounted(() => {
  stopTimer()
  stopVoice()
})

async function loadStyles() {
  try {
    const res = await fetch(`${BASE}/api/interview/styles`)
    if (res.ok) styles.value = await res.json()
  } catch { }
}

async function loadKbStats() {
  try {
    const res = await fetch(`${BASE}/api/interview/kb/stats`, { headers: authHeaders() })
    if (res.ok) kbStats.value = await res.json()
  } catch { }
}

async function loadKbSegments() {
  kbSegmentsLoading.value = true
  kbSegments.value = []
  kbSegmentOffset.value = 0
  try {
    const res = await fetch(
      `${BASE}/api/interview/kb/segments?limit=${KB_SEG_PAGE}&offset=0`,
      { headers: authHeaders() }
    )
    if (res.ok) {
      const data = await res.json()
      kbSegments.value = data.segments ?? []
      kbSegmentOffset.value = (data.segments ?? []).length
    }
  } catch { }
  kbSegmentsLoading.value = false
}

async function loadMoreSegments() {
  if (kbSegmentsLoading.value) return
  kbSegmentsLoading.value = true
  try {
    const res = await fetch(
      `${BASE}/api/interview/kb/segments?limit=${KB_SEG_PAGE}&offset=${kbSegmentOffset.value}`,
      { headers: authHeaders() }
    )
    if (res.ok) {
      const data = await res.json()
      kbSegments.value = [...kbSegments.value, ...(data.segments ?? [])]
      kbSegmentOffset.value += (data.segments ?? []).length
    }
  } catch { }
  kbSegmentsLoading.value = false
}

async function clearKb() {
  try {
    await ElMessageBox.confirm('确认清空全部面经知识库？此操作不可恢复。', '清空确认', {
      type: 'warning', confirmButtonText: '确认清空', cancelButtonText: '取消'
    })
  } catch { return }
  try {
    const res = await fetch(`${BASE}/api/interview/kb/clear`, {
      method: 'DELETE', headers: authHeaders()
    })
    if (res.ok) {
      ElMessage.success('知识库已清空')
      await loadKbStats()
      kbSegments.value = []
      kbSegmentOffset.value = 0
    }
  } catch { ElMessage.error('清空失败') }
}

function onJobSearch() {
  if (selectedJob.value) return
  if (jobSearchTimer) clearTimeout(jobSearchTimer)
  const q = jobSearchText.value.trim()
  if (!q) {
    jobSearchResults.value = []
    jobSearchTotal.value = 0
    return
  }
  jobSearchTimer = setTimeout(() => doJobSearch(q), 300)
}

async function doJobSearch(keyword: string) {
  lastSearchKeyword = keyword
  jobSearchOffset.value = 0
  jobSearchResults.value = []
  jobSearchTotal.value = 0
  jobSearching.value = true
  try {
    const res = await fetch(
      `${BASE}/api/matching/jobs/search?keyword=${encodeURIComponent(keyword)}&limit=${JOB_SEARCH_PAGE}&offset=0`
    )
    if (res.ok) {
      const data = await res.json()
      jobSearchResults.value = data.jobs ?? data
      jobSearchTotal.value = data.total ?? (data.jobs ?? data).length
      jobSearchOffset.value = (data.jobs ?? data).length
    }
  } catch { }
  jobSearching.value = false
}

async function loadMoreJobs() {
  if (jobSearchLoadingMore.value) return
  jobSearchLoadingMore.value = true
  try {
    const res = await fetch(
      `${BASE}/api/matching/jobs/search?keyword=${encodeURIComponent(lastSearchKeyword)}&limit=${JOB_SEARCH_PAGE}&offset=${jobSearchOffset.value}`
    )
    if (res.ok) {
      const data = await res.json()
      const newJobs = data.jobs ?? []
      jobSearchResults.value = [...jobSearchResults.value, ...newJobs]
      jobSearchOffset.value += newJobs.length
    }
  } catch { }
  jobSearchLoadingMore.value = false
}

async function selectJob(job: JobResult) {
  selectedJob.value = job
  jobSearchText.value = ''
  jobSearchResults.value = []
  jobSearchTotal.value = 0
  showJobDropdown.value = false
  fullJobDetail.value = null
  try {
    const res = await fetch(`${BASE}/api/matching/jobs/${job.id}`)
    if (res.ok) fullJobDetail.value = await res.json()
  } catch { }
}

function clearSelectedJob() {
  selectedJob.value = null
  fullJobDetail.value = null
  jobSearchText.value = ''
  jobSearchResults.value = []
  jobSearchTotal.value = 0
}

function onJobInputBlur() {
  setTimeout(() => { showJobDropdown.value = false }, 200)
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.[0]) resumeFile.value = input.files[0]
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) resumeFile.value = file
}

async function startInterview() {
  showErrors.value = false

  if (!resumeFile.value || !selectedJob.value) {
    showErrors.value = true
    ElMessage.warning('请上传简历并选择应聘岗位')
    return
  }

  starting.value = true
  messages.value = []
  streamingText.value = ''
  turnCount.value = 0
  summaryText.value = ''

  const form = new FormData()
  form.append('file', resumeFile.value)

  const params = new URLSearchParams({
    style: selectedStyle.value,
    job_name: selectedJob.value.job_name,
    job_id: String(selectedJob.value.id),
  })

  try {
    const res = await fetch(`${BASE}/api/interview/session/start?${params}`, {
      method: 'POST',
      headers: authHeaders(),
      body: form,
    })

    if (!res.ok) throw new Error('启动失败')

    phase.value = 'chat'
    startTimer()
    starting.value = false
    streaming.value = true

    await readSSE(res, (event) => {
      if (event.type === 'session') {
        sessionId.value = event.session_id
      } else if (event.type === 'token') {
        streamingText.value += event.text
        scrollToBottom()
      } else if (event.type === 'done') {
        messages.value.push({ role: 'assistant', content: streamingText.value })
        streamingText.value = ''
        streaming.value = false
      } else if (event.type === 'error') {
        streaming.value = false
        ElMessage.error('开场白生成失败：' + (event.message || '未知错误'))
      }
    })
    streaming.value = false
    scrollToBottom()
  } catch (e: any) {
    starting.value = false
    ElMessage.error(e.message || '启动面试失败，请检查后端服务')
  }
}

async function sendMessage() {
  const msg = userInput.value.trim()
  if (!msg || streaming.value) return

  messages.value.push({ role: 'user', content: msg })
  userInput.value = ''
  streaming.value = true
  streamingText.value = ''
  scrollToBottom()

  try {
    const res = await fetch(`${BASE}/api/interview/session/${sessionId.value}/chat`, {
      method: 'POST',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg }),
    })

    if (!res.ok) throw new Error('请求失败')

    await readSSE(res, (event) => {
      if (event.type === 'token') {
        streamingText.value += event.text
        scrollToBottom()
      } else if (event.type === 'done') {
        messages.value.push({ role: 'assistant', content: streamingText.value })
        streamingText.value = ''
        turnCount.value = event.turn ?? turnCount.value + 1
        streaming.value = false
        scrollToBottom()
      } else if (event.type === 'error') {
        throw new Error(event.message)
      }
    })
  } catch (e: any) {
    streaming.value = false
    streamingText.value = ''
    ElMessage.error(e.message || '发送失败')
  } finally {
    streaming.value = false
  }
}

async function confirmFinish() {
  try {
    await ElMessageBox.confirm('确定结束面试并生成评估报告吗？', '结束面试', {
      confirmButtonText: '结束并生成报告',
      cancelButtonText: '继续面试',
      type: 'warning',
    })
    await finishInterview()
  } catch { }
}

async function finishInterview() {
  stopTimer()
  phase.value = 'summary'
  summaryStreaming.value = true
  summaryText.value = ''

  try {
    const res = await fetch(`${BASE}/api/interview/session/${sessionId.value}/finish`, {
      method: 'POST',
      headers: authHeaders(),
    })

    if (!res.ok) throw new Error('生成报告失败')

    await readSSE(res, (event) => {
      if (event.type === 'token') {
        summaryText.value += event.text
      } else if (event.type === 'done') {
        summaryStreaming.value = false
      } else if (event.type === 'error') {
        throw new Error(event.message)
      }
    })
  } catch (e: any) {
    summaryStreaming.value = false
    ElMessage.error(e.message || '生成报告失败')
  }
}

function reviewHistory() {
  showHistory.value = true
}

function restartInterview() {
  phase.value = 'setup'
  sessionId.value = ''
  messages.value = []
  turnCount.value = 0
  summaryText.value = ''
  elapsed.value = 0
  showErrors.value = false
}

async function readSSE(res: Response, handler: (event: any) => void) {
  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buf = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    const lines = buf.split('\n')
    buf = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const raw = line.slice(6).trim()
        if (raw === '[DONE]') return
        try {
          const parsed = JSON.parse(raw)
          handler(parsed)
        } catch (e) {
          if (e instanceof SyntaxError) continue
          throw e
        }
      }
    }
  }
}

function toggleVoice() {
  if (isRecording.value) {
    stopVoice()
  } else {
    startVoice()
  }
}

function startVoice() {
  voiceError.value = ''
  const SpeechRecognition =
    (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  if (!SpeechRecognition) {
    voiceError.value = '当前浏览器不支持语音识别，请使用 Chrome 或 Edge'
    return
  }

  recognition = new SpeechRecognition()
  recognition.lang = 'zh-CN'
  recognition.continuous = true
  recognition.interimResults = true

  recognition.onstart = () => {
    isRecording.value = true
  }

  recognition.onresult = (e: any) => {
    let final = ''
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) final += e.results[i][0].transcript
    }
    if (final) userInput.value += final
  }

  recognition.onerror = (e: any) => {
    isRecording.value = false
    if (e.error !== 'aborted') {
      voiceError.value = `语音识别错误: ${e.error}`
    }
  }

  recognition.onend = () => {
    isRecording.value = false
  }

  recognition.start()
}

function stopVoice() {
  if (recognition) {
    recognition.stop()
    recognition = null
  }
  isRecording.value = false
}

function onKbFileChange(file: any) {
  kbFiles.value.push(file.raw)
}

async function uploadKbFiles() {
  if (kbFiles.value.length === 0) return
  kbUploading.value = true
  kbUploadResult.value = ''
  let totalChunks = 0

  for (const file of kbFiles.value) {
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch(`${BASE}/api/interview/kb/ingest`, {
        method: 'POST',
        headers: authHeaders(),
        body: form,
      })
      const data = await res.json()
      totalChunks += data.chunks || 0
    } catch { }
  }

  kbUploading.value = false
  kbFiles.value = []
  kbUploadResult.value = `成功入库 ${totalChunks} 个片段`
  await loadKbStats()
}

function scrollToBottom() {
  nextTick(() => {
    if (msgList.value) {
      msgList.value.scrollTop = msgList.value.scrollHeight
    }
  })
}

function startTimer() {
  startTime.value = Date.now()
  elapsed.value = 0
  timerInterval = setInterval(() => {
    elapsed.value = Math.floor((Date.now() - startTime.value) / 1000)
  }, 1000)
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

function renderMd(text: string): string {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^#{1,3}\s(.+)$/gm, '<strong>$1</strong>')
    .replace(/^[-•]\s(.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
    .replace(/\n/g, '<br>')
}
</script>

<style scoped>
.iv-wrap {
  --p-deep: #3D1F6B;
  --p-main: #6B3FA0;
  --p-mid: #9B7BB8;
  --p-light: #C8ADE0;
  --p-pale: #EDE3F5;
  --p-ghost: #F8F4FC;
  --p-wash: #FBF9FE;
  --gold: #A0783A;
  --gold-lt: #C9A45C;
  --text-dk: #1C0E35;
  --text-md: #4A3068;
  --text-lt: #8A6FAB;
  --border: #D4BEE8;
  --border-lt: #E8DAF5;
  --warn: #C0392B;
  --ok: #5A7A52;
}

.iv-wrap {
  height: 100%;
  background: transparent;
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  overflow-y: auto;
}

/* ── 设置阶段 ─────────────────────────────────────────────────── */
.iv-setup {
  max-width: 860px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  flex-direction: column;
}


.iv-style-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 16px;
  flex-shrink: 0;
}
.iv-style-card {
  position: relative;
  background: var(--p-wash);
  border: 1.5px solid var(--border-lt);
  border-radius: 8px;
  padding: 12px 10px 10px;
  cursor: pointer;
  text-align: center;
  transition: all .22s;
}
.iv-style-card:hover {
  border-color: var(--p-mid);
  background: var(--p-ghost);
  box-shadow: 0 2px 10px rgba(107, 63, 160, .12);
}
.iv-style-card.active {
  border-color: var(--p-main);
  background: var(--p-pale);
  box-shadow: 0 2px 12px rgba(61, 31, 107, .14);
}

.iv-style-icon {
  font-size: 22px;
  margin-bottom: 5px;
  line-height: 1;
}
.iv-style-name { font-size: 13px; font-weight: 600; color: var(--text-dk); margin-bottom: 3px; }
.iv-style-desc { font-size: 11px; color: var(--text-lt); line-height: 1.4; }
.iv-style-check {
  position: absolute;
  top: 6px; right: 8px;
  color: var(--p-main); font-weight: bold; font-size: 12px;
}

/* 必填标记 */
.iv-required { color: var(--warn); margin-left: 2px; }

/* 两栏并排布局 */
.iv-setup-cols {
  display: flex;
  gap: 14px;
  margin-bottom: 12px;
}

/* 单栏卡片 */
.iv-col-card {
  flex: 1;
  background: var(--p-wash);
  border: 1px solid var(--border-lt);
  border-radius: 10px;
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: border-color .2s;
}
.iv-col-card.is-error {
  border-color: var(--warn);
  background: #fff9f9;
}

.iv-col-label {
  font-size: 13px; font-weight: 600; color: var(--text-md); flex-shrink: 0;
}

/* 简历卡：上传区固定最小高度 */
.iv-col-resume .iv-upload-zone { min-height: 130px; }

/* 岗位卡 */
.iv-col-job { overflow: hidden; }

/* 上传区 */
.iv-upload-zone {
  border: 1.5px dashed var(--border);
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  color: var(--text-lt);
  font-size: 13px;
  transition: all .22s;
  min-height: 100px;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px;
  background: var(--p-ghost);
}
.iv-upload-zone:hover, .iv-upload-zone.dragging {
  border-color: var(--p-main);
  color: var(--p-main);
  background: var(--p-pale);
}
.iv-upload-zone.has-file {
  border-color: var(--ok);
  background: #f2f7f1;
  color: var(--ok);
}

/* 上传图标：直接展示 emoji，加淡紫背景 */
.iv-upload-icon {
  font-size: 28px;
  line-height: 1;
}
.iv-upload-name { font-weight: 600; font-size: 13px; }

/* 已选岗位预览卡 */
.iv-job-preview-card {
  background: var(--p-pale);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  flex-shrink: 0;
}
.iv-job-preview-name { font-size: 14px; font-weight: 700; color: var(--text-dk); margin-bottom: 5px; }
.iv-job-preview-meta { display: flex; gap: 10px; font-size: 12px; color: var(--text-lt); margin-bottom: 5px; flex-wrap: wrap; }
.iv-job-preview-jd {
  font-size: 12px;
  color: var(--text-md);
  line-height: 1.65;
  max-height: 220px;
  overflow-y: auto;
  white-space: pre-line;
  border-top: 1px solid var(--border-lt);
  padding-top: 8px;
  margin-top: 2px;
}

/* 岗位搜索选择器 */
.iv-job-selector { flex-shrink: 0; }

.iv-job-search-wrap {
  position: relative;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 6px 10px;
  min-height: 40px;
  display: flex; align-items: center;
  flex-wrap: wrap; gap: 6px;
  cursor: text;
  transition: border-color .2s;
  background: var(--p-wash);
}
.iv-job-search-wrap:focus-within {
  border-color: var(--p-main);
  box-shadow: 0 0 0 2px rgba(107, 63, 160, .12);
}

.iv-job-input {
  border: none; outline: none;
  font-size: 13px; flex: 1;
  min-width: 120px; background: transparent;
  color: var(--text-dk);
}

.iv-job-selected-tag {
  display: inline-flex; align-items: center; gap: 5px;
  background: var(--p-pale);
  border: 1px solid var(--border);
  border-radius: 5px;
  padding: 3px 10px;
  font-size: 13px; color: var(--p-deep);
  cursor: pointer; flex: 1;
}
.iv-job-selected-tag:hover { background: #E5D8F5; }
.iv-job-tag-company { color: var(--text-lt); font-size: 12px; }
.iv-job-tag-city { color: var(--text-lt); font-size: 11px; }
.iv-job-tag-remove { margin-left: 4px; color: var(--p-mid); font-size: 12px; }

/* 搜索下拉 */
.iv-job-dropdown {
  margin-top: 4px;
  background: var(--p-wash);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(61, 31, 107, .12);
  max-height: 320px; overflow-y: auto;
}

.iv-job-searching {
  padding: 16px; text-align: center;
  color: var(--text-lt); font-size: 13px;
}

.iv-job-item {
  padding: 10px 14px; cursor: pointer;
  border-bottom: 1px solid var(--border-lt);
  transition: background .15s;
}
.iv-job-item:last-child { border-bottom: none; }
.iv-job-item:hover { background: var(--p-pale); }

.iv-job-item-name { font-size: 14px; font-weight: 600; color: var(--text-dk); margin-bottom: 4px; }
.iv-job-item-meta { display: flex; gap: 10px; font-size: 12px; margin-bottom: 3px; }
.iv-job-item-company { color: var(--text-md); }
.iv-job-item-city { color: var(--text-lt); }
.iv-job-item-salary { color: var(--gold); font-weight: 500; }
.iv-job-item-preview { font-size: 11px; color: var(--p-light); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.iv-job-dropdown-count {
  padding: 6px 14px 4px; font-size: 11px;
  color: var(--text-lt); border-bottom: 1px solid var(--border-lt);
}
.iv-job-load-more {
  padding: 10px 14px; text-align: center;
  font-size: 12px; color: var(--p-main);
  cursor: pointer; border-top: 1px solid var(--border-lt);
  transition: background .15s;
}
.iv-job-load-more:hover { background: var(--p-pale); }

/* 校验提示 */
.iv-validation-tip {
  color: var(--warn); font-size: 13px;
  margin-bottom: 8px; padding: 0 4px; flex-shrink: 0;
}
.iv-validation-tip span { margin-right: 12px; }

/* ── 知识库可展开区 ─────────────────────────────────────────────── */
.iv-kb-section {
  flex-shrink: 0; margin-bottom: 12px;
  border-radius: 8px; overflow: hidden;
  border: 1px solid var(--border-lt);
  background: var(--p-wash);
}
.iv-kb-bar {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px;
  font-size: 13px; color: var(--text-md);
  cursor: pointer; user-select: none;
  transition: background .15s;
}
.iv-kb-bar:hover { background: var(--p-pale); }
.iv-kb-bar-text { flex: 1; }
.iv-kb-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.iv-kb-dot.ready { background: var(--ok); }
.iv-kb-dot.empty { background: var(--gold); }
.iv-kb-arrow {
  color: var(--p-mid); font-size: 12px;
  transition: transform .2s;
}
.iv-kb-arrow.expanded { transform: rotate(180deg); }
.iv-kb-expand {
  border-top: 1px solid var(--border-lt);
  padding: 12px 16px;
  display: flex; gap: 12px;
}
.iv-kb-expand-upload {
  flex: 0 0 280px; display: flex;
  flex-direction: column; gap: 8px;
}
.iv-kb-upload-area :deep(.el-upload-dragger) {
  padding: 12px; height: auto;
}
.iv-kb-expand-footer {
  display: flex; align-items: center; justify-content: flex-end;
}
.iv-kb-upload-result { font-size: 12px; color: var(--ok); }

/* 片段列表 */
.iv-kb-segments {
  flex: 1; min-width: 0;
  display: flex; flex-direction: column; gap: 6px;
}
.iv-kb-segments-header {
  font-size: 12px; font-weight: 600; color: var(--text-md);
  display: flex; align-items: center; justify-content: space-between;
  padding-bottom: 4px; border-bottom: 1px solid var(--border-lt);
}
.iv-kb-seg-list {
  max-height: 200px; overflow-y: auto;
  display: flex; flex-direction: column; gap: 6px;
}
.iv-kb-seg-item {
  background: var(--p-ghost);
  border: 1px solid var(--border-lt);
  border-radius: 5px; padding: 8px 10px;
}
.iv-kb-seg-source {
  font-size: 11px; color: var(--text-lt); font-weight: 500; margin-bottom: 3px;
}
.iv-kb-seg-preview {
  font-size: 12px; color: var(--text-md); line-height: 1.5;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}
.iv-kb-seg-more {
  text-align: center; font-size: 12px; color: var(--p-main);
  padding: 6px 0; cursor: pointer; border-top: 1px solid var(--border-lt);
}
.iv-kb-seg-more:hover { background: var(--p-pale); }

/* 开始面试按钮 */
.iv-start-btn {
  width: 100%; height: 46px; font-size: 15px; flex-shrink: 0;
  background: var(--p-deep) !important;
  border-color: var(--p-deep) !important;
  color: #f5eeff !important;
  letter-spacing: .05em;
}
.iv-start-btn:hover {
  background: var(--p-main) !important;
  border-color: var(--p-main) !important;
}

/* ── 面试对话阶段 ─────────────────────────────────────────────── */
.iv-chat-wrap {
  max-width: 860px; margin: 0 auto;
  display: flex; flex-direction: column;
  height: calc(100vh - 100px);
}

.iv-chat-header {
  display: flex; align-items: center; gap: 12px;
  background: var(--p-wash);
  border: 1px solid var(--border-lt);
  border-radius: 10px;
  padding: 12px 18px; margin-bottom: 12px;
  box-shadow: 0 1px 6px rgba(61, 31, 107, .06);
  flex-shrink: 0;
}
.iv-chat-title { display: flex; align-items: center; gap: 8px; flex: 1; }
.iv-chat-style-badge {
  background: var(--p-pale); color: var(--p-deep);
  padding: 4px 12px; border-radius: 4px;
  font-size: 13px; font-weight: 600;
  border: 1px solid var(--border);
}
.iv-chat-job { font-size: 13px; color: var(--text-lt); }
.iv-chat-meta { display: flex; gap: 12px; font-size: 13px; color: var(--text-lt); }

/* 结束面试按钮覆盖 */
.iv-chat-header :deep(.el-button--danger.is-plain) {
  color: var(--warn) !important;
  border-color: var(--warn) !important;
  background: transparent !important;
}

/* 消息列表 */
.iv-msg-list {
  flex: 1; overflow-y: auto;
  padding: 20px 16px;
  background: var(--p-ghost);
  border: 1px solid var(--border-lt);
  border-radius: 10px; margin-bottom: 12px;
  box-shadow: inset 0 1px 4px rgba(61,31,107,.04);
}

.iv-msg-row {
  display: flex; gap: 10px;
  margin-bottom: 20px; align-items: flex-start;
}
.iv-msg-row.user { flex-direction: row-reverse; }

/* 头像：直接展示 emoji，加淡紫背景 */
.iv-msg-avatar {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: var(--p-pale);
  border: 1.5px solid var(--border);
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; flex-shrink: 0;
}
.iv-msg-row.user .iv-msg-avatar {
  background: var(--p-pale);
  border-color: var(--p-mid);
}

.iv-msg-bubble {
  max-width: 72%;
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 14px; line-height: 1.75;
  word-break: break-word;
}
.iv-msg-row.assistant .iv-msg-bubble {
  background: var(--p-wash);
  border: 1px solid var(--border-lt);
  color: var(--text-dk);
  border-bottom-left-radius: 3px;
}
.iv-msg-row.user .iv-msg-bubble {
  background: var(--p-deep);
  color: #f0e8ff;
  border-bottom-right-radius: 3px;
}
.iv-streaming {
  background: var(--p-pale) !important;
  border-color: var(--border) !important;
}
:deep(.cursor) {
  display: inline-block;
  width: 2px; height: 1em;
  background: var(--p-main);
  margin-left: 2px;
  animation: blink 1s step-end infinite;
  vertical-align: text-bottom;
}
@keyframes blink { 50% { opacity: 0; } }

/* 输入区 */
.iv-input-area {
  background: var(--p-wash);
  border: 1px solid var(--border-lt);
  border-radius: 10px;
  padding: 14px 16px;
  box-shadow: 0 1px 4px rgba(61,31,107,.05);
  flex-shrink: 0;
}
/* 输入框 override */
.iv-input-area :deep(.el-textarea__inner) {
  border-color: var(--border) !important;
  background: var(--p-ghost) !important;
  color: var(--text-dk) !important;
  border-radius: 6px !important;
}
.iv-input-area :deep(.el-textarea__inner):focus {
  border-color: var(--p-main) !important;
  box-shadow: 0 0 0 2px rgba(107,63,160,.1) !important;
}
.iv-input-actions {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 10px;
}
.iv-input-tip { font-size: 12px; color: var(--p-light); }
.iv-input-btns { display: flex; gap: 8px; align-items: center; }

/* 发送按钮 override */
.iv-input-btns :deep(.el-button--primary) {
  background: var(--p-main) !important;
  border-color: var(--p-main) !important;
}
.iv-input-btns :deep(.el-button--primary:hover) {
  background: var(--p-deep) !important;
  border-color: var(--p-deep) !important;
}

/* 语音按钮 */
.iv-input-btns :deep(.el-button--default) {
  border-color: var(--border) !important;
  color: var(--p-mid) !important;
  background: var(--p-ghost) !important;
}
.iv-input-btns :deep(.el-button--default:hover) {
  border-color: var(--p-mid) !important;
  color: var(--p-main) !important;
  background: var(--p-pale) !important;
}

.iv-recording {
  animation: pulse-rec 1.2s ease-in-out infinite;
}
@keyframes pulse-rec {
  0%, 100% { box-shadow: 0 0 0 0 rgba(192, 57, 43, .35); }
  50% { box-shadow: 0 0 0 6px rgba(192, 57, 43, 0); }
}

.iv-voice-hint {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; color: var(--warn); margin-top: 8px;
}
.iv-voice-dot {
  width: 8px; height: 8px; border-radius: 50%; background: var(--warn);
  animation: pulse-dot 1s ease-in-out infinite;
}
@keyframes pulse-dot { 0%, 100% { opacity: 1; } 50% { opacity: .3; } }
.iv-voice-error { font-size: 12px; color: var(--gold); margin-top: 6px; }

/* ── 总结阶段 ─────────────────────────────────────────────────── */
.iv-summary-wrap { max-width: 760px; margin: 0 auto; }
.iv-summary-header { text-align: center; margin-bottom: 24px; }

/* 总结图标：直接展示 emoji */
.iv-summary-icon { font-size: 48px; margin-bottom: 8px; }

.iv-summary-header h2 {
  font-size: 20px; font-weight: 700;
  color: var(--text-dk);
  margin: 0 0 6px;
  letter-spacing: .04em;
}
.iv-summary-meta { font-size: 13px; color: var(--text-lt); }

/* 总结卡片 override */
.iv-summary-card { padding: 8px; }
.iv-summary-card :deep(.el-card__body) {
  background: var(--p-ghost) !important;
}
.iv-summary-content { font-size: 14px; line-height: 1.85; color: var(--text-dk); }
.iv-summary-loading {
  display: flex; align-items: center; gap: 10px;
  color: var(--text-lt); padding: 40px 0; justify-content: center;
}
.iv-summary-actions {
  display: flex; justify-content: center; gap: 12px; margin-top: 20px;
}
.iv-summary-actions :deep(.el-button--primary) {
  background: var(--p-deep) !important;
  border-color: var(--p-deep) !important;
}
.iv-summary-actions :deep(.el-button--default) {
  color: var(--p-main) !important;
  border-color: var(--border) !important;
}

/* ── 历史抽屉 ─────────────────────────────────────────────────── */
.iv-history-drawer { padding: 8px 0; }
.iv-history-item { margin-bottom: 18px; }
.iv-history-role {
  font-size: 12px; font-weight: 600;
  color: var(--text-lt); margin-bottom: 6px;
}
.iv-history-item.assistant .iv-history-role { color: var(--p-main); }
.iv-history-item.user .iv-history-role { color: var(--gold); }
.iv-history-text {
  font-size: 13px; line-height: 1.7; color: var(--text-dk);
  background: var(--p-ghost);
  border: 1px solid var(--border-lt);
  border-radius: 6px; padding: 10px 14px;
}

/* ── 知识库弹窗 ─────────────────────────────────────────────── */
.iv-kb-dialog { padding: 4px 0; }

/* ── Element Plus 全局覆盖（scoped 内只影响本组件） ─────────────── */
/* primary 按钮统一走古典紫 */
:deep(.el-button--primary) {
  background: var(--p-main) !important;
  border-color: var(--p-main) !important;
}
:deep(.el-button--primary:hover),
:deep(.el-button--primary:focus) {
  background: var(--p-deep) !important;
  border-color: var(--p-deep) !important;
}
/* danger 按钮保留红色但降饱和 */
:deep(.el-button--danger) {
  background: var(--warn) !important;
  border-color: var(--warn) !important;
}
/* text 类按钮 */
:deep(.el-button--primary.is-text),
:deep(.el-button.is-text[type="primary"]) {
  color: var(--p-main) !important;
  background: transparent !important;
}

/* ── 响应式 ───────────────────────────────────────────────────── */
@media (max-width: 700px) {
  .iv-style-grid { grid-template-columns: repeat(2, 1fr); }
  .iv-setup-cols { flex-direction: column; gap: 8px; }
  .iv-msg-bubble { max-width: 88%; }
}
</style>
