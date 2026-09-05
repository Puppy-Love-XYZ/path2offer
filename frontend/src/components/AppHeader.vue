<template>
  <header class="pp-header">
    <div class="pp-header__brand">
      <span class="pp-header__wordmark">
        Path<sup class="pp-header__sup">2</sup>Offer
      </span>
      <span class="pp-header__divider" aria-hidden="true" />
      <span class="pp-header__page">{{ pageLabel }}</span>
    </div>

    <div class="pp-header__user-wrap" ref="userRef">
      <button class="pp-header__user-btn" type="button" @click="menuOpen = !menuOpen" :aria-expanded="menuOpen"
        aria-haspopup="menu">
        <span class="pp-user-indicator" aria-hidden="true" />
        <span class="pp-header__username">{{ displayName || '—' }}</span>
        <span class="pp-header__chevron" :class="{ open: menuOpen }" aria-hidden="true" />
      </button>

      <Transition name="pp-header-menu">
        <div v-if="menuOpen" class="pp-header__menu" role="menu">
          <button class="pp-hmenu-item" role="menuitem" @click="go('/profile')">
            个人信息
          </button>
          <button class="pp-hmenu-item" role="menuitem" @click="go('/profile?tab=security')">
            修改密码
          </button>
          <div class="pp-hmenu-rule" role="separator" />
          <button class="pp-hmenu-item pp-hmenu-item--danger" role="menuitem" @click="doLogout">
            退出登录
          </button>
        </div>
      </Transition>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const route = useRoute()
const router = useRouter()
const { displayName, logout } = useAuth()

const PAGE_LABELS: Record<string, string> = {
  '/persona': '岗位画像',
  '/matching': '岗位匹配',
  '/resume': '简历分析',
  '/interview': '模拟面试',
  '/profile': '个人中心',
}

const pageLabel = computed(() => {
  const hit = Object.entries(PAGE_LABELS).find(([p]) => route.path.startsWith(p))
  return hit ? hit[1] : ''
})

const menuOpen = ref(false)
const userRef = ref<HTMLElement | null>(null)

function go(path: string) {
  menuOpen.value = false
  router.push(path)
}

function doLogout() {
  menuOpen.value = false
  logout()
  router.push('/login').catch(() => { })
}

function onClickOutside(e: MouseEvent) {
  if (userRef.value && !userRef.value.contains(e.target as Node)) {
    menuOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', onClickOutside, true))
onUnmounted(() => document.removeEventListener('click', onClickOutside, true))
</script>

<style scoped>
.pp-header {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  background: #FBFBFB;
  border-bottom: 0.5px solid #E5E5E5;
  flex-shrink: 0;
  position: relative;
  z-index: 100;
  font-family: 'Inter', system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
}

.pp-header__brand {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.pp-header__wordmark {
  font-family: 'Georgia', serif;
  font-size: 16px;
  font-weight: 400;
  color: #1A1A1A;
  letter-spacing: -0.02em;
  line-height: 1;
}

.pp-header__sup {
  font-family: 'Georgia', serif;
  font-size: 9px;
  vertical-align: super;
  line-height: 0;
  margin-left: 0.5px;
}

.pp-header__divider {
  display: inline-block;
  width: 0;
  height: 12px;
  border-left: 0.5px solid #CCCCCC;
  align-self: center;
}

.pp-header__page {
  font-family: 'Inter', system-ui, sans-serif;
  font-size: 12px;
  color: #9CA3AF;
  font-weight: 400;
  letter-spacing: 0.02em;
}

.pp-header__user-wrap {
  position: relative;
}

.pp-header__user-btn {
  all: unset;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 5px 8px;
  border-radius: 3px;
  transition: background 140ms ease;
}

.pp-header__user-btn:hover {
  background: #F3F4F5;
}

.pp-user-indicator {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #1A3C34;
  flex-shrink: 0;
}

.pp-header__username {
  font-size: 12px;
  font-weight: 500;
  color: #4B5563;
  white-space: nowrap;
}

.pp-header__chevron {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-right: 1px solid #9CA3AF;
  border-bottom: 1px solid #9CA3AF;
  transform: rotate(45deg) translateY(-2px);
  transition: transform 140ms ease;
}

.pp-header__chevron.open {
  transform: rotate(225deg) translateY(-2px);
}

.pp-header__menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 144px;
  background: #FBFBFB;
  border: 0.5px solid #E0E0E0;
  border-radius: 3px;
  padding: 5px;
  z-index: 200;
}

.pp-hmenu-item {
  all: unset;
  display: block;
  width: 100%;
  box-sizing: border-box;
  padding: 8px 12px;
  font-size: 12.5px;
  color: #4B5563;
  cursor: pointer;
  border-radius: 2px;
  transition: background 120ms ease, color 120ms ease;
}

.pp-hmenu-item:hover {
  background: #F2F6F5;
  color: #1A3C34;
}

.pp-hmenu-item--danger {
  color: #9B4A4A;
}

.pp-hmenu-item--danger:hover {
  background: #FAF0F0;
  color: #7A3030;
}

.pp-hmenu-rule {
  height: 0.5px;
  background: #EBEBEB;
  margin: 4px 8px;
}

.pp-header-menu-enter-active {
  transition: opacity 140ms ease, transform 140ms ease;
}

.pp-header-menu-leave-active {
  transition: opacity 100ms ease;
}

.pp-header-menu-enter-from,
.pp-header-menu-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>