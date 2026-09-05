<template>
  <aside
    :class="['sidebar', { 'sidebar--collapsed': collapsed }]"
    role="navigation"
    aria-label="主导航"
  >

    <!-- ══════════════════════════════
         品牌区（折叠时收起至高度0）
    ══════════════════════════════ -->
    <div class="brand-wrap">
      <div class="brand">
        <div class="wordmark">Path<sup class="sup">²</sup>Offer</div>
        <div class="tagline">智能就业决策</div>
      </div>
      <div class="hairline" />
    </div>

    <!-- ══════════════════════════════
         时间轴导航
    ══════════════════════════════ -->
    <nav class="nav">

      <div class="section-label">就业路径</div>

      <ul class="nav-list" role="list">
        <li
          v-for="(item, idx) in navItems"
          :key="item.path"
          class="nav-item"
          role="listitem"
        >
          <!-- 时间轴连接线 -->
          <div v-if="idx > 0" class="tl-conn" />

          <!-- 可点击行 -->
          <button
            class="nav-btn"
            :class="{ 'nav-btn--active': isActive(idx) }"
            type="button"
            :aria-current="isActive(idx) ? 'page' : undefined"
            :title="item.label"
            @click="go(item.path)"
          >
            <!-- 激活左色条 -->
            <span v-if="isActive(idx) && !collapsed" class="accent-bar" aria-hidden="true" />

            <!-- 时间轴节点 -->
            <span
              class="tl-node"
              :class="{ 'tl-node--active': isActive(idx) }"
              aria-hidden="true"
            >
              <el-icon :size="14"><component :is="item.icon" /></el-icon>
            </span>

            <!-- 文字标签 -->
            <span class="nav-label">{{ item.label }}</span>
          </button>

        </li>
      </ul>
    </nav>

    <!-- 弹性留白 -->
    <div class="spacer" />

    <!-- ══════════════════════════════
         底部进度点
    ══════════════════════════════ -->
    <div class="prog-area">
      <div class="prog-row">
        <span
          v-for="(_, i) in navItems"
          :key="i"
          class="prog-dot"
          :class="{ 'prog-dot--active': isActive(i), 'prog-dot--done': isDone(i) }"
        />
      </div>
    </div>

    <!-- ══════════════════════════════
         底部折叠按钮
    ══════════════════════════════ -->
    <button
      class="sidebar-toggle"
      type="button"
      :title="collapsed ? '展开侧边栏' : '收起侧边栏'"
      @click="collapsed = !collapsed"
    >
      <!-- 单个图标，折叠时旋转 180° -->
      <el-icon class="toggle-arrow" :size="12"><DArrowLeft /></el-icon>
    </button>

  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  DataAnalysis, Document, Monitor, ChatDotRound, DArrowLeft, Compass,
} from '@element-plus/icons-vue'

interface NavItem {
  path:  string
  label: string
  icon:  unknown
}

const route    = useRoute()
const router   = useRouter()
const collapsed = ref(false)

const navItems: NavItem[] = [
  { path: '/persona',   label: '岗位图谱', icon: DataAnalysis  },
  { path: '/position-def', label: '新兴岗位动态', icon: Compass    },
  { path: '/resume',    label: '简历分析', icon: Document      },
  { path: '/matching',  label: '人岗匹配', icon: Monitor       },
  { path: '/interview', label: '模拟面试', icon: ChatDotRound  },
]

const activeIdx = computed<number>(() => {
  const idx = navItems.findIndex(
    item => route.path === item.path || route.path.startsWith(item.path + '/'),
  )
  return idx >= 0 ? idx : -1
})

function isActive(idx: number): boolean { return activeIdx.value === idx }
function isDone(idx: number):   boolean { return activeIdx.value > idx  }
function go(path: string):      void    { router.push(path).catch(() => {}) }
</script>

<style scoped>
/* ════════════════════════════════════════════════════════
   PureSidebar — Dark "Ink" sidebar + Paper main content
   ────────────────────────────────────────────────────────
   侧边栏色板（深色，低饱和度）:
     背景     #1B2236  (深海军蓝, S≈33%)
     边框     rgba(255,255,255,0.05)
     静默文字 rgba(255,255,255,0.38)
     激活文字 #FFFFFF
     激活底色 rgba(255,255,255,0.10)
     激活色条 rgba(255,255,255,0.75)
     连接线   rgba(255,255,255,0.10)
     节点底色 rgba(255,255,255,0.06)
   ════════════════════════════════════════════════════════ */

