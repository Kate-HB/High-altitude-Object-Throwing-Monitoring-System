<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  fetchCameraAIStatus,
  fetchCameraStatus,
  startCamera,
  startCameraAI,
  stopCamera,
  stopCameraAI,
} from '../api/camera'
import { fetchFile } from '../api/files'
import { playAlarm } from '../utils/alarm'

// ── Camera state ──
const running = ref(false)
const cameraIndex = ref(0)
const cameraWidth = ref(1280)
const cameraHeight = ref(720)
const streamUrl = '/api/camera/stream'
const errorMsg = ref('')
let statusEventSource = null

// ── AI state ──
const aiEnabled = ref(false)
const aiTaskId = ref(null)
const aiFrameCount = ref(0)
const aiActiveTracks = ref(0)
const aiTotalEvents = ref(0)
const aiLatestEvents = ref([])
const snapshotUrls = ref({})
let aiPollTimer = null
let aiFirstPoll = true

// ── ROI drawing ──
const roi = ref({ x: 0, y: 0, width: null, height: null })
const drawingROI = ref(false)
const drawStart = ref({ x: 0, y: 0 })
const canvasRef = ref(null)
const imgRef = ref(null)

const hasROI = computed(() => roi.value.width && roi.value.width > 10)

function getCanvasPos(e) {
  const rect = canvasRef.value?.getBoundingClientRect()
  if (!rect) return { x: 0, y: 0 }
  const imgRect = imgRef.value?.getBoundingClientRect()
  const scaleX = cameraWidth.value / (imgRect?.width || cameraWidth.value)
  const scaleY = cameraHeight.value / (imgRect?.height || cameraHeight.value)
  return {
    x: Math.round((e.clientX - rect.left) * scaleX),
    y: Math.round((e.clientY - rect.top) * scaleY),
  }
}

function onROIDown(e) {
  if (aiEnabled.value) return
  const pos = getCanvasPos(e)
  drawingROI.value = true
  drawStart.value = pos
  roi.value = { x: pos.x, y: pos.y, width: null, height: null }
  drawROI()
}

function onROIMove(e) {
  if (!drawingROI.value) return
  const pos = getCanvasPos(e)
  roi.value = {
    x: Math.min(drawStart.value.x, pos.x),
    y: Math.min(drawStart.value.y, pos.y),
    width: Math.abs(pos.x - drawStart.value.x),
    height: Math.abs(pos.y - drawStart.value.y),
  }
  drawROI()
}

function onROIUp() {
  drawingROI.value = false
  if (roi.value.width && roi.value.width < 10) {
    roi.value = { x: 0, y: 0, width: null, height: null }
    drawROI()
  }
}

function drawROI() {
  const c = canvasRef.value
  if (!c) return
  const ctx = c.getContext('2d')
  ctx.clearRect(0, 0, c.width, c.height)
  const r = roi.value
  if (r.width && r.width > 0) {
    ctx.strokeStyle = '#00d8ff'
    ctx.lineWidth = 2
    ctx.strokeRect(r.x, r.y, r.width, r.height)
  }
}

// ── Camera control ──
function updateStatus(data) {
  running.value = data.status === 'online'
  cameraIndex.value = data.camera_index || 0
  cameraWidth.value = data.width || 640
  cameraHeight.value = data.height || 480
}

async function refreshStatus() {
  try {
    const res = await fetchCameraStatus()
    updateStatus(res.data || {})
  } catch {
    running.value = false
  }
}

async function handleStart() {
  errorMsg.value = ''
  try {
    const res = await startCamera(0, cameraWidth.value, cameraHeight.value)
    const data = res.data || {}
    if (data.status === 'error') {
      errorMsg.value = data.message || '摄像头不可用'
      return
    }
    running.value = true
  } catch {
    errorMsg.value = '摄像头启动失败，请检查设备连接'
  }
}

async function handleStop() {
  errorMsg.value = ''
  if (aiEnabled.value) await handleAIStop()
  try {
    await stopCamera()
  } finally {
    running.value = false
  }
}

// ── AI control ──
async function handleAIStart() {
  if (!hasROI.value) {
    errorMsg.value = '请先在画面上拖拽绘制ROI区域'
    return
  }
  errorMsg.value = ''
  try {
    const res = await startCameraAI(roi.value, {})
    const data = res.data || {}
    if (data.status === 'error') {
      errorMsg.value = data.message || 'AI启动失败'
      return
    }
    aiEnabled.value = true
    aiTaskId.value = data.task_id
    aiFirstPoll = true
    aiPollTimer = setInterval(refreshAIStatus, 2000)
  } catch (e) {
    errorMsg.value = e.message || 'AI启动失败'
  }
}

