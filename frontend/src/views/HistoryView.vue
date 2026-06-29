<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchEvents } from '../api/events'

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

const events = ref(demoEvents)
const selectedEvent = ref(demoEvents[0])
const loading = ref(false)
const filters = ref({ status: '', start: '', end: '', confidence: '' })

const trackInfo = computed(() => ({
  track_id: selectedEvent.value?.track_id ?? 12,
  start_frame: 118,
  end_frame: 166,
  timestamp: '00:04.72',
}))

function selectEvent(event) {
  selectedEvent.value = event
}

async function loadEvents() {
  loading.value = true
  try {
    const res = await fetchEvents({ limit: 50 })
    const list = res.data?.events || []
    if (list.length) {
      events.value = list.map(item => ({
        ...item,
        type: '疑似抛物事件',
        created_at: item.created_at || '--',
      }))
      selectedEvent.value = events.value[0]
    }
  } catch {
    events.value = demoEvents
    selectedEvent.value = demoEvents[0]
  } finally {
    loading.value = false
  }
}

onMounted(loadEvents)
</script>

<template>
  <div class="history-page">
    <section class="filter-card">
      <input v-model="filters.status" placeholder="状态" />
      <input v-model="filters.start" placeholder="开始时间" />
      <input v-model="filters.end" placeholder="结束时间" />
      <input v-model="filters.confidence" placeholder="最低置信度" />
      <button @click="loadEvents">查询</button>
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
          v-for="event in events"
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
      </div>

      <aside class="right-column">
        <div class="video-card">
          <div class="video-mark"></div>
          <strong>结果视频</strong>
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

.filter-card input {
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
