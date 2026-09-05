<!-- PATH2OFFER-PANORAMA-EMERGING-ROLE-SKILL-5LEVEL-20260904 -->
<template>
  <div class="panorama-root">
    <section class="panorama-toolbar" aria-label="全景图谱筛选器">
      <div class="panorama-toolbar__intro">
        <div class="panorama-toolbar__title-row">
          <div class="panorama-summary-pills">
            <span class="is-domain"><strong>{{ visibleStats.domainCount }}</strong> 领域</span>
            <span class="is-role"><strong>{{ visibleStats.roleCount }}</strong> 岗位</span>
            <span class="is-skill"><strong>{{ visibleStats.skillCount }}</strong> 技能</span>
            <span class="is-emerging"><strong>{{ visibleStats.emergingRoleCount }}</strong> 新兴岗<em>·</em><strong>{{ visibleStats.emergingSkillCount }}</strong> 新兴技</span>
          </div>
        </div>
      </div>

      <div class="panorama-filter-grid">
        <label class="panorama-control panorama-control--search">
          <span class="panorama-control__label">节点搜索</span>
          <span class="panorama-search-box">
            <el-icon><Search /></el-icon>
            <input
              v-model.trim="searchKeyword"
              type="text"
              placeholder="输入岗位或技能，回车高亮"
              @keyup.enter="focusSearchResult"
            />
            <button v-if="searchKeyword" type="button" @click="clearSearch">清除</button>
          </span>
        </label>

        <label class="panorama-control">
          <span class="panorama-control__label">岗位数量</span>
          <div class="panorama-select-shell">
            <el-select
              v-model="roleLimit"
              class="panorama-tech-select"
              popper-class="panorama-premium-popper"
              aria-label="岗位数量"
            >
              <el-option
                v-for="option in ROLE_LIMIT_OPTIONS"
                :key="`role-limit-${option}`"
                :label="getRoleLimitLabel(option)"
                :value="option"
              />
            </el-select>
          </div>
        </label>

        <label class="panorama-control">
          <span class="panorama-control__label">岗位招聘数</span>
          <div class="panorama-select-shell">
            <el-select
              v-model="minRoleCount"
              class="panorama-tech-select"
              popper-class="panorama-premium-popper"
              aria-label="岗位招聘数"
            >
              <el-option label="≥ 2" :value="2" />
              <el-option label="≥ 3" :value="3" />
              <el-option label="≥ 5" :value="5" />
              <el-option label="≥ 10" :value="10" />
              <el-option label="≥ 20" :value="20" />
            </el-select>
          </div>
        </label>

        <label class="panorama-control">
          <span class="panorama-control__label">技能数量</span>
          <div class="panorama-select-shell">
            <el-select
              v-model="skillLimit"
              class="panorama-tech-select"
              popper-class="panorama-premium-popper"
              aria-label="技能数量"
            >
              <el-option label="Top 24" :value="24" />
              <el-option label="Top 36" :value="36" />
              <el-option label="Top 60" :value="60" />
              <el-option label="Top 100" :value="100" />
              <el-option label="Top 160" :value="160" />
              <el-option label="全部技能" :value="0" />
            </el-select>
          </div>
        </label>

        <label class="panorama-control">
          <span class="panorama-control__label">技能需求数</span>
          <div class="panorama-select-shell">
            <el-select
              v-model="minSkillCount"
              class="panorama-tech-select"
              popper-class="panorama-premium-popper"
              aria-label="技能需求数"
            >
              <el-option label="≥ 2" :value="2" />
              <el-option label="≥ 5" :value="5" />
              <el-option label="≥ 10" :value="10" />
              <el-option label="≥ 20" :value="20" />
              <el-option label="≥ 40" :value="40" />
            </el-select>
          </div>
        </label>



      </div>

      <div class="panorama-toolbar__footer">
        <div class="panorama-domain-filters" aria-label="领域筛选">
          <button
            v-for="domain in graphModel.domains"
            :key="domain.id"
            type="button"
            class="panorama-domain-filter"
            :class="{ 'is-active': activeDomainNames.has(domain.name) }"
            :style="{ '--domain-color': getDomainColor(domain.name) }"
            @click="toggleDomain(domain.name)"
          >
            <i></i>{{ domain.name }}
          </button>
        </div>

        <div class="panorama-legend">
          <span><i class="legend-dot legend-dot--domain"></i>领域</span>
          <span><i class="legend-dot legend-dot--role"></i>岗位</span>
          <span><i class="legend-dot legend-dot--skill"></i>技能栈</span>
          <span
            class="panorama-legend__emerging"
            :title="`新兴岗位：新兴程度 > ${emergingThresholdLabel}；新兴技能：命中技能库“近年新兴/前沿探索”，前沿探索优先使用更深色；颜色越深表示新兴程度越高`"
          >
            <span class="emerging-mini-scale" aria-hidden="true">
              <i
                v-for="level in emergingLegendLevels"
                :key="level.key"
                :style="{ background: level.color }"
                :title="`${level.label}：${level.levelName}新兴度`"
                :aria-label="`${level.label}：${level.levelName}新兴度`"
              ></i>
            </span>
            <small><b>新兴标注</b> · 岗位 &gt;{{ emergingThresholdLabel }}（每 20 分一档）/ 技能按词库 · 越深越新兴</small>
          </span>
        </div>

        <div class="panorama-toolbar__actions">
          <button type="button" class="panorama-reset-filter is-secondary" @click="resetView">
            <el-icon><RefreshLeft /></el-icon>重置视图
          </button>
          <button type="button" class="panorama-reset-filter" @click="resetFilters">
            <el-icon><RefreshLeft /></el-icon>重置筛选
          </button>
        </div>
      </div>
    </section>

    <div class="panorama-shell">
      <div ref="scrollRef" class="panorama-stage">
        <div class="panorama-stage__backdrop" aria-hidden="true">
          <span class="panorama-orbit panorama-orbit--a"></span>
          <span class="panorama-orbit panorama-orbit--b"></span>
          <span class="panorama-grid-glow"></span>
        </div>

        <div ref="chartRef" class="panorama-chart"></div>

        <div class="panorama-stage__status">
          <span>滚轮缩放 · 拖拽平移 · 双击清除高亮</span>
          <strong>{{ visibleStats.linkCount.toLocaleString() }} 条可视关系</strong>
        </div>

        <div class="panorama-zoom-controls" aria-label="图谱缩放">
          <button type="button" title="缩小" aria-label="缩小" @click="changeZoom(-1)">
            <el-icon><Minus /></el-icon>
          </button>
          <button type="button" title="放大" aria-label="放大" @click="changeZoom(1)">
            <el-icon><Plus /></el-icon>
          </button>
          <button type="button" title="重置视图" aria-label="重置视图" @click="resetView">
            <el-icon><RefreshLeft /></el-icon>
          </button>
        </div>
      </div>

      <aside class="panorama-detail" :class="{ 'is-collapsed': detailCollapsed }">
        <template v-if="detailCollapsed">
          <button
            type="button"
            class="panorama-detail__collapsed-toggle"
            title="展开详情"
            aria-label="展开详情"
            @click="detailCollapsed = false"
          >
            <el-icon><ArrowLeft /></el-icon>
          </button>
        </template>

        <template v-else>
          <header class="panorama-detail__head">
            <div>
              <div class="panorama-detail__badge" :class="`is-level-${detail.level}`">{{ detail.badge }}</div>
              <div class="panorama-detail__title">{{ detail.title }}</div>
              <div class="panorama-detail__subtitle">{{ detail.subtitle }}</div>
            </div>
            <button type="button" class="panorama-icon-button" title="收起详情" @click="detailCollapsed = true">
              <el-icon><ArrowRight /></el-icon>
            </button>
          </header>

          <div class="panorama-detail__stats">
            <div v-for="stat in detail.stats" :key="stat.label" class="panorama-stat">
              <span>{{ stat.label }}</span>
              <strong>{{ stat.value }}</strong>
            </div>
          </div>

          <section v-if="detail.rows.length" class="panorama-detail__section">
            <div class="panorama-detail__section-head">
              <span>{{ detail.listTitle }}</span>
              <small>{{ detail.listHint }}</small>
            </div>
            <div class="panorama-detail__rows">
              <button
                v-for="row in detail.rows"
                :key="row.key"
                type="button"
                class="panorama-detail__row"
                @click="selectNode(row.nodeId)"
              >
                <span class="panorama-detail__row-name">{{ row.name }}</span>
                <span class="panorama-detail__bar"><i :style="{ width: `${row.percent}%` }"></i></span>
                <strong>{{ row.value }}</strong>
              </button>
            </div>
          </section>

          <section v-else class="panorama-detail__section panorama-detail__guide">
            <div class="panorama-detail__section-head"><span>图谱阅读方式</span></div>
            <div class="panorama-guide-item"><b>01</b><span>领域是一级锚点，使用低饱和矿物色建立稳定语义。</span></div>
            <div class="panorama-guide-item"><b>02</b><span>岗位是二级节点，文字内嵌圆形节点，避免标签与圆圈错位。</span></div>
            <div class="panorama-guide-item"><b>03</b><span>技能栈集中在中部技能场，统一使用独立矿物青与胶囊节点。</span></div>
            <div class="panorama-guide-item"><b>04</b><span>默认控制节点规模与关系密度，减少交叉并保持足够留白。</span></div>
          </section>

          <footer class="panorama-detail__footer">
            <span>当前筛选</span>
            <strong>{{ filterSummary }}</strong>
          </footer>
        </template>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { ArrowLeft, ArrowRight, Minus, Plus, RefreshLeft, Search } from '@element-plus/icons-vue'
import domainPositionData from '../../../backend/graph_base_data/domain_position.json'
import skillLexiconData from "../../../backend/app/skill_lexicon.json";

const props = withDefaults(defineProps<{ emergingThreshold?: number }>(), {
  emergingThreshold: 20,
})

type LayoutMode = 'orbit' | 'petal' | 'cluster'
type LabelDensity = 'sparse' | 'balanced' | 'all'
type NodeRecord = DomainNode | RoleNode | SkillNode

interface RoleSkillRef {
  skillId: string
  name: string
  count: number
}

interface RoleNode {
  id: string
  name: string
  total: number
  domainId: string
  domainName: string
  allSkills: RoleSkillRef[]
  emergingScore: number
  level: 2
}

interface DomainNode {
  id: string
  name: string
  total: number
  roles: RoleNode[]
  level: 1
}

interface SkillNode {
  id: string
  name: string
  count: number
  roleIds: string[]
  roleNames: string[]
  domainIds: string[]
  primaryDomainId: string
  primaryDomainName: string
  emergingTier: number
  emergingCategory: '' | '近年新兴' | '前沿探索'
  emergingWeight: '' | '强新兴' | '弱新兴'
  level: 3
}

interface GraphModel {
  domains: DomainNode[]
  roles: RoleNode[]
  skills: SkillNode[]
  nodeLookup: Map<string, NodeRecord>
  maxRoleTotal: number
  maxSkillTotal: number
}

interface VisibleGraph {
  domains: DomainNode[]
  roles: RoleNode[]
  skills: SkillNode[]
  roleIdSet: Set<string>
  skillIdSet: Set<string>
}

interface DetailRow {
  key: string
  nodeId: string
  name: string
  value: string
  percent: number
}

const DOMAIN_ORDER = ['人工智能', '智能系统', '物联网', '大数据'] as const
const DOMAIN_COLORS: Record<string, string> = {
  人工智能: '#3A5E82',
  智能系统: '#3E716F',
  物联网: '#9A704A',
  大数据: '#665F84',
}
const SKILL_DARK = '#245F6D'
const ROLE_FALLBACK_COLOR = '#66788B'
const rawDomains = Array.isArray(domainPositionData) ? (domainPositionData as any[]) : []
const rawSkillLexicon = (skillLexiconData || {}) as Record<string, any>

const normalizeSkillKey = (value: unknown) =>
  typeof value === 'string'
    ? value.trim().replace(/\s+/g, ' ').toLocaleLowerCase()
    : ''

const makeSkillSet = (value: unknown) =>
  new Set(
    (Array.isArray(value) ? value : [])
      .map(normalizeSkillKey)
      .filter(Boolean),
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

  if (isFrontier) {
    return {
      tier: isStrong ? 5 : 4,
      category: '前沿探索' as const,
      weight: isStrong ? '强新兴' as const : isWeak ? '弱新兴' as const : '',
    }
  }

  if (isRecent) {
    return {
      tier: isStrong ? 3 : isWeak ? 1 : 2,
      category: '近年新兴' as const,
      weight: isStrong ? '强新兴' as const : isWeak ? '弱新兴' as const : '',
    }
  }

  return {
    tier: 0,
    category: '' as const,
    weight: '' as const,
  }
}

