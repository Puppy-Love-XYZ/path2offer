<template>
  <div class="geo-heatmap-card">
    <div class="chart-header">
      <h3 class="chart-title">岗位地理分布热力图</h3>
      <div class="chart-subtitle">{{ jobName }}岗位在中国的分布情况</div>
    </div>
    <div class="map-container" ref="mapContainer"></div>
    <div v-if="loading" class="loading-overlay">
      <el-icon class="is-loading">
        <Loading />
      </el-icon>
      <span>加载地理数据中...</span>
    </div>
    <div v-if="error" class="error-message">
      <el-icon>
        <Warning />
      </el-icon>
      <span>{{ error }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.heat'
import { Loading, Warning } from '@element-plus/icons-vue'

declare module 'leaflet' {
  namespace heat {
    function layer(latlngs: number[][], options?: any): any
  }
  namespace L {
    function heatLayer(latlngs: number[][], options?: any): any
  }
}

import { fetchJobGeoDistribution } from '../api/analysis'

const props = defineProps<{
  jobName: string
}>()

const emit = defineEmits<{
  (e: 'cityClick', city: string, count: number): void
}>()

const mapContainer = ref<HTMLElement | null>(null)
const map = ref<any>(null)
const heatLayer = ref<any>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const cityData = ref<any[]>([])
const geoData = ref<any[]>([])

const initMap = () => {
  if (!mapContainer.value) return

  map.value = L.map(mapContainer.value, {
    center: [35.86166, 104.195397],
    zoom: 5,
    minZoom: 4,
    maxZoom: 12,
    zoomControl: true,
    attributionControl: true,
    maxBounds: [
      [53.55, 73.66],
      [18.17, 135.08]
    ],
    maxBoundsViscosity: 0.9
  })

  const tileLayer = L.tileLayer('https://webst01.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}', {
    attribution: '© 高德地图',
    maxZoom: 18
  })

  if (map.value) {
    tileLayer.addTo(map.value)
  }
}

const clearMap = () => {
  if (heatLayer.value && map.value) {
    map.value.removeLayer(heatLayer.value)
    heatLayer.value = null
  }
}

const updateHeatmap = async () => {
  if (!props.jobName) return

  loading.value = true
  error.value = null

  try {
    clearMap()

    const data = await fetchJobGeoDistribution(props.jobName)
    cityData.value = data.city_data || []
    geoData.value = data.geo_data || []

    if (cityData.value.length > 0 && map.value) {
      const heatData = cityData.value.map((item: any) => [
        item.lat,
        item.lng,
        item.value
      ])

      heatLayer.value = (L as any).heatLayer(heatData, {
        radius: 35,
        blur: 25,
        maxZoom: 12,
        minOpacity: 0.3,
        maxOpacity: 0.9,
        gradient: {
          0.0: '#ffffcc',
          0.2: '#ffeda0',
          0.3: '#fed976',
          0.4: '#feb24c',
          0.5: '#fd8d3c',
          0.6: '#fc4e2a',
          0.7: '#e31a1c',
          0.8: '#bd0026',
          1.0: '#800026'
        }
      })

      if (map.value) {
        heatLayer.value.addTo(map.value)
      }

      if (cityData.value.length > 0 && map.value) {
        const bounds = L.latLngBounds(
          cityData.value.map((item: any) => L.latLng(item.lat, item.lng))
        )
        map.value.fitBounds(bounds, { padding: [50, 50] })
      }
    }
  } catch (err) {
    console.error('Failed to load geo data:', err)
    error.value = '加载地理数据失败，请重试'
  } finally {
    loading.value = false
  }
}

watch(() => props.jobName, (newJobName) => {
  if (newJobName) {
    updateHeatmap()
  }
})

onMounted(() => {
  initMap()
  if (props.jobName) {
    updateHeatmap()
  }
})

onBeforeUnmount(() => {
  if (map.value) {
    map.value.remove()
  }
})
</script>

<style scoped>
.geo-heatmap-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid #f0f0f0;
  position: relative;
  height: 100%;
  min-height: 450px;
  display: flex;
  flex-direction: column;
}

.chart-header {
  margin-bottom: 16px;
  text-align: center;
}

.chart-title {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.chart-subtitle {
  font-size: 12px;
  color: #909399;
}

.map-container {
  flex: 1;
  border-radius: 4px;
  overflow: hidden;
  min-height: 400px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 8px;
  z-index: 1000;
}

.loading-overlay .is-loading {
  font-size: 24px;
  color: #409EFF;
}

.error-message {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(255, 73, 73, 0.1);
  border: 1px solid #F56C6C;
  border-radius: 4px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #F56C6C;
  z-index: 1000;
}

:deep(.city-marker) {
  background: transparent;
  border: none;
  transform: translate(-50%, -50%);
  transition: transform 0.2s ease;
}

:deep(.city-marker.clickable:hover) {
  transform: translate(-50%, -50%) scale(1.1);
  z-index: 100;
}

:deep(.marker-content) {
  color: white;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

:deep(.city-marker.clickable .marker-content:hover) {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}

:deep(.leaflet-popup-content) {
  min-width: 120px;
}

:deep(.popup-content h4) {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 14px;
}

:deep(.popup-content p) {
  margin: 0;
  color: #606266;
  font-size: 12px;
}

:deep(.click-hint) {
  margin-top: 8px !important;
  cursor: pointer;
}

:deep(.click-hint:hover) {
  text-decoration: underline;
}

:deep(.leaflet-container) {
  background: #f0f2f5;
}

:deep(.leaflet-control-attribution) {
  font-size: 10px;
}
</style>