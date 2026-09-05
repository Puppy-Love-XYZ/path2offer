<template>
  <div class="domain-root">
    <div class="domain-shell">
      <div class="domain-graph" ref="graphWrapRef">
        <div class="domain-legend">
          <span class="domain-legend__item"><i class="domain-swatch domain-swatch--domain"></i>领域</span>
          <span class="domain-legend__item"><i class="domain-swatch domain-swatch--role"></i>岗位</span>
          <span class="domain-legend__item"><i class="domain-swatch domain-swatch--skill"></i>技术栈</span>
          <span class="domain-legend__item"><i class="domain-swatch domain-swatch--emerging"></i>新兴度越高越深</span>
          <span class="domain-legend__item"><i class="domain-swatch domain-swatch--normal-skill"></i>普通技能</span>
          <span class="domain-legend__item"><i class="domain-line domain-line--solid"></i>领域包含岗位</span>
          <span class="domain-legend__item"><i class="domain-line domain-line--dashed"></i>岗位需要技术栈</span>
        </div>

        <div class="domain-controls">
          <label class="domain-select-wrap">
            <span class="domain-control-label">岗位区间</span>
            <select v-model="selectedRangeKey" class="domain-select">
              <option v-for="option in rangeOptions" :key="option.key" :value="option.key">
                {{ option.label }}
              </option>
            </select>
          </label>

          <button
            type="button"
            class="domain-emerging-toggle"
            :class="{ active: emergingOnly }"
            @click="toggleEmergingOnly"
          >
            <span class="domain-emerging-toggle__dot"></span>
            仅新兴岗位
          </button>
        </div>

        <el-button
          circle
          text
          class="domain-reset"
          title="重置视图"
          aria-label="重置视图"
          @click="resetView"
        >
          <el-icon><RefreshLeft /></el-icon>
        </el-button>

        <div class="domain-scroll-area">
          <div class="domain-graph__spacer" :style="{ height: `${graphTopSpace}px` }"></div>

          <div class="domain-canvas" :style="{ width: `${canvasSize.width}px`, height: `${canvasSize.height}px` }">
            <div ref="chartRef" class="domain-chart"></div>
          </div>
        </div>
      </div>

      <aside class="domain-detail">
        <div class="domain-detail__head">
          <div>
            <div class="domain-detail__badge">{{ detail.badge }}</div>
            <div class="domain-detail__hint">{{ detail.hint }}</div>
          </div>
        </div>

        <div class="domain-detail__body">
          <div class="domain-detail__title">{{ detail.title }}</div>
          <div class="domain-detail__subtitle">{{ detail.subtitle }}</div>

          <div class="domain-detail__stats">
            <div v-for="stat in detail.stats" :key="stat.label" class="domain-stat">
              <span class="domain-stat__label">{{ stat.label }}</span>
              <strong>{{ stat.value }}</strong>
            </div>
          </div>

          <div v-for="section in detail.sections" :key="section.title" class="domain-detail__section">
            <div class="domain-detail__section-head">
              <div class="domain-detail__section-title">{{ section.title }}</div>
              <div v-if="section.subtitle" class="domain-detail__section-subtitle">{{ section.subtitle }}</div>
            </div>

            <div v-if="section.rows.length" class="domain-detail__rows">
              <div v-for="row in section.rows" :key="row.key" class="domain-detail__row">
                <div class="domain-detail__row-main">
                  <span class="domain-detail__row-name">{{ row.name }}</span>
                  <span v-if="row.meta" class="domain-detail__row-meta">{{ row.meta }}</span>
                </div>
                <strong class="domain-detail__row-value">{{ row.value }}</strong>
              </div>
            </div>

            <div v-else class="domain-detail__empty">{{ section.emptyText }}</div>
          </div>

          <div class="domain-detail__note">{{ detail.note }}</div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { RefreshLeft } from '@element-plus/icons-vue'
import domainPositionData from '../../../backend/graph_base_data/domain_position.json'
import skillLexiconData from '../../../backend/app/skill_lexicon.json'

type DomainName = '人工智能' | '智能系统' | '物联网' | '大数据'

interface JobRef {
  name: string
  count: number
}

interface SkillRef {
  name: string
  count: number
}

interface RoleNode {
  id: string
  name: string
  total: number
  emergence: number
  source: any
  jobs: JobRef[]
  skills: SkillRef[]
  level: 2
}

interface DomainNode {
  id: string
  name: string
  total: number
  roles: RoleNode[]
  level: 1
}

interface GraphModel {
  domain: DomainNode
  minRoleTotal: number
  maxRoleTotal: number
  minRoleSize: number
  maxRoleSize: number
  domainSize: number
}

interface VisibleModel {
  roles: RoleNode[]
  minRoleTotal: number
  maxRoleTotal: number
  minRoleSize: number
  maxRoleSize: number
  visibleTotal: number
}

interface FlowSkillNode {
  id: string
  name: string
  total: number
  roleIds: string[]
  emergingTier: number
  emergingCategory: '' | '近年新兴' | '前沿探索'
  emergingWeight: '' | '强新兴' | '弱新兴'
  level: 3
}

interface DetailStat {
  label: string
  value: string
}

interface DetailRow {
  key: string
  name: string
  value: string
  meta?: string
}

interface DetailSection {
  title: string
  subtitle?: string
  rows: DetailRow[]
  emptyText: string
}

const props = defineProps<{
  domainName: string
}>()

const DOMAIN_ORDER: DomainName[] = ['人工智能', '智能系统', '物联网', '大数据']
const DOMAIN_COLORS: Record<DomainName, string> = {
  人工智能: '#3A5E82',
  智能系统: '#3E716F',
  物联网: '#9A704A',
  大数据: '#665F84',
}
const RANGE_SIZE = 10
const rawDomains = Array.isArray(domainPositionData) ? (domainPositionData as any[]) : []
const rawSkillLexicon = (skillLexiconData || {}) as Record<string, any>

