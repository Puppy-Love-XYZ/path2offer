<template>
  <EChartsCard
    title="薪资分布透视"
    :options="chartOptions"
    height="350px"
  />
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import EChartsCard from './EChartsCard.vue'


const salaryData = ref([
  { category: '应届生', min: 6, q1: 8, median: 10, q3: 12, max: 15 },
  { category: '1-3年', min: 10, q1: 12, median: 15, q3: 18, max: 25 },
  { category: '3-5年', min: 15, q1: 18, median: 22, q3: 28, max: 35 },
  { category: '5-10年', min: 20, q1: 25, median: 32, q3: 40, max: 50 },
  { category: '10年以上', min: 30, q1: 35, median: 45, q3: 55, max: 70 }
])


const educationData = ref([
  { category: '专科', min: 8, q1: 10, median: 12, q3: 15, max: 20 },
  { category: '本科', min: 10, q1: 12, median: 16, q3: 20, max: 28 },
  { category: '硕士', min: 15, q1: 18, median: 22, q3: 28, max: 35 },
  { category: '博士', min: 20, q1: 25, median: 30, q3: 38, max: 50 }
])


const currentData = ref('experience')

// 图表配置
const chartOptions = computed(() => {
  const data = currentData.value === 'experience' ? salaryData.value : educationData.value
  
  return {
    title: {
      show: false
    },
    tooltip: {
      trigger: 'item',
      formatter: function(params: any) {
        const data = params.data
        return `${data.category}<br/>
                最低薪资: ${data.min}k<br/>
                下四分位: ${data.q1}k<br/>
                中位数: ${data.median}k<br/>
                上四分位: ${data.q3}k<br/>
                最高薪资: ${data.max}k`
      }
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%',
      top: '10%'
    },
    xAxis: {
      type: 'category',
      data: data.map(item => item.category),
      axisLabel: {
        interval: 0,
        rotate: 0,
        fontSize: 11
      }
    },
    yAxis: {
      type: 'value',
      name: '薪资 (K)',
      nameLocation: 'middle',
      nameGap: 30,
      axisLabel: {
        formatter: '{value}k'
      }
    },
    series: [
      {
        name: '薪资分布',
        type: 'boxplot',
        data: data.map(item => [item.min, item.q1, item.median, item.q3, item.max]),
        itemStyle: {
          color: '#409EFF',
          borderColor: '#337ecc'
        },
        emphasis: {
          itemStyle: {
            color: '#66b1ff',
            borderColor: '#4c9fff',
            borderWidth: 2,
            shadowBlur: 5,
            shadowOffsetX: 0,
            shadowOffsetY: 0,
            shadowColor: 'rgba(64, 158, 255, 0.5)'
          }
        }
      }
    ]
  }
})

const toggleDataView = () => {
  currentData.value = currentData.value === 'experience' ? 'education' : 'experience'
}


defineExpose({
  toggleDataView,
  currentData
})
</script>

<style scoped>

</style>