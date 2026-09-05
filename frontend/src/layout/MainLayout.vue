<template>
  <div class="pp-main-layout">

    <!-- 左侧：极简侧边栏 -->
    <PureSidebar />

    <!-- 右侧：顶栏 + 内容 -->
    <div class="pp-content-shell">

      <!-- 极简顶栏 -->
      <header class="pp-topbar">
        <div class="pp-topbar__left">
          <span class="pp-topbar__page-label">{{ pageLabel }}</span>
        </div>
        <div class="pp-topbar__right">
          <div
            class="pp-topbar__user"
            @click="menuOpen = !menuOpen"
            ref="userRef"
          >
            <!-- 用户头像（首字母） -->
            <span class="pp-user-avatar" aria-hidden="true">{{ (user?.username || '?').charAt(0).toUpperCase() }}</span>
            <span class="pp-topbar__username">{{ user?.username || '—' }}</span>
            <!-- CSS 绘制的极细下箭头 -->
            <span class="pp-chevron" :class="{ 'pp-chevron--open': menuOpen }" aria-hidden="true" />
          </div>

          <!-- 下拉菜单 -->
          <Transition name="pp-menu">
            <div v-if="menuOpen" class="pp-topbar__menu">
              <button class="pp-menu-item" @click="go('/profile')">个人信息</button>
              <button class="pp-menu-item" @click="go('/profile?tab=security')">修改密码</button>
              <div class="pp-menu-rule" />
              <button class="pp-menu-item pp-menu-item--danger" @click="handleLogout">退出登录</button>
            </div>
          </Transition>
        </div>
      </header>

      <!-- 页面内容 -->
      <main class="pp-main-content">
        <slot />
      </main>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PureSidebar from '../components/design/PureSidebar.vue'
import { useAuth } from '../composables/useAuth'

defineOptions({ name: 'MainLayout' })

const route  = useRoute()
const router = useRouter()
const { user, logout } = useAuth()

/* ── 当前页面标签 ── */
const PAGE_LABELS: Record<string, string> = {
  '/persona':   '岗位图谱',
  '/position-def': '新兴岗位动态',
  '/matching':  '人岗匹配',
  '/resume':    '简历分析',
  '/interview': '模拟面试',
  '/profile':   '个人中心',
}

const pageLabel = computed(() => {
  const hit = Object.entries(PAGE_LABELS).find(([p]) => route.path.startsWith(p))
  return hit ? hit[1] : 'Path²Offer'
})

/* ── 用户菜单 ── */
const menuOpen  = ref(false)
const userRef   = ref<HTMLElement | null>(null)

function go(path: string) {
  menuOpen.value = false
  router.push(path)
}

function handleLogout() {
  menuOpen.value = false
  logout()
  router.push('/login').catch(() => {})
}

function onClickOutside(e: MouseEvent) {
  if (userRef.value && !userRef.value.contains(e.target as Node)) {
    menuOpen.value = false
  }
}

onMounted(()  => document.addEventListener('click', onClickOutside, true))
onUnmounted(() => document.removeEventListener('click', onClickOutside, true))
</script>

<style scoped>
/* ── 整体布局 ── */
.pp-main-layout {
  height:   100vh;
  display:  flex;
  overflow: hidden;
}

/* ── 右侧容器：顶栏 + 内容纵向排布 ── */
.pp-content-shell {
  flex:            1;
  display:         flex;
  flex-direction:  column;
  overflow:        hidden;
  background:      #F8F9FA;
  min-width:       0;
}

/* ── 极简顶栏 ── */
.pp-topbar {
  height:         52px;
  min-height:     52px;
  display:        flex;
  align-items:    center;
  justify-content: space-between;
  padding:        0 28px 0 32px;
  background:     #FBFBFB;
  border-bottom:  0.5px solid #E5E5E5;
  flex-shrink:    0;
  position:       relative;
  z-index:        40;
}

/* 左：页面名称（衬线）*/
.pp-topbar__left {}

.pp-topbar__page-label {
  font-family:    'Georgia', 'Noto Serif SC', serif;
  font-size:      15px;
  font-weight:    400;
  color:          #1A1A1A;
  letter-spacing: -0.01em;
}

/* 右：用户区 */
.pp-topbar__right {
  position: relative;
}

.pp-topbar__user {
  display:     flex;
  align-items: center;
  gap:         7px;
  cursor:      pointer;
  padding:     5px 8px;
  border-radius: 3px;
  transition:  background 140ms ease;
  user-select: none;
}

.pp-topbar__user:hover {
  background: #F2F3F4;
}

/* CSS 绘制：首字母头像 */
.pp-user-avatar {
  display:        inline-flex;
  align-items:    center;
  justify-content: center;
  width:          24px;
  height:         24px;
  border-radius:  50%;
  background:     #1A3C34;
  color:          #EDFAF6;
  font-family:    var(--pp-font-body);
  font-size:      11px;
  font-weight:    600;
  letter-spacing: 0;
  flex-shrink:    0;
  user-select:    none;
}

.pp-topbar__username {
  font-family:  var(--pp-font-body);
  font-size:    13px;
  font-weight:  500;
  color:        #4B5563;
  white-space:  nowrap;
}

/* CSS 绘制：极细下箭头（chevron）*/
.pp-chevron {
  display:      inline-block;
  width:        8px;
  height:       8px;
  border-right: 1px solid #9CA3AF;
  border-bottom: 1px solid #9CA3AF;
  transform:    rotate(45deg) translateY(-2px);
  transition:   transform 140ms ease;
  flex-shrink:  0;
}

.pp-chevron--open {
  transform: rotate(225deg) translateY(-2px);
}

/* ── 下拉菜单 ── */
.pp-topbar__menu {
  position:      absolute;
  top:           calc(100% + 6px);
  right:         0;
  min-width:     148px;
  background:    #FBFBFB;
  border:        0.5px solid #E0E0E0;
  border-radius: 3px;
  padding:       5px;
  z-index:       200;
}

.pp-menu-item {
  all:           unset;
  display:       block;
  width:         100%;
  padding:       8px 12px;
  font-family:   var(--pp-font-body);
  font-size:     12.5px;
  color:         #4B5563;
  cursor:        pointer;
  border-radius: 2px;
  transition:    background 120ms ease, color 120ms ease;
  box-sizing:    border-box;
}

.pp-menu-item:hover {
  background: #F2F6F5;
  color:      #1A3C34;
}

.pp-menu-item--danger {
  color: #9B4A4A;
}

.pp-menu-item--danger:hover {
  background: #FAF0F0;
  color:      #7A3030;
}

.pp-menu-rule {
  height:     0.5px;
  background: #EBEBEB;
  margin:     4px 8px;
}

/* ── 下拉动画 ── */
.pp-menu-enter-active { transition: opacity 140ms ease, transform 140ms ease; }
.pp-menu-leave-active { transition: opacity 100ms ease, transform 100ms ease; }
.pp-menu-enter-from,
.pp-menu-leave-to     { opacity: 0; transform: translateY(-4px); }

/* ── 主内容区 ── */
.pp-main-content {
  flex:       1;
  overflow-y: auto;
  display:    flex;
  flex-direction: column;
}
</style>