const normalizeCount = (value: unknown) => {
  if (typeof value === 'number') return Number.isFinite(value) ? value : 0
  if (typeof value === 'string') return Number(value) || 0
  return 0
}

const safeName = (value: unknown, fallback = '') => {
  const text = typeof value === 'string' ? value.trim() : ''
  return text || fallback
}

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max)

const normalizeEmergingScore = (value: unknown) => {
  const raw = normalizeCount(value)
  if (raw <= 0) return 0
  return clamp(raw > 1 ? raw / 100 : raw, 0, 1)
}

const emergingThresholdNormalized = computed(() =>
  normalizeEmergingScore(props.emergingThreshold),
)

const emergingThresholdLabel = computed(() => {
  const value = emergingThresholdNormalized.value * 100
  return Number.isInteger(value) ? `${value.toFixed(0)}` : `${value.toFixed(1)}`
})

const isEmergingRole = (role: RoleNode) =>
  role.emergingScore > emergingThresholdNormalized.value

const formatEmergingScore = (score: number) => {
  const value = normalizeEmergingScore(score) * 100
  return Number.isInteger(value) ? `${value.toFixed(0)}` : `${value.toFixed(1)}`
}

// 新兴岗位统一使用与系统主色一致的靛蓝同色系。
// 超过 20% 后每 20 分进入下一档，颜色越深表示新兴程度越高。
// 同一个分值无论如何切换筛选，始终对应同一档颜色。
const EMERGING_LEVEL_COLORS = [
  '#AAB6FF',
  '#7F91F2',
  '#5B6CD4',
  '#38479B',
] as const

const EMERGING_LEVEL_NAMES = ['低', '中', '高', '极高'] as const

const emergingLegendLevels = computed(() => {
  const threshold = emergingThresholdNormalized.value * 100
  const step = 20
  return EMERGING_LEVEL_COLORS.map((color, index) => {
    const min = threshold + index * step
    const max = index === EMERGING_LEVEL_COLORS.length - 1
      ? 100
      : Math.min(threshold + (index + 1) * step, 100)
    const formatBoundary = (value: number) =>
      Number.isInteger(value) ? `${value.toFixed(0)}` : `${value.toFixed(1)}`
    return {
      key: `emerging-${index}`,
      index,
      color,
      glow: hexToRgba(color, 0.18 + index * 0.035),
      levelName: EMERGING_LEVEL_NAMES[index]!,
      min,
      max,
      label: index === EMERGING_LEVEL_COLORS.length - 1
        ? `${formatBoundary(min)}+`
        : `${formatBoundary(min)}–${formatBoundary(max)}`,
    }
  })
})

const getEmergingLevel = (score: number) => {
  const percent = normalizeEmergingScore(score) * 100
  const levels = emergingLegendLevels.value
  const index = clamp(
    Math.floor((percent - emergingThresholdNormalized.value * 100) / 20),
    0,
    levels.length - 1,
  )
  return levels[index] ?? levels[levels.length - 1]!
}

const hexToRgba = (hex: string, alpha: number) => {
  const normalized = hex.replace('#', '')
  const value = Number.parseInt(normalized, 16)
  const r = (value >> 16) & 255
  const g = (value >> 8) & 255
  const b = value & 255
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

const lighten = (hex: string, amount: number) => {
  const normalized = hex.replace('#', '')
  const value = Number.parseInt(normalized, 16)
  const ratio = clamp(amount, 0, 1)
  const r = Math.round(((value >> 16) & 255) * (1 - ratio) + 255 * ratio)
  const g = Math.round(((value >> 8) & 255) * (1 - ratio) + 255 * ratio)
  const b = Math.round((value & 255) * (1 - ratio) + 255 * ratio)
  return `rgb(${r}, ${g}, ${b})`
}

const getEmergingVisual = (score: number) => {
  const level = getEmergingLevel(score)
  const depth = level.index / Math.max(EMERGING_LEVEL_COLORS.length - 1, 1)
  return {
    color: level.color,
    levelName: level.levelName,
    rangeLabel: level.label,
    shadowColor: hexToRgba(level.color, 0.30 + depth * 0.18),
    shadowBlur: 11 + level.index * 3.2,
    borderWidth: 2.6 + level.index * 0.32,
  }
}

const isEmergingSkill = (skill: SkillNode) => skill.emergingTier > 0

const getSkillEmergingVisual = (skill: SkillNode) => {
  const index = clamp(
    Math.round(skill.emergingTier) - 1,
    0,
    EMERGING_LEVEL_COLORS.length - 1,
  )
  const color = EMERGING_LEVEL_COLORS[index]!
  const depth = index / Math.max(EMERGING_LEVEL_COLORS.length - 1, 1)
  return {
    color,
    levelName: EMERGING_LEVEL_NAMES[index]!,
    shadowColor: hexToRgba(color, 0.28 + depth * 0.18),
    shadowBlur: 9 + index * 2.6,
    borderWidth: 1.55 + index * 0.24,
  }
}

const shortText = (text: string, max: number) => {
  if (text.length <= max) return text
  return `${text.slice(0, Math.max(2, max - 1))}…`
}

const getDomainColor = (name: string) => DOMAIN_COLORS[name] || ROLE_FALLBACK_COLOR

const buildGraphModel = (): GraphModel => {
  const domains: DomainNode[] = []
  const roles: RoleNode[] = []
  const nodeLookup = new Map<string, NodeRecord>()
  const globalSkillMap = new Map<string, {
    count: number
    roleIds: Set<string>
    roleNames: Set<string>
    domainCounts: Map<string, number>
  }>()

  DOMAIN_ORDER.forEach((domainName, domainIndex) => {
    const rawDomain = rawDomains.find(item => safeName(item?.领域) === domainName)
    const roleMap = new Map<string, { total: number; skills: Map<string, number>; emergingScore: number }>()
    const rawRoles = Array.isArray(rawDomain?.岗位) ? rawDomain.岗位 : []

    rawRoles.forEach((rawRole: any) => {
      const roleName = safeName(rawRole?.岗位名称)
      if (!roleName) return
      const entry = roleMap.get(roleName) || { total: 0, skills: new Map<string, number>(), emergingScore: 0 }
      entry.total += normalizeCount(rawRole?.职位数量)
      entry.emergingScore = Math.max(entry.emergingScore, normalizeEmergingScore(rawRole?.新兴程度))
      const rawSkills = Array.isArray(rawRole?.技术栈) ? rawRole.技术栈 : []
      rawSkills.forEach((rawSkill: any) => {
        const skillName = safeName(rawSkill?.所需技术)
        const count = normalizeCount(rawSkill?.被需要次数)
        if (!skillName || count <= 0) return
        entry.skills.set(skillName, (entry.skills.get(skillName) || 0) + count)
      })
      roleMap.set(roleName, entry)
    })

    const domainId = `domain-${domainIndex}`
    const domainRoles = [...roleMap.entries()]
      .map(([name, entry], roleIndex) => {
        const roleId = `role-${domainIndex}-${roleIndex}`
        const allSkills = [...entry.skills.entries()]
          .map(([skillName, count]) => ({ skillId: '', name: skillName, count }))
          .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, 'zh-Hans-CN'))
        const role: RoleNode = {
          id: roleId,
          name,
          total: entry.total,
          domainId,
          domainName,
          allSkills,
          emergingScore: entry.emergingScore,
          level: 2,
        }
        return role
      })
      .filter(role => role.total > 0)
      .sort((a, b) => b.total - a.total || a.name.localeCompare(b.name, 'zh-Hans-CN'))

    domainRoles.forEach((role, roleIndex) => {
      role.id = `role-${domainIndex}-${roleIndex}`
      roles.push(role)
      nodeLookup.set(role.id, role)
      role.allSkills.forEach(skill => {
        const entry = globalSkillMap.get(skill.name) || {
          count: 0,
          roleIds: new Set<string>(),
          roleNames: new Set<string>(),
          domainCounts: new Map<string, number>(),
        }
        entry.count += skill.count
        entry.roleIds.add(role.id)
        entry.roleNames.add(role.name)
        entry.domainCounts.set(domainId, (entry.domainCounts.get(domainId) || 0) + skill.count)
        globalSkillMap.set(skill.name, entry)
      })
    })

    const domain: DomainNode = {
      id: domainId,
      name: domainName,
      total: domainRoles.reduce((sum, role) => sum + role.total, 0),
      roles: domainRoles,
      level: 1,
    }
    domains.push(domain)
    nodeLookup.set(domain.id, domain)
  })

  const skills = [...globalSkillMap.entries()]
    .sort((a, b) => b[1].count - a[1].count || a[0].localeCompare(b[0], 'zh-Hans-CN'))
    .map(([name, entry], index) => {
      const primary = [...entry.domainCounts.entries()].sort((a, b) => b[1] - a[1])[0]
      const primaryDomainId = primary?.[0] || domains[0]?.id || ''
      const primaryDomainName = domains.find(domain => domain.id === primaryDomainId)?.name || ''
      const emergingMeta = getSkillEmergingMeta(name)
      const skill: SkillNode = {
        id: `skill-${index}`,
        name,
        count: entry.count,
        roleIds: [...entry.roleIds],
        roleNames: [...entry.roleNames],
        domainIds: [...entry.domainCounts.keys()],
        primaryDomainId,
        primaryDomainName,
        emergingTier: emergingMeta.tier,
        emergingCategory: emergingMeta.category,
        emergingWeight: emergingMeta.weight,
        level: 3,
      }
      nodeLookup.set(skill.id, skill)
      return skill
    })

  const skillIdByName = new Map(skills.map(skill => [skill.name, skill.id]))
  roles.forEach(role => {
    role.allSkills = role.allSkills.map(skill => ({
      ...skill,
      skillId: skillIdByName.get(skill.name) || '',
    }))
  })

  return {
    domains,
    roles,
    skills,
    nodeLookup,
    maxRoleTotal: Math.max(...roles.map(role => role.total), 1),
    maxSkillTotal: Math.max(...skills.map(skill => skill.count), 1),
  }
}

const graphModel = buildGraphModel()

// 完整图谱的全局稳定索引。
// 筛选时只隐藏节点，不重新给剩余节点编号，因此坐标不会洗牌。
const fullSkillIndexById = new Map(
  graphModel.skills.map((skill, index) => [skill.id, index]),
)
const fullRolePlacementById = new Map<string, { domainIndex: number; localIndex: number; count: number }>()
graphModel.domains.forEach((domain, domainIndex) => {
  domain.roles.forEach((role, localIndex) => {
    fullRolePlacementById.set(role.id, {
      domainIndex,
      localIndex,
      count: domain.roles.length,
    })
  })
})
const DEFAULT_MIN_ROLE_COUNT = 2
const FULL_ROLE_COUNT = graphModel.roles.filter(role => role.total >= DEFAULT_MIN_ROLE_COUNT).length
const ROLE_LIMIT_OPTIONS = (() => {
  if (FULL_ROLE_COUNT <= 0) return [0]
  const options: number[] = []
  for (let value = 25; value < FULL_ROLE_COUNT; value += 25) options.push(value)
  options.push(0)
  return options
})()
const DEFAULT_ROLE_LIMIT = 50
const scrollRef = ref<HTMLDivElement | null>(null)
const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null
let resizeObserver: ResizeObserver | null = null

const viewportSize = ref({ width: 1200, height: 720 })
const selectedNodeId = ref('')
const searchKeyword = ref('')
const roleLimit = ref(DEFAULT_ROLE_LIMIT)
const minRoleCount = ref(DEFAULT_MIN_ROLE_COUNT)
const skillLimit = ref(100)
const minSkillCount = ref(2)
const labelDensity = ref<LabelDensity>('all')
const skillsPerRole = ref(5)
const layoutMode = ref<LayoutMode>('orbit')
const DEFAULT_GRAPH_ZOOM = 1
const detailCollapsed = ref(true)
const activeDomainNames = ref(new Set<string>(DOMAIN_ORDER))

