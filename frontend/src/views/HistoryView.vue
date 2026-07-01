<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { fetchEvents } from '../api/events'
import { fetchFile } from '../api/files'

const demoEvents = [
  { id: 1, created_at: '06-25 20:10', type: '疑似抛物事件', confidence: 0.82, status: 'unconfirmed', track_id: 12 },
  { id: 2, created_at: '06-25 20:11', type: '疑似抛物事件', confidence: 0.78, status: 'unconfirmed', track_id: 13 },
  { id: 3, created_at: '06-25 20:12', type: '疑似抛物事件', confidence: 0.74, status: 'unconfirmed', track_id: 14 },
  { id: 4, created_at: '06-25 20:13', type: '疑似抛物事件', confidence: 0.70, status: 'unconfirmed', track_id: 15 },
  { id: 5, created_at: '06-25 20:14', type: '疑似抛物事件', confidence: 0.66, status: 'unconfirmed', track_id: 16 },
  { id: 6, created_at: '06-25 20:15', type: '疑似抛物事件', confidence: 0.62, status: 'unconfirmed', track_id: 17 },
  { id: 7, created_at: '06-25 20:16', type: '疑似抛物事件', confidence: 0.58, status: 'unconfirmed', track_id: 18 },
  { id: 8, created_at: '06-25 20:17', type: '疑似抛物事件', confidence: 0.54, status: 'unconfirmed', track_id: 19 },
]

const allEvents = ref(demoEvents)
const selectedEvent = ref(demoEvents[0])
const videoUrl = ref(null)
const fullVideoUrl = ref(null)
const loading = ref(false)
const filters = ref({ status: '', start: '', end: '', confidence: '' })

const page = ref(1)
const pageSize = 7

const filteredEvents = computed(() => {
  let list = allEvents.value
  const f = filters.value
  if (f.status) list = list.filter(e => e.status === f.status)
  if (f.confidence) list = list.filter(e => Number(e.confidence || 0) >= Number(f.confidence))
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredEvents.value.length / pageSize)))
const pagedEvents = computed(() => filteredEvents.value.slice((page.value - 1) * pageSize, page.value * pageSize))

const trackInfo = computed(() => ({
  track_id: selectedEvent.value?.track_id ?? 12,
  start_frame: 118,
  end_frame: 166,
  timestamp: '00:04.72',
}))

function goPage(p) {
  page.value = Math.max(1, Math.min(totalPages.value, p))
}

async function selectEvent(event) {
  selectedEvent.value = event
  if (videoUrl.value) { URL.revokeObjectURL(videoUrl.value); videoUrl.value = null }
  if (event.task_result_video_path) {
    try {
      const res = await fetchFile(event.task_result_video_path)
      videoUrl.value = URL.createObjectURL(res.data)
    } catch { /* ignore */ }
  }
}

function doQuery() {
  page.value = 1
  loadEvents()
}

function openFullVideo() {
  if (videoUrl.value) fullVideoUrl.value = videoUrl.value
}
function closeFullVideo() { fullVideoUrl.value = null }

async function loadEvents() {
  loading.value = true
  try {
    const params = { limit: 200 }
    if (filters.value.status) params.status = filters.value.status
    const res = await fetchEvents(params)
    const list = res.data?.events || []
    if (list.length) {
      allEvents.value = list.map(item => ({
        ...item,
        type: '疑似抛物事件',
        created_at: item.created_at || '--',
      }))
      selectedEvent.value = allEvents.value[0]
      const first = allEvents.value[0]
      if (videoUrl.value) { URL.revokeObjectURL(videoUrl.value); videoUrl.value = null }
      if (first?.task_result_video_path) {
        try {
          const r = await fetchFile(first.task_result_video_path)
          videoUrl.value = URL.createObjectURL(r.data)
        } catch { /* ignore */ }
      }
    }
  } catch {
    allEvents.value = demoEvents
    selectedEvent.value = demoEvents[0]
  } finally {
    loading.value = false
  }
}

onBeforeUnmount(() => {
  if (videoUrl.value) URL.revokeObjectURL(videoUrl.value)
})

onMounted(loadEvents)
</script>

