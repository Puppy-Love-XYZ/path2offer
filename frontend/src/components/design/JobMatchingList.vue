<template>
  <div class="jml-wrap">

    <!-- 列表头 -->
    <div class="jml-header">
      <div class="jml-header-left">
        <div class="jml-header-eyebrow">智能人岗匹配 · 语义向量</div>
        <h2 class="jml-header-title">Top {{ jobs.length }} 推荐岗位</h2>
      </div>
      <div class="jml-header-right">
        <span class="jml-header-hint">Hover 维度可查看详情</span>
      </div>
    </div>
    <div class="jml-divider-strong" />

    <!-- 卡片列表 -->
    <div class="jml-list">
      <div
        v-for="(job, idx) in jobs"
        :key="job.id"
        class="jml-card"
        @click="$emit('select', job)"
      >
        <!-- 排名 -->
        <div class="jml-rank" :class="`jml-rank--${idx + 1}`">
          #{{ idx + 1 }}
        </div>

        <!-- 主体信息 -->
        <div class="jml-body">
          <div class="jml-title">{{ job.job_summary }}</div>
          <div class="jml-company">{{ job.job_name || '—' }}</div>

          <!-- 标签行 -->
          <div class="jml-tags">
            <span v-if="job.work_city"          class="jml-tag">{{ job.work_city }}</span>
            <span v-if="job.salary_min || job.salary_max" class="jml-tag jml-tag--salary">{{ formatSalary(job.salary_min, job.salary_max) }}</span>
            <span v-if="job.your_education"     class="jml-tag">{{ job.your_education }}</span>
            <span v-if="job.working_exp"        class="jml-tag">{{ job.working_exp }}</span>
            <span v-if="job.company_size"       class="jml-tag">{{ job.company_size }}</span>
          </div>

          <!-- 维度得分 pill（hover 显示详情） -->
          <div class="jml-scores">

            <!-- 语义理解 -->
            <div class="jml-pill-wrap">
              <span class="jml-score-pill jml-score-semantic">
                语义理解 {{ semScore(job) }}
              </span>
              <div class="jml-tooltip jml-tooltip--semantic">
                <div class="tt-title">语义理解</div>
                <div class="tt-desc">基于 SBERT 将简历与岗位描述编码为向量，计算余弦相似度</div>
                <div class="tt-row"><span class="tt-label">得分</span><span class="tt-val">{{ semScore(job) }} / 100</span></div>
                <div class="tt-row"><span class="tt-label">权重</span><span class="tt-val">40%</span></div>
              </div>
            </div>

            <!-- 技能匹配 -->
            <div class="jml-pill-wrap">
              <span class="jml-score-pill jml-score-skill">
                技能匹配 {{ job.score_skill !== undefined ? job.score_skill : '—' }}
              </span>
              <div class="jml-tooltip jml-tooltip--skill">
                <div class="tt-title">技能匹配</div>
                <template v-if="job.dimensions?.skills">
                  <div class="tt-row">
                    <span class="tt-label">命中关键词</span>
                    <span class="tt-val">{{ job.dimensions.skills.matched_count ?? '—' }} / {{ job.dimensions.skills.total_count ?? '—' }} 个</span>
                  </div>
                  <div v-if="job.dimensions.skills.matched_skills?.length" class="tt-skills">
                    <span v-for="sk in job.dimensions.skills.matched_skills" :key="sk" class="tt-skill-tag">{{ sk }}</span>
                  </div>
                </template>
                <div v-else class="tt-desc">技能关键词覆盖率（TF-IDF + W2V 扩展）</div>
                <div class="tt-row"><span class="tt-label">权重</span><span class="tt-val">40%</span></div>
              </div>
            </div>

            <!-- 经验修正 -->
            <div class="jml-pill-wrap">
              <span class="jml-score-pill jml-score-exp">
                经验修正 {{ job.score_exp !== undefined ? job.score_exp : '—' }}
              </span>
              <div class="jml-tooltip jml-tooltip--exp">
                <div class="tt-title">经验修正</div>
                <div v-if="job.dimensions?.experience?.match" class="tt-match">{{ job.dimensions.experience.match }}</div>
                <div v-else class="tt-desc">根据简历工作年限与岗位要求比对打分</div>
                <div class="tt-row"><span class="tt-label">权重</span><span class="tt-val">20%</span></div>
              </div>
            </div>

          </div>
        </div>

        <!-- 右侧：环形得分 + 操作按钮 -->
        <div class="jml-right" @click.stop>

          <!-- 得分大字 -->
          <div class="jml-score-num" :class="scoreClass(job.score)">
            {{ (job.score * 100).toFixed(2) }}
          </div>

          <!-- 操作按钮 -->
          <div class="jml-actions">
            <button
              class="jml-act-btn jml-act-match"
              title="深度匹配分析"
              @click.stop="$emit('match', job)"
            >⚡</button>
            <button
              class="jml-act-btn jml-act-fav"
              :class="{ 'is-faved': favoriteIds.includes(job.id) }"
              :title="favoriteIds.includes(job.id) ? '取消收藏' : '收藏岗位'"
              @click.stop="$emit('favorite', job)"
            >{{ favoriteIds.includes(job.id) ? '♥' : '♡' }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!jobs.length && !loading" class="jml-empty">
      <div class="jml-empty-icon">◈</div>
      <p>上传简历后，系统将为你匹配最相关的岗位</p>
    </div>

  </div>
</template>

<script setup lang="ts">
/* ── 类型 ── */
export interface MatchedJob {
  id:              number
  job_summary:     string    // 职位名
  job_name?:       string    // 公司名
  work_city?:      string
  salary_min?:     number
  salary_max?:     number
  working_exp?:    string
  your_education?: string
  company_size?:   string
  score:           number    // 0~1 综合得分
  ai_summary?:     string
  score_semantic?: number
  score_skill?:    number
  score_exp?:      number
  dimensions?: {
    semantic?:   { score: number; weight?: number; label?: string }
    skills?:     { score: number; weight?: number; label?: string; matched_skills?: string[]; matched_count?: number; total_count?: number; w2v_used?: boolean }
    experience?: { score: number; weight?: number; label?: string; match?: string }
    education?:  { score: number; label?: string; match?: string }
  }
}

interface Props {
  jobs?:        MatchedJob[]
  loading?:     boolean
  favoriteIds?: number[]
}

const props = withDefaults(defineProps<Props>(), {
  jobs:        () => [],
  loading:     false,
  favoriteIds: () => [],
})

defineEmits<{
  (e: 'select',   job: MatchedJob): void
  (e: 'match',    job: MatchedJob): void
  (e: 'favorite', job: MatchedJob): void
}>()

/* ── 工具函数 ── */
function semScore(job: MatchedJob): number {
  return job.score_semantic !== undefined ? job.score_semantic : Math.round(job.score * 100)
}

function formatSalary(min?: number, max?: number): string {
  if (!min && !max) return ''
  if (min && max) return `¥${min}–${max}k`
  if (min)        return `¥${min}k 起`
  return `¥${max}k 以下`
}

function scoreClass(score: number): string {
  const p = score * 100
  if (p >= 60) return 'score--green'
  if (p >= 40) return 'score--brown'
  return 'score--red'
}
</script>

<style scoped>
/* ─── 根容器 ─────────────────────────────── */
.jml-wrap {
  font-family: 'Inter', 'PingFang SC', system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* ─── 列表头 ─────────────────────────────── */
.jml-header {
  display:         flex;
  align-items:     flex-end;
  justify-content: space-between;
  padding:         12px 0 10px;
  flex-shrink:     0;
}

.jml-header-eyebrow {
  font-size:      9px;
  font-weight:    600;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color:          #4A7C68;
  margin-bottom:  4px;
}

.jml-header-title {
  font-family:    'Georgia', serif;
  font-size:      1.375rem;
  font-weight:    400;
  color:          #1A3C34;
  letter-spacing: -0.02em;
  margin:         0;
}

.jml-header-right {
  display:     flex;
  align-items: center;
  gap:         12px;
}

.jml-header-hint {
  font-size:  11px;
  color:      #B8BAC0;
  font-style: italic;
}

.jml-divider-strong {
  height:        0;
  border-top:    1.5px solid #1A3C34;
  margin-bottom: 4px;
  flex-shrink:   0;
}

/* ─── 卡片列表 ───────────────────────────── */
.jml-list {
  display:        flex;
  flex-direction: column;
  gap:            0;
  flex:           1;
  overflow-y:     auto;
  min-height:     0;
}

/* ─── 单张卡片 ───────────────────────────── */
.jml-card {
  display:         flex;
  align-items:     center;
  gap:             14px;
  padding:         14px 10px;
  border-bottom:   0.5px solid #E2EDE9;
  cursor:          pointer;
  transition:      background 140ms ease;
  border-radius:   3px;
}

.jml-card:hover   { background: #F2F8F6; }
.jml-card:last-child { border-bottom: none; }

/* ─── 排名 ───────────────────────────────── */
.jml-rank {
  font-family:  'Georgia', serif;
  font-size:    15px;
  font-style:   italic;
  font-weight:  700;
  flex-shrink:  0;
  width:        32px;
  text-align:   center;
}

.jml-rank--1 { color: #B8860B; }
.jml-rank--2 { color: #6B7280; }
.jml-rank--3 { color: #8B4513; }
.jml-rank--4,
.jml-rank--5 { color: #B8BAC0; }

/* ─── 主体 ───────────────────────────────── */
.jml-body {
  flex:      1;
  min-width: 0;
  display:   flex;
  flex-direction: column;
  gap:       4px;
}

.jml-title {
  font-family:   'Georgia', serif;
  font-size:     15px;
  font-weight:   400;
  color:         #1A1A1A;
  overflow:      hidden;
  text-overflow: ellipsis;
  white-space:   nowrap;
  line-height:   1.3;
}

.jml-company {
  font-size:  12px;
  color:      #9CA3AF;
  line-height: 1.3;
}

/* ─── 标签 ───────────────────────────────── */
.jml-tags {
  display:  flex;
  flex-wrap: wrap;
  gap:       4px;
  margin-top: 2px;
}

.jml-tag {
  display:       inline-block;
  padding:       1px 7px;
  font-size:     11px;
  border:        0.5px solid #C8D8D2;
  border-radius: 2px;
  color:         #4B5563;
  background:    #F5FAF8;
  white-space:   nowrap;
}

.jml-tag--salary {
  color:        #1A3C34;
  border-color: #9AC6B8;
  background:   #EEF4F2;
  font-weight:  500;
}

/* ─── 维度得分 pills ─────────────────────── */
.jml-scores {
  display:  flex;
  flex-wrap: wrap;
  gap:       5px;
  margin-top: 3px;
}

.jml-score-pill {
  display:       inline-block;
  padding:       1px 8px;
  font-size:     11px;
  font-weight:   500;
  border-radius: 999px;
  white-space:   nowrap;
  cursor:        default;
}

.jml-score-semantic {
  background: #EEF4F2;
  color:      #1A3C34;
  border:     0.5px solid #9AC6B8;
}

.jml-score-skill {
  background: #EFF6FF;
  color:      #1E40AF;
  border:     0.5px solid #BFDBFE;
}

.jml-score-exp {
  background: #FEF3C7;
  color:      #92400E;
  border:     0.5px solid #FCD34D;
}

/* ─── 右侧区域 ───────────────────────────── */
.jml-right {
  flex-shrink:    0;
  display:        flex;
  flex-direction: column;
  align-items:    center;
  gap:            6px;
}

/* ─── 得分大字 ───────────────────────────── */
.jml-score-num {
  font-family:  'Georgia', serif;
  font-size:    28px;
  font-weight:  400;
  line-height:  1;
  letter-spacing: -0.02em;
  flex-shrink:  0;
  min-width:    64px;
  text-align:   right;
}

.score--green { color: #1A3C34; }
.score--brown { color: #92400E; }
.score--red   { color: #DC2626; }

/* ─── 操作按钮 ───────────────────────────── */
.jml-actions {
  display: flex;
  gap:     5px;
}

.jml-act-btn {
  display:       inline-flex;
  align-items:   center;
  justify-content: center;
  width:         28px;
  height:        28px;
  border:        0.5px solid #DCDCDC;
  border-radius: 2px;
  background:    #FBFBFB;
  font-size:     13px;
  cursor:        pointer;
  transition:    border-color 140ms, color 140ms, background 140ms;
  color:         #6B7280;
}

.jml-act-match:hover {
  border-color: #1A3C34;
  color:        #1A3C34;
  background:   #EEF4F2;
}

.jml-act-fav:hover:not(.is-faved) {
  border-color: #9B4A4A;
  color:        #9B4A4A;
  background:   #FAF0F0;
}

.jml-act-fav.is-faved {
  border-color: #9B4A4A;
  color:        #9B4A4A;
  background:   #FAF0F0;
}

/* ─── Pill hover 弹出详情 ────────────────── */
.jml-pill-wrap {
  position: relative;
  display:  inline-block;
}

.jml-tooltip {
  display:        none;
  position:       absolute;
  top:            calc(100% + 6px);
  left:           0;
  z-index:        200;
  min-width:      200px;
  max-width:      280px;
  background:     #1A1A1A;
  color:          #F3F4F6;
  border-radius:  5px;
  padding:        10px 12px;
  box-shadow:     0 6px 20px rgba(0,0,0,0.25);
  pointer-events: none;
  white-space:    normal;
}
.jml-tooltip::after {
  content:             '';
  position:            absolute;
  bottom:              100%;
  left:                14px;
  border:              5px solid transparent;
  border-bottom-color: #1A1A1A;
}
.jml-pill-wrap:hover .jml-tooltip { display: block; }

.tt-title {
  font-size:      12px;
  font-weight:    600;
  margin-bottom:  6px;
  color:          #fff;
  letter-spacing: 0.02em;
}
.tt-desc {
  font-size:     11.5px;
  color:         #9CA3AF;
  line-height:   1.5;
  margin-bottom: 6px;
}
.tt-row {
  display:         flex;
  justify-content: space-between;
  align-items:     center;
  gap:             8px;
  font-size:       11.5px;
  padding:         2px 0;
}
.tt-label { color: #9CA3AF; flex-shrink: 0; }
.tt-val   { color: #E5E7EB; font-weight: 500; text-align: right; }

.tt-match {
  font-size:     11.5px;
  color:         #D1FAE5;
  line-height:   1.5;
  margin-bottom: 6px;
  padding:       4px 8px;
  background:    rgba(26,60,52,0.5);
  border-radius: 3px;
  border-left:   2px solid #4A7C68;
}
.tt-skills {
  display:   flex;
  flex-wrap: wrap;
  gap:       4px;
  margin:    6px 0;
}
.tt-skill-tag {
  display:       inline-block;
  padding:       1px 7px;
  background:    rgba(74,124,104,0.3);
  border:        0.5px solid #4A7C68;
  border-radius: 999px;
  font-size:     11px;
  color:         #A7F3D0;
}

/* ─── 空状态 ─────────────────────────────── */
.jml-empty {
  display:        flex;
  flex-direction: column;
  align-items:    center;
  justify-content: center;
  flex:           1;
  gap:            10px;
  color:          #9CA3AF;
  font-size:      13px;
  padding:        40px 20px;
  text-align:     center;
}

.jml-empty-icon {
  font-size: 28px;
  color:     #C8D8D2;
}
</style>