const visibleGraph = computed<VisibleGraph>(() => {
  const domains = graphModel.domains.filter(domain => activeDomainNames.value.has(domain.name))
  const domainIds = new Set(domains.map(domain => domain.id))
  let roles = graphModel.roles
    .filter(role => domainIds.has(role.domainId) && role.total >= minRoleCount.value)
    .sort((a, b) => b.total - a.total || a.name.localeCompare(b.name, 'zh-Hans-CN'))

  if (roleLimit.value > 0) roles = roles.slice(0, roleLimit.value)
  const roleIdSet = new Set(roles.map(role => role.id))

  // 技能需求数按“当前可见岗位覆盖数”计算：
  // 一个技能被多少个当前可见岗位使用，就记为多少次需求。
  // 这样 ≥2 / ≥5 / ≥10 / ≥20 / ≥40 会真正随岗位筛选联动。
  const visibleSkillDemandCount = new Map<string, number>()
  roles.forEach(role => {
    const seenSkillIds = new Set<string>()
    role.allSkills.forEach(skill => {
      if (!skill.skillId || seenSkillIds.has(skill.skillId)) return
      seenSkillIds.add(skill.skillId)
      visibleSkillDemandCount.set(
        skill.skillId,
        (visibleSkillDemandCount.get(skill.skillId) || 0) + 1,
      )
    })
  })

  let skills = graphModel.skills
    .filter(skill => (visibleSkillDemandCount.get(skill.id) || 0) >= minSkillCount.value)
    .sort((a, b) => {
      const demandDiff =
        (visibleSkillDemandCount.get(b.id) || 0) -
        (visibleSkillDemandCount.get(a.id) || 0)
      if (demandDiff !== 0) return demandDiff
      return b.count - a.count || a.name.localeCompare(b.name, 'zh-Hans-CN')
    })

  if (skillLimit.value > 0) skills = skills.slice(0, skillLimit.value)
  const skillIdSet = new Set(skills.map(skill => skill.id))

  return { domains, roles, skills, roleIdSet, skillIdSet }
})

const visibleStats = computed(() => {
  const graph = visibleGraph.value
  let linkCount = graph.roles.length
  graph.roles.forEach(role => {
    linkCount += role.allSkills
      .slice(0, skillsPerRole.value)
      .filter(skill => graph.skillIdSet.has(skill.skillId)).length
  })
  return {
    domainCount: graph.domains.length,
    roleCount: graph.roles.length,
    skillCount: graph.skills.length,
    emergingRoleCount: graph.roles.filter(isEmergingRole).length,
    emergingSkillCount: graph.skills.filter(isEmergingSkill).length,
    linkCount,
  }
})

const formatLimitText = (value: number, unit: string) => value > 0 ? `Top ${value}` : `全部${unit}`
const getRoleLimitLabel = (value: number) => value > 0 ? `Top ${value}` : `全部岗位（${FULL_ROLE_COUNT}）`

const filterSummary = computed(() => {
  const roleText = formatLimitText(roleLimit.value, '岗位')
  const skillText = formatLimitText(skillLimit.value, '技能')
  return `岗位 ${roleText} / ≥${minRoleCount.value}；技能 ${skillText} / ≥${minSkillCount.value}`
})

const selectedRecord = computed<NodeRecord | null>(() => {
  if (!selectedNodeId.value) return null
  return graphModel.nodeLookup.get(selectedNodeId.value) || null
})

const selectionSet = computed<Set<string> | null>(() => {
  const record = selectedRecord.value
  if (!record) return null
  const ids = new Set<string>([record.id])

  if (record.level === 1) {
    visibleGraph.value.roles.filter(role => role.domainId === record.id).forEach(role => {
      ids.add(role.id)
      role.allSkills.slice(0, skillsPerRole.value).forEach(skill => {
        if (visibleGraph.value.skillIdSet.has(skill.skillId)) ids.add(skill.skillId)
      })
    })
  } else if (record.level === 2) {
    ids.add(record.domainId)
    record.allSkills.slice(0, skillsPerRole.value).forEach(skill => {
      if (visibleGraph.value.skillIdSet.has(skill.skillId)) ids.add(skill.skillId)
    })
  } else {
    record.roleIds.filter(roleId => visibleGraph.value.roleIdSet.has(roleId)).forEach(roleId => {
      ids.add(roleId)
      const role = graphModel.nodeLookup.get(roleId)
      if (role?.level === 2) ids.add(role.domainId)
    })
  }

  return ids
})

const toRows = (items: Array<{ key: string; nodeId: string; name: string; count: number }>): DetailRow[] => {
  const max = Math.max(...items.map(item => item.count), 1)
  return items.map(item => ({
    key: item.key,
    nodeId: item.nodeId,
    name: item.name,
    value: item.count.toLocaleString(),
    percent: clamp(Math.round((item.count / max) * 100), 8, 100),
  }))
}

const detail = computed(() => {
  const record = selectedRecord.value
  if (!record) {
    return {
      level: 0,
      badge: '全景总览',
      title: '从层级关系中读懂岗位结构',
      subtitle: '点击节点查看其上下游关系；筛选器只影响可视层，不会修改原始数据。',
      stats: [
        { label: '领域', value: visibleStats.value.domainCount.toLocaleString() },
        { label: '岗位', value: visibleStats.value.roleCount.toLocaleString() },
        { label: '技能', value: visibleStats.value.skillCount.toLocaleString() },
      ],
      listTitle: '',
      listHint: '',
      rows: [] as DetailRow[],
    }
  }

  if (record.level === 1) {
    const visibleRoles = visibleGraph.value.roles.filter(role => role.domainId === record.id)
    const rows = toRows(visibleRoles.slice(0, 8).map(role => ({
      key: role.id,
      nodeId: role.id,
      name: role.name,
      count: role.total,
    })))
    return {
      level: 1,
      badge: '一级 · 领域',
      title: record.name,
      subtitle: '领域节点聚合其下岗位招聘规模，并作为岗位层的视觉锚点。',
      stats: [
        { label: '招聘量', value: record.total.toLocaleString() },
        { label: '可视岗位', value: visibleRoles.length.toLocaleString() },
        { label: '领域占比', value: `${Math.round((record.total / Math.max(graphModel.domains.reduce((s, d) => s + d.total, 0), 1)) * 100)}%` },
      ],
      listTitle: '热门岗位',
      listHint: '点击可继续下钻',
      rows,
    }
  }

  if (record.level === 2) {
    const rows = toRows(record.allSkills
      .filter(skill => visibleGraph.value.skillIdSet.has(skill.skillId))
      .slice(0, 10)
      .map(skill => ({ key: skill.skillId, nodeId: skill.skillId, name: skill.name, count: skill.count })))
    const emerging = isEmergingRole(record)
    const emergingScore = formatEmergingScore(record.emergingScore)
    const emergingVisual = emerging ? getEmergingVisual(record.emergingScore) : null
    return {
      level: 2,
      badge: emerging ? `二级 · ${emergingVisual?.levelName}新兴度` : '二级 · 岗位',
      title: record.name,
      subtitle: `所属领域：${record.domainName} · 新兴程度 ${emergingScore}`,
      stats: [
        { label: '招聘量', value: record.total.toLocaleString() },
        { label: '技能总数', value: record.allSkills.length.toLocaleString() },
        {
          label: '新兴程度',
          value: emerging
            ? `${emergingScore} · ${emergingVisual?.levelName}（${emergingVisual?.rangeLabel}）`
            : emergingScore,
        },
      ],
      listTitle: '核心技能栈',
      listHint: '按需求次数排序',
      rows,
    }
  }

  const visibleRoles = record.roleIds
    .filter(roleId => visibleGraph.value.roleIdSet.has(roleId))
    .map(roleId => graphModel.nodeLookup.get(roleId))
    .filter((node): node is RoleNode => Boolean(node && node.level === 2))
    .sort((a, b) => b.total - a.total)
  const rows = toRows(visibleRoles.slice(0, 10).map(role => ({
    key: role.id,
    nodeId: role.id,
    name: role.name,
    count: role.total,
  })))
  const emergingSkill = isEmergingSkill(record)
  const skillVisual = emergingSkill ? getSkillEmergingVisual(record) : null
  const skillEmergingText = emergingSkill
    ? `${record.emergingCategory}${record.emergingWeight ? ` · ${record.emergingWeight}` : ''}`
    : '传统 / 主流技能'

  return {
    level: 3,
    badge: emergingSkill ? `三级 · ${skillVisual?.levelName}新兴技能` : '三级 · 技能栈',
    title: record.name,
    subtitle: `主要归属：${record.primaryDomainName || '跨领域技能'}${emergingSkill ? ` · ${skillEmergingText}` : ''}`,
    stats: [
      { label: '需求次数', value: record.count.toLocaleString() },
      { label: '关联岗位', value: record.roleIds.length.toLocaleString() },
      { label: '技能层级', value: skillEmergingText },
    ],
    listTitle: '关联岗位',
    listHint: '按岗位招聘量排序',
    rows,
  }
})

const toggleDomain = (name: string) => {
  const next = new Set(activeDomainNames.value)
  if (next.has(name)) {
    if (next.size === 1) return
    next.delete(name)
  } else {
    next.add(name)
  }
  activeDomainNames.value = next
  selectedNodeId.value = ''
}

const resetFilters = () => {
  activeDomainNames.value = new Set<string>(DOMAIN_ORDER)
  roleLimit.value = DEFAULT_ROLE_LIMIT
  minRoleCount.value = DEFAULT_MIN_ROLE_COUNT
  skillLimit.value = 100
  minSkillCount.value = 2
  labelDensity.value = 'all'
  skillsPerRole.value = 5
  layoutMode.value = 'orbit'
  searchKeyword.value = ''
  selectedNodeId.value = ''
  resetView()
}

const clearSearch = () => {
  searchKeyword.value = ''
  selectedNodeId.value = ''
  renderGraph()
}

const focusSearchResult = () => {
  const keyword = searchKeyword.value.toLowerCase()
  if (!keyword) return
  const candidates: NodeRecord[] = [
    ...visibleGraph.value.roles,
    ...visibleGraph.value.skills,
    ...visibleGraph.value.domains,
  ]
  const match = candidates.find(node => node.name.toLowerCase() === keyword)
    || candidates.find(node => node.name.toLowerCase().includes(keyword))
  if (!match) return
  selectedNodeId.value = match.id
  renderGraph()
}

const selectNode = (nodeId: string) => {
  selectedNodeId.value = nodeId
  renderGraph()
}

const getLayoutScale = (width: number, height: number) =>
  clamp(Math.min(width / 1380, height / 620), 0.78, 1.08)

const getDomainCenters = (width: number, height: number) => {
  const centerX = width * 0.5
  const centerY = height * 0.5

  // 横向优先铺满：四个领域更靠近左右两侧，但仍保留安全区。
  const topSpreadX = width * 0.405
  const bottomSpreadX = width * 0.365
  const spreadY = height * 0.17

  return [
    { x: centerX - topSpreadX, y: centerY - spreadY },
    { x: centerX + topSpreadX, y: centerY - spreadY },
    { x: centerX - bottomSpreadX, y: centerY + spreadY },
    { x: centerX + bottomSpreadX, y: centerY + spreadY },
  ]
}

const OUTWARD_ANGLES = [Math.PI * 1.25, Math.PI * 1.75, Math.PI * 0.75, Math.PI * 0.25]

const getRoleRingGeometry = (ring: number) => {
  const radius = 88 + ring * 54
  const span = Math.PI * 1.18

  // 岗位节点直径约 43~58px，按弧长保守分配，避免同环节点互压。
  const capacity = Math.max(
    5,
    Math.floor((radius * span) / 54),
  )

  return { radius, span, capacity }
}

const rolePoint = (
  domainIndex: number,
  index: number,
  count: number,
  center: { x: number; y: number },
  width: number,
  height: number,
) => {
  let ring = 0
  let cursor = index
  let consumed = 0
  let geometry = getRoleRingGeometry(ring)

  // 岗位再多也继续向外增加新环，不再把节点塞回最后一环。
  while (cursor >= geometry.capacity) {
    cursor -= geometry.capacity
    consumed += geometry.capacity
    ring += 1
    geometry = getRoleRingGeometry(ring)
  }

  const remaining = Math.max(1, count - consumed)
  const slotsOnRing = Math.max(1, Math.min(geometry.capacity, remaining))
  const t = slotsOnRing <= 1 ? 0.5 : cursor / (slotsOnRing - 1)

  const baseAngle = OUTWARD_ANGLES[domainIndex] ?? Math.PI
  const phase = ring * (domainIndex % 2 === 0 ? -0.025 : 0.025)
  const angle = baseAngle - geometry.span / 2 + t * geometry.span + phase

  const scale = getLayoutScale(width, height)
  const radius = geometry.radius * scale

  return {
    x: center.x + Math.cos(angle) * radius * 1.08,
    y: center.y + Math.sin(angle) * radius * 0.64,
  }
}

