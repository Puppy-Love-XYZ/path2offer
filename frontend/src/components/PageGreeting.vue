<template>
  <div v-if="greetingName" class="pp-greeting">
    <div class="pp-greeting__left">
      <span class="pp-greeting__name">{{ greetingName }}</span>
      <span class="pp-greeting__sep" aria-hidden="true" />
      <span class="pp-greeting__tip">{{ tip }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuth } from '@/composables/useAuth'

defineProps<{ tip: string }>()

const { user, displayName } = useAuth()

const greetingName = computed(() => displayName.value || user.value?.username || '')
</script>

<style scoped>
.pp-greeting {
  display: flex;
  align-items: center;
  padding: 14px 0 10px;
  gap: 16px;
  font-family: 'Inter', 'PingFang SC', system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
}

.pp-greeting__left {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}

.pp-greeting__name {
  font-family: 'Georgia', 'Noto Serif SC', serif;
  font-size: 15px;
  font-weight: 400;
  color: #1A1A1A;
  letter-spacing: -0.01em;
  white-space: nowrap;
}

.pp-greeting__sep {
  display: inline-block;
  width: 0;
  height: 11px;
  border-left: 0.5px solid #D0D0D0;
  align-self: center;
  flex-shrink: 0;
}

.pp-greeting__tip {
  font-size: 12.5px;
  color: #9CA3AF;
  line-height: 1.4;
  font-style: italic;
}
</style>