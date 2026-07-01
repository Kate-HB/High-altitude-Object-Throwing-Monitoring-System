<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { fetchOverview } from '../api/statistics'
import { normalizeOverview } from '../utils/dashboard'

const overview = ref(normalizeOverview(null))
const loading = ref(false)

// Chart refs
const trendRef = ref(null)
const confRef = ref(null)
const statusRef = ref(null)
let trendChart = null
let confChart = null
let statusChart = null

// ── Metrics ──
const metrics = computed(() => {
  const status = overview.value.status_distribution
  return [
    { label: '今日事件', value: overview.value.today_event_count, color: '#ffb020', glow: 'rgba(255, 176, 32, 0.22)' },
    { label: '累计事件', value: overview.value.total_event_count, color: '#00d8ff', glow: 'rgba(0, 216, 255, 0.22)' },
    { label: '已确认', value: status.confirmed || 0, color: '#00ffb2', glow: 'rgba(0, 255, 178, 0.22)' },
    { label: '误报', value: status.false_alarm || 0, color: '#ff4d4f', glow: 'rgba(255, 77, 79, 0.22)' },
  ]
})

const recentEvents = computed(() => overview.value.recent_events)

// ── Chart options ──
const COLORS = { text: '#91a8c7', border: '#1e3a5f', cyan: '#00d8ff', green: '#00ffb2', yellow: '#ffb020', red: '#ff4d4f' }

function makeTrendOption(data) {
  const dates = data.map(d => d.date?.slice(5) || d.date) // MM-DD
  const values = data.map(d => d.count)
  return {
    grid: { top: 16, right: 16, bottom: 28, left: 36 },
    xAxis: { type: 'category', data: dates, axisLine: { lineStyle: { color: COLORS.border } }, axisLabel: { color: COLORS.text, fontSize: 12 } },
    yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { color: '#1e3a5f33' } }, axisLabel: { color: COLORS.text, fontSize: 12 } },
    series: [{ type: 'bar', data: values, barWidth: 18, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#12c6e8' }, { offset: 1, color: '#0d8196' }]), borderRadius: [4, 4, 0, 0] } }],
    tooltip: { trigger: 'axis' },
  }
}

function makeConfOption(dist) {
  const data = [
    { name: '0.35-0.5', value: dist['low_0.35_0.5'] || 0 },
    { name: '0.5-0.7', value: dist['mid_0.5_0.7'] || 0 },
    { name: '0.7-1.0', value: dist['high_0.7_1.0'] || 0 },
  ]
  return {
    grid: { top: 16, right: 16, bottom: 28, left: 36 },
    xAxis: { type: 'category', data: data.map(d => d.name), axisLine: { lineStyle: { color: COLORS.border } }, axisLabel: { color: COLORS.text, fontSize: 12 } },
    yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { color: '#1e3a5f33' } }, axisLabel: { color: COLORS.text, fontSize: 12 } },
    series: [{
      type: 'bar', data: data.map((d, i) => ({ value: d.value, itemStyle: { color: ['#11d0a1', '#d99a22', '#df464c'][i], borderRadius: [4, 4, 0, 0] } })), barWidth: 36,
    }],
    tooltip: { trigger: 'axis' },
  }
}

function makeStatusOption(dist) {
  const data = [
    { name: '待确认', value: dist.unconfirmed || 0, itemStyle: { color: COLORS.yellow } },
    { name: '已确认', value: dist.confirmed || 0, itemStyle: { color: COLORS.green } },
    { name: '误报', value: dist.false_alarm || 0, itemStyle: { color: COLORS.red } },
  ].filter(d => d.value > 0)
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, textStyle: { color: COLORS.text } },
    series: [{
      type: 'pie', radius: ['45%', '70%'], center: ['50%', '45%'], data,
      label: { color: COLORS.text },
    }],
  }
}

function initCharts() {
  if (trendRef.value) trendChart = echarts.init(trendRef.value, null, { height: 240 })
  if (confRef.value) confChart = echarts.init(confRef.value, null, { height: 240 })
  if (statusRef.value) statusChart = echarts.init(statusRef.value, null, { height: 240 })
}