const SKILL_RING_CAPACITIES = [6, 9, 12, 16, 20, 25, 30, 36, 42, 48, 55, 62]

const getSkillRingGeometry = (ring: number) => {
  // 完整技能场保持同心圆。
  // 半径间距 36px，容量按节点真实宽度做保守限制。
  const radius = 78 + ring * 39
  const presetCapacity = SKILL_RING_CAPACITIES[ring]
  const capacity = presetCapacity
    ?? Math.max(66, Math.floor((Math.PI * 2 * radius) / 48))

  return { radius, capacity }
}

const skillPoint = (
  globalIndex: number,
  fullCount: number,
  width: number,
  height: number,
) => {
  const centerX = width * 0.5
  const centerY = height * 0.5

  let ring = 0
  let cursor = globalIndex
  let consumed = 0
  let geometry = getSkillRingGeometry(ring)

  while (cursor >= geometry.capacity) {
    cursor -= geometry.capacity
    consumed += geometry.capacity
    ring += 1
    geometry = getSkillRingGeometry(ring)
  }

  // 永远按完整技能总数排布，筛选只隐藏，不重新洗牌。
  const remaining = Math.max(1, fullCount - consumed)
  const slotsOnRing = Math.max(1, Math.min(geometry.capacity, remaining))

  // 相邻圆环错相，避免不同环在同一径向线上发生文字碰撞。
  const angleOffset = -Math.PI / 2 + ring * 0.23
  const angle = (Math.PI * 2 * cursor) / slotsOnRing + angleOffset

  return {
    // 保留“环”的层次关系，但将圆环映射为更宽的同心椭圆，
    // 横向吃满空白，纵向保持紧凑，避免整体 fitZoom 被高度拖小。
    x: centerX + Math.cos(angle) * geometry.radius * 1.28,
    y: centerY + Math.sin(angle) * geometry.radius * 0.76,
  }
}

const getTextVisualUnits = (text: string) =>
  [...text].reduce((total, char) => {
    if (/[\u3400-\u9FFF\uF900-\uFAFF]/.test(char)) return total + 1
    if (/[A-Z]/.test(char)) return total + 0.68
    if (/[a-z0-9]/.test(char)) return total + 0.56
    if (/[\s\-_/+.]/.test(char)) return total + 0.34
    return total + 0.5
  }, 0)

const getStableSkillNodeMetrics = (globalRank: number, skillName: string) => {
  // 节点仍随外圈逐级紧凑，但最大宽度不再压得过窄。
  // 这样绝大多数中英文技能名可以完整展示，只有真正超长的名称才截断。
  let maxWidth = 90
  let height = 28
  let fontSize = 9

  if (globalRank >= 6) {
    maxWidth = 86
    height = 27
    fontSize = 8.8
  }
  if (globalRank >= 15) {
    maxWidth = 82
    height = 26
    fontSize = 8.6
  }
  if (globalRank >= 27) {
    maxWidth = 78
    height = 25
    fontSize = 8.4
  }
  if (globalRank >= 43) {
    maxWidth = 76
    height = 24
    fontSize = 8.2
  }
  if (globalRank >= 63) {
    maxWidth = 74
    height = 23
    fontSize = 8.0
  }
  if (globalRank >= 88) {
    maxWidth = 72
    height = 22
    fontSize = 7.8
  }
  if (globalRank >= 118) {
    maxWidth = 70
    height = 22
    fontSize = 7.7
  }
  if (globalRank >= 154) {
    maxWidth = 68
    height = 21
    fontSize = 7.6
  }
  if (globalRank >= 196) {
    maxWidth = 66
    height = 21
    fontSize = 7.5
  }
  if (globalRank >= 244) {
    maxWidth = 64
    height = 20
    fontSize = 7.4
  }

  const visualUnits = getTextVisualUnits(skillName)
  const estimatedWidth = 14 + visualUnits * fontSize * 0.96

  return {
    width: clamp(estimatedWidth, 32, maxWidth),
    height,
    fontSize,
  }
}

const getRoleLabelLayout = (
  roleName: string,
  nodeSize: number,
  globalRank: number,
) => {
  const normalized = roleName.replace(/\s+/g, ' ').trim()
  const chars = [...normalized]
  const fontSize = globalRank < 12 ? 9.2 : globalRank < 40 ? 8.6 : 8.2
  const innerWidth = Math.max(26, nodeSize * 0.76)

  // 中文岗位名按圆内真实宽度估算单行容量。
  // 5 个字会自然排成 3 + 2；7 个字会排成 4 + 3。
  const perLine = clamp(
    Math.floor(innerWidth / Math.max(fontSize * 0.94, 1)),
    3,
    5,
  )

  if (chars.length <= perLine) {
    return {
      text: normalized,
      fontSize,
      lineHeight: fontSize + 2,
      width: innerWidth,
      height: Math.max(fontSize + 3, nodeSize * 0.42),
    }
  }

  const maxChars = perLine * 2
  const displayChars =
    chars.length > maxChars
      ? [...chars.slice(0, Math.max(1, maxChars - 1)), '…']
      : chars

  // 两行采用均衡分配，而不是固定每行 N 字。
  // 因此 5 字 = 3/2、6 字 = 3/3、7 字 = 4/3。
  const firstLineCount = Math.ceil(displayChars.length / 2)
  const firstLine = displayChars.slice(0, firstLineCount).join('')
  const secondLine = displayChars.slice(firstLineCount).join('')

  return {
    text: `${firstLine}\n${secondLine}`,
    fontSize,
    lineHeight: fontSize + 1.7,
    width: innerWidth,
    height: Math.min(nodeSize * 0.72, (fontSize + 1.7) * 2 + 2),
  }
}

type PackedRectNode = {
  id: string
  x: number
  y: number
  width: number
  height: number
}

type BaselinePackedLayout = {
  positions: Map<string, { x: number; y: number }>
  center: [number, number]
  zoom: number
  nodeScale: number
}

const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5))
const PACK_CELL_SIZE = 72

const getBaselineNodeScale = (width: number, height: number) =>
  clamp(Math.min(width / 1600, height / 620), 0.84, 1)

const getBaselineRoles = () => visibleGraph.value.roles

const getBaselineSkills = () => visibleGraph.value.skills

const getBaselineDomainCenters = (width: number, height: number) => [
  { x: width * 0.115, y: height * 0.27 },
  { x: width * 0.885, y: height * 0.27 },
  { x: width * 0.135, y: height * 0.73 },
  { x: width * 0.865, y: height * 0.73 },
]

const getPackCellRange = (
  x: number,
  y: number,
  width: number,
  height: number,
  gap: number,
) => ({
  minX: Math.floor((x - width * 0.5 - gap) / PACK_CELL_SIZE),
  maxX: Math.floor((x + width * 0.5 + gap) / PACK_CELL_SIZE),
  minY: Math.floor((y - height * 0.5 - gap) / PACK_CELL_SIZE),
  maxY: Math.floor((y + height * 0.5 + gap) / PACK_CELL_SIZE),
})

const addPackedRectToGrid = (
  grid: Map<string, PackedRectNode[]>,
  node: PackedRectNode,
  gap = 2,
) => {
  const range = getPackCellRange(
    node.x,
    node.y,
    node.width,
    node.height,
    gap,
  )

  for (let gx = range.minX; gx <= range.maxX; gx += 1) {
    for (let gy = range.minY; gy <= range.maxY; gy += 1) {
      const key = `${gx}:${gy}`
      const bucket = grid.get(key) || []
      bucket.push(node)
      grid.set(key, bucket)
    }
  }
}

const packedRectFits = (
  grid: Map<string, PackedRectNode[]>,
  x: number,
  y: number,
  width: number,
  height: number,
  stageWidth: number,
  stageHeight: number,
  gap = 2,
  boundary = 3,
) => {
  if (
    x - width * 0.5 < boundary
    || x + width * 0.5 > stageWidth - boundary
    || y - height * 0.5 < boundary
    || y + height * 0.5 > stageHeight - boundary
  ) {
    return false
  }

  const range = getPackCellRange(x, y, width, height, gap)
  const visited = new Set<string>()

  for (let gx = range.minX; gx <= range.maxX; gx += 1) {
    for (let gy = range.minY; gy <= range.maxY; gy += 1) {
      const bucket = grid.get(`${gx}:${gy}`)
      if (!bucket) continue

      for (const other of bucket) {
        if (visited.has(other.id)) continue
        visited.add(other.id)

        const overlapX =
          (width + other.width) * 0.5 + gap - Math.abs(x - other.x)
        const overlapY =
          (height + other.height) * 0.5 + gap - Math.abs(y - other.y)

        if (overlapX > 0 && overlapY > 0) return false
      }
    }
  }

  return true
}

let baselinePackedLayoutCacheKey = ''
let baselinePackedLayoutCache: BaselinePackedLayout | null = null

