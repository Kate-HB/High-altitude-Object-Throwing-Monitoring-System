<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Search, VideoPlay, Refresh } from '@element-plus/icons-vue'
import { fetchEvents } from '../api/events'
import { fetchFile } from '../api/files'

// ── State ──
const events = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const selectedEvent = ref(null)
const snapshotUrl = ref('')
const videoUrl = ref('')
const mediaLoading = ref(false)

const filters = ref({
  status: '',
  min_confidence: '',
  task_id: '',
})

// ── Computed ──
const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '待确认', value: 'unconfirmed' },
  { label: '已确认', value: 'confirmed' },
  { label: '误报', value: 'false_alarm' },
]

const statusTagType = (s) => {
  const map = { unconfirmed: 'warning', confirmed: 'success', false_alarm: 'info' }
  return map[s] || 'info'
}

const statusLabel = (s) => {
  const map = { unconfirmed: '待确认', confirmed: '已确认', false_alarm: '误报' }
  return map[s] || s
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
    const params = {
      limit: pageSize.value,
      offset: (page.value - 1) * pageSize.value,
    }
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.task_id) params.task_id = Number(filters.value.task_id)

    const res = await fetchEvents(params)
    const list = res.data?.events || []
    events.value = list

    // Client-side confidence filter
    if (filters.value.min_confidence) {
      const min = parseFloat(filters.value.min_confidence)
      if (!isNaN(min)) {
        events.value = events.value.filter(e => (e.confidence || 0) >= min)
      }
    }

    total.value = res.data?.count ?? events.value.length
  } catch {
    events.value = []
  } finally {
    loading.value = false
  }
}

function handleFilter() {
  page.value = 1
  loadEvents()
}

async function selectEvent(event) {
  selectedEvent.value = event
  mediaLoading.value = true

  // Revoke previous blob URLs before creating new ones
  if (snapshotUrl.value) { URL.revokeObjectURL(snapshotUrl.value); snapshotUrl.value = '' }
  if (videoUrl.value) { URL.revokeObjectURL(videoUrl.value); videoUrl.value = '' }

  try {
    if (event.snapshot_path) {
      const res = await fetchFile(event.snapshot_path)
      snapshotUrl.value = URL.createObjectURL(res.data)
    }
  } catch { /* no snapshot */ }

  try {
    if (event.result_video_path) {
      const res = await fetchFile(event.result_video_path)
      videoUrl.value = URL.createObjectURL(res.data)
    }
  } catch { /* no video */ }

  mediaLoading.value = false
}

// ── Lifecycle ──
onMounted(loadEvents)

onUnmounted(() => {
  if (snapshotUrl.value) URL.revokeObjectURL(snapshotUrl.value)
  if (videoUrl.value) URL.revokeObjectURL(videoUrl.value)
})

defineOptions({ name: 'HistoryView' })
</script>

<template>
  <div class="history-page">
    <h2 class="page-heading">历史事件</h2>

    <!-- Filter bar -->
    <div class="filter-card">
      <div class="filter-row">
        <div class="filter-item">
          <label>状态</label>
          <el-select v-model="filters.status" size="small" style="width:130px">
            <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </div>
        <div class="filter-item">
          <label>最低置信度</label>
          <el-input-number v-model="filters.min_confidence" :min="0" :max="1" :step="0.05" :precision="2" size="small" style="width:140px" placeholder="0.00" />
        </div>
        <div class="filter-item">
          <label>任务ID</label>
          <el-input v-model="filters.task_id" size="small" style="width:120px" placeholder="可选" clearable />
        </div>
        <el-button type="primary" size="small" :icon="Search" @click="handleFilter">筛选</el-button>
        <el-button size="small" :icon="Refresh" @click="loadEvents">刷新</el-button>
      </div>
    </div>

    <!-- Events table -->
    <div class="table-card">
      <el-table
        :data="events"
        v-loading="loading"
        highlight-current-row
        @row-click="selectEvent"
        class="events-table"
        size="small"
        empty-text="暂无匹配事件"
      >
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="video_task_id" label="任务ID" width="70" />
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
            <el-tag :type="statusTagType(row.status)" size="small" effect="dark">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="截图" width="120">
          <template #default="{ row }">
            <span :style="{ color: row.snapshot_path ? '#00d8ff' : '#52657f', fontSize: '12px' }">
              {{ row.snapshot_path ? '有截图' : '无截图' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="视频" width="140">
          <template #default="{ row }">
            <span :style="{ color: row.result_video_path ? '#00d8ff' : '#52657f', fontSize: '12px' }">
              {{ row.result_video_path ? '有结果视频' : '视频生成中' }}
            </span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          background
          small
          @current-change="loadEvents"
        />
      </div>
    </div>

    <!-- Media panel -->
    <div v-if="selectedEvent" class="media-card">
      <h3 class="section-title">事件 #{{ selectedEvent.id }} 详情</h3>
      <div class="media-grid">
        <div class="media-panel">
          <span class="panel-label">事件截图</span>
          <div v-loading="mediaLoading" class="media-box">
            <img v-if="snapshotUrl" :src="snapshotUrl" class="media-img" />
            <span v-else-if="!mediaLoading" class="no-media">暂无截图</span>
          </div>
        </div>
        <div class="media-panel">
          <span class="panel-label">结果视频</span>
          <div v-loading="mediaLoading" class="media-box">
            <video v-if="videoUrl" :src="videoUrl" controls class="media-video">
              您的浏览器不支持视频播放
            </video>
            <el-icon v-else-if="!mediaLoading" :size="36" color="#52657f"><VideoPlay /></el-icon>
            <span v-if="!videoUrl && !mediaLoading" class="no-media">结果视频生成中</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.history-page { max-width: 1080px; }

.page-heading {
  margin: 4px 0 24px;
  color: #eaf6ff;
  font-size: 24px;
  font-weight: 700;
}

/* Filter */
.filter-card {
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
  padding: 14px 22px;
  margin-bottom: 20px;
}
.filter-row {
  display: flex;
  align-items: flex-end;
  gap: 18px;
  flex-wrap: wrap;
}
.filter-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.filter-item label {
  color: #91a8c7;
  font-size: 12px;
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
.conf-cell {
  font-weight: 700;
  font-family: "DIN Alternate", Consolas, monospace;
}
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

/* Media */
.media-card {
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
  padding: 18px 22px;
}
.section-title {
  margin: 0 0 16px;
  color: #eaf6ff;
  font-size: 15px;
  font-weight: 600;
}
.media-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 28px;
}
.panel-label {
  display: block;
  margin-bottom: 8px;
  color: #91a8c7;
  font-size: 13px;
}
.media-box {
  min-height: 220px;
  background: #0d1a2b;
  border: 1px solid #1e3a5f;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.media-img {
  width: 100%;
  max-height: 260px;
  object-fit: contain;
}
.media-video {
  width: 100%;
  max-height: 300px;
  outline: none;
}
.no-media {
  margin-top: 8px;
  color: #52657f;
  font-size: 13px;
}
</style>