async function handleAIStop() {
  try {
    await stopCameraAI()
  } catch {
    // ignore
  }
  aiEnabled.value = false
  aiTaskId.value = null
  clearInterval(aiPollTimer)
  aiPollTimer = null
}

async function refreshAIStatus() {
  try {
    const res = await fetchCameraAIStatus()
    const data = res.data || {}
    if (!data.ai_enabled) {
      aiEnabled.value = false
      clearInterval(aiPollTimer)
      aiPollTimer = null
      return
    }
    aiFrameCount.value = data.frame_count
    aiActiveTracks.value = data.active_tracks
    const prevTotal = aiTotalEvents.value
    aiTotalEvents.value = data.total_events
    if (!aiFirstPoll && data.total_events > prevTotal) {
      playAlarm()
    }
    aiFirstPoll = false
    if (data.latest_events?.length) {
      aiLatestEvents.value = data.latest_events
      // Load snapshot images for new events
      for (const evt of data.latest_events) {
        if (!evt.snapshot_path || snapshotUrls.value[evt.track_id]) continue
        try {
          const fres = await fetchFile(evt.snapshot_path)
          snapshotUrls.value[evt.track_id] = URL.createObjectURL(fres.data)
        } catch {
          // ignore
        }
      }
    }
  } catch {
    // polling failure — ignore
  }
}

onMounted(() => {
  refreshStatus()
  statusEventSource = new EventSource('/api/camera/status/stream')
  statusEventSource.onmessage = (e) => {
    try { updateStatus(JSON.parse(e.data)) } catch { /* ignore */ }
  }
  statusEventSource.onerror = () => { /* auto-reconnect */ }
})

onBeforeUnmount(() => {
  if (statusEventSource) { statusEventSource.close(); statusEventSource = null }
  clearInterval(aiPollTimer)
  Object.values(snapshotUrls.value).forEach(url => URL.revokeObjectURL(url))
})
</script>

<template>
  <div class="monitor-page">
    <section class="control-card">
      <button class="primary-action" :disabled="running" @click="handleStart">启动摄像头</button>
      <button class="secondary-action" :disabled="!running" @click="handleStop">停止摄像头</button>
      <button
        v-if="!aiEnabled"
        class="ai-action"
        :disabled="!running || !hasROI"
        @click="handleAIStart"
      >
        AI检测 {{ hasROI ? '开' : '(需ROI)' }}
      </button>
      <button v-else class="ai-stop-action" @click="handleAIStop">AI检测 关</button>
      <span :class="['pill', running ? 'cyan' : 'red']">{{ running ? '运行中' : '已停止' }}</span>
      <span :class="['pill', aiEnabled ? 'cyan' : 'yellow']">{{ aiEnabled ? 'AI检测中' : '未入AI' }}</span>
      <span v-if="errorMsg" class="error-text">{{ errorMsg }}</span>
    </section>

    <section class="monitor-grid">
      <div class="camera-card">
        <div class="stream-container" v-if="running">
          <img ref="imgRef" :src="streamUrl" :key="streamUrl" alt="MJPEG camera stream" />
          <canvas
            v-if="!aiEnabled"
            ref="canvasRef"
            :width="cameraWidth"
            :height="cameraHeight"
            class="roi-canvas"
            @mousedown="onROIDown"
            @mousemove="onROIMove"
            @mouseup="onROIUp"
            @mouseleave="onROIUp"
          />
        </div>
        <template v-else>
          <div class="scan-glow"></div>
          <strong>摄像头未启动<br />点击"启动摄像头"开始</strong>
        </template>
        <div v-if="aiEnabled" class="ai-badge">
          帧: {{ aiFrameCount }} | 目标: {{ aiActiveTracks }} | 事件: {{ aiTotalEvents }}
        </div>
      </div>

      <aside class="status-card">
        <h3>摄像头状态</h3>
        <div class="status-list">
          <p><span>运行状态</span><span :class="running ? 'green' : 'red'">{{ running ? '在线' : '离线' }}</span></p>
          <p><span>设备编号</span><span>{{ cameraIndex }}</span></p>
          <p><span>分辨率</span><span>{{ cameraWidth }} × {{ cameraHeight }}</span></p>
          <p><span>流格式</span><span>{{ aiEnabled ? 'MJPEG (AI标注)' : 'MJPEG' }}</span></p>
        </div>

        <div v-if="aiEnabled" class="ai-section">
          <h3>AI 检测状态</h3>
          <div class="status-list">
            <p><span>任务ID</span><span>#{{ aiTaskId }}</span></p>
            <p><span>处理帧数</span><span>{{ aiFrameCount }}</span></p>
            <p><span>活跃目标</span><span class="cyan">{{ aiActiveTracks }}</span></p>
            <p><span>检出事件</span><span class="red">{{ aiTotalEvents }}</span></p>
          </div>

          <div v-if="aiLatestEvents.length" class="event-mini-list">
            <h4>最新事件</h4>
            <div v-for="evt in aiLatestEvents.slice(-5).reverse()" :key="evt.track_id" class="event-mini-row">
              <img
                v-if="snapshotUrls[evt.track_id]"
                :src="snapshotUrls[evt.track_id]"
                class="event-snapshot"
              />
              <div class="event-mini-info">
                <span>Track #{{ evt.track_id }}</span>
                <span>置信度 {{ (evt.confidence * 100).toFixed(0) }}%</span>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </section>
  </div>
