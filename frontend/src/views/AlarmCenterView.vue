<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchEvents, updateEventStatus } from '../api/events'

const demoEvents = [
  { id: 1, created_at: '06-25 20:10', type: '疑似抛物事件', confidence: 0.82, status: 'unconfirmed', track_id: 12 },
  { id: 2, created_at: '06-25 20:11', type: '疑似抛物事件', confidence: 0.78, status: 'unconfirmed', track_id: 13 },
  { id: 3, created_at: '06-25 20:12', type: '疑似抛物事件', confidence: 0.74, status: 'unconfirmed', track_id: 14 },
  { id: 4, created_at: '06-25 20:13', type: '疑似抛物事件', confidence: 0.70, status: 'unconfirmed', track_id: 15 },
  { id: 5, created_at: '06-25 20:14', type: '疑似抛物事件', confidence: 0.66, status: 'unconfirmed', track_id: 16 },
  { id: 6, created_at: '06-25 20:15', type: '疑似抛物事件', confidence: 0.62, status: 'unconfirmed', track_id: 17 },
  { id: 7, created_at: '06-25 20:16', type: '疑似抛物事件', confidence: 0.58, status: 'unconfirmed', track_id: 18 },
]

const events = ref(demoEvents)
const selectedEvent = ref(demoEvents[0])
const loading = ref(false)

const page = ref(1)
const pageSize = 7
const totalPages = computed(() => Math.max(1, Math.ceil(events.value.length / pageSize)))
const pagedEvents = computed(() => events.value.slice((page.value - 1) * pageSize, page.value * pageSize))

const latestAlarm = computed(() => events.value.find(item => item.status === 'unconfirmed') || events.value[0])

function goPage(p) {
  page.value = Math.max(1, Math.min(totalPages.value, p))
}

function selectEvent(event) {
  selectedEvent.value = event
}

async function setEventStatus(status) {
  if (!selectedEvent.value) return
  try {
    await updateEventStatus(selectedEvent.value.id, status)
  } catch {
    // 演示页允许后端未启动时本地更新状态
  }
  selectedEvent.value.status = status
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
  <div class="alarm-page">
    <section class="alarm-banner">
      <h2>{{ latestAlarm ? '检测到疑似高空抛物事件' : '暂无报警事件' }}</h2>
      <div class="banner-actions">
        <button class="primary-action" @click="setEventStatus('confirmed')">确认事件</button>
        <button class="secondary-action" @click="setEventStatus('false_alarm')">标记误报</button>
      </div>
    </section>

    <section class="alarm-grid">
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
        <div class="snapshot-card">
          <div class="snapshot-mark"></div>
          <strong>事件截图</strong>
        </div>
        <div class="detail-card">
          <h3>事件详情</h3>
          <p>状态：{{ selectedEvent?.status || 'unconfirmed' }}</p>
          <p>置信度：{{ selectedEvent ? Number(selectedEvent.confidence || 0).toFixed(2) : '0.86' }}</p>
          <p>轨迹：连续下降帧占比 78%</p>
          <p>ROI：命中</p>
        </div>
      </aside>
    </section>
  </div>
</template>

<style scoped>
.alarm-page {
  max-width: 1080px;
  min-height: calc(100vh - 136px);
  padding: 0;
}

.alarm-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 116px;
  padding: 0 28px;
  margin-bottom: 32px;
  background: rgba(255, 77, 79, 0.11);
  border: 1px solid #ff4d4f;
  border-radius: 8px;
}

.alarm-banner h2 {
  color: #ff4d4f;
  font-size: 24px;
  font-weight: 800;
}

.banner-actions {
  display: flex;
  gap: 14px;
}

.banner-actions button {
  min-width: 128px;
  height: 48px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 800;
  cursor: pointer;
}

.primary-action {
  color: #04101c;
  background: #12c6e8;
  border: 1px solid #12c6e8;
}

.secondary-action {
  color: #eaf6ff;
  background: #0b1728;
  border: 1px solid #1e3a5f;
}

.alarm-grid {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 32px;
}

.event-table,
.snapshot-card,
.detail-card {
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
}

.event-table {
  padding: 20px 24px;
}

.table-head,
.table-row {
  display: grid;
  grid-template-columns: 0.8fr 1fr 0.6fr 0.8fr;
  align-items: center;
  width: 100%;
  min-height: 52px;
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

.snapshot-card {
  display: grid;
  place-items: center;
  height: 246px;
  background: #050b14;
  color: #d6e4f2;
  font-size: 18px;
}

.snapshot-mark {
  width: 128px;
  height: 48px;
  margin-bottom: -78px;
  border-radius: 50%;
  background: rgba(0, 216, 255, 0.12);
}

.detail-card {
  min-height: 214px;
  padding: 28px 30px;
}

.detail-card h3 {
  margin-bottom: 28px;
  color: #eaf6ff;
  font-size: 20px;
}

.detail-card p {
  color: #91a8c7;
  font-size: 16px;
  line-height: 1.35;
}
</style>