function updateCharts() {
  const trendData = overview.value.daily_trend
  const confData = overview.value.confidence_distribution
  const statusData = overview.value.status_distribution
  if (trendChart && trendData.length) trendChart.setOption(makeTrendOption(trendData))
  if (confChart) confChart.setOption(makeConfOption(confData))
  if (statusChart) statusChart.setOption(makeStatusOption(statusData))
}

function disposeCharts() {
  trendChart?.dispose()
  confChart?.dispose()
  statusChart?.dispose()
  trendChart = confChart = statusChart = null
}

function handleResize() {
  trendChart?.resize()
  confChart?.resize()
  statusChart?.resize()
}

async function loadOverview() {
  loading.value = true
  try {
    const res = await fetchOverview()
    overview.value = normalizeOverview(res.data)
  } catch {
    overview.value = normalizeOverview(null)
  } finally {
    loading.value = false
    await nextTick()
    updateCharts()
  }
}

onMounted(async () => {
  await nextTick()
  initCharts()
  await loadOverview()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  disposeCharts()
})

watch(overview, () => {
  nextTick(() => updateCharts())
}, { deep: true })
</script>

<template>
  <div class="dashboard-page" v-loading="loading">
    <!-- Metric row -->
    <section class="metric-row">
      <div v-for="item in metrics" :key="item.label" class="metric-card">
        <span>{{ item.label }}</span>
        <strong :style="{ color: item.color }">{{ item.value }}</strong>
        <i :style="{ background: item.glow }"></i>
      </div>
    </section>

    <!-- Charts row -->
    <section class="chart-grid">
      <div class="panel">
        <h3>近7日事件趋势</h3>
        <div ref="trendRef" class="echarts-box"></div>
      </div>
      <div class="panel">
        <h3>置信度分布</h3>
        <div ref="confRef" class="echarts-box"></div>
      </div>
    </section>

    <!-- Bottom row -->
    <section class="bottom-grid">
      <div class="panel">
        <h3>状态分布</h3>
        <div ref="statusRef" class="echarts-box"></div>
      </div>
      <div class="panel recent-panel">
        <div class="table-head">
          <span>时间</span>
          <span>置信度</span>
          <span>状态</span>
        </div>
        <div v-if="recentEvents.length === 0" class="empty-row">暂无报警事件</div>
        <div v-for="event in recentEvents" :key="event.id" class="table-row">
          <span>{{ event.created_at }}</span>
          <span>{{ (event.confidence * 100).toFixed(0) }}%</span>
          <span :class="['status-tag', event.status]">{{ event.status === 'confirmed' ? '已确认' : event.status === 'false_alarm' ? '误报' : '待确认' }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.dashboard-page {
  max-width: 1080px;
}

.metric-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

.metric-card,
.panel {
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
}

.metric-card {
  position: relative;
  height: 112px;
  padding: 22px;
  overflow: hidden;
}

.metric-card span {
  display: block;
  color: #91a8c7;
  font-size: 14px;
}

.metric-card strong {
  display: block;
  margin-top: 18px;
  font-family: "DIN Alternate", Consolas, monospace;
  font-size: 34px;
  line-height: 1;
}

.metric-card i {
  position: absolute;
  top: 28px;
  right: 28px;
  width: 54px;
  height: 54px;
  border-radius: 50%;
}

.chart-grid,
.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}

.chart-grid { margin-bottom: 32px; }

.panel {
  height: 300px;
  padding: 22px;
}

.panel h3 {
  color: #eaf6ff;
  font-size: 16px;
  margin-bottom: 8px;
}

.echarts-box {
  width: 100%;
  height: 240px;
}

.recent-panel {
  padding: 20px 22px;
  overflow-y: auto;
}

.table-head,
.table-row {
  display: grid;
  grid-template-columns: 1fr 0.6fr 0.6fr;
  min-height: 42px;
  align-items: center;
  border-bottom: 1px solid #1e3a5f;
  color: #d6e4f2;
  font-size: 14px;
}

.table-head {
  color: #91a8c7;
  font-weight: 700;
}

.empty-row {
  color: #52657f;
  padding: 20px 0;
  text-align: center;
}

.status-tag.unconfirmed { color: #ffb020; }
.status-tag.confirmed { color: #00ffb2; }
.status-tag.false_alarm { color: #91a8c7; }
</style>