const buildBaselinePackedLayout = (
  width: number,
  height: number,
): BaselinePackedLayout => {
  const graph = visibleGraph.value
  const cacheKey = [
    `${Math.round(width)}x${Math.round(height)}`,
    graph.domains.map(node => node.id).join(','),
    graph.roles.map(node => node.id).join(','),
    graph.skills.map(node => node.id).join(','),
  ].join('|')
  if (
    baselinePackedLayoutCache
    && baselinePackedLayoutCacheKey === cacheKey
  ) {
    return baselinePackedLayoutCache
  }

  const positions = new Map<string, { x: number; y: number }>()
  const grid = new Map<string, PackedRectNode[]>()
  const nodeScale = getBaselineNodeScale(width, height)
  const domainCenters = getBaselineDomainCenters(width, height)
  const baselineRoles = getBaselineRoles()
  const baselineSkills = getBaselineSkills()

  const roleBuckets = graphModel.domains.map(domain =>
    baselineRoles.filter(role => role.domainId === domain.id),
  )

  const place = (
    id: string,
    x: number,
    y: number,
    nodeWidth: number,
    nodeHeight: number,
    gap = 2,
  ) => {
    const node: PackedRectNode = {
      id,
      x,
      y,
      width: nodeWidth,
      height: nodeHeight,
    }
    positions.set(id, { x, y })
    addPackedRectToGrid(grid, node, gap)
  }

  // 1. Four domain anchors.
  graphModel.domains.forEach((domain, domainIndex) => {
    const center = domainCenters[domainIndex] || domainCenters[0]
    if (!center) return
    const size = 78 * nodeScale
    place(domain.id, center.x, center.y, size, size, 3)
  })

  // 2. Roles: deterministic golden-angle packing around each domain.
  //    The four clusters can use almost the whole side regions, but they can
  //    never overlap an already placed node.
  const outwardAngles = [Math.PI, 0, Math.PI, 0]

  roleBuckets.forEach((bucket, domainIndex) => {
    const center = domainCenters[domainIndex] || domainCenters[0]
    if (!center) return

    bucket.forEach(role => {
      const importance = Math.sqrt(role.total / graphModel.maxRoleTotal)
      const rawSize = clamp(43 + importance * 15, 43, 58)
      const size = rawSize * nodeScale
      let placed = false

      for (let attempt = 1; attempt < 14000; attempt += 1) {
        const radius = (48 + 4.6 * Math.sqrt(attempt)) * nodeScale
        const angle =
          (outwardAngles[domainIndex] || 0)
          + attempt * GOLDEN_ANGLE

        const x = center.x + Math.cos(angle) * radius * 1.08
        const y = center.y + Math.sin(angle) * radius * 0.88

        if (
          !packedRectFits(
            grid,
            x,
            y,
            size,
            size,
            width,
            height,
            2,
            3,
          )
        ) {
          continue
        }

        place(role.id, x, y, size, size, 2)
        placed = true
        break
      }

      // Defensive fallback. On ordinary desktop viewports this branch is not
      // expected; it preserves a finite, visible coordinate if the viewport is
      // exceptionally small.
      if (!placed) {
        const fallback = fullRolePlacementById.get(role.id)
        const fallbackCenter = domainCenters[domainIndex] || { x: width * 0.5, y: height * 0.5 }
        const point = rolePoint(
          domainIndex,
          fallback?.localIndex ?? 0,
          fallback?.count ?? bucket.length,
          fallbackCenter,
          width,
          height,
        )
        const x = clamp(point.x, size * 0.5 + 3, width - size * 0.5 - 3)
        const y = clamp(point.y, size * 0.5 + 3, height - size * 0.5 - 3)
        place(role.id, x, y, size, size, 2)
      }
    })
  })

  // 3. Skills: concentric elliptical rings.
  //    Each candidate is accepted only when its real rounded-rect box does not
  //    intersect any domain, role, or previous skill. This preserves the
  //    central ring visual while giving a hard no-overlap guarantee.
  const skillCenterX = width * 0.5
  const skillCenterY = height * 0.5

  baselineSkills.forEach((skill, globalRank) => {
    const metrics = getStableSkillNodeMetrics(globalRank, skill.name)
    const nodeWidth = metrics.width * nodeScale
    const nodeHeight = metrics.height * nodeScale
    let placed = false

    for (let ring = 0; ring < 30 && !placed; ring += 1) {
      const baseRadius = (42 + ring * 19) * nodeScale
      const rx = baseRadius * 1.42
      const ry = baseRadius * 0.88

      // Ramanujan ellipse circumference approximation.
      const perimeter = Math.PI * (
        3 * (rx + ry)
        - Math.sqrt((3 * rx + ry) * (rx + 3 * ry))
      )

      const slots = Math.max(
        8,
        Math.floor(
          perimeter / Math.max(28, 35 * nodeScale),
        ),
      )

      const angleOffset = -Math.PI / 2 + ring * 0.19

      for (let slot = 0; slot < slots; slot += 1) {
        const angle =
          angleOffset + (Math.PI * 2 * slot) / slots
        const x = skillCenterX + Math.cos(angle) * rx
        const y = skillCenterY + Math.sin(angle) * ry

        if (
          !packedRectFits(
            grid,
            x,
            y,
            nodeWidth,
            nodeHeight,
            width,
            height,
            2,
            2.5,
          )
        ) {
          continue
        }

        place(
          skill.id,
          x,
          y,
          nodeWidth,
          nodeHeight,
          2,
        )
        placed = true
        break
      }
    }

    // Defensive fallback for very narrow/mobile viewports.
    if (!placed) {
      for (let attempt = 1; attempt < 16000; attempt += 1) {
        const radius = 10 + 4.7 * Math.sqrt(attempt)
        const angle =
          attempt * GOLDEN_ANGLE + globalRank * 0.037
        const x =
          skillCenterX + Math.cos(angle) * radius * 1.42
        const y =
          skillCenterY + Math.sin(angle) * radius * 0.93

        if (
          !packedRectFits(
            grid,
            x,
            y,
            nodeWidth,
            nodeHeight,
            width,
            height,
            1.5,
            2,
          )
        ) {
          continue
        }

        place(
          skill.id,
          x,
          y,
          nodeWidth,
          nodeHeight,
          1.5,
        )
        placed = true
        break
      }
    }
  })

  // Use the actual center-point bounds. ECharts graph/view natively fits these
  // x/y points to the viewport; because this layout itself is already almost
  // screen-sized, its native fit scale stays ~1 instead of shrinking the graph.
  const packedPoints = [...positions.values()]
  let minX = Number.POSITIVE_INFINITY
  let maxX = Number.NEGATIVE_INFINITY
  let minY = Number.POSITIVE_INFINITY
  let maxY = Number.NEGATIVE_INFINITY

  packedPoints.forEach(point => {
    minX = Math.min(minX, point.x)
    maxX = Math.max(maxX, point.x)
    minY = Math.min(minY, point.y)
    maxY = Math.max(maxY, point.y)
  })

  const result: BaselinePackedLayout = {
    positions,
    center: [
      Number.isFinite(minX + maxX) ? (minX + maxX) * 0.5 : width * 0.5,
      Number.isFinite(minY + maxY) ? (minY + maxY) * 0.5 : height * 0.5,
    ],
    zoom: 0.99,
    nodeScale,
  }

  baselinePackedLayoutCacheKey = cacheKey
  baselinePackedLayoutCache = result
  return result
}


const getNodeVisualHalfSize = (node: any) => {
  const rawSize = node?.symbolSize
  if (Array.isArray(rawSize)) {
    return {
      halfWidth: Math.max(Number(rawSize[0]) || 0, 0) * 0.5,
      halfHeight: Math.max(Number(rawSize[1]) || 0, 0) * 0.5,
    }
  }
  const size = Math.max(Number(rawSize) || 0, 0)
  return { halfWidth: size * 0.5, halfHeight: size * 0.5 }
}

const getDefaultGraphView = (nodes: any[], width: number, height: number) => {
  const packedLayout = buildBaselinePackedLayout(width, height)
  return {
    center: packedLayout.center,
    zoom: packedLayout.zoom,
  }
}

const shouldShowLabel = (level: number, rank: number) => {
  if (level === 1) return true
  if (labelDensity.value === 'all') return true
  if (labelDensity.value === 'balanced') return level === 2 ? rank < 64 : rank < 48
  return level === 2 ? rank < 36 : rank < 28
}

const wrapNodeText = (text: string, perLine = 5, maxLines = 2) => {
  const normalized = text.replace(/\s+/g, ' ').trim()
  if (!normalized) return ''
  const maxLength = perLine * maxLines
  const clipped = normalized.length > maxLength ? `${normalized.slice(0, Math.max(2, maxLength - 1))}…` : normalized
  const lines: string[] = []
  for (let i = 0; i < clipped.length && lines.length < maxLines; i += perLine) lines.push(clipped.slice(i, i + perLine))
  return lines.join('\n')
}

const domainGradient = (color: string) => new echarts.graphic.RadialGradient(0.34, 0.28, 0.9, [
  { offset: 0, color: lighten(color, 0.18) },
  { offset: 0.62, color },
  { offset: 1, color: lighten(color, 0.04) },
])

const roleGradient = (color: string) => new echarts.graphic.LinearGradient(0, 0, 1, 1, [
  { offset: 0, color: lighten(color, 0.91) },
  { offset: 1, color: lighten(color, 0.78) },
])

const skillGradient = () => new echarts.graphic.LinearGradient(0, 0, 1, 1, [
  { offset: 0, color: '#F4FBFC' },
  { offset: 0.62, color: '#E1F0F3' },
  { offset: 1, color: '#D5E8EC' },
])

const emergingSkillGradient = (color: string) =>
  new echarts.graphic.LinearGradient(0, 0, 1, 1, [
    { offset: 0, color: lighten(color, 0.91) },
    { offset: 0.58, color: lighten(color, 0.84) },
    { offset: 1, color: lighten(color, 0.76) },
  ])