const EMERGING_LEVEL_COLORS = [
  '#AAB6FF',
  '#7F91F2',
  '#5B6CD4',
  '#38479B',
] as const
const EMERGING_LEVEL_NAMES = ['低', '中', '高', '极高'] as const
const EMERGING_THRESHOLD = 0.2

const normalizeSkillKey = (value: unknown) =>
  typeof value === 'string' ? value.trim().replace(/\s+/g, ' ').toLocaleLowerCase() : ''

const makeSkillSet = (value: unknown) => new Set(
  (Array.isArray(value) ? value : []).map(normalizeSkillKey).filter(Boolean),
)

const recentEmergingSkillSet = makeSkillSet(rawSkillLexicon['近年新兴'])
const frontierSkillSet = makeSkillSet(rawSkillLexicon['前沿探索'])
const strongEmergingSkillSet = makeSkillSet(rawSkillLexicon?._新兴权重?.['强新兴'])
const weakEmergingSkillSet = makeSkillSet(rawSkillLexicon?._新兴权重?.['弱新兴'])

const getSkillEmergingMeta = (name: string) => {
  const key = normalizeSkillKey(name)
  const isFrontier = frontierSkillSet.has(key)
  const isRecent = recentEmergingSkillSet.has(key)
  const isStrong = strongEmergingSkillSet.has(key)
  const isWeak = weakEmergingSkillSet.has(key)
  const emergingWeight: '' | '强新兴' | '弱新兴' = isStrong ? '强新兴' : isWeak ? '弱新兴' : ''

  if (isFrontier) {
    return {
      emergingTier: isStrong ? 5 : 4,
      emergingCategory: '前沿探索' as const,
      emergingWeight,
    }
  }
  if (isRecent) {
    return {
      emergingTier: isStrong ? 3 : isWeak ? 1 : 2,
      emergingCategory: '近年新兴' as const,
      emergingWeight,
    }
  }
  return { emergingTier: 0, emergingCategory: '' as const, emergingWeight: '' as const }
}

const graphWrapRef = ref<HTMLDivElement | null>(null)
const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null
let resizeObserver: ResizeObserver | null = null
const graphSize = ref({ width: 0, height: 0 })
const selectedNodeId = ref<string>('')
const selectedRangeKey = ref('0-10')
const emergingOnly = ref(false)
const FLOW_TOP_SPACE = 108

const safeName = (value: string, fallback: string) => {
  const text = (value || '').trim()
  return text || fallback
}

const normalizeCount = (value: any) => {
  if (typeof value === 'number') return value
  if (typeof value === 'string') return Number(value) || 0
  return 0
}

const sumJobCounts = (roleRaw: any) => {
  const jobs = Array.isArray(roleRaw?.职位) ? roleRaw.职位 : []
  const summed = jobs.reduce((total: number, jobRaw: any) => total + normalizeCount(jobRaw?.招聘次数), 0)
  return summed > 0 ? summed : normalizeCount(roleRaw?.职位数量)
}

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max)

const normalizeEmergingScore = (value: unknown) => {
  const raw = normalizeCount(value)
  if (raw <= 0) return 0
  return clamp(raw > 1 ? raw / 100 : raw, 0, 1)
}

const hexToRgba = (hex: string, alpha: number) => {
  const value = Number.parseInt(hex.replace('#', ''), 16)
  return `rgba(${(value >> 16) & 255}, ${(value >> 8) & 255}, ${value & 255}, ${alpha})`
}

const lighten = (hex: string, amount: number) => {
  const value = Number.parseInt(hex.replace('#', ''), 16)
  const ratio = clamp(amount, 0, 1)
  const mix = (channel: number) => Math.round(channel * (1 - ratio) + 255 * ratio)
  return `rgb(${mix((value >> 16) & 255)}, ${mix((value >> 8) & 255)}, ${mix(value & 255)})`
}

const getEmergingVisual = (score: number) => {
  const percent = normalizeEmergingScore(score) * 100
  const index = clamp(Math.floor((percent - 20) / 20), 0, EMERGING_LEVEL_COLORS.length - 1)
  const color = EMERGING_LEVEL_COLORS[index]!
  return {
    color,
    levelName: EMERGING_LEVEL_NAMES[index],
    shadowColor: hexToRgba(color, 0.30 + index * 0.045),
    shadowBlur: 11 + index * 3.2,
    borderWidth: 2.6 + index * 0.32,
  }
}

const getSkillEmergingVisual = (tier: number) => {
  const index = clamp(Math.round(tier) - 1, 0, EMERGING_LEVEL_COLORS.length - 1)
  const color = EMERGING_LEVEL_COLORS[index]!
  return {
    color,
    shadowColor: hexToRgba(color, 0.28 + index * 0.045),
    shadowBlur: 9 + index * 2.6,
    borderWidth: 1.55 + index * 0.24,
  }
}

const emergingSkillGradient = (color: string) => new echarts.graphic.LinearGradient(0, 0, 1, 1, [
  { offset: 0, color: lighten(color, 0.91) },
  { offset: 0.58, color: lighten(color, 0.84) },
  { offset: 1, color: lighten(color, 0.76) },
])

// Keep role fills and normal borders identical to PanoramaGraph; only the
// domain view's ellipse geometry differs.
const roleGradient = (color: string) => new echarts.graphic.LinearGradient(0, 0, 1, 1, [
  { offset: 0, color: lighten(color, 0.91) },
  { offset: 1, color: lighten(color, 0.78) },
])

const splitLabel = (value: string, max = 6) => {
  const text = (value || '').trim()
  if (!text) return ''
  if (text.length <= max) return text
  return `${text.slice(0, max)}\n${text.slice(max)}`
}

const estimateRoleSizeRange = (maxLen: number, roleCount: number) => {
  const byName = clamp(42 + maxLen * 2.5, 54, 80)
  const byCount = clamp(80 - Math.min(22, Math.floor(roleCount * 0.18)), 46, 80)
  const maxSize = Math.round(Math.min(byName + 10, byCount + 10, 90))
  const minSize = Math.round(clamp(maxSize - 26, 42, maxSize - 8))
  return { minSize, maxSize }
}

