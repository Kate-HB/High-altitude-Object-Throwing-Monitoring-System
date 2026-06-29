<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Bell, Check, CircleClose, WarningFilled, Search } from '@element-plus/icons-vue'
import { fetchEvents, updateEventStatus } from '../api/events'
import { fetchFile } from '../api/files'

// ── State ──
const events = ref([])
const loading = ref(false)
const selectedEvent = ref(null)
const snapshotUrl = ref('')
const snapshotLoading = ref(false)
let pollTimer = null

// ── Computed ──
const latestAlarm = computed(() => {
  const unconfirmed = events.value.filter(e => e.status === 'unconfirmed')
  return unconfirmed.length ? unconfirmed[0] : events.value[0] || null
})

const statusTagType = (status) => {
  const map = { unconfirmed: 'warning', confirmed: 'success', false_alarm: 'info' }
  return map[status] || 'info'
}

const statusLabel = (status) => {
  const map = { unconfirmed: '待确认', confirmed: '已确认', false_alarm: '误报' }
  return map[status] || status
}

const confidenceColor = (val) => {
  if (val >= 0.7) return '#ff4d4f'
  if (val >= 0.5) return '#ffb020'
  return '#00d8ff'
}

// ── Methods ──
async function loadEvents() {
  loading.value = true
  try {
    const res = await fetchEvents({ limit: 100 })
    events.value = (res.data?.events || []).slice(0, 50)
  } catch {
    // silent
  } finally {
    loading.value = false
  }
}

async function confirmEvent(event) {
  try {
    await updateEventStatus(event.id, 'confirmed')
    event.status = 'confirmed'
    if (selectedEvent.value?.id === event.id) selectedEvent.value.status = 'confirmed'
  } catch {
    // network error — status stays unchanged
  }
}

async function rejectEvent(event) {
  try {
    await updateEventStatus(event.id, 'false_alarm')
    event.status = 'false_alarm'
    if (selectedEvent.value?.id === event.id) selectedEvent.value.status = 'false_alarm'
  } catch {
    // network error — status stays unchanged
  }
}

async function selectEvent(event) {
  selectedEvent.value = event
  snapshotLoading.value = true
  if (snapshotUrl.value) {
    URL.revokeObjectURL(snapshotUrl.value)
    snapshotUrl.value = ''
  }
  try {
    if (event.snapshot_path) {
      const res = await fetchFile(event.snapshot_path)
      snapshotUrl.value = URL.createObjectURL(res.data)
    }
  } catch {
    snapshotUrl.value = ''
  } finally {
    snapshotLoading.value = false
  }
}

// ── Lifecycle ──
onMounted(() => {
  loadEvents()
  pollTimer = setInterval(loadEvents, 15000)
})

onUnmounted(() => {
  clearInterval(pollTimer)
  if (snapshotUrl.value) URL.revokeObjectURL(snapshotUrl.value)
})

defineOptions({ name: 'AlarmCenterView' })
</script>