<template>
  <div class="history-page">
    <section class="filter-card">
      <select v-model="filters.status">
        <option value="">全部状态</option>
        <option value="unconfirmed">未确认</option>
        <option value="confirmed">已确认</option>
        <option value="false_alarm">误报</option>
      </select>
      <select v-model="filters.start">
        <option value="">开始时间</option>
        <option value="today">今天</option>
        <option value="3days">最近3天</option>
        <option value="7days">最近7天</option>
        <option value="30days">最近30天</option>
      </select>
      <select v-model="filters.end">
        <option value="">结束时间</option>
        <option value="today">今天</option>
        <option value="3days">最近3天</option>
        <option value="7days">最近7天</option>
        <option value="30days">最近30天</option>
      </select>
      <select v-model="filters.confidence">
        <option value="">最低置信度</option>
        <option value="0.5">≥ 0.5</option>
        <option value="0.6">≥ 0.6</option>
        <option value="0.7">≥ 0.7</option>
        <option value="0.8">≥ 0.8</option>
        <option value="0.9">≥ 0.9</option>
      </select>
      <button @click="doQuery">查询</button>
    </section>

    <section class="history-grid">
      <div class="event-table" v-loading="loading">
        <div class="table-head">
          <span>时间</span>
          <span>类型</span>
          <span>置信度</span>
          <span>状态</span>
        </div>
        <button
          v-for="event in pagedEvents"
          :key="event.id"
          class="table-row"
          :class="{ active: selectedEvent?.id === event.id }"
          @click="selectEvent(event)"
        >
          <span>{{ event.created_at }}</span>
          <span>{{ event.type }}</span>
          <span>{{ Number(event.confidence || 0).toFixed(2) }}</span>
          <span>{{ event.status === 'unconfirmed' ? '未确认' : event.status }}</span>
        </button>
      <div class="pager" v-if="totalPages > 1">
        <button :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
        <span>第 {{ page }} / {{ totalPages }} 页</span>
        <button :disabled="page >= totalPages" @click="goPage(page + 1)">下一页</button>
      </div>
      </div>

      <aside class="right-column">
        <div class="video-card" @click="openFullVideo">
          <video
            v-if="videoUrl"
            :src="videoUrl"
            class="result-video"
            controls
          />
          <template v-else>
            <div class="video-mark"></div>
            <strong>结果视频</strong>
          </template>
        </div>
        <div class="track-card">
          <h3>轨迹数据</h3>
          <p>track_id: {{ trackInfo.track_id }}</p>
          <p>start_frame: {{ trackInfo.start_frame }}</p>
          <p>end_frame: {{ trackInfo.end_frame }}</p>
          <p>timestamp: {{ trackInfo.timestamp }}</p>
        </div>
      </aside>
    </section>

    <div v-if="fullVideoUrl" class="video-overlay" @click.self="closeFullVideo">
      <button class="close-btn" @click="closeFullVideo">✕</button>
      <video :src="fullVideoUrl" class="full-video" controls autoplay />
    </div>
  </div>
</template>

<style scoped>
.history-page {
  max-width: 1080px;
}

.filter-card {
  display: grid;
  grid-template-columns: repeat(4, 150px) 120px;
  justify-content: space-between;
  gap: 0;
  align-items: center;
  min-height: 122px;
  padding: 0 24px;
  margin-bottom: 32px;
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
}

.filter-card input,
.filter-card select {
  height: 54px;
  padding: 0 24px;
  color: #eaf6ff;
  background: #0d1a2b;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  font-size: 16px;
  outline: none;
}

.filter-card input::placeholder {
  color: #91a8c7;
}

.filter-card button {
  height: 54px;
  color: #04101c;
  background: #12c6e8;
  border: 1px solid #12c6e8;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 800;
  cursor: pointer;
}

.history-grid {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 32px;
}

.event-table,
.video-card,
.track-card {
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
}

.event-table {
  padding: 18px 22px;
}

.table-head,
.table-row {
  display: grid;
  grid-template-columns: 0.8fr 1fr 0.6fr 0.8fr;
  align-items: center;
  width: 100%;
  min-height: 48px;
  padding: 0 4px;
  border: 0;
  border-bottom: 1px solid #1e3a5f;
  background: transparent;
  color: #d6e4f2;
  text-align: left;
  font-size: 14px;
}

.table-head {
  min-height: 32px;
  color: #91a8c7;
  font-weight: 800;
}

.table-row {
  cursor: pointer;
}

.table-row:hover,
.table-row.active {
  background: rgba(0, 216, 255, 0.06);
}

.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding: 16px 0 4px;
  color: #91a8c7;
  font-size: 14px;
}
.pager button {
  min-width: 80px;
  height: 36px;
  padding: 0 16px;
  color: #eaf6ff;
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}
.pager button:hover:not(:disabled) {
  background: rgba(0, 216, 255, 0.12);
}
.pager button:disabled {
  color: #52657f;
  cursor: not-allowed;
  opacity: 0.5;
}

.right-column {
  display: grid;
  gap: 24px;
}

.video-card {
  display: grid;
  place-items: center;
  height: 220px;
  background: #050b14;
  color: #d6e4f2;
  font-size: 18px;
  overflow: hidden;
  cursor: pointer;
}

.result-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.video-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn {
  position: absolute;
  top: 20px;
  right: 28px;
  width: 40px;
  height: 40px;
  border: none;
  background: rgba(255,255,255,0.15);
  color: #fff;
  font-size: 20px;
  border-radius: 50%;
  cursor: pointer;
  z-index: 1;
}

.full-video {
  max-width: 90vw;
  max-height: 90vh;
  border-radius: 8px;
  box-shadow: 0 0 60px rgba(0, 216, 255, 0.15);
}

.video-mark {
  width: 128px;
  height: 48px;
  margin-bottom: -78px;
  border-radius: 50%;
  background: rgba(0, 216, 255, 0.12);
}

.track-card {
  min-height: 190px;
  padding: 24px 28px;
}

.track-card h3 {
  margin-bottom: 28px;
  color: #eaf6ff;
  font-size: 20px;
}

.track-card p {
  color: #91a8c7;
  font-size: 16px;
  line-height: 1.35;
}
</style>