const estimateDomainSize = (roleSize: number) => clamp(roleSize + 14, 66, 104)

const parseRangeKey = (key: string) => {
  if (key === 'all') return null
  const [startText, endText] = key.split('-')
  const start = Number(startText)
  const end = Number(endText)
  if (!Number.isFinite(start) || !Number.isFinite(end)) return null
  return { start, end }
}

const buildGraphModel = (): GraphModel => {
  const defaultDomain: DomainName = '人工智能'
  const domainName: DomainName = DOMAIN_ORDER.includes(props.domainName as DomainName)
    ? (props.domainName as DomainName)
    : defaultDomain
  const domainRaw = rawDomains.find(item => safeName(item?.领域, '') === domainName)

  const roleMap = new Map<string, {
    total: number
    emergenceSum: number
    emergenceWeight: number
    jobMap: Map<string, number>
    skillMap: Map<string, number>
    source: any
  }>()

  const roles = Array.isArray(domainRaw?.岗位) ? domainRaw.岗位 : []
  roles.forEach((roleRaw: any) => {
    const roleName = safeName(roleRaw?.岗位名称, '')
    if (!roleName) return

    const total = sumJobCounts(roleRaw)
    if (total <= 1) return

    const emergence = Number(roleRaw?.新兴程度)
    const entry = roleMap.get(roleName) || {
      total: 0,
      emergenceSum: 0,
      emergenceWeight: 0,
      jobMap: new Map<string, number>(),
      skillMap: new Map<string, number>(),
      source: roleRaw,
    }

    entry.total += total
    entry.emergenceSum += (Number.isFinite(emergence) ? emergence : 0) * total
    entry.emergenceWeight += total
    entry.source = entry.source || roleRaw

    const jobs = Array.isArray(roleRaw?.职位) ? roleRaw.职位 : []
    jobs.forEach((jobRaw: any) => {
      const jobName = safeName(jobRaw?.职位名称, '')
      const jobCount = normalizeCount(jobRaw?.招聘次数)
      if (!jobName || jobCount <= 0) return
      entry.jobMap.set(jobName, (entry.jobMap.get(jobName) || 0) + jobCount)
    })

    const skillRows = Array.isArray(roleRaw?.技术栈) ? roleRaw.技术栈 : []
    skillRows.forEach((skillRaw: any) => {
      const skillName = safeName(skillRaw?.所需技术, '')
      const skillCount = normalizeCount(skillRaw?.被需要次数)
      if (!skillName || skillCount <= 0) return
      entry.skillMap.set(skillName, (entry.skillMap.get(skillName) || 0) + skillCount)
    })

    roleMap.set(roleName, entry)
  })

  const roleNodes: RoleNode[] = [...roleMap.entries()]
    .map(([name, entry]) => {
      const jobs = [...entry.jobMap.entries()]
        .map(([jobName, count]) => ({ name: jobName, count }))
        .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, 'zh-Hans-CN'))

      const skills = [...entry.skillMap.entries()]
        .map(([skillName, count]) => ({ name: skillName, count }))
        .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, 'zh-Hans-CN'))

      return {
        id: '',
        name,
        total: entry.total,
        emergence: entry.emergenceWeight > 0 ? entry.emergenceSum / entry.emergenceWeight : 0,
        source: entry.source,
        jobs,
        skills,
        level: 2 as const,
      }
    })
    .sort((a, b) => b.total - a.total || b.emergence - a.emergence || a.name.localeCompare(b.name, 'zh-Hans-CN'))
    .map((role, index) => ({
      ...role,
      id: `role-${index}`,
    }))

  const { minSize: minRoleSize, maxSize: maxRoleSize } = estimateRoleSizeRange(
    Math.max(...roleNodes.map(role => role.name.length), 1),
    roleNodes.length,
  )
  const minRoleTotal = Math.min(...roleNodes.map(role => role.total), 1)
  const maxRoleTotal = Math.max(...roleNodes.map(role => role.total), 1)
  const domainSize = estimateDomainSize(maxRoleSize)

  const domainNode: DomainNode = {
    id: `domain-${domainName}`,
    name: domainName,
    total: roleNodes.reduce((sum, role) => sum + role.total, 0),
    roles: roleNodes,
    level: 1,
  }

  return {
    domain: domainNode,
    minRoleTotal,
    maxRoleTotal,
    minRoleSize,
    maxRoleSize,
    domainSize,
  }
}

const graphModel = computed<GraphModel>(() => buildGraphModel())

const rangeOptions = computed(() => {
  const total = graphModel.value.domain.roles.length
  const options: Array<{ key: string, label: string }> = []
  for (let start = 0; start < total; start += RANGE_SIZE) {
    const end = Math.min(total, start + RANGE_SIZE)
    options.push({ key: `${start}-${end}`, label: `${start + 1}-${end}` })
  }
  if (!options.length) {
    options.push({ key: '0-0', label: '暂无岗位' })
  }
  return options
})

const visibleRoles = computed(() => {
  const roles = graphModel.value.domain.roles
  const range = parseRangeKey(selectedRangeKey.value)
  const rangedRoles = range ? roles.slice(range.start, range.end) : roles
  return emergingOnly.value
    ? rangedRoles.filter(role => normalizeEmergingScore(role.emergence) > EMERGING_THRESHOLD)
    : rangedRoles
})

const visibleModel = computed<VisibleModel>(() => {
  const roles = visibleRoles.value
  const minLen = Math.max(...roles.map(role => role.name.length), 1)
  const { minSize, maxSize } = estimateRoleSizeRange(minLen, roles.length)
  const minRoleTotal = Math.min(...roles.map(role => role.total), 1)
  const maxRoleTotal = Math.max(...roles.map(role => role.total), 1)
  return {
    roles,
    minRoleTotal,
    maxRoleTotal,
    minRoleSize: minSize,
    maxRoleSize: maxSize,
    visibleTotal: roles.reduce((sum, role) => sum + role.total, 0),
  }
})