</template>

<style scoped>
.monitor-page {
  max-width: 1080px;
}

.control-card,
.camera-card,
.status-card {
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
}

.control-card {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 80px;
  padding: 12px 24px;
  margin-bottom: 32px;
  flex-wrap: wrap;
}

.control-card button {
  min-width: 120px;
  height: 48px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 800;
  cursor: pointer;
}

.control-card button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
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

.ai-action {
  color: #04101c;
  background: #00ffb2;
  border: 1px solid #00ffb2;
}

.ai-stop-action {
  color: #04101c;
  background: #ff4d4f;
  border: 1px solid #ff4d4f;
}

.pill {
  display: inline-flex;
  align-items: center;
  height: 36px;
  padding: 0 18px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 800;
}

.pill.cyan { color: #00d8ff; border: 1px solid #00d8ff; }
.pill.red { color: #ff4d4f; border: 1px solid #ff4d4f; }
.pill.yellow { color: #ffb020; border: 1px solid #ffb020; }

.error-text {
  color: #ff4d4f;
  font-size: 14px;
  max-width: 400px;
}

.monitor-grid {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 32px;
}

.camera-card {
  position: relative;
  display: grid;
  place-items: center;
  height: 480px;
  background: #050b14;
  overflow: hidden;
}

.stream-container {
  position: relative;
  width: 100%;
  height: 100%;
}

.camera-card img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.roi-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  cursor: crosshair;
}

.scan-glow {
  width: 246px;
  height: 106px;
  border-radius: 50%;
  background: rgba(0, 216, 255, 0.12);
}

.camera-card strong {
  position: absolute;
  color: #91a8c7;
  font-size: 18px;
  line-height: 1.4;
  text-align: center;
}

.ai-badge {
  position: absolute;
  bottom: 8px;
  left: 8px;
  padding: 4px 12px;
  background: rgba(0, 0, 0, 0.65);
  border-radius: 6px;
  color: #00d8ff;
  font-size: 12px;
  font-weight: 600;
}

.status-card {
  min-height: 480px;
  padding: 24px 20px;
  overflow-y: auto;
}

.status-card h3 {
  margin-bottom: 18px;
  color: #eaf6ff;
  font-size: 18px;
}

.status-list p {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #1e3a5f;
  color: #91a8c7;
  font-size: 14px;
}

.status-list p span:last-child {
  color: #d6e4f2;
  font-weight: 600;
}

.green { color: #00ffb2 !important; }
.red { color: #ff4d4f !important; }
.cyan { color: #00d8ff !important; }

.ai-section {
  margin-top: 24px;
  padding-top: 18px;
  border-top: 1px solid #1e3a5f;
}

.event-mini-list {
  margin-top: 12px;
}

.event-mini-list h4 {
  color: #91a8c7;
  font-size: 13px;
  margin-bottom: 8px;
}

.event-mini-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid #1e3a5f;
}

.event-snapshot {
  width: 64px;
  height: 48px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid #1e3a5f;
}

.event-mini-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.event-mini-info span:first-child {
  color: #00d8ff;
  font-size: 13px;
  font-weight: 600;
}

.event-mini-info span:last-child {
  color: #91a8c7;
  font-size: 12px;
}
</style>
