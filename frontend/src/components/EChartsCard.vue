<template>
  <div class="chart-card">
    <div class="chart-header" v-if="title || $slots.title">
      <slot name="title">
        <h3 class="chart-title">{{ title }}</h3>
      </slot>
      <div class="chart-actions" v-if="$slots.actions">
        <slot name="actions"></slot>
      </div>
    </div>
    <div 
      ref="chartRef" 
      class="chart-container" 
      :style="{ height: height }"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

import 'echarts-wordcloud'


interface Props {
  title?: string
  options: any
  height?: string
  theme?: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: '300px',
  theme: 'default',
  loading: false
})

const emit = defineEmits<{ (e: 'chart-click', params: any): void }>()

const chartRef = ref<HTMLDivElement>()
let chartInstance: echarts.ECharts | null = null


const initChart = () => {
  if (!chartRef.value) return

  if (chartInstance) {
    chartInstance.dispose()
  }


  chartInstance = echarts.init(chartRef.value, props.theme)

  
  if (props.options) {
    chartInstance.setOption(props.options)
  }

 
  chartInstance.on('click', (params: any) => {
    emit('chart-click', params)
  })

 
  window.addEventListener('resize', handleResize)
}


const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}


const updateChart = () => {
  if (chartInstance && props.options) {
    chartInstance.setOption(props.options, true)
  }
}


const setLoading = (loading: boolean) => {
  if (chartInstance) {
    if (loading) {
      chartInstance.showLoading()
    } else {
      chartInstance.hideLoading()
    }
  }
}


watch(() => props.options, () => {
  updateChart()
}, { deep: true })


watch(() => props.loading, (newLoading) => {
  setLoading(newLoading)
})


onMounted(() => {
  nextTick(() => {
    initChart()
  })
})


onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  window.removeEventListener('resize', handleResize)
})


defineExpose({
  chartInstance,
  updateChart,
  setLoading
})
</script>

<style scoped>
.chart-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #f0f0f0;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.chart-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.chart-actions {
  display: flex;
  gap: 8px;
}

.chart-container {
  width: 100%;
  min-height: 200px;
}
</style>