const visibleSkills = computed<FlowSkillNode[]>(() => {
  const skillMap = new Map<string, FlowSkillNode>()

  visibleRoles.value.forEach(role => {
    role.skills.slice(0, 3).forEach(skill => {
      const key = skill.name
      if (!key) return
      const entry: FlowSkillNode = skillMap.get(key) || {
        id: `skill-${key}`,
        name: key,
        total: 0,
        roleIds: [],
        ...getSkillEmergingMeta(key),
        level: 3 as const,
      }
      entry.total += skill.count
      if (!entry.roleIds.includes(role.id)) entry.roleIds.push(role.id)
      skillMap.set(key, entry)
    })
  })

  return [...skillMap.values()]
    .sort((a, b) => b.total - a.total || a.name.localeCompare(b.name, 'zh-Hans-CN'))
})

const isRingMode = computed(() => false)
const graphTopSpace = computed(() => FLOW_TOP_SPACE)

const selectedRecord = computed<DomainNode | RoleNode | FlowSkillNode | null>(() => {
  const model = graphModel.value
  if (!selectedNodeId.value) return null
  if (selectedNodeId.value === model.domain.id) return model.domain
  const role = visibleRoles.value.find(item => item.id === selectedNodeId.value)
  if (role) return role
  return visibleSkills.value.find(item => item.id === selectedNodeId.value) || null
})

const graphMetrics = computed(() => {
  const model = visibleModel.value
  const roleCount = Math.max(model.roles.length, 1)
  const ringGap = Math.max(64, Math.round(model.maxRoleSize + 24))
  const minRadius = Math.max(96, Math.round(graphModel.value.domainSize * 0.7 + model.maxRoleSize * 0.65))
  const ringPlan: Array<{ radius: number, count: number }> = []

  let remaining = roleCount
  let radius = minRadius

  while (remaining > 0) {
    const capacity = Math.max(6, Math.floor((2 * Math.PI * radius) / (model.maxRoleSize + 18)))
    const count = Math.min(remaining, capacity)
    ringPlan.push({ radius, count })
    remaining -= count
    radius += ringGap
  }

  const lastRing = ringPlan[ringPlan.length - 1]
  const outerRadius = lastRing ? lastRing.radius : minRadius
  return {
    ringPlan,
    outerRadius,
    ringGap,
  }
})

const flowMetrics = computed(() => {
  const roles = visibleRoles.value
  const skills = visibleSkills.value
  const canvasWidth = Math.max(graphSize.value.width || 0, 1)
  const canvasHeight = Math.max((graphSize.value.height || 0) - graphTopSpace.value, 260)
  const roleNameMax = Math.max(...roles.map(role => role.name.length), 1)
  const skillNameMax = Math.max(...skills.map(skill => skill.name.length), 1)
  const roleCount = Math.max(roles.length, 1)
  const skillRows = Math.max(skills.length, 1)
  const roleGap = 12
  const roleHeight = Math.min(38, Math.max(24, Math.floor((canvasHeight - 20 - roleGap * (roleCount - 1)) / roleCount)))
  const skillHeight = Math.min(26, Math.max(12, Math.floor((canvasHeight - 20) / skillRows)))
  const roleStep = roleCount > 1
    ? roleHeight + roleGap
    : 0
  const skillStep = skillRows > 1
    ? (canvasHeight - skillHeight - 20) / (skillRows - 1)
    : 0
  const skillAreaLeft = Math.round(canvasWidth * 0.66)
  const skillAreaWidth = Math.max(120, canvasWidth - skillAreaLeft - 20)
  const skillWidth = Math.min(
    skillAreaWidth,
    260,
    Math.max(170, 126 + skillNameMax * 3.2),
  )
  return {
    canvasWidth,
    canvasHeight,
    roleStep,
    skillStep,
    roleWidth: clamp(150 + Math.min(roleNameMax, 16) * 4, 170, 230),
    roleHeight,
    skillWidth,
    skillHeight,
    skillRows,
  }
})

const canvasSize = computed(() => {
  if (!isRingMode.value) {
    return {
      width: flowMetrics.value.canvasWidth,
      height: flowMetrics.value.canvasHeight,
    }
  }

  const metrics = graphMetrics.value
  const padding = 140
  const diameter = Math.round(metrics.outerRadius * 2 + padding)
  return {
    width: Math.max(graphSize.value.width || 0, diameter),
    height: Math.max(graphSize.value.height || 0, diameter),
  }
})

