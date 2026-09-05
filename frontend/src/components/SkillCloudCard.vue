<template>
  <div class="chart-card">
    <div class="chart-header">
      <h3 class="chart-title">技能需求词云</h3>
      <div class="chart-subtitle">市场需求最火热的技术标签</div>
    </div>
    <div class="skill-cloud">
      <div 
        v-for="skill in skillData" 
        :key="skill.name"
        class="skill-tag"
        :style="getSkillStyle(skill)"
        @click="handleSkillClick(skill)"
      >
        {{ skill.name }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'


const skillData = ref([
  { name: 'Vue.js', value: 1200, category: 'frontend' },
  { name: 'React', value: 1100, category: 'frontend' },
  { name: 'TypeScript', value: 1000, category: 'language' },
  { name: 'Python', value: 950, category: 'backend' },
  { name: 'Java', value: 900, category: 'backend' },
  { name: 'JavaScript', value: 880, category: 'language' },
  { name: 'Node.js', value: 820, category: 'backend' },
  { name: 'Spring Boot', value: 780, category: 'backend' },
  { name: 'MySQL', value: 750, category: 'database' },
  { name: 'Docker', value: 720, category: 'devops' },
  { name: 'Kubernetes', value: 680, category: 'devops' },
  { name: 'AWS', value: 650, category: 'cloud' },
  { name: 'MongoDB', value: 620, category: 'database' },
  { name: 'Redis', value: 590, category: 'database' },
  { name: '微服务', value: 560, category: 'architecture' },
  { name: 'AI/ML', value: 520, category: 'ai' },
  { name: 'DevOps', value: 480, category: 'devops' },
  { name: '敏捷开发', value: 450, category: 'methodology' },
  { name: 'RESTful API', value: 420, category: 'backend' },
  { name: 'GraphQL', value: 380, category: 'backend' }
])


const getSkillStyle = (skill: any) => {
  const maxValue = Math.max(...skillData.value.map(s => s.value))
  const minValue = Math.min(...skillData.value.map(s => s.value))
  

  const fontSize = 14 + ((skill.value - minValue) / (maxValue - minValue)) * 18
  

  const categoryColors = {
    frontend: '#409EFF',
    backend: '#67C23A',
    database: '#E6A23C',
    devops: '#F56C6C',
    cloud: '#909399',
    ai: '#9C27B0',
    language: '#FF9800',
    architecture: '#00BCD4',
    methodology: '#795548'
  }
  
  return {
    fontSize: `${fontSize}px`,
    color: categoryColors[skill.category as keyof typeof categoryColors] || '#409EFF',
    fontWeight: skill.value > 800 ? 'bold' : 'normal'
  }
}

const handleSkillClick = (skill: any) => {
  console.log(`点击技能: ${skill.name}, 需求强度: ${skill.value}`)
  
}

onMounted(() => {
  console.log('技能词云组件已加载')
})
</script>

<style scoped>
.chart-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #f0f0f0;
  height: 350px;
  display: flex;
  flex-direction: column;
}

.chart-header {
  margin-bottom: 16px;
  text-align: center;
}

.chart-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.chart-subtitle {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.skill-cloud {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 10px;
  overflow: hidden;
}

.skill-tag {
  display: inline-block;
  padding: 4px 8px;
  margin: 2px;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.1);
  user-select: none;
  position: relative;
}

.skill-tag:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 10;
}

.skill-tag::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: inherit;
  opacity: 0.1;
  background: currentColor;
  z-index: -1;
}
</style>