const buildGraphOption = () => {
  const width = Math.max(viewportSize.value.width, 720)
  const height = Math.max(viewportSize.value.height, 440)
  const centers = getDomainCenters(width, height)
  const selectedIds = selectionSet.value
  const graph = visibleGraph.value
  const packedLayout = buildBaselinePackedLayout(width, height)
  const nodes: any[] = []
  const links: any[] = []
  const domainIndexById = new Map(graphModel.domains.map((domain, index) => [domain.id, index]))
  const visibleRoleRank = new Map(graph.roles.map((role, index) => [role.id, index]))
  const roleBuckets = graphModel.domains.map(() => [] as RoleNode[])

  graph.roles.forEach(role => {
    const index = domainIndexById.get(role.domainId) ?? 0
    roleBuckets[index]?.push(role)
  })

  graph.domains.forEach(domain => {
    const domainIndex = domainIndexById.get(domain.id) ?? 0
    const center = centers[domainIndex] || centers[0]
    if (!center) return
    const color = getDomainColor(domain.name)
    const active = !selectedIds || selectedIds.has(domain.id)
    nodes.push({
      id: domain.id,
      name: domain.name,
      level: 1,
      value: domain.total,
      x: packedLayout.positions.get(domain.id)?.x ?? center.x,
      y: packedLayout.positions.get(domain.id)?.y ?? center.y,
      symbol: 'circle',
      symbolSize: 78 * packedLayout.nodeScale,
      draggable: true,
      z: 8,
      itemStyle: {
        color: domainGradient(color),
        borderColor: active ? 'rgba(255,255,255,.96)' : 'rgba(255,255,255,.72)',
        borderWidth: active ? 3.2 : 2,
        opacity: active ? 1 : 0.20,
        shadowBlur: active ? 26 : 8,
        shadowOffsetY: 7,
        shadowColor: hexToRgba(color, active ? 0.25 : 0.08),
      },
      label: {
        show: true,
        position: 'inside',
        align: 'center',
        verticalAlign: 'middle',
        color: '#FFFFFF',
        fontSize: 13.5,
        fontWeight: 800,
        lineHeight: 17,
        formatter: `${domain.name}\n{count|${domain.total.toLocaleString()}}`,
        rich: {
          count: {
            color: 'rgba(255,255,255,.74)',
            width: 66 * packedLayout.nodeScale,
            align: 'center',
            fontSize: 9.5,
            fontWeight: 650,
            lineHeight: 14,
          },
        },
      },
    })
  })

  roleBuckets.forEach((bucket, domainIndex) => {
    const domain = graphModel.domains[domainIndex]
    const center = centers[domainIndex]
    if (!domain || !center || !activeDomainNames.value.has(domain.name)) return
    const color = getDomainColor(domain.name)
    bucket.forEach((role, localIndex) => {
      const stablePlacement = fullRolePlacementById.get(role.id)
      const fallbackPoint = rolePoint(
        domainIndex,
        stablePlacement?.localIndex ?? localIndex,
        stablePlacement?.count ?? bucket.length,
        center,
        width,
        height,
      )
      const point = packedLayout.positions.get(role.id) ?? fallbackPoint
      const globalRank = visibleRoleRank.get(role.id) ?? 9999
      const active = !selectedIds || selectedIds.has(role.id)
      const importance = Math.sqrt(role.total / graphModel.maxRoleTotal)
      const size = clamp(43 + importance * 15, 43, 58) * packedLayout.nodeScale
      const showLabel = shouldShowLabel(2, globalRank)
      const roleLabel = getRoleLabelLayout(role.name, size, globalRank)
      const emerging = isEmergingRole(role)
      const emergingVisual = emerging ? getEmergingVisual(role.emergingScore) : null
      nodes.push({
        id: role.id,
        name: role.name,
        level: 2,
        value: role.total,
        emergingScore: role.emergingScore,
        isEmerging: emerging,
        x: point.x,
        y: point.y,
        symbol: 'circle',
        symbolSize: size,
        draggable: true,
        z: 6,
        itemStyle: {
          color: roleGradient(color),
          borderColor: emergingVisual
            ? emergingVisual.color
            : active ? hexToRgba(color, 0.88) : hexToRgba(color, 0.30),
          borderWidth: emergingVisual
            ? emergingVisual.borderWidth
            : active ? 1.8 : 1,
          // 新兴岗位即使在节点高亮/筛选切换后处于“非当前关系”状态，
          // 也保留足够不透明度，避免暖色光晕被普通淡化逻辑吃掉。
          opacity: active ? 0.98 : emerging ? 0.82 : 0.15,
          shadowBlur: emergingVisual
            ? emergingVisual.shadowBlur
            : active && globalRank < 24 ? 10 : 3,
          shadowOffsetY: emerging ? 0 : 3,
          shadowColor: emergingVisual
            ? emergingVisual.shadowColor
            : hexToRgba(color, active ? 0.12 : 0.04),
        },
        emphasis: emergingVisual ? {
          itemStyle: {
            borderColor: emergingVisual.color,
            borderWidth: emergingVisual.borderWidth + 0.7,
            shadowBlur: emergingVisual.shadowBlur + 7,
            shadowColor: emergingVisual.shadowColor,
          },
        } : undefined,
        blur: emergingVisual ? {
          itemStyle: {
            opacity: 0.82,
            borderColor: emergingVisual.color,
            borderWidth: emergingVisual.borderWidth,
            shadowBlur: emergingVisual.shadowBlur,
            shadowColor: emergingVisual.shadowColor,
          },
          label: { opacity: 0.90 },
        } : undefined,
        label: {
          show: showLabel,
          position: 'inside',
          distance: 0,
          width: roleLabel.width,
          height: roleLabel.height,
          overflow: 'truncate',
          ellipsis: '…',
          color: active ? '#25394C' : emerging ? '#5460B8' : '#8794A2',
          fontFamily: '"Segoe UI", "Microsoft YaHei UI", "PingFang SC", sans-serif',
          fontSize: roleLabel.fontSize,
          fontWeight: emerging ? 800 : globalRank < 16 ? 720 : 650,
          lineHeight: roleLabel.lineHeight,
          opacity: active ? 1 : emerging ? 0.90 : 0.28,
          formatter: roleLabel.text,
          align: 'center',
          verticalAlign: 'middle',
        },
      })
      links.push({
        source: domain.id,
        target: role.id,
        relationLevel: 1,
        lineStyle: {
          color: hexToRgba(color, active ? 0.24 : 0.055),
          width: active ? 0.95 : 0.6,
          opacity: 1,
          curveness: (localIndex % 2 === 0 ? 1 : -1) * (0.028 + (localIndex % 4) * 0.008),
        },
      })
    })
  })

  graph.skills.forEach((skill, index) => {
    const globalRank = fullSkillIndexById.get(skill.id) ?? index
    const point = packedLayout.positions.get(skill.id)
      ?? skillPoint(globalRank, graphModel.skills.length, width, height)
    const active = !selectedIds || selectedIds.has(skill.id)
    const emergingSkill = isEmergingSkill(skill)
    const emergingSkillVisual = emergingSkill ? getSkillEmergingVisual(skill) : null
    const metrics = getStableSkillNodeMetrics(globalRank, skill.name)
    const nodeWidth = metrics.width * packedLayout.nodeScale
    const nodeHeight = metrics.height * packedLayout.nodeScale

    // 小胶囊文字采用真实节点宽度约束，而不是按字符数硬截断。
    // 保留左右各约 5px 内边距，确保文字永远留在 roundRect 内。
    const skillLabelFontSize = Math.max(
      7.2,
      metrics.fontSize * packedLayout.nodeScale,
    )
    // 左右只保留约 4px 内边距，最大化完整文字展示面积。
    const skillLabelWidth = Math.max(12, nodeWidth - 8)
    const skillLabelLineHeight = Math.max(
      9,
      Math.min(nodeHeight - 4, skillLabelFontSize + 2),
    )
    nodes.push({
      id: skill.id,
      name: skill.name,
      level: 3,
      value: skill.count,
      isEmergingSkill: emergingSkill,
      emergingTier: skill.emergingTier,
      emergingCategory: skill.emergingCategory,
      emergingWeight: skill.emergingWeight,
      x: point.x,
      y: point.y,
      symbol: 'roundRect',
      symbolSize: [nodeWidth, nodeHeight],
      draggable: true,
      z: 7,
      itemStyle: {
        color: emergingSkillVisual
          ? emergingSkillGradient(emergingSkillVisual.color)
          : skillGradient(),
        borderColor: emergingSkillVisual
          ? emergingSkillVisual.color
          : active ? 'rgba(47,127,142,.72)' : 'rgba(47,127,142,.22)',
        borderWidth: emergingSkillVisual
          ? emergingSkillVisual.borderWidth
          : active ? 1.25 : 0.8,
        // 新兴技能在点击岗位/领域造成其它技能淡化时，仍保持清晰可辨。
        opacity: active ? 0.98 : emergingSkill ? 0.84 : 0.16,
        shadowBlur: emergingSkillVisual
          ? emergingSkillVisual.shadowBlur
          : active && globalRank < 16 ? 11 : 3,
        shadowOffsetY: emergingSkill ? 0 : 3,
        shadowColor: emergingSkillVisual
          ? emergingSkillVisual.shadowColor
          : 'rgba(47,127,142,.12)',
      },
      emphasis: emergingSkillVisual ? {
        itemStyle: {
          borderColor: emergingSkillVisual.color,
          borderWidth: emergingSkillVisual.borderWidth + 0.45,
          shadowBlur: emergingSkillVisual.shadowBlur + 5,
          shadowColor: emergingSkillVisual.shadowColor,
        },
      } : undefined,
      blur: emergingSkillVisual ? {
        itemStyle: {
          opacity: 0.84,
          borderColor: emergingSkillVisual.color,
          borderWidth: emergingSkillVisual.borderWidth,
          shadowBlur: emergingSkillVisual.shadowBlur,
          shadowColor: emergingSkillVisual.shadowColor,
        },
        label: { opacity: 0.88 },
      } : undefined,
      label: {
        show: shouldShowLabel(3, globalRank),
        position: 'inside',
        align: 'center',
        verticalAlign: 'middle',
        width: skillLabelWidth,
        height: skillLabelLineHeight,
        overflow: 'truncate',
        ellipsis: '…',
        color: active
          ? emergingSkill ? '#3E4AA2' : '#174F5D'
          : emergingSkill ? '#5965B4' : '#7C9199',
        fontFamily: '"Segoe UI", "Microsoft YaHei UI", "PingFang SC", sans-serif',
        fontSize: skillLabelFontSize,
        fontWeight: emergingSkill ? 800 : 700,
        letterSpacing: -0.15,
        lineHeight: skillLabelLineHeight,
        opacity: active ? 1 : emergingSkill ? 0.90 : 0.28,
        textBorderColor: 'rgba(255,255,255,.82)',
        textBorderWidth: 0.55,
        formatter: skill.name,
      },
    })
  })

  graph.roles.forEach((role, roleIndex) => {
    const relationSkills = role.allSkills
      .filter(skill => graph.skillIdSet.has(skill.skillId))
      .slice(0, skillsPerRole.value)
    const domainIndex = domainIndexById.get(role.domainId) ?? 0
    const color = getDomainColor(role.domainName)
    relationSkills.forEach((skill, skillIndex) => {
      const active = !selectedIds || (selectedIds.has(role.id) && selectedIds.has(skill.skillId))
      const bendSign = domainIndex === 0 || domainIndex === 3 ? 1 : -1
      const bend = bendSign * (0.055 + ((roleIndex + skillIndex) % 4) * 0.018)
      links.push({
        source: role.id,
        target: skill.skillId,
        relationLevel: 2,
        lineStyle: {
          color: active ? hexToRgba(color, 0.22) : hexToRgba(color, 0.038),
          type: 'solid',
          width: active ? 0.9 : 0.5,
          opacity: 1,
          curveness: bend,
        },
      })
    })
  })

  const defaultView = getDefaultGraphView(nodes, width, height)

  return {
    backgroundColor: 'transparent',
    animationDuration: 460,
    animationDurationUpdate: 260,
    animationEasing: 'cubicOut',
    tooltip: {
      trigger: 'item',
      confine: true,
      backgroundColor: 'rgba(22, 35, 50, .96)',
      borderColor: 'rgba(255,255,255,.10)',
      borderWidth: 1,
      padding: [11, 13],
      extraCssText: 'box-shadow:0 14px 32px rgba(16,34,54,.20);border-radius:10px;',
      textStyle: { color: '#F8FAFC', fontSize: 12 },
      formatter: (params: any) => {
        if (params?.dataType === 'edge') {
          return Number(params.data?.relationLevel) === 1 ? '领域 → 岗位' : '岗位 → 技能栈'
        }
        const data = params?.data
        if (!data) return ''
        const levelText = data.level === 1 ? '领域' : data.level === 2 ? '岗位' : '技能栈'
        const base = `<strong style="font-size:13px">${data.name}</strong><br/><span style="opacity:.62">${levelText}</span> · ${Number(data.value || 0).toLocaleString()}`
        if (data.level === 2) {
          const score = formatEmergingScore(Number(data.emergingScore || 0))
          if (data.isEmerging) {
            const visual = getEmergingVisual(Number(data.emergingScore || 0))
            return `${base}<br/><span style="color:${visual.color};font-weight:800">✦ ${visual.levelName}新兴度</span> · ${score}（${visual.rangeLabel}）`
          }
          return `${base}<br/><span style="opacity:.62">新兴程度 ${score}</span>`
        }
        if (data.level === 3 && data.isEmergingSkill) {
          const index = clamp(Number(data.emergingTier || 1) - 1, 0, EMERGING_LEVEL_COLORS.length - 1)
          const color = EMERGING_LEVEL_COLORS[index]
          const meta = [data.emergingCategory, data.emergingWeight].filter(Boolean).join(' · ')
          return `${base}<br/><span style="color:${color};font-weight:800">✦ 新兴技能</span> · ${meta}`
        }
        return base
      },
    },
    series: [{
      type: 'graph',
      layout: 'none',
      left: 44,
      right: 44,
      top: 44,
      bottom: 44,
      roam: true,
      draggable: true,
      nodeScaleRatio: 1,
      data: nodes,
      links,
      symbol: 'circle',
      edgeSymbol: ['none', 'none'],
      center: defaultView.center,
      zoom: defaultView.zoom,
      scaleLimit: { min: 0.82, max: 2.6 },
      labelLayout: { hideOverlap: false },
      emphasis: {
        focus: 'adjacency',
        scale: 1.06,
        itemStyle: { shadowBlur: 18 },
        lineStyle: { width: 1.45, opacity: 0.82 },
      },
      blur: {
        itemStyle: { opacity: 0.075 },
        lineStyle: { opacity: 0.018 },
        label: { opacity: 0.06 },
      },
    }],
  }
}

const renderGraph = () => {
  if (!chartInstance) return
  chartInstance.setOption(buildGraphOption() as any, true)
}

const onNodeClick = (params: any) => {
  const id = params?.data?.id
  if (!id) return
  selectedNodeId.value = selectedNodeId.value === id ? '' : String(id)
  renderGraph()
}

const clearSelection = () => {
  selectedNodeId.value = ''
  renderGraph()
}

const initChart = async () => {
  if (!chartRef.value) return
  chartInstance?.dispose()
  chartInstance = echarts.init(chartRef.value)
  chartInstance.on('click', onNodeClick)
  chartInstance.on('dblclick', clearSelection)
  await nextTick()
  renderGraph()
}

const changeZoom = (direction: number) => {
  if (!chartInstance) return
  const option = chartInstance.getOption() as any
  const currentZoom = Number(option?.series?.[0]?.zoom || 1)

  // 原来约 +18% / -15%，步幅偏大。
  // 现在使用对称约 12% 步幅，操作更细，但仍有明显反馈。
  const zoomStep = 1.12
  const nextZoom = clamp(
    currentZoom * (direction > 0 ? zoomStep : 1 / zoomStep),
    0.82,
    2.6,
  )

  chartInstance.setOption({ series: [{ zoom: nextZoom }] })
}

const resetView = () => {
  // “重置视图”回到默认全景：Top50 岗位 + Top100 技能。
  activeDomainNames.value = new Set<string>(DOMAIN_ORDER)
  roleLimit.value = DEFAULT_ROLE_LIMIT
  minRoleCount.value = DEFAULT_MIN_ROLE_COUNT
  skillLimit.value = 100
  minSkillCount.value = 2
  selectedNodeId.value = ''
  searchKeyword.value = ''

  if (!chartInstance) return
  chartInstance.setOption(buildGraphOption() as any, true)
}

const syncViewportSize = () => {
  if (!scrollRef.value) return
  viewportSize.value = {
    width: Math.max(scrollRef.value.clientWidth, 720),
    height: Math.max(scrollRef.value.clientHeight, 440),
  }
}

watch(
  [roleLimit, minRoleCount, skillLimit, minSkillCount, labelDensity, skillsPerRole, layoutMode, activeDomainNames],
  async () => {
    selectedNodeId.value = ''
    await nextTick()
    renderGraph()
  },
  { deep: true },
)

watch(
  () => [viewportSize.value.width, viewportSize.value.height, detailCollapsed.value],
  async () => {
    await nextTick()
    chartInstance?.resize()
    renderGraph()
  },
)