const buildThreeLayerOption = () => {
  const domain = graphModel.value.domain
  const roles = visibleRoles.value
  const skills = visibleSkills.value
  const model = visibleModel.value
  const metrics = flowMetrics.value
  const width = metrics.canvasWidth
  const height = metrics.canvasHeight
  const roleWidth = metrics.roleWidth
  const roleHeight = metrics.roleHeight
  const skillWidth = metrics.skillWidth
  const skillHeight = metrics.skillHeight
  const roleTop = 10 + roleHeight / 2
  const skillTop = 10 + skillHeight / 2
  const domainWidth = clamp(128 + domain.name.length * 9, 140, 176)
  const domainHeight = 64
  const domainX = Math.max(domainWidth / 2 + 16, Math.round(width * 0.09))
  const roleX = Math.round(width * 0.43)
  const skillAreaLeft = Math.round(width * 0.66)
  const skillX = skillAreaLeft + (width - skillAreaLeft) / 2
  const domainY = height / 2
  const initialCenter: [number, number] = [width / 2, height / 2]
  const roleIndexMap = new Map(roles.map((role, index) => [role.id, index]))
  const orderedSkills = [...skills]
    .map(skill => {
      const relatedIndexes = skill.roleIds
        .map(id => roleIndexMap.get(id))
        .filter((value): value is number => typeof value === 'number')
      const firstRoleIndex = relatedIndexes.length ? Math.min(...relatedIndexes) : Number.MAX_SAFE_INTEGER
      const avgRoleIndex = relatedIndexes.length
        ? relatedIndexes.reduce((sum, value) => sum + value, 0) / relatedIndexes.length
        : firstRoleIndex
      return { ...skill, firstRoleIndex, avgRoleIndex }
    })
    .sort((a, b) => a.firstRoleIndex - b.firstRoleIndex || a.avgRoleIndex - b.avgRoleIndex || b.total - a.total || a.name.localeCompare(b.name, 'zh-Hans-CN'))

  const totalDemand = Math.max(skills.reduce((sum, skill) => sum + skill.total, 0), 1)
  const nodes: any[] = []
  const links: any[] = []

  nodes.push({
    id: domain.id,
    name: domain.name,
    level: 1,
    value: domain.total,
    x: domainX,
    y: domainY,
    symbol: 'diamond',
    symbolSize: [domainWidth, domainHeight],
    draggable: true,
    itemStyle: {
      color: '#4A7DC8',
      borderColor: '#ffffff',
      borderWidth: 1.6,
      opacity: 1,
      shadowBlur: 14,
      shadowColor: 'rgba(74, 125, 200, 0.18)',
    },
    label: {
      show: true,
      position: 'inside',
      color: '#ffffff',
      fontSize: 14,
      fontWeight: 800,
      formatter: () => `${domain.name}\n${domain.roles.length.toLocaleString()} 岗`,
    },
    tooltip: {
      formatter: () => `${domain.name}<br/>岗位数量：${domain.roles.length.toLocaleString()}<br/>招聘总量：${domain.total.toLocaleString()}`,
    },
  })

  roles.forEach((role, index) => {
    const y = roleTop + index * metrics.roleStep
    const roleLinkWidth = 1.1 + 4 * Math.sqrt(role.total / Math.max(model.maxRoleTotal, 1))
    const isEmergingRole = normalizeEmergingScore(role.emergence) > EMERGING_THRESHOLD
    const emergingVisual = isEmergingRole ? getEmergingVisual(role.emergence) : null
    const roleColor = DOMAIN_COLORS[domain.name as DomainName] || '#66788B'

    nodes.push({
      id: role.id,
      name: role.name,
      level: 2,
      value: role.total,
      x: roleX,
      y,
      symbol: 'circle',
      symbolSize: [roleWidth, roleHeight],
      draggable: true,
      itemStyle: {
        color: roleGradient(roleColor),
        borderColor: emergingVisual ? emergingVisual.color : hexToRgba(roleColor, 0.88),
        borderWidth: emergingVisual ? emergingVisual.borderWidth : 1.8,
        borderType: 'solid',
        opacity: 1,
        shadowBlur: emergingVisual ? emergingVisual.shadowBlur : 8,
        shadowColor: emergingVisual ? emergingVisual.shadowColor : hexToRgba(roleColor, 0.12),
      },
      emphasis: emergingVisual ? {
        itemStyle: {
          borderColor: emergingVisual.color,
          borderWidth: emergingVisual.borderWidth + 0.7,
          shadowBlur: emergingVisual.shadowBlur + 6,
          shadowColor: emergingVisual.shadowColor,
        },
      } : undefined,
      label: {
        show: true,
        position: 'inside',
        color: '#344533',
        fontSize: 10.5,
        fontWeight: 700,
        lineHeight: 13,
        width: roleWidth - 16,
        overflow: 'break',
        formatter: () => `${splitLabel(role.name, Math.max(7, Math.floor((roleWidth - 24) / 11)))}\n（${role.total.toLocaleString()}）`,
      },
      tooltip: {
        formatter: () => `${role.name}<br/>岗位招聘次数：${role.total.toLocaleString()}<br/>新兴程度：${(normalizeEmergingScore(role.emergence) * 100).toFixed(1)}%`,
      },
    })

    links.push({
      source: domain.id,
      target: role.id,
      lineStyle: {
        color: '#6A8A9E',
        width: roleLinkWidth,
        opacity: 0.36,
        curveness: 0.04,
      },
    })
  })

  orderedSkills.forEach((skill, index) => {
    const y = skillTop + index * metrics.skillStep
    const skillLinkWeightMax = Math.max(
      ...roles
        .filter(role => role.skills.slice(0, 3).some(item => item.name === skill.name))
        .flatMap(role => role.skills.slice(0, 3).filter(item => item.name === skill.name).map(item => item.count)),
      1,
    )
    const pct = ((skill.total / totalDemand) * 100).toFixed(1)

    nodes.push({
      id: skill.id,
      name: skill.name,
      level: 3,
      value: skill.total,
      x: skillX,
      y,
      symbol: 'roundRect',
      symbolSize: [skillWidth, skillHeight],
      draggable: true,
      itemStyle: {
        color: skill.emergingTier > 0 ? emergingSkillGradient(getSkillEmergingVisual(skill.emergingTier).color) : '#D7F0DC',
        borderColor: skill.emergingTier > 0 ? getSkillEmergingVisual(skill.emergingTier).color : '#72B77A',
        borderWidth: skill.emergingTier > 0 ? getSkillEmergingVisual(skill.emergingTier).borderWidth : 1.2,
        opacity: 1,
        shadowBlur: skill.emergingTier > 0 ? getSkillEmergingVisual(skill.emergingTier).shadowBlur : 8,
        shadowColor: skill.emergingTier > 0 ? getSkillEmergingVisual(skill.emergingTier).shadowColor : 'rgba(86, 156, 96, 0.18)',
      },
      emphasis: skill.emergingTier > 0 ? {
        itemStyle: {
          borderColor: getSkillEmergingVisual(skill.emergingTier).color,
          borderWidth: getSkillEmergingVisual(skill.emergingTier).borderWidth + 0.45,
          shadowBlur: getSkillEmergingVisual(skill.emergingTier).shadowBlur + 5,
          shadowColor: getSkillEmergingVisual(skill.emergingTier).shadowColor,
        },
      } : undefined,
      label: {
        show: true,
        position: 'inside',
        color: skill.emergingTier > 0 ? '#3E4AA2' : '#2F6B3A',
        fontSize: 8.6,
        fontWeight: 700,
        lineHeight: 11,
        width: skillWidth - 14,
        overflow: 'truncate',
        formatter: () => `${skill.name} (${skill.total.toLocaleString()} | ${pct}%)`,
      },
      tooltip: {
        formatter: () => `${skill.name}<br/>技术栈被需求次数：${skill.total.toLocaleString()}<br/>占总技能需求：${pct}%${skill.emergingTier > 0 ? `<br/>新兴技能：${skill.emergingCategory}` : '<br/>普通技能栈'}`,
      },
    })

    roles.forEach(role => {
      const skillEntry = role.skills.slice(0, 3).find(item => item.name === skill.name)
      if (!skillEntry) return
      const linkWidth = 0.95 + 3.2 * Math.sqrt(skillEntry.count / skillLinkWeightMax)
      links.push({
        source: role.id,
        target: skill.id,
        lineStyle: {
          color: '#6A8A9E',
          width: linkWidth,
          opacity: 0.36,
          type: 'solid',
          curveness: 0.08,
        },
      })
    })
  })

  return {
    backgroundColor: '#F7F9FC',
    animation: false,
    animationDuration: 0,
    animationDurationUpdate: 0,
    tooltip: {
      trigger: 'item',
      confine: true,
      backgroundColor: 'rgba(23, 40, 58, 0.94)',
      borderWidth: 0,
      textStyle: { color: '#fff', fontSize: 11 },
    },
    series: [{
      type: 'graph',
      layout: 'none',
      roam: false,
      draggable: false,
      data: nodes,
      links,
      symbol: 'circle',
      edgeSymbol: ['none', 'none'],
      focusNodeAdjacency: true,
      center: initialCenter,
      zoom: 1,
      lineStyle: { color: '#6A8A9E', width: 1 },
      blur: {
        itemStyle: { opacity: 0.25 },
        lineStyle: { opacity: 0.06 },
      },
      emphasis: {
        focus: 'adjacency',
        scale: false,
        itemStyle: {
          borderColor: '#ffffff',
          borderWidth: 3,
          shadowBlur: 16,
        },
        lineStyle: {
          width: 2.4,
          opacity: 1,
        },
      },
    }],
  }
}

