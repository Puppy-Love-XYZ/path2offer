<template>
  <aside class="app-sidebar">
    <div class="brand">
      <div class="brand-logo">
        <img src="../assets/logo.png" alt="logo" />
      </div>
      <div class="brand-info">
        <span class="brand-name">Path2Offer</span>
        <span class="brand-sub">智能就业决策系统</span>
      </div>
    </div>

    <nav class="stepper-nav">
      <template v-for="(step, idx) in steps" :key="step.key">
        <div class="step-item" :class="{
          'is-active': activeIdx === idx,
          'is-done': activeIdx > idx,
        }" @click="navigateTo(step)" role="button">
          <div class="active-bg" />
          <div class="node-col">
            <div class="node-ring" :class="{ pulsing: activeIdx === idx }">
              <el-icon class="node-icon">
                <component :is="step.icon" />
              </el-icon>
            </div>
          </div>
          <div class="label-col">
            <span class="step-seq">STEP {{ idx + 1 }}</span>
            <span class="step-name">{{ step.label }}</span>
          </div>
        </div>
        <div v-if="idx < steps.length - 1" class="connector">
          <div class="connector-track">
            <div class="connector-fill" :class="{ lit: activeIdx > idx }" />
          </div>
        </div>
      </template>
    </nav>

    <div class="sidebar-footer">
      <div class="progress-dots">
        <div v-for="(_, idx) in steps" :key="idx" class="pdot" :class="{
          'pdot--active': activeIdx === idx,
          'pdot--done': activeIdx > idx,
        }" />
      </div>
      <span class="progress-label">{{ activeIdx + 1 }} / {{ steps.length }}</span>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { DataAnalysis, Document, Monitor, ChatDotRound } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const steps = [
  { key: 'persona', label: '岗位画像', icon: DataAnalysis, path: '/persona' },
  { key: 'resume', label: '简历分析', icon: Document, path: '/resume' },
  { key: 'matching', label: '岗位匹配', icon: Monitor, path: '/matching' },
  { key: 'interview', label: '模拟面试', icon: ChatDotRound, path: '/interview' },
] as const

const activeIdx = computed(() => {
  const idx = steps.findIndex(s => route.path.startsWith(s.path))
  return idx >= 0 ? idx : 0
})

function navigateTo(step: (typeof steps)[number]) {
  router.push(step.path)
}
</script>

<style scoped>
.app-sidebar {
  width: 220px;
  min-width: 220px;
  height: 100%;
  background: linear-gradient(160deg, #1e1b4b 0%, #312e81 48%, #1a1740 100%);
  display: flex;
  flex-direction: column;
  box-shadow: 4px 0 28px rgba(79, 70, 229, 0.22);
  position: relative;
  overflow: hidden;
}

.app-sidebar::before {
  content: '';
  position: absolute;
  top: -60px;
  left: -40px;
  width: 220px;
  height: 220px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.28) 0%, transparent 65%);
  pointer-events: none;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 22px 20px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
  flex-shrink: 0;
}

.brand-logo {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.5);
  overflow: hidden;
}

.brand-logo img {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

.brand-info {
  display: flex;
  flex-direction: column;
}

.brand-name {
  font-size: 15px;
  font-weight: 800;
  color: #ffffff;
  line-height: 1.1;
  letter-spacing: -0.3px;
}

.brand-sub {
  font-size: 9px;
  color: rgba(255, 255, 255, 0.35);
  letter-spacing: 0.6px;
  margin-top: 2px;
}

.stepper-nav {
  flex: 1;
  padding: 24px 14px 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 10px;
  border-radius: 12px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: transform 0.15s;
  user-select: none;
}

.step-item:hover {
  transform: translateX(3px);
}

.active-bg {
  position: absolute;
  inset: 0;
  border-radius: 12px;
  background: linear-gradient(100deg, rgba(99, 102, 241, 0.22) 0%, rgba(139, 92, 246, 0.1) 100%);
  border: 1px solid rgba(99, 102, 241, 0.28);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.is-active .active-bg {
  opacity: 1;
}

.node-col {
  flex-shrink: 0;
  width: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.node-ring {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.06);
  border: 1.5px solid rgba(255, 255, 255, 0.1);
  transition: background 0.3s, box-shadow 0.3s, transform 0.3s;
}

.is-done .node-ring {
  background: linear-gradient(135deg, #4338ca, #6366f1);
  border-color: transparent;
  box-shadow: 0 2px 12px rgba(99, 102, 241, 0.45);
}

.is-active .node-ring {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-color: transparent;
  box-shadow: 0 4px 22px rgba(99, 102, 241, 0.65);
  transform: scale(1.08);
}

@keyframes breathe {

  0%,
  100% {
    box-shadow: 0 4px 22px rgba(99, 102, 241, 0.5);
  }

  50% {
    box-shadow: 0 4px 32px rgba(139, 92, 246, 0.9),
      0 0 0 9px rgba(99, 102, 241, 0.09);
  }
}

.node-ring.pulsing {
  animation: breathe 2.6s ease-in-out infinite;
}

.node-icon {
  font-size: 17px;
  color: rgba(255, 255, 255, 0.35);
  transition: color 0.3s;
}

.is-done .node-icon,
.is-active .node-icon {
  color: #ffffff;
}

.label-col {
  display: flex;
  flex-direction: column;
  gap: 2px;
  position: relative;
  z-index: 1;
}

.step-seq {
  font-size: 9.5px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.2);
  letter-spacing: 1px;
  text-transform: uppercase;
  transition: color 0.3s;
}

.is-active .step-seq {
  color: rgba(165, 180, 252, 0.75);
}

.is-done .step-seq {
  color: rgba(99, 102, 241, 0.6);
}

.step-name {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.38);
  transition: color 0.3s;
  line-height: 1.2;
}

.is-active .step-name {
  font-weight: 700;
  color: #ffffff;
}

.is-done .step-name {
  font-weight: 600;
  color: rgba(165, 180, 252, 0.82);
}

.connector-track {
  width: 2px;
  height: 26px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 1px;
  margin-left: 31px;
  overflow: hidden;
  position: relative;
}

.connector-fill {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, #6366f1, #8b5cf6);
  border-radius: 1px;
  transform: scaleY(0);
  transform-origin: top center;
  transition: transform 0.45s cubic-bezier(0.4, 0, 0.2, 1);
}

.connector-fill.lit {
  transform: scaleY(1);
}

.sidebar-footer {
  padding: 14px 20px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.progress-dots {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pdot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.14);
  transition: background 0.3s, width 0.3s, border-radius 0.3s;
}

.pdot--done {
  background: #6366f1;
}

.pdot--active {
  width: 20px;
  border-radius: 3px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.55);
}

.progress-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.28);
  font-weight: 500;
}
</style>