<template>
  <div class="alarm-page">
    <h2 class="page-heading">报警中心</h2>

    <!-- Hero card: latest alarm -->
    <div v-if="latestAlarm" class="hero-card" :class="{ unconfirmed: latestAlarm.status === 'unconfirmed' }">
      <div class="hero-left">
        <el-icon :size="28" color="#ff4d4f"><WarningFilled /></el-icon>
        <div class="hero-info">
          <span class="hero-label">{{ latestAlarm.status === 'unconfirmed' ? '⚠ 最新报警' : '最近事件' }}</span>
          <span class="hero-meta">
            事件 #{{ latestAlarm.id }} · Track {{ latestAlarm.track_id }} · 置信度 {{ (latestAlarm.confidence * 100).toFixed(1) }}%
          </span>
        </div>
      </div>
      <div class="hero-right">
        <span class="hero-time">{{ latestAlarm.created_at }}</span>
        <el-tag :type="statusTagType(latestAlarm.status)" size="small" effect="dark">{{ statusLabel(latestAlarm.status) }}</el-tag>
      </div>
    </div>

    <!-- Events table -->
    <div class="table-card">
      <h3 class="section-title">报警事件列表</h3>
      <el-table
        :data="events"
        v-loading="loading"
        highlight-current-row
        @row-click="selectEvent"
        class="events-table"
        size="small"
        empty-text="暂无报警事件"
      >
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="created_at" label="时间" width="170" />
        <el-table-column prop="track_id" label="跟踪ID" width="80" />
        <el-table-column label="置信度" width="110">
          <template #default="{ row }">
            <span :style="{ color: confidenceColor(row.confidence) }" class="conf-cell">
              {{ row.confidence ? (row.confidence * 100).toFixed(1) + '%' : '--' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small" effect="dark">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="160">
          <template #default="{ row }">
            <template v-if="row.status === 'unconfirmed'">
              <el-button type="success" size="small" :icon="Check" @click.stop="confirmEvent(row)">确认</el-button>
              <el-button type="info" size="small" :icon="CircleClose" @click.stop="rejectEvent(row)">误报</el-button>
            </template>
            <span v-else class="done-label">
              {{ row.status === 'confirmed' ? '已确认' : '已排除' }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Detail panel -->
    <div v-if="selectedEvent" class="detail-card">
      <h3 class="section-title">事件详情 #{{ selectedEvent.id }}</h3>
      <div class="detail-grid">
        <div class="detail-snapshot">
          <div v-loading="snapshotLoading" class="snapshot-box">
            <img v-if="snapshotUrl" :src="snapshotUrl" class="snapshot-img" />
            <el-icon v-else :size="36" color="#52657f"><Search /></el-icon>
            <span v-if="!snapshotUrl && !snapshotLoading" class="no-snapshot">暂无截图</span>
          </div>
        </div>
        <div class="detail-info">
          <div class="info-row"><span class="info-key">事件ID</span><span>{{ selectedEvent.id }}</span></div>
          <div class="info-row"><span class="info-key">跟踪ID</span><span>{{ selectedEvent.track_id }}</span></div>
          <div class="info-row"><span class="info-key">置信度</span>
            <span :style="{ color: confidenceColor(selectedEvent.confidence) }">
              {{ selectedEvent.confidence ? (selectedEvent.confidence * 100).toFixed(1) + '%' : '--' }}
            </span>
          </div>
          <div class="info-row"><span class="info-key">状态</span>
            <el-tag :type="statusTagType(selectedEvent.status)" size="small" effect="dark">{{ statusLabel(selectedEvent.status) }}</el-tag>
          </div>
          <div class="info-row"><span class="info-key">时间</span><span>{{ selectedEvent.created_at }}</span></div>
          <div class="info-row"><span class="info-key">任务ID</span><span>{{ selectedEvent.video_task_id }}</span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.alarm-page { max-width: 1080px; }

.page-heading {
  margin: 4px 0 24px;
  color: #eaf6ff;
  font-size: 24px;
  font-weight: 700;
}

/* Hero */
.hero-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 28px;
  margin-bottom: 24px;
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
}
.hero-card.unconfirmed {
  border-color: #ff4d4f;
  box-shadow: 0 0 20px rgba(255, 77, 79, 0.18);
}
.hero-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.hero-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.hero-label {
  color: #eaf6ff;
  font-size: 16px;
  font-weight: 700;
}
.hero-meta {
  color: #91a8c7;
  font-size: 13px;
}
.hero-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.hero-time {
  color: #91a8c7;
  font-size: 13px;
}

/* Table */
.table-card {
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
  padding: 18px 22px;
  margin-bottom: 24px;
}
.section-title {
  margin: 0 0 16px;
  color: #eaf6ff;
  font-size: 15px;
  font-weight: 600;
}
.conf-cell {
  font-weight: 700;
  font-family: "DIN Alternate", Consolas, monospace;
}
.done-label {
  color: #52657f;
  font-size: 13px;
}

/* Table overrides */
.events-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: transparent;
  --el-table-border-color: #1e3a5f;
  --el-table-header-text-color: #91a8c7;
  --el-table-text-color: #eaf6ff;
  --el-table-row-hover-bg-color: rgba(0, 216, 255, 0.06);
}
.events-table :deep(.el-table__empty-text) { color: #52657f; }
.events-table :deep(.el-table__body tr) { cursor: pointer; }

/* Detail */
.detail-card {
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
  padding: 18px 22px;
}
.detail-grid {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 28px;
}
.snapshot-box {
  min-height: 200px;
  background: #0d1a2b;
  border: 1px solid #1e3a5f;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.snapshot-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  max-height: 260px;
}
.no-snapshot {
  margin-top: 8px;
  color: #52657f;
  font-size: 13px;
}
.detail-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.info-row {
  display: flex;
  align-items: center;
  gap: 16px;
  color: #eaf6ff;
  font-size: 14px;
}
.info-key {
  color: #91a8c7;
  width: 70px;
  flex-shrink: 0;
}
</style>