/* ── 侧边栏主体 ── */
.sidebar {
  width:          220px;
  min-width:      220px;
  height:         100vh;
  background:     linear-gradient(170deg, #0C1A2D 0%, #152845 48%, #1C3456 100%);
  border-right:   1px solid rgba(255, 255, 255, 0.05);
  display:        flex;
  flex-direction: column;
  font-family:    'Inter', 'PingFang SC', 'Helvetica Neue', system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
  flex-shrink:    0;
  overflow:       hidden;
  transition:
    width     320ms cubic-bezier(0.4, 0, 0.2, 1),
    min-width 320ms cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar--collapsed {
  width:     64px;
  min-width: 64px;
}

/* ── 品牌区包装（折叠时高度收至 0） ── */
.brand-wrap {
  overflow:   hidden;
  max-height: 100px;
  opacity:    1;
  transition:
    max-height 320ms cubic-bezier(0.4, 0, 0.2, 1),
    opacity    200ms ease;
}

.sidebar--collapsed .brand-wrap {
  max-height: 0;
  opacity:    0;
  pointer-events: none;
}

.brand {
  padding: 26px 20px 18px;
}

.wordmark {
  font-family:    Georgia, 'Noto Serif SC', 'Times New Roman', serif;
  font-size:      17px;
  font-weight:    400;
  color:          rgba(255, 255, 255, 0.92);
  letter-spacing: -0.02em;
  line-height:    1;
  user-select:    none;
  white-space:    nowrap;
}

.sup {
  font-size:      10px;
  vertical-align: super;
  line-height:    0;
  margin-left:    1px;
}

.tagline {
  margin-top:     7px;
  font-size:      8px;
  font-weight:    700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color:          rgba(255, 255, 255, 0.25);
  line-height:    1;
  user-select:    none;
  white-space:    nowrap;
}

/* ── 发丝线 ── */
.hairline {
  height:     1px;
  background: rgba(255, 255, 255, 0.07);
  margin:     0 16px;
}

/* ── 导航区 ── */
.nav {
  padding: 18px 0 12px;
  flex-shrink: 0;
  /* 折叠时顶部多留空间 */
  transition: padding-top 320ms cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar--collapsed .nav {
  padding-top: 22px;
}

/* 分节小标 */
.section-label {
  font-size:      8px;
  font-weight:    700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color:          rgba(255, 255, 255, 0.22);
  padding:        0 16px;
  margin-bottom:  12px;
  line-height:    1;
  user-select:    none;
  white-space:    nowrap;
  /* 折叠时淡出 */
  opacity:    1;
  max-height: 20px;
  overflow:   hidden;
  transition:
    opacity    200ms ease,
    max-height 200ms ease,
    margin     200ms ease;
}

.sidebar--collapsed .section-label {
  opacity:    0;
  max-height: 0;
  margin:     0;
}

/* ── 导航列表 ── */
.nav-list {
  list-style: none;
  margin:     0;
  padding:    0;
}

/* 折叠时：nav-item 居中排列（用于连接线对齐） */
.nav-item {
  display: block;
}

.sidebar--collapsed .nav-item {
  display:        flex;
  flex-direction: column;
  align-items:    center;
}

/* ── 时间轴连接线 ── */
/*
  连接线对齐计算：
  展开: nav-btn padding-left=14px, node 宽=32px
        → node 中心 = 14+16 = 30px from nav-item left
  折叠: nav-item flex center, line margin auto → 自动居中
*/
.tl-conn {
  width:  1px;
  height: 14px;
  background: linear-gradient(
    to bottom,
    rgba(255, 255, 255, 0.04),
    rgba(255, 255, 255, 0.12) 25%,
    rgba(255, 255, 255, 0.12) 75%,
    rgba(255, 255, 255, 0.04)
  );
  margin-left:   30px;
  border-radius: 1px;
}

.sidebar--collapsed .tl-conn {
  margin-left:  auto;
  margin-right: auto;
}

/* ── 导航按钮 ── */
.nav-btn {
  all:           unset;
  display:       flex;
  align-items:   center;
  gap:           10px;
  width:         100%;
  box-sizing:    border-box;
  padding:       4px 14px;
  border-radius: 8px;
  cursor:        pointer;
  position:      relative;
  transition:    background 150ms ease;
}

.nav-btn:hover:not(.nav-btn--active) {
  background: rgba(255, 255, 255, 0.06);
}

.nav-btn--active {
  background: rgba(255, 255, 255, 0.10);
}

/* 折叠时：内容居中 */
.sidebar--collapsed .nav-btn {
  padding:         4px 0;
  justify-content: center;
}

/* ── 激活左色条 ── */
.accent-bar {
  position:      absolute;
  left:          0;
  top:           50%;
  transform:     translateY(-50%);
  width:         3px;
  height:        20px;
  background:    rgba(255, 255, 255, 0.7);
  border-radius: 0 2px 2px 0;
  animation:     barIn 250ms cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

@keyframes barIn {
  from { opacity: 0; height: 5px; }
  to   { opacity: 1; height: 20px; }
}

/* ── 时间轴节点 ── */
.tl-node {
  width:           32px;
  height:          32px;
  border-radius:   8px;
  display:         flex;
  align-items:     center;
  justify-content: center;
  flex-shrink:     0;
  color:           rgba(255, 255, 255, 0.35);
  background:      rgba(255, 255, 255, 0.06);
  border:          1px solid rgba(255, 255, 255, 0.09);
  transition:
    background   200ms ease,
    border-color 200ms ease,
    color        200ms ease,
    box-shadow   200ms ease;
}

.nav-btn:hover:not(.nav-btn--active) .tl-node {
  background:   rgba(255, 255, 255, 0.10);
  border-color: rgba(255, 255, 255, 0.15);
  color:        rgba(255, 255, 255, 0.60);
}

.tl-node--active {
  background:   rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.28);
  color:        #FFFFFF;
  box-shadow:   0 0 0 3px rgba(255, 255, 255, 0.05);
}

/* ── 文字标签 ── */
.nav-label {
  font-size:      13.5px;
  font-weight:    400;
  letter-spacing: 0.01em;
  color:          rgba(255, 255, 255, 0.42);
  white-space:    nowrap;
  overflow:       hidden;
  flex:           1;
  line-height:    1;
  /* 折叠时淡出 + 收缩 */
  opacity:    1;
  max-width:  160px;
  transition:
    opacity   200ms ease,
    max-width 300ms cubic-bezier(0.4, 0, 0.2, 1),
    color     150ms ease;
}

.sidebar--collapsed .nav-label {
  opacity:   0;
  max-width: 0;
}

.nav-btn--active .nav-label {
  font-weight: 600;
  color:       rgba(255, 255, 255, 0.95);
}

.nav-btn:hover:not(.nav-btn--active) .nav-label {
  color: rgba(255, 255, 255, 0.68);
}

/* ── 弹性留白 ── */
.spacer { flex: 1; }

/* ── 底部进度点 ── */
.prog-area {
  padding-bottom: 10px;
  flex-shrink:    0;
  /* 折叠时隐藏 */
  opacity:    1;
  max-height: 32px;
  overflow:   hidden;
  transition:
    opacity    200ms ease,
    max-height 200ms ease;
}

.sidebar--collapsed .prog-area {
  opacity:    0;
  max-height: 0;
}

.prog-row {
  display:         flex;
  align-items:     center;
  justify-content: center;
  gap:             6px;
}

.prog-dot {
  width:         5px;
  height:        5px;
  border-radius: 50%;
  background:    rgba(255, 255, 255, 0.16);
  transition:
    background    250ms ease,
    width         250ms ease,
    border-radius 250ms ease;
}

.prog-dot--done {
  background: rgba(255, 255, 255, 0.32);
}

.prog-dot--active {
  width:         16px;
  border-radius: 3px;
  background:    rgba(255, 255, 255, 0.7);
}

/* ════════════════════════════════════════════════════════
   底部折叠按钮
   ════════════════════════════════════════════════════════ */
.sidebar-toggle {
  all:             unset;
  display:         flex;
  align-items:     center;
  justify-content: center;
  width:           100%;
  box-sizing:      border-box;
  padding:         14px 0;
  cursor:          pointer;
  flex-shrink:     0;
  /* 顶部分隔线 */
  border-top:      1px solid rgba(255, 255, 255, 0.07);
  color:           rgba(255, 255, 255, 0.28);
  transition:
    background 160ms ease,
    color      160ms ease;
}

.sidebar-toggle:hover {
  background: rgba(255, 255, 255, 0.05);
  color:      rgba(255, 255, 255, 0.55);
}

/* 折叠时：同样居中，无需额外样式 */
.sidebar--collapsed .sidebar-toggle {
  padding: 14px 0;
}

/* 折叠按钮图标（默认 ← 指向左，折叠后旋转 180° → 指向右） */
.toggle-arrow {
  flex-shrink: 0;
  transition:  transform 320ms cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar--collapsed .toggle-arrow {
  transform: rotate(180deg);
}
</style>
