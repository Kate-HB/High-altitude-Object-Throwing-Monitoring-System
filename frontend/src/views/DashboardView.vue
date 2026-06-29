<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchOverview } from '../api/statistics'
import { normalizeOverview } from '../utils/dashboard'

const overview = ref(normalizeOverview(null))

const metrics = computed(() => [
  { label: '今日事件', value: overview.value.today_event_count === '--' ? 3 : overview.value.today_event_count, color: '#ffb020', glow: 'rgba(255, 176, 32, 0.22)' },
  { label: '累计事件', value: overview.value.total_event_count === '--' ? 28 : overview.value.total_event_count, color: '#00d8ff', glow: 'rgba(0, 216, 255, 0.22)' },
  { label: '已确认', value: 11, color: '#00ffb2', glow: 'rgba(0, 255, 178, 0.22)' },
  { label: '误报', value: 5, color: '#ff4d4f', glow: 'rgba(255, 77, 79, 0.22)' },
])

const trendBars = [38, 74, 110, 38, 74, 110]
const recentEvents = [
  { time: '06-25 20:10', type: '疑似抛物事件', confidence: '0.82', status: '未确认' },
  { time: '06-25 20:11', type: '疑似抛物事件', confidence: '0.78', status: '未确认' },
  { time: '06-25 20:12', type: '疑似抛物事件', confidence: '0.74', status: '未确认' },
  { time: '06-25 20:13', type: '疑似抛物事件', confidence: '0.70', status: '未确认' },
]

async function loadOverview() {
  try {
    const res = await fetchOverview()
    overview.value = normalizeOverview(res.data)
  } catch {
    overview.value = normalizeOverview(null)
  }
}

onMounted(loadOverview)
</script>

<template>
  <div class="dashboard-page">
    <section class="metric-row">
      <div v-for="item in metrics" :key="item.label" class="metric-card">
        <span>{{ item.label }}</span>
        <strong :style="{ color: item.color }">{{ item.value }}</strong>
        <i :style="{ background: item.glow }"></i>
      </div>
    </section>

    <section class="middle-grid">
      <div class="panel trend-panel">
        <h3>事件趋势</h3>
        <div class="trend-chart">
          <i v-for="(bar, index) in trendBars" :key="index" :style="{ height: `${bar}px` }"></i>
        </div>
      </div>

      <div class="panel distribution-panel">
        <h3>置信度分布 0.35-1.0</h3>
        <div class="bar-list">
          <div><i class="green short"></i><span>0.35-0.5</span></div>
          <div><i class="yellow mid"></i><span>0.5-0.7</span></div>
          <div><i class="red long"></i><span>0.7-1.0</span></div>
        </div>
      </div>
    </section>

    <section class="bottom-grid">
      <div class="panel status-panel">
        <h3>状态分布</h3>
        <div class="bar-list">
          <div><i class="green short"></i><span>0.35-0.5</span></div>
          <div><i class="yellow mid"></i><span>0.5-0.7</span></div>
          <div><i class="red long"></i><span>0.7-1.0</span></div>
        </div>
      </div>

      <div class="panel recent-panel">
        <div class="table-head">
          <span>时间</span>
          <span>类型</span>
          <span>置信度</span>
          <span>状态</span>
        </div>
        <div v-for="event in recentEvents" :key="event.time" class="table-row">
          <span>{{ event.time }}</span>
          <span>{{ event.type }}</span>
          <span>{{ event.confidence }}</span>
          <span>{{ event.status }}</span>
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
  margin-bottom: 40px;
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

.middle-grid,
.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
}

.middle-grid {
  margin-bottom: 40px;
}

.panel {
  height: 260px;
  padding: 22px;
}

.panel h3 {
  color: #eaf6ff;
  font-size: 18px;
}

.trend-chart {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 34px;
  height: 176px;
  padding-top: 34px;
}

.trend-chart i {
  width: 32px;
  border-radius: 4px;
  background: linear-gradient(180deg, #12c6e8, #0d8196);
}

.bar-list {
  margin: 34px 0 0 26px;
}

.bar-list div {
  display: grid;
  gap: 8px;
  margin-bottom: 8px;
}

.bar-list i {
  display: block;
  height: 18px;
  border-radius: 999px;
}

.bar-list span {
  color: #91a8c7;
  font-size: 14px;
}

.green { background: #11d0a1; }
.yellow { background: #d99a22; }
.red { background: #df464c; }
.short { width: 110px; }
.mid { width: 190px; }
.long { width: 270px; }

.recent-panel {
  padding: 20px 22px;
}

.table-head,
.table-row {
  display: grid;
  grid-template-columns: 0.9fr 1.1fr 0.7fr 0.7fr;
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
</style>