onMounted(async () => {
  syncViewportSize()
  if (scrollRef.value && typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => {
      syncViewportSize()
      chartInstance?.resize()
    })
    resizeObserver.observe(scrollRef.value)
  }
  await initChart()
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
  if (chartInstance) {
    chartInstance.off('click', onNodeClick)
    chartInstance.off('dblclick', clearSelection)
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.panorama-root {
  --ink-strong: #17283a;
  --ink: #3d5267;
  --ink-soft: #7f8e9d;
  --metal-line: rgba(73, 96, 119, 0.13);
  --mineral: #2f7f8e;
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: var(--ink-strong);
  font-family: Inter, "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
}

.panorama-toolbar {
  position: relative;
  z-index: 4;
  flex: 0 0 auto;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  grid-template-areas:
    "intro footer"
    "filters filters";
  align-items: center;
  column-gap: 10px;
  row-gap: 5px;
  padding: 7px 12px 7px;
  overflow: hidden;
  border: 1px solid rgba(66, 88, 110, 0.13);
  border-radius: 13px;
  background:
    linear-gradient(112deg, rgba(255,255,255,.985) 0%, rgba(248,251,253,.97) 56%, rgba(239,247,249,.90) 100%);
  box-shadow: 0 8px 22px rgba(30, 50, 70, .055), inset 0 1px 0 rgba(255,255,255,.9);
}

.panorama-toolbar::after {
  content: "";
  position: absolute;
  width: 360px;
  height: 90px;
  right: -100px;
  top: -46px;
  border: 1px solid rgba(47,127,142,.11);
  border-radius: 50%;
  transform: rotate(-8deg);
  pointer-events: none;
}

.panorama-toolbar__intro { grid-area: intro; min-width: 0; }

.panorama-toolbar__eyebrow {
  color: #8796a4;
  font-size: 8px;
  font-weight: 800;
  letter-spacing: .19em;
}

.panorama-toolbar__title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 2px;
}

.panorama-toolbar__title-row h3 {
  margin: 0;
  color: #17283a;
  font-size: 15px;
  line-height: 1.35;
  letter-spacing: -.015em;
}

.panorama-toolbar__title-row p {
  margin: 2px 0 0;
  color: #8896a4;
  font-size: 9px;
}

.panorama-summary-pills {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
}

.panorama-summary-pills span {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  padding: 5px 8px;
  border: 1px solid rgba(71, 94, 117, .10);
  border-radius: 999px;
  color: #6e7f8f;
  background: rgba(247,249,251,.86);
  font-size: 9.5px;
}

.panorama-summary-pills strong { color: #2f4559; font-size: 11.5px; font-variant-numeric: tabular-nums; }
.panorama-summary-pills .is-domain { color: #355d82; background: rgba(58, 94, 130, .10); border-color: rgba(58, 94, 130, .20); }
.panorama-summary-pills .is-domain strong { color: #33495f; }
.panorama-summary-pills .is-role { color: #625789; background: rgba(102, 95, 132, .10); border-color: rgba(102, 95, 132, .20); }
.panorama-summary-pills .is-role strong { color: #34516f; }
.panorama-summary-pills .is-skill { color: #2f6f7c; background: rgba(47,127,142,.10); border-color: rgba(47,127,142,.20); }
.panorama-summary-pills .is-skill strong { color: #2f6e7b; }
.panorama-summary-pills .is-emerging {
  color: #5f69b3;
  background: rgba(91,108,212,.09);
  border-color: rgba(91,108,212,.20);
}
.panorama-summary-pills .is-emerging strong { color: #4856aa; }
.panorama-summary-pills .is-emerging em {
  margin: 0 2px;
  color: rgba(72,86,170,.42);
  font-style: normal;
  font-weight: 500;
}

.panorama-filter-grid {
  grid-area: filters;
  width: 100%;
  min-width: 0;
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) repeat(4, minmax(0, 1fr));
  align-items: end;
  gap: 12px;
  min-height: 58px;
  margin: 0;
  box-sizing: border-box;
}

.panorama-control {
  width: 100%;
  min-width: 0;
  min-height: 58px;
  display: grid;
  grid-template-rows: 16px 40px;
  row-gap: 2px;
  align-items: end;
  box-sizing: border-box;
}

.panorama-control--search {
  min-width: 0;
  margin: 0;
}

.panorama-control__label {
  width: 100%;
  height: 18px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #17354a;
  font-family: 'Times New Roman', Times, serif;
  font-size: 12px;
  font-weight: 700;
  line-height: 18px;
  letter-spacing: .025em;
  text-align: center;
  text-rendering: geometricPrecision;
  -webkit-font-smoothing: antialiased;
}

/* 五个筛选项共享同一标题基线和控件基线。 */
.panorama-control:not(.panorama-control--search) {
  justify-items: center;
}

.panorama-control:not(.panorama-control--search) .panorama-control__label {
  width: 100%;
  padding: 0;
  text-align: center;
}

.panorama-search-box {
  position: relative;
  grid-row: 2;
  width: 100%;
  min-width: 0;
  height: 40px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 0 13px;
  overflow: hidden;
  border: 1px solid rgba(28, 63, 83, .26);
  border-radius: 9px 12px 9px 12px;
  background:
    linear-gradient(180deg, rgba(255,255,255,.998) 0%, rgba(246,249,251,.998) 64%, rgba(241,246,248,.996) 100%);
  color: #17354a;
  outline: none;
  box-shadow:
    0 5px 14px rgba(18,47,64,.065),
    inset 0 1px 0 rgba(255,255,255,1),
    inset 0 0 0 1px rgba(255,255,255,.38),
    inset 0 -1px 0 rgba(25,101,117,.055);
  transition:
    border-color .18s ease,
    box-shadow .18s ease,
    background .18s ease;
}

.panorama-search-box::before {
  content: "";
  position: absolute;
  z-index: 2;
  top: 0;
  left: 16px;
  width: 34%;
  height: 1px;
  pointer-events: none;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(58,143,153,.22) 16%,
    rgba(116,220,218,.82) 50%,
    rgba(56,143,154,.22) 84%,
    transparent 100%
  );
  filter: drop-shadow(0 0 4px rgba(72,177,183,.22));
}

.panorama-search-box::after {
  content: "";
  position: absolute;
  right: 4px;
  bottom: 4px;
  width: 11px;
  height: 11px;
  pointer-events: none;
  border-right: 1px solid rgba(35,133,147,.52);
  border-bottom: 1px solid rgba(35,133,147,.52);
  border-radius: 0 0 5px 0;
}

.panorama-search-box:focus-within {
  border-color: rgba(30, 107, 127, .56);
  background: #ffffff;
  box-shadow:
    0 0 0 3px rgba(39,128,145,.06),
    0 7px 18px rgba(17,59,76,.085),
    inset 0 1px 0 rgba(255,255,255,1);
}

/* Element Plus 科技感下拉框。 */
.panorama-tech-select {
  width: 100%;
  min-width: 0;
}

.panorama-select-shell {
  position: relative;
  grid-row: 2;
  width: 100%;
  min-width: 0;
  height: 40px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  overflow: hidden;
  border: 1px solid rgba(28, 63, 83, .26);
  border-radius: 9px 12px 9px 12px;
  background:
    linear-gradient(180deg, rgba(255,255,255,.998) 0%, rgba(246,249,251,.998) 64%, rgba(241,246,248,.996) 100%);
  box-shadow:
    0 5px 14px rgba(18,47,64,.065),
    inset 0 1px 0 rgba(255,255,255,1),
    inset 0 0 0 1px rgba(255,255,255,.38),
    inset 0 -1px 0 rgba(25,101,117,.055);
  transition:
    border-color .2s ease,
    box-shadow .2s ease,
    background .2s ease;
}

.panorama-select-shell::before {
  content: "";
  position: absolute;
  z-index: 3;
  top: 0;
  left: 11%;
  width: 57%;
  height: 1px;
  pointer-events: none;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(58, 143, 153, .24) 14%,
    rgba(116, 220, 218, .92) 50%,
    rgba(56, 143, 154, .26) 86%,
    transparent 100%
  );
  filter: drop-shadow(0 0 4px rgba(72, 177, 183, .26));
}

.panorama-select-shell::after {
  content: "";
  position: absolute;
  z-index: 3;
  right: 3px;
  bottom: 3px;
  width: 12px;
  height: 12px;
  pointer-events: none;
  border-right: 1px solid rgba(35, 133, 147, .62);
  border-bottom: 1px solid rgba(35, 133, 147, .62);
  border-radius: 0 0 5px 0;
}

.panorama-select-shell:hover {
  border-color: rgba(31, 96, 116, .46);
  background:
    linear-gradient(180deg, #ffffff 0%, rgba(244,249,250,.999) 64%, rgba(238,245,247,.997) 100%);
  box-shadow:
    0 7px 18px rgba(17,59,76,.09),
    inset 0 1px 0 rgba(255,255,255,1),
    inset 0 -1px 0 rgba(25,101,117,.065);
}

.panorama-select-shell:focus-within {
  border-color: rgba(30, 107, 127, .56);
  background: #ffffff;
  box-shadow:
    0 0 0 3px rgba(39,128,145,.06),
    0 7px 18px rgba(17,59,76,.085),
    inset 0 1px 0 rgba(255,255,255,1);
}

.panorama-select-shell .panorama-tech-select {
  width: 100%;
  min-width: 0;
  flex: 1 1 auto;
}

.panorama-control :deep(.panorama-tech-select .el-select__wrapper) {
  width: 100%;
  min-width: 0;
  min-height: 36px;
  padding: 0 12px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  box-shadow: none;
}





.panorama-control :deep(.panorama-tech-select .el-select__selection) {
  justify-content: center;
}

.panorama-control :deep(.panorama-tech-select .el-select__selected-item) {
  width: 100%;
  color: #17354a;
  font-family: 'Times New Roman', Times, serif;
  font-size: 12.2px;
  font-weight: 700;
  line-height: 1.2;
  text-align: center;
  letter-spacing: .025em;
  text-rendering: geometricPrecision;
  -webkit-font-smoothing: antialiased;
  text-shadow: 0 1px 0 rgba(255,255,255,.58);
}

.panorama-control :deep(.panorama-tech-select .el-select__suffix) {
  color: #173f55;
  opacity: .95;
  transform: scale(.94);
  transform-origin: center;
  filter: drop-shadow(0 1px 0 rgba(255,255,255,.7));
  transition: color .18s ease, opacity .18s ease;
}

.panorama-control :deep(.panorama-tech-select .el-select__caret) {
  font-size: 13px;
  transition: transform .18s ease, color .18s ease;
}

.panorama-control :deep(.panorama-tech-select .el-select__wrapper.is-focused .el-select__caret) {
  color: #2f7f8e;
}

.panorama-search-box { display: flex; align-items: center; gap: 8px; padding: 0 11px; }
.panorama-search-box .el-icon { color: #71889a; font-size: 13px; }
.panorama-search-box input {
  min-width: 0;
  flex: 1;
  border: 0;
  outline: 0;
  color: #17354a;
  background: transparent;
  font-family: 'Times New Roman', Times, serif;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.2;
  letter-spacing: .02em;
  text-rendering: geometricPrecision;
  -webkit-font-smoothing: antialiased;
}
.panorama-search-box input::placeholder {
  color: #7890a0;
  font-family: 'Times New Roman', Times, serif;
  font-weight: 400;
  opacity: .92;
}
.panorama-search-box button {
  border: 0;
  background: transparent;
  color: #4f7085;
  font-size: 10.5px;
  font-weight: 600;
  cursor: pointer;
}

.panorama-toolbar__footer {
  grid-area: footer;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  flex-wrap: nowrap;
  gap: 8px;
  margin: 0;
  overflow: hidden;
}
.panorama-domain-filters, .panorama-legend { display: flex; align-items: center; gap: 6px; flex-wrap: nowrap; flex-shrink: 0; }
.panorama-toolbar__actions { display: flex; align-items: center; gap: 6px; flex-wrap: nowrap; flex-shrink: 0; }

.panorama-domain-filter {
  --domain-color: #66788b;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 8px;
  border: 1px solid rgba(75, 98, 119, .12);
  border-radius: 999px;
  color: #83919e;
  background: rgba(255,255,255,.72);
  font-size: 8.8px;
  font-weight: 650;
  cursor: pointer;
  transition: all .18s ease;
}

.panorama-domain-filter i { width: 6px; height: 6px; border-radius: 50%; background: #c7d0d8; }
.panorama-domain-filter.is-active {
  color: var(--domain-color);
  border-color: color-mix(in srgb, var(--domain-color) 26%, white);
  background: color-mix(in srgb, var(--domain-color) 5.5%, white);
}
.panorama-domain-filter.is-active i { background: var(--domain-color); box-shadow: 0 0 0 3px color-mix(in srgb, var(--domain-color) 10%, transparent); }

.panorama-legend { min-width: 0; margin-left: 2px; color: #748695; font-size: 8.4px; }
.panorama-legend > span { display: inline-flex; align-items: center; gap: 4px; white-space: nowrap; }
.legend-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; }
.legend-dot--domain { background: #3a5e82; box-shadow: 0 0 0 2px rgba(58,94,130,.10); }
.legend-dot--role { background: #edf2f5; border: 1px solid #7f94a8; }
.legend-dot--skill { width: 12px; height: 7px; border-radius: 3px; background: #dcecef; border: 1px solid #2f7f8e; }
.panorama-legend__emerging {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-width: 0;
  color: #67729a;
  font-family: inherit;
  font-weight: 650;
}
.emerging-mini-scale {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}
.emerging-mini-scale i {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  box-shadow: 0 0 0 1px rgba(56, 71, 155, .09);
}
.panorama-legend__emerging small {
  color: #7681a7;
  font-family: inherit;
  font-size: 8px;
  font-weight: 600;
  letter-spacing: 0;
  white-space: nowrap;
}
.panorama-legend__emerging small b {
  color: #5664ba;
  font-family: inherit;
  font-weight: 800;
}

.panorama-reset-filter {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
  padding: 5px 9px;
  border: 1px solid rgba(69, 92, 113, .12);
  border-radius: 8px;
  color: #607486;
  background: #fff;
  font-size: 9px;
  cursor: pointer;
}
.panorama-reset-filter.is-secondary { background: rgba(248, 251, 253, 0.92); }

.panorama-shell {
  position: relative;
  min-height: 0;
  height: auto;
  flex: 1 1 0;
  display: flex;
  overflow: hidden;
  border: 1px solid rgba(64, 86, 107, .12);
  border-radius: 16px;
  background: #f8fafb;
  box-shadow: 0 14px 34px rgba(24, 43, 60, .07);
}

.panorama-stage {
  position: relative;
  min-width: 0;
  min-height: 0;
  height: 100%;
  flex: 1 1 auto;
  overflow: hidden;
  background:
    radial-gradient(ellipse at 50% 50%, rgba(224,241,244,.62) 0%, rgba(247,250,252,.25) 24%, transparent 46%),
    linear-gradient(180deg, #fbfcfd 0%, #f4f7f9 100%);
}

.panorama-stage::before,
.panorama-stage::after {
  content: "";
  position: absolute;
  pointer-events: none;
  z-index: 0;
}

.panorama-stage::before {
  inset: 0;
  opacity: .46;
  background-image:
    linear-gradient(rgba(66, 91, 113, .038) 1px, transparent 1px),
    linear-gradient(90deg, rgba(66, 91, 113, .038) 1px, transparent 1px),
    radial-gradient(circle, rgba(47,127,142,.12) 1px, transparent 1.2px);
  background-size: 32px 32px, 32px 32px, 16px 16px;
  mask-image: linear-gradient(to bottom, transparent, #000 12%, #000 88%, transparent);
}

.panorama-stage::after {
  left: 50%;
  top: 50%;
  width: 36%;
  height: 58%;
  border: 1px solid rgba(47,127,142,.08);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 0 0 22px rgba(47,127,142,.018), 0 0 0 48px rgba(47,127,142,.012);
}

.panorama-stage__backdrop, .panorama-chart { position: absolute; inset: 0; }
.panorama-stage__backdrop { pointer-events: none; overflow: hidden; }
.panorama-grid-glow { position: absolute; inset: 0; background: radial-gradient(circle at 50% 50%, rgba(47,127,142,.07), transparent 44%); }
.panorama-orbit { position: absolute; left: 50%; top: 50%; border: 1px solid rgba(76, 98, 118, .045); border-radius: 50%; transform: translate(-50%, -50%); }
.panorama-orbit--a { width: 44%; height: 68%; }
.panorama-orbit--b { width: 80%; height: 98%; border-style: dashed; }
.panorama-chart { z-index: 1; }

.panorama-stage__status {
  position: absolute;
  z-index: 3;
  left: 14px;
  bottom: 12px;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 6px 9px;
  border: 1px solid rgba(69, 92, 112, .09);
  border-radius: 999px;
  color: #8493a0;
  background: rgba(255,255,255,.84);
  box-shadow: 0 5px 18px rgba(28,47,65,.055);
  backdrop-filter: blur(10px);
  font-size: 8.3px;
}
.panorama-stage__status strong { color: #526a7d; font-weight: 700; }

.panorama-zoom-controls { position: absolute; z-index: 3; right: 14px; bottom: 12px; display: flex; gap: 5px; }
.panorama-zoom-controls button,
.panorama-icon-button,
.panorama-detail__collapsed-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  padding: 0;
  border: 1px solid rgba(64, 87, 108, .12);
  border-radius: 8px;
  color: #607586;
  background: rgba(255,255,255,.90);
  box-shadow: 0 3px 10px rgba(29,49,68,.055);
  cursor: pointer;
  transition: all .18s ease;
}
.panorama-zoom-controls button:hover,
.panorama-icon-button:hover,
.panorama-detail__collapsed-toggle:hover { color: #2f6e7a; border-color: rgba(47,127,142,.25); transform: translateY(-1px); }

.panorama-detail {
  position: relative;
  z-index: 2;
  width: 244px;
  flex: 0 0 244px;
  padding: 16px;
  overflow: auto;
  border-left: 1px solid rgba(64, 86, 106, .10);
  background:
    linear-gradient(180deg, rgba(255,255,255,.96), rgba(248,250,251,.94)),
    radial-gradient(circle at 100% 0%, rgba(47,127,142,.06), transparent 34%);
  backdrop-filter: blur(18px);
  transition: width .2s ease, flex-basis .2s ease, padding .2s ease;
}
.panorama-detail.is-collapsed { width: 46px; flex-basis: 46px; padding: 12px 8px; overflow: hidden; }
.panorama-detail__collapsed-toggle { margin: 2px auto; }
.panorama-detail__head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }

.panorama-detail__badge {
  display: inline-flex;
  padding: 4px 7px;
  border: 1px solid rgba(73,95,114,.07);
  border-radius: 5px;
  color: #5f7485;
  background: #f3f6f8;
  font-size: 8.2px;
  font-weight: 800;
  letter-spacing: .055em;
}
.panorama-detail__badge.is-level-1 { color: #3a5e82; background: #edf2f7; }
.panorama-detail__badge.is-level-2 { color: #536a7b; background: #f0f4f6; }
.panorama-detail__badge.is-level-3 { color: #2f6f7c; background: #eaf4f5; }
.panorama-detail__title { margin-top: 9px; color: #182a3c; font-size: 16.5px; line-height: 1.35; font-weight: 800; }
.panorama-detail__subtitle { margin-top: 4px; color: #8794a0; font-size: 9.2px; line-height: 1.55; }

.panorama-detail__stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; margin-top: 14px; }
.panorama-stat { min-width: 0; padding: 9px 8px; border: 1px solid rgba(70,93,113,.075); border-radius: 9px; background: rgba(246,248,250,.82); }
.panorama-stat span { display: block; color: #8a97a2; font-size: 8.2px; }
.panorama-stat strong { display: block; margin-top: 3px; overflow: hidden; color: #2b4154; font-size: 12.5px; text-overflow: ellipsis; white-space: nowrap; font-variant-numeric: tabular-nums; }
.panorama-detail__section { margin-top: 16px; }
.panorama-detail__section-head { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; margin-bottom: 8px; color: #475e71; font-size: 9.8px; font-weight: 800; }
.panorama-detail__section-head small { color: #9da8b2; font-size: 7.8px; font-weight: 500; }
.panorama-detail__rows { display: flex; flex-direction: column; gap: 5px; }

.panorama-detail__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 54px auto;
  align-items: center;
  gap: 7px;
  width: 100%;
  padding: 7px 8px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: #566b7d;
  text-align: left;
  cursor: pointer;
  transition: all .15s ease;
}
.panorama-detail__row:hover { border-color: rgba(47,127,142,.12); background: rgba(47,127,142,.04); }
.panorama-detail__row-name { overflow: hidden; font-size: 9.3px; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.panorama-detail__row strong { color: #344b5e; font-size: 8.8px; font-variant-numeric: tabular-nums; }
.panorama-detail__bar { height: 3px; overflow: hidden; border-radius: 999px; background: #e8edf0; }
.panorama-detail__bar i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #647f98, #2f7f8e); }
.panorama-detail__guide { display: flex; flex-direction: column; gap: 7px; }
.panorama-guide-item { display: grid; grid-template-columns: 28px 1fr; gap: 7px; align-items: start; padding: 8px; border: 1px solid rgba(76,98,117,.055); border-radius: 8px; background: #f7f9fa; }
.panorama-guide-item b { color: #2f7f8e; font-size: 8.8px; letter-spacing: .05em; }
.panorama-guide-item span { color: #6f8190; font-size: 8.8px; line-height: 1.5; }
.panorama-detail__footer { display: flex; flex-direction: column; gap: 3px; margin-top: 16px; padding-top: 12px; border-top: 1px solid rgba(67,90,109,.085); }
.panorama-detail__footer span { color: #9ba6af; font-size: 8.2px; }
.panorama-detail__footer strong { color: #617687; font-size: 8.3px; line-height: 1.45; font-weight: 600; }

@media (max-width: 1180px) {
  .panorama-toolbar {
    grid-template-columns: auto minmax(0, 1fr);
    grid-template-areas:
      "intro footer"
      "filters filters";
    row-gap: 5px;
  }
  .panorama-filter-grid {
    grid-template-columns: minmax(0, 1.45fr) repeat(4, minmax(0, 1fr));
    gap: 9px;
  }
  .panorama-legend__emerging small { font-size: 7.6px; }
  .emerging-mini-scale { gap: 1px; }
}

@media (max-width: 900px) {
  .panorama-root { min-height: 720px; }
  .panorama-filter-grid {
    grid-template-columns: minmax(0, 1.35fr) repeat(4, minmax(0, 1fr));
    gap: 6px;
  }
  .panorama-control__label { font-size: 10.5px; }
  .panorama-search-box { padding: 0 8px; }
  .panorama-search-box input { font-size: 10.5px; }
  .panorama-control :deep(.panorama-tech-select .el-select__wrapper) { padding: 0 7px; }
  .panorama-control :deep(.panorama-tech-select .el-select__selected-item) { font-size: 10.8px; }
}
</style>

<style>
/* PATH2OFFER PREMIUM SELECT POPPER */
.panorama-premium-popper.el-popper {
  overflow: hidden;
  border: 1px solid rgba(33, 75, 96, .28) !important;
  border-radius: 10px !important;
  background:
    radial-gradient(90% 120% at 12% -28%, rgba(53, 148, 158, .10), transparent 48%),
    linear-gradient(180deg, rgba(253,255,255,.997), rgba(245,249,250,.997)) !important;
  box-shadow:
    0 16px 36px rgba(19, 48, 66, .16),
    inset 0 1px 0 rgba(255,255,255,.95) !important;
  backdrop-filter: blur(16px);
}

.panorama-premium-popper .el-popper__arrow::before {
  border-color: rgba(33, 75, 96, .20) !important;
  background: #f9fcfc !important;
}

.panorama-premium-popper .el-select-dropdown {
  padding: 5px;
}

.panorama-premium-popper .el-select-dropdown__list {
  margin: 0;
  padding: 0;
}

.panorama-premium-popper .el-select-dropdown__item {
  position: relative;
  height: 38px;
  margin: 2px 0;
  padding: 0 14px !important;
  border-radius: 7px;
  color: #17354a;
  font-family: 'Times New Roman', Times, serif;
  font-size: 12.2px;
  font-weight: 700;
  line-height: 38px;
  letter-spacing: .025em;
  text-align: center;
  transition:
    color .15s ease,
    background .15s ease,
    box-shadow .15s ease;
}

.panorama-premium-popper .el-select-dropdown__item:hover,
.panorama-premium-popper .el-select-dropdown__item.is-hovering {
  color: #12384d;
  background:
    linear-gradient(90deg, rgba(37, 116, 132, .08), rgba(58, 147, 153, .045));
}

.panorama-premium-popper .el-select-dropdown__item.is-selected {
  color: #0f5470;
  background:
    linear-gradient(90deg, rgba(38, 127, 143, .13), rgba(57, 153, 158, .07));
  box-shadow:
    inset 3px 0 0 rgba(38, 133, 149, .72),
    inset -1px 0 0 rgba(38, 133, 149, .05);
  font-weight: 650;
}

.panorama-premium-popper .el-select-dropdown__item.is-selected::after {
  content: "";
  position: absolute;
  right: 10px;
  top: 50%;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  transform: translateY(-50%);
  background: rgba(48, 150, 158, .72);
  box-shadow: 0 0 7px rgba(48, 150, 158, .28);
}
</style>

