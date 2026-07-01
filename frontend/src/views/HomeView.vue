<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchHealth } from '../api/health'
import { fetchSystemStatus } from '../api/system'
import { fetchOverview } from '../api/statistics'
import { formatHealthStatus, normalizeOverview } from '../utils/dashboard'

const backendOnline = ref(false)
const algoOnline = ref(false)
const dbOnline = ref(false)
const systemStatus = ref(null)
const overview = ref(normalizeOverview(null))
const loading = ref(true)

const statCards = computed(() => [
  { label: '今日事件', value: overview.value.today_event_count, accent: '#ffb020' },
  { label: '累计事件', value: overview.value.total_event_count, accent: '#00d8ff' },
  { label: '后端状态', value: backendOnline.value ? 'Running' : 'Offline', accent: backendOnline.value ? '#00ffb2' : '#ff4d4f' },
  { label: '算法状态', value: algoOnline.value ? 'Ready' : 'Missing', accent: algoOnline.value ? '#00ffb2' : '#ff4d4f' },
])

const trendBars = computed(() => {
  const data = overview.value.daily_trend || []
  if (!data.length) return []
  const max = Math.max(...data.map((item) => item.count || 0), 1)
  return data.slice(-6).map((item, index) => ({
    key: item.date || index,
    height: Math.max(28, Math.round(((item.count || 0) / max) * 84)),
  }))
})

const recentEvents = computed(() => {
  const events = overview.value.recent_events || []
  if (events.length) return events.slice(0, 5)
  return []
})

onMounted(async () => {
  try {
    const h = await fetchHealth()
    backendOnline.value = formatHealthStatus(h)
  } catch {
    backendOnline.value = false
  }

  try {
    const s = await fetchSystemStatus()
    systemStatus.value = s.data
    algoOnline.value = s.data.algorithm?.status === 'ready'
    dbOnline.value = s.data.database?.status === 'connected'
  } catch {
    algoOnline.value = false
    dbOnline.value = false
  }

  try {
    const stats = await fetchOverview()
    overview.value = normalizeOverview(stats.data)
  } catch {
    overview.value = normalizeOverview(null)
  }

  loading.value = false
})
</script>

<template>
  <div class="home-page">
    <section class="stat-row">
      <div v-for="card in statCards" :key="card.label" class="stat-card">
        <span class="stat-label">{{ card.label }}</span>
        <span class="stat-value" :style="{ color: card.accent }">{{ card.value }}</span>
        <i class="stat-glow" :style="{ background: card.accent }"></i>
      </div>
    </section>

    <section class="content-grid">
      <div class="chart-card">
        <h3 class="section-title">近7日事件趋势</h3>
        <div class="bar-chart" v-if="trendBars.length">
          <i
            v-for="bar in trendBars"
            :key="bar.key"
            class="trend-bar"
            :style="{ height: `${bar.height}px` }"
          ></i>
        </div>
        <div v-else class="empty-chart">暂无趋势数据</div>
      </div>

      <div class="table-card">
        <div class="table-head">时间<span>类型</span><span>置信度</span><span>状态</span></div>
        <template v-if="recentEvents.length">
          <div v-for="event in recentEvents" :key="event.id" class="table-row">
            <span>{{ event.created_at || '--' }}</span>
            <span>疑似抛物事件</span>
            <span>{{ event.confidence ?? '--' }}</span>
            <span>{{ event.status || '--' }}</span>
          </div>
        </template>
        <div v-else class="empty-row">暂无报警事件</div>
      </div>
    </section>

    <section class="flow-card">
      <h3 class="flow-title">主演示闭环</h3>
      <p>登录 → 上传视频 → ROI → YOLOv11检测 → DeepSORT处理 → 轨迹判断 → 报警 → 入库 → 历史回放 → 数据看板</p>
    </section>
  </div>
</template>

<style scoped>
.home-page {
  max-width: 1080px;
}

.page-heading {
  margin: 4px 0 24px;
  color: #eaf6ff;
  font-size: 30px;
  font-weight: 700;
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 30px;
}

.stat-card {
  position: relative;
  min-height: 112px;
  padding: 18px 22px;
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
  overflow: hidden;
}

.stat-label {
  font-size: 13px;
  color: #91a8c7;
}

.stat-value {
  display: block;
  margin-top: 10px;
  font-size: 32px;
  font-weight: 700;
  font-family: "DIN Alternate", Consolas, monospace;
}

.stat-glow {
  position: absolute;
  top: 26px;
  right: 22px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  opacity: 0.28;
  filter: blur(1px);
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
  margin-bottom: 34px;
}

.chart-card,
.table-card,
.flow-card {
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
}

.chart-card {
  height: 260px;
  padding: 18px 22px;
}

.section-title {
  margin: 0;
  color: #eaf6ff;
  font-size: 15px;
  font-weight: 600;
}

.bar-chart {
  height: 170px;
  display: flex;
  align-items: flex-end;
  gap: 30px;
  padding: 42px 10px 0;
}

.trend-bar {
  width: 32px;
  border-radius: 4px;
  background: linear-gradient(180deg, #16c9e4, #0e8aa4);
}

.empty-chart {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #52657f;
  font-size: 14px;
}

.table-card {
  height: 264px;
  padding: 18px 18px 0;
  overflow: hidden;
}

.table-head,
.table-row {
  display: grid;
  grid-template-columns: 1.2fr 1.3fr 0.8fr 0.8fr;
  gap: 12px;
  align-items: center;
  min-height: 42px;
  border-bottom: 1px solid #1e3a5f;
  font-size: 13px;
}

.table-head {
  min-height: 30px;
  color: #91a8c7;
  font-weight: 600;
}

.table-row {
  color: #eaf6ff;
}

.empty-row {
  padding: 70px 0;
  text-align: center;
  color: #52657f;
  font-size: 14px;
}

.flow-card {
  min-height: 120px;
  padding: 26px 32px;
}

.flow-title {
  color: #eaf6ff;
  font-size: 18px;
  margin-bottom: 20px;
}

.flow-card p {
  color: #00d8ff;
  font-size: 18px;
  font-weight: 700;
}
</style>