const buildFlowOption = () => {
  return buildThreeLayerOption() as any
}

const buildGraphOption = () => buildFlowOption() as any

const renderGraph = () => {
  if (!chartInstance) return
  const option = buildGraphOption() as any
  chartInstance.setOption(option, true)
}

const syncGraphSize = () => {
  if (!graphWrapRef.value) return
  const width = graphWrapRef.value.clientWidth
  const height = graphWrapRef.value.clientHeight
  if (graphSize.value.width === width && graphSize.value.height === height) return
  graphSize.value = { width, height }
}

const initChart = async () => {
  if (!chartRef.value) return
  if (chartInstance) {
    chartInstance.dispose()
  }
  chartInstance = echarts.init(chartRef.value)
  chartInstance.on('click', onNodeClick)
  await nextTick()
  renderGraph()
}

const resetView = () => {
  selectedNodeId.value = ''
  renderGraph()
}

const onNodeClick = (params: any) => {
  if (!params?.data?.id) return
  const id = params.data.id as string
  if (selectedNodeId.value === id) {
    resetView()
    return
  }
  selectedNodeId.value = id
  renderGraph()
}

const toggleEmergingOnly = () => {
  emergingOnly.value = !emergingOnly.value
  selectedNodeId.value = ''
  renderGraph()
}

const domainOverviewStats = computed<DetailStat[]>(() => {
  const visible = visibleModel.value
  const uniqueSkills = new Map<string, number>()
  visible.roles.forEach(role => {
    role.skills.forEach(skill => {
      uniqueSkills.set(skill.name, (uniqueSkills.get(skill.name) || 0) + skill.count)
    })
  })

  return [
    { label: '岗位数量', value: visible.roles.length.toLocaleString() },
    { label: '职位招聘人数', value: visible.visibleTotal.toLocaleString() },
    { label: '技术栈数', value: uniqueSkills.size.toLocaleString() },
    {
      label: '技术栈被需求次数',
      value: [...uniqueSkills.values()].reduce((sum, count) => sum + count, 0).toLocaleString(),
    },
  ]
})

const detail = computed(() => {
  const model = graphModel.value
  const visible = visibleModel.value
  const record = selectedRecord.value

  if (!record || (record as DomainNode).level === 1) {
    const topRoles = [...visible.roles]
      .sort((a, b) => b.total - a.total || b.emergence - a.emergence || a.name.localeCompare(b.name, 'zh-Hans-CN'))
      .slice(0, 12)
      .map(role => ({
        key: `overview-role-${role.id}`,
        name: role.name,
        value: role.total.toLocaleString(),
        meta: `新兴 ${role.emergence.toFixed(3)}`,
      }))

    const uniqueSkills = new Map<string, number>()
    visible.roles.forEach(role => {
      role.skills.forEach(skill => {
        uniqueSkills.set(skill.name, (uniqueSkills.get(skill.name) || 0) + skill.count)
      })
    })

    const topSkills = [...uniqueSkills.entries()]
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, 'zh-Hans-CN'))
      .slice(0, 12)
      .map((skill, index) => ({
        key: `overview-skill-${index}-${skill.name}`,
        name: skill.name,
        value: skill.count.toLocaleString(),
        meta: '领域汇总',
      }))

    return {
      badge: `${model.domain.name} · 圆环视图`,
      hint: '点击岗位节点查看岗位档案',
      title: model.domain.name,
      subtitle: `当前显示 ${visible.roles.length.toLocaleString()} 个岗位 / 领域共 ${model.domain.roles.length.toLocaleString()} 个岗位`,
      stats: domainOverviewStats.value,
      sections: [
        {
          title: '岗位概览',
          subtitle: '按招聘量排序',
          rows: topRoles,
          emptyText: '暂无岗位数据。',
        },
        {
          title: '技能概览',
          subtitle: '按需求次数排序',
          rows: topSkills,
          emptyText: '暂无技能数据。',
        },
      ] as DetailSection[],
      note: isRingMode.value
        ? '圆环越靠近中心，岗位招聘总量越高。'
        : '灰色连线表示领域、岗位和技术栈的对应关系。',
    }
  }

  if (record.level === 3) {
    const skill = record as FlowSkillNode
    const totalDemand = Math.max(visibleSkills.value.reduce((sum, item) => sum + item.total, 0), 1)
    const relatedRoles = visible.roles
      .filter(role => skill.roleIds.includes(role.id))
      .sort((a, b) => b.total - a.total || a.name.localeCompare(b.name, 'zh-Hans-CN'))
    const relatedRoleRows = relatedRoles.map(role => {
      const usage = role.skills.find(item => item.name === skill.name)?.count || 0
      return {
        key: `${skill.id}-${role.id}`,
        name: role.name,
        value: `${usage.toLocaleString()} 次`,
        meta: `岗位招聘量 ${role.total.toLocaleString()}`,
      }
    })

    return {
      badge: '技术栈画像',
      hint: `被需要 ${skill.total.toLocaleString()} 次`,
      title: skill.name,
      subtitle: `当前领域：${model.domain.name}`,
      stats: [
        { label: '被需要次数', value: skill.total.toLocaleString() },
        { label: '需求占比', value: `${((skill.total / totalDemand) * 100).toFixed(1)}%` },
        { label: '关联岗位', value: relatedRoles.length.toLocaleString() },
      ],
      sections: [
        {
          title: '关联岗位',
          subtitle: '技术栈需求次数 / 岗位招聘量',
          rows: relatedRoleRows,
          emptyText: '暂无关联岗位。',
        },
      ] as DetailSection[],
      note: '被需要次数为当前可视岗位中该技术栈需求次数的汇总；需求占比以当前可视技术栈总需求次数为基准。',
    }
  }

  const role = record as RoleNode
  const jobRows = role.jobs.map((job, index) => ({
    key: `${role.id}-job-${index}`,
    name: job.name,
    value: job.count.toLocaleString(),
    meta: '职位招聘人数',
  }))
  const skillRows = role.skills.map((skill, index) => ({
    key: `${role.id}-skill-${index}`,
    name: skill.name,
    value: skill.count.toLocaleString(),
    meta: '技术栈被需求次数',
  }))

  return {
    badge: '岗位档案',
    hint: `新兴程度 ${role.emergence.toFixed(4)}`,
    title: role.name,
    subtitle: `所属领域：${model.domain.name}`,
    stats: [
      { label: '新兴程度', value: role.emergence.toFixed(4) },
      { label: '职位数量', value: role.jobs.length.toLocaleString() },
      { label: '职位招聘人数', value: role.total.toLocaleString() },
      { label: '技术栈数', value: role.skills.length.toLocaleString() },
      {
        label: '技术栈被需求次数',
        value: role.skills.reduce((sum, item) => sum + item.count, 0).toLocaleString(),
      },
    ],
    sections: [
      {
        title: '职位样本',
        subtitle: '岗位下的职位名称与招聘人数',
        rows: jobRows,
        emptyText: '暂无职位数据。',
      },
      {
        title: '技术栈画像',
        subtitle: '岗位下的完整技术栈与需求次数',
        rows: skillRows,
        emptyText: '暂无技术栈数据。',
      },
    ] as DetailSection[],
    note: emergingOnly.value
      ? '当前仅显示新兴程度超过 20% 的岗位及其关联技术栈。'
      : '岗位按招聘人数降序排列；靛蓝描边表示新兴岗位，颜色越深新兴程度越高；普通技能栈使用绿色。',
  }
})

watch(
  () => selectedRangeKey.value,
  async () => {
    selectedNodeId.value = ''
    await nextTick()
    renderGraph()
  },
)

watch(
  () => props.domainName,
  async () => {
    selectedRangeKey.value = '0-10'
    emergingOnly.value = false
    selectedNodeId.value = ''
    await nextTick()
    renderGraph()
  },
)

watch(
  () => [graphSize.value.width, graphSize.value.height, canvasSize.value.width, canvasSize.value.height],
  async () => {
    await nextTick()
    chartInstance?.resize()
    renderGraph()
  },
)

onMounted(async () => {
  syncGraphSize()
  if (graphWrapRef.value && typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => {
      syncGraphSize()
    })
    resizeObserver.observe(graphWrapRef.value)
  }
  await nextTick()
  await initChart()
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
  if (chartInstance) {
    chartInstance.off('click', onNodeClick)
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.domain-root {
  width: 100%;
  height: 100%;
  min-height: 0;
}

.domain-shell {
  height: 100%;
  min-height: 0;
  display: flex;
  gap: 10px;
}

.domain-graph {
  position: relative;
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  border: 1px solid rgba(128, 149, 183, 0.14);
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 253, 0.98) 100%);
}

.domain-scroll-area {
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.domain-graph__spacer {
  width: 100%;
  flex: 0 0 auto;
}

.domain-canvas {
  position: relative;
}

.domain-chart {
  position: absolute;
  inset: 0;
}

.domain-legend {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 3;
  display: inline-flex;
  gap: 8px;
  flex-wrap: wrap;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(128, 149, 183, 0.12);
  box-shadow: 0 3px 12px rgba(28, 41, 61, 0.05);
  font-size: 11px;
  color: #52627a;
}

.domain-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.domain-swatch,
.domain-ring {
  flex: 0 0 auto;
}

.domain-swatch {
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

.domain-swatch--domain {
  background: #4a7dc8;
  transform: rotate(45deg);
}

.domain-swatch--role {
  width: 16px;
  height: 9px;
  border-radius: 5px;
  background: linear-gradient(135deg, #e7eef4 0%, #d1dee8 100%);
  border: 1px solid #3a5e82;
}

.domain-swatch--skill {
  width: 16px;
  height: 8px;
  border-radius: 999px;
  background: #d7f0dc;
  border: 1px solid #72b77a;
}

.domain-swatch--emerging {
  width: 16px;
  height: 8px;
  border-radius: 999px;
  background: linear-gradient(90deg, #aab6ff 0%, #7f91f2 33%, #5b6cd4 66%, #38479b 100%);
  box-shadow: 0 0 7px rgba(91, 108, 212, 0.28);
}

.domain-swatch--normal-skill {
  width: 16px;
  height: 8px;
  border-radius: 999px;
  background: #d7f0dc;
  border: 1px solid #72b77a;
}

.domain-line {
  width: 22px;
  height: 0;
  border-top: 2px solid #6a8a9e;
}

.domain-line--dashed {
  border-top-style: solid;
  border-top-color: #6a8a9e;
}

.domain-ring {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1.5px solid #9fb0c4;
}

.domain-legend__hint {
  color: #7a8aa1;
}

.domain-controls {
  position: absolute;
  top: 12px;
  right: 14px;
  z-index: 4;
  display: flex;
  align-items: center;
  gap: 8px;
}

.domain-select-wrap {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 30px;
  padding: 3px 6px 3px 9px;
  border: 1px solid rgba(128, 149, 183, 0.2);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 8px rgba(28, 41, 61, 0.05);
}

.domain-control-label {
  color: #7a8799;
  font-size: 11px;
  white-space: nowrap;
}

.domain-select {
  min-width: 72px;
  height: 24px;
  border: 0;
  outline: 0;
  background: transparent;
  color: #334155;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

.domain-emerging-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 11px;
  border: 1px solid rgba(128, 149, 183, 0.2);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.95);
  color: #64748b;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(28, 41, 61, 0.05);
  transition: all 0.16s ease;
}

.domain-emerging-toggle:hover {
  border-color: rgba(91, 108, 212, 0.58);
  color: #38479b;
}

.domain-emerging-toggle.active {
  border-color: rgba(91, 108, 212, 0.72);
  background: #eef0ff;
  color: #38479b;
  box-shadow: 0 4px 12px rgba(91, 108, 212, 0.16);
}

.domain-emerging-toggle__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #cbd5e1;
  box-shadow: 0 0 0 2px rgba(203, 213, 225, 0.25);
}

.domain-emerging-toggle.active .domain-emerging-toggle__dot {
  background: #5b6cd4;
  box-shadow: 0 0 6px rgba(91, 108, 212, 0.48);
}

.domain-filters {
  position: absolute;
  top: 52px;
  left: 12px;
  right: 12px;
  z-index: 3;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  align-items: center;
  max-height: none;
  overflow: hidden;
  pointer-events: none;
}

.domain-filter {
  pointer-events: auto;
  min-width: 48px;
  height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid rgba(128, 149, 183, 0.2);
  background: rgba(255, 255, 255, 0.92);
  color: #52627a;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(28, 41, 61, 0.05);
  transition: all 0.16s ease;
}

.domain-filter:hover {
  color: #3b6fa8;
  border-color: rgba(74, 125, 200, 0.38);
}

.domain-filter.active {
  color: #ffffff;
  border-color: transparent;
  background: linear-gradient(135deg, #3b6fa8 0%, #4a7dc8 100%);
  box-shadow: 0 5px 14px rgba(74, 125, 200, 0.20);
}

.domain-reset {
  position: absolute;
  left: 12px;
  bottom: 12px;
  z-index: 3;
  width: 34px;
  height: 34px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(128, 149, 183, 0.12);
  box-shadow: 0 2px 10px rgba(28, 41, 61, 0.06);
}

.domain-detail {
  width: 340px;
  min-width: 0;
  padding: 16px 15px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.97);
  border: 1px solid rgba(128, 149, 183, 0.14);
  box-shadow: 0 8px 20px rgba(28, 41, 61, 0.07);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.domain-detail__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  flex: 0 0 auto;
}

.domain-detail__badge {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  background: #ebf2ff;
  color: #3b6fa8;
  font-size: 12px;
  font-weight: 700;
}

.domain-detail__hint {
  margin-top: 6px;
  font-size: 11px;
  color: #7a8aa1;
}

.domain-detail__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-right: 4px;
  margin-top: 10px;
}

.domain-detail__body::-webkit-scrollbar {
  width: 10px;
}

.domain-detail__body::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.42);
  border-radius: 999px;
}

.domain-detail__body::-webkit-scrollbar-track {
  background: transparent;
}

.domain-detail__title {
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.2;
}

.domain-detail__subtitle {
  margin-top: 6px;
  font-size: 12px;
  color: #66758d;
}

.domain-detail__stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 12px;
}

.domain-stat {
  padding: 10px 10px 9px;
  border-radius: 10px;
  background: #f7f9fc;
  border: 1px solid rgba(153, 168, 187, 0.16);
}

.domain-stat__label {
  display: block;
  font-size: 11px;
  color: #718197;
  margin-bottom: 2px;
}

.domain-stat strong {
  font-size: 15px;
  color: #142033;
}

.domain-detail__section {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.domain-detail__section-head {
  margin-bottom: 8px;
}

.domain-detail__section-title {
  font-size: 12px;
  font-weight: 700;
  color: #0f172a;
}

.domain-detail__section-subtitle {
  margin-top: 3px;
  font-size: 11px;
  color: #7a8799;
}

.domain-detail__rows {
  display: grid;
  gap: 8px;
}

.domain-detail__row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #edf1f6;
}

.domain-detail__row-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1 1 auto;
}

.domain-detail__row-name {
  min-width: 0;
  color: #334155;
  font-size: 12px;
  overflow-wrap: anywhere;
}

.domain-detail__row-meta {
  font-size: 11px;
  color: #8a95a6;
}

.domain-detail__row-value {
  flex: 0 0 auto;
  color: #142033;
  font-size: 12px;
  white-space: nowrap;
}

.domain-detail__empty {
  padding: 10px 0;
  color: #7a8799;
  font-size: 12px;
}

.domain-detail__note {
  margin-top: 12px;
  padding-top: 10px;
  font-size: 11px;
  color: #7a8799;
  line-height: 1.5;
}

@media (max-width: 1200px) {
  .domain-shell {
    flex-direction: column;
  }

  .domain-detail {
    width: auto;
    min-height: 300px;
  }
}
</style>
