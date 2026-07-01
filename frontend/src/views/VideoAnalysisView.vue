<script setup>
defineOptions({ name: 'VideoAnalysisView' })
import { computed, nextTick, onActivated, onBeforeUnmount, onDeactivated, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadVideo, analyzeTask, fetchTask } from '../api/videos'
import { fetchEvents, updateEventStatus } from '../api/events'
import { fetchFile } from '../api/files'
import { normalizeTaskProgress } from '../utils/dashboard'

// ── Step state ──
const step = ref('upload') // upload | configure | running | done

// ── Upload ──
const fileInput = ref(null)
const selectedFile = ref(null)
const uploadLoading = ref(false)
const uploadProgress = ref(0)

const allowedExtensions = ['.mp4', '.avi', '.mov', '.mkv']

function onFileChange(e) {
  const f = e.target.files?.[0]
  if (!f) return
  const ext = '.' + f.name.split('.').pop().toLowerCase()
  if (!allowedExtensions.includes(ext)) {
    ElMessage.error(`不支持的文件格式: ${ext}，仅支持 ${allowedExtensions.join(', ')}`)
    return
  }
  selectedFile.value = f
}

async function doUpload() {
  if (!selectedFile.value) return
  uploadLoading.value = true
  uploadProgress.value = 0
  try {
    const fd = new FormData()
    fd.append('file', selectedFile.value)
    const res = await uploadVideo(fd, (p) => { uploadProgress.value = p })
    taskId.value = res.data.task_id
    totalFrames.value = res.data.total_frames
    videoUrl.value = URL.createObjectURL(selectedFile.value)
    step.value = 'configure'
    await nextTick()
    ElMessage.success('上传成功')
  } catch (e) {
    ElMessage.error(e.message || '上传失败')
  } finally {
    uploadLoading.value = false
  }
}

// ── Video preview ──
const taskId = ref(null)
const totalFrames = ref(0)
const videoUrl = ref(null)
const videoRef = ref(null)
const canvasRef = ref(null)
const resultVideoUrl = ref(null)
const previewUrl = ref(null)

function openPreview(url) { previewUrl.value = url }
function closePreview() { previewUrl.value = null }

// ── ROI drawing ──
const roi = ref({ x: 0, y: 0, width: null, height: null })
const drawing = ref(false)
const resizing = ref(false)
const resizeHandle = ref(null) // 'nw','n','ne','e','se','s','sw','w'
const drawStart = ref({ x: 0, y: 0 })
const roiBeforeResize = ref(null)
const canvasWidth = ref(640)
const canvasHeight = ref(360)

const HANDLE_SIZE = 12
const HANDLE_HIT = 16

function getHandleRects(r) {
  if (!r.width || !r.height) return []
  const cx = r.x + r.width / 2
  const cy = r.y + r.height / 2
  return [
    { key: 'nw', x: r.x, y: r.y, cursor: 'nwse-resize' },
    { key: 'n',  x: cx, y: r.y, cursor: 'ns-resize' },
    { key: 'ne', x: r.x + r.width, y: r.y, cursor: 'nesw-resize' },
    { key: 'e',  x: r.x + r.width, y: cy, cursor: 'ew-resize' },
    { key: 'se', x: r.x + r.width, y: r.y + r.height, cursor: 'nwse-resize' },
    { key: 's',  x: cx, y: r.y + r.height, cursor: 'ns-resize' },
    { key: 'sw', x: r.x, y: r.y + r.height, cursor: 'nesw-resize' },
    { key: 'w',  x: r.x, y: cy, cursor: 'ew-resize' },
  ]
}

function hitTestHandle(pos) {
  if (!roi.value.width || !roi.value.height) return null
  const handles = getHandleRects(roi.value)
  for (const h of handles) {
    if (Math.abs(pos.x - h.x) <= HANDLE_HIT && Math.abs(pos.y - h.y) <= HANDLE_HIT) {
      return { key: h.key, cursor: h.cursor }
    }
  }
  return null
}

// hover cursor feedback
const canvasCursor = ref('crosshair')
function updateCursor(e) {
  if (drawing.value || resizing.value) return
  const pos = getCanvasPos(e)
  const h = hitTestHandle(pos)
  canvasCursor.value = h ? h.cursor : 'crosshair'
}

function onVideoLoad() {
  const v = videoRef.value
  if (!v) return
  canvasWidth.value = v.videoWidth || 640
  canvasHeight.value = v.videoHeight || 360
  if (v.readyState >= 2) {
    try { v.currentTime = 0 } catch { drawVideoFrame() }
  }
}

function onVideoSeeked() { drawVideoFrame() }

function drawVideoFrame() {
  const v = videoRef.value
  const c = canvasRef.value
  if (!v || !c) return
  const ctx = c.getContext('2d')
  const W = c.width, H = c.height
  ctx.drawImage(v, 0, 0, W, H)
  const r = roi.value
  if (r.width && r.height) {
    // Dim overlay outside ROI
    ctx.fillStyle = 'rgba(0,0,0,0.35)'
    ctx.fillRect(0, 0, W, r.y)
    ctx.fillRect(0, r.y, r.x, r.height)
    ctx.fillRect(r.x + r.width, r.y, W - r.x - r.width, r.height)
    ctx.fillRect(0, r.y + r.height, W, H - r.y - r.height)

    // ROI border — solid line
    ctx.strokeStyle = '#00d8ff'
    ctx.lineWidth = 2.5
    ctx.setLineDash([])
    ctx.strokeRect(r.x, r.y, r.width, r.height)

    // Inner glow
    ctx.strokeStyle = 'rgba(0,216,255,0.25)'
    ctx.lineWidth = 6
    ctx.strokeRect(r.x, r.y, r.width, r.height)

    // Corner accent L-lines
    const cl = Math.min(r.width, r.height, 40) * 0.45
    ctx.strokeStyle = '#00d8ff'
    ctx.lineWidth = 2.5
    ctx.beginPath()
    ctx.moveTo(r.x, r.y + cl); ctx.lineTo(r.x, r.y); ctx.lineTo(r.x + cl, r.y)
    ctx.moveTo(r.x + r.width - cl, r.y); ctx.lineTo(r.x + r.width, r.y); ctx.lineTo(r.x + r.width, r.y + cl)
    ctx.moveTo(r.x + r.width, r.y + r.height - cl); ctx.lineTo(r.x + r.width, r.y + r.height); ctx.lineTo(r.x + r.width - cl, r.y + r.height)
    ctx.moveTo(r.x + cl, r.y + r.height); ctx.lineTo(r.x, r.y + r.height); ctx.lineTo(r.x, r.y + r.height - cl)
    ctx.stroke()

    // Resize handles — white-filled circles with cyan ring
    for (const h of getHandleRects(r)) {
      ctx.beginPath()
      ctx.arc(h.x, h.y, HANDLE_SIZE / 2, 0, Math.PI * 2)
      ctx.fillStyle = '#fff'
      ctx.fill()
      ctx.strokeStyle = '#00d8ff'
      ctx.lineWidth = 2
      ctx.stroke()
    }
  }
}

function getCanvasPos(e) {
  const rect = canvasRef.value.getBoundingClientRect()
  const clientX = e.touches ? e.touches[0].clientX : e.clientX
  const clientY = e.touches ? e.touches[0].clientY : e.clientY
  const px = clientX - rect.left
  const py = clientY - rect.top

  // Account for object-fit: contain letterboxing
  const cw = canvasWidth.value
  const ch = canvasHeight.value
  const canvasAspect = cw / ch
  const rectAspect = rect.width / rect.height
  let drawW, drawH, offsetX, offsetY
  if (canvasAspect > rectAspect) {
    drawW = rect.width
    drawH = rect.width / canvasAspect
    offsetX = 0
    offsetY = (rect.height - drawH) / 2
  } else {
    drawH = rect.height
    drawW = rect.height * canvasAspect
    offsetX = (rect.width - drawW) / 2
    offsetY = 0
  }
  return {
    x: Math.round(((px - offsetX) / drawW) * cw),
    y: Math.round(((py - offsetY) / drawH) * ch),
  }
}

function clampROI(r) {
  const clamped = { ...r }
  if (clamped.x < 0) { clamped.width += clamped.x; clamped.x = 0 }
  if (clamped.y < 0) { clamped.height += clamped.y; clamped.y = 0 }
  if (clamped.x + clamped.width > canvasWidth.value) clamped.width = canvasWidth.value - clamped.x
  if (clamped.y + clamped.height > canvasHeight.value) clamped.height = canvasHeight.value - clamped.y
  if (clamped.width < 0) clamped.width = 0
  if (clamped.height < 0) clamped.height = 0
  return clamped
}

function onPointerDown(e) {
  e.preventDefault()
  const pos = getCanvasPos(e)
  const h = hitTestHandle(pos)

  if (h) {
    resizing.value = true
    resizeHandle.value = h.key
    roiBeforeResize.value = { ...roi.value }
    drawStart.value = pos
  } else {
    drawing.value = true
    drawStart.value = pos
    roi.value = { x: pos.x, y: pos.y, width: null, height: null }
  }
}

function onPointerMove(e) {
  e.preventDefault()
  const pos = getCanvasPos(e)

  if (resizing.value) {
    const old = roiBeforeResize.value
    const dx = pos.x - drawStart.value.x
    const dy = pos.y - drawStart.value.y
    let nr = { x: old.x, y: old.y, width: old.width, height: old.height }

    switch (resizeHandle.value) {
      case 'nw': nr.x = old.x + dx; nr.y = old.y + dy; nr.width = old.width - dx; nr.height = old.height - dy; break
      case 'n':  nr.y = old.y + dy; nr.height = old.height - dy; break
      case 'ne': nr.y = old.y + dy; nr.width = old.width + dx; nr.height = old.height - dy; break
      case 'e':  nr.width = old.width + dx; break
      case 'se': nr.width = old.width + dx; nr.height = old.height + dy; break
      case 's':  nr.height = old.height + dy; break
      case 'sw': nr.x = old.x + dx; nr.width = old.width - dx; nr.height = old.height + dy; break
      case 'w':  nr.x = old.x + dx; nr.width = old.width - dx; break
    }
    roi.value = clampROI(nr)
    drawVideoFrame()
  } else if (drawing.value) {
    roi.value = clampROI({
      x: Math.min(drawStart.value.x, pos.x),
      y: Math.min(drawStart.value.y, pos.y),
      width: Math.abs(pos.x - drawStart.value.x),
      height: Math.abs(pos.y - drawStart.value.y),
    })
    drawVideoFrame()
  } else {
    updateCursor(e)
  }
}

function onPointerUp() {
  if (resizing.value) {
    resizing.value = false
    resizeHandle.value = null
    roiBeforeResize.value = null
    if (roi.value.width && roi.value.width < 10) {
      roi.value = { x: 0, y: 0, width: null, height: null }
      drawVideoFrame()
    }
  }
  if (drawing.value) {
    drawing.value = false
    if (roi.value.width && roi.value.width < 10) {
      roi.value = { x: 0, y: 0, width: null, height: null }
      drawVideoFrame()
    }
  }
}

function onKeyDown(e) {
  if (e.key === 'Delete' || e.key === 'Backspace') {
    if (roi.value.width) {
      roi.value = { x: 0, y: 0, width: null, height: null }
      drawVideoFrame()
    }
  }
}

// ── Analysis ──
const analyzing = ref(false)
const progress = ref(0)
const taskStatus = ref('')
const taskError = ref('')
const events = ref([])
const processedFrames = ref(0)
const resultVideoPath = ref('')
const snapshotUrls = ref({}) // eventId -> blob URL
let pollTimer = null

async function doAnalyze() {
  if (!roi.value.width || !roi.value.height) {
    ElMessage.warning('请先在视频上绘制ROI区域')
    return
  }
  analyzing.value = true
  try {
    const res = await analyzeTask(taskId.value, {
      roi_x: roi.value.x,
      roi_y: roi.value.y,
      roi_width: roi.value.width,
      roi_height: roi.value.height,
    })
    step.value = 'running'
    taskStatus.value = 'running'
    startPolling()
  } catch (e) {
    ElMessage.error(e.message || '启动分析失败')
  } finally {
    analyzing.value = false
  }
}

function startPolling() {
  pollTimer = setInterval(async () => {
    try {
      const res = await fetchTask(taskId.value)
      const t = res.data
      progress.value = normalizeTaskProgress(t)
      taskStatus.value = t.status
      processedFrames.value = t.processed_frames || 0
      resultVideoPath.value = t.result_video_path || ''
      // Fetch events from dedicated endpoint
      try {
        const evRes = await fetchEvents({ task_id: taskId.value })
        events.value = evRes.data?.events || []
      } catch {
        events.value = t.events || []
      }
      if (t.status === 'success' || t.status === 'failed') {
        clearInterval(pollTimer)
        pollTimer = null
        step.value = 'done'
        taskError.value = t.error_message || ''
        if (t.status === 'success') {
          await loadResultVideo(t.result_video_path)
          await loadSnapshotImages(events.value)
          ElMessage.success('分析完成')
        } else {
          ElMessage.error(t.error_message || '分析失败')
        }
      }
    } catch {
      // polling failure — ignore, retry next interval
    }
  }, 1500)
}

async function loadResultVideo(path) {
  if (!path) return
  try {
    const res = await fetchFile(path)
    if (resultVideoUrl.value) URL.revokeObjectURL(resultVideoUrl.value)
    resultVideoUrl.value = URL.createObjectURL(res.data)
  } catch {
    resultVideoUrl.value = null
  }
}

async function loadSnapshotImages(evts) {
  for (const evt of evts) {
    if (!evt.snapshot_path || snapshotUrls.value[evt.id]) continue
    try {
      const res = await fetchFile(evt.snapshot_path)
      snapshotUrls.value[evt.id] = URL.createObjectURL(res.data)
    } catch {
      // ignore
    }
  }
}

async function onConfirmEvent(eventId) {
  try {
    await updateEventStatus(eventId, 'confirmed')
    const idx = events.value.findIndex(e => e.id === eventId)
    if (idx !== -1) events.value[idx].status = 'confirmed'
    ElMessage.success('事件已确认')
  } catch {
    ElMessage.error('状态更新失败')
  }
}

async function onFalseAlarm(eventId) {
  try {
    await updateEventStatus(eventId, 'false_alarm')
    const idx = events.value.findIndex(e => e.id === eventId)
    if (idx !== -1) events.value[idx].status = 'false_alarm'
    ElMessage.success('已标记为误报')
  } catch {
    ElMessage.error('状态更新失败')
  }
}

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (videoUrl.value) URL.revokeObjectURL(videoUrl.value)
  if (resultVideoUrl.value) URL.revokeObjectURL(resultVideoUrl.value)
  Object.values(snapshotUrls.value).forEach(url => URL.revokeObjectURL(url))
})

onDeactivated(() => {
  // Pause polling when navigating away (keep-alive)
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
})

onActivated(() => {
  // Resume polling if task is still running
  if (taskStatus.value === 'running' && !pollTimer) {
    startPolling()
  }
})

// ── Status helpers ──
const statusText = computed(() => {
  const map = { pending: '等待中', running: '分析中', success: '已完成', failed: '失败' }
  return map[taskStatus.value] || taskStatus.value
})

const statusColor = computed(() => {
  const map = { running: '#00d8ff', success: '#00ffb2', failed: '#ff4d4f' }
  return map[taskStatus.value] || '#91a8c7'
})

const progressStatus = computed(() => {
  const map = { running: '', success: 'success', failed: 'exception' }
  return map[taskStatus.value] || ''
})

const eventTagType = (s) => {
  const map = { unconfirmed: 'warning', confirmed: 'success', false_alarm: 'info' }
  return map[s] || 'info'
}

// ── Reset ──
function reset() {
  step.value = 'upload'
  selectedFile.value = null
  taskId.value = null
  totalFrames.value = 0
  roi.value = { x: 0, y: 0, width: null, height: null }
  progress.value = 0
  taskStatus.value = ''
  taskError.value = ''
  events.value = []
  processedFrames.value = 0
  resultVideoPath.value = ''
  uploadProgress.value = 0
  if (fileInput.value) fileInput.value.value = ''
  if (videoUrl.value) { URL.revokeObjectURL(videoUrl.value); videoUrl.value = null }
  if (resultVideoUrl.value) { URL.revokeObjectURL(resultVideoUrl.value); resultVideoUrl.value = null }
  Object.values(snapshotUrls.value).forEach(url => URL.revokeObjectURL(url))
  snapshotUrls.value = {}
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}
</script>

<template>
  <div class="analysis-page" @keydown="onKeyDown" tabindex="0">
    <section class="analysis-grid">
      <div class="left-column">
        <div class="panel upload-panel">
          <h3 class="panel-title">上传视频</h3>
          <div class="upload-box" @click="fileInput?.click()">
            <input
              ref="fileInput"
              type="file"
              accept=".mp4,.avi,.mov,.mkv"
              style="display:none"
              @change="onFileChange"
            />
            <template v-if="!selectedFile">
              <p class="upload-hint">拖拽或选择 MP4/AVI</p>
            </template>
            <template v-else>
              <p class="file-name">{{ selectedFile.name }}</p>
              <p class="file-size">{{ (selectedFile.size / 1024 / 1024).toFixed(1) }} MB</p>
            </template>
          </div>
          <div class="button-row">
            <el-button
              type="primary"
              :loading="uploadLoading"
              :disabled="!selectedFile || step !== 'upload'"
              @click.stop="doUpload"
            >
              {{ uploadLoading ? `上传中 ${uploadProgress}%` : '选择视频' }}
            </el-button>
            <el-button v-if="selectedFile" @click="reset">重置</el-button>
          </div>
        </div>

        <div class="panel params-panel">
          <h3 class="panel-title">快速参数</h3>
          <p class="param-text">detect_confidence = 0.35</p>
          <div class="slider-track">
            <i></i>
          </div>
        </div>
      </div>

      <div class="center-column">
        <div class="video-panel roi-panel">
          <video
            ref="videoRef"
            :src="videoUrl"
            class="hidden-video"
            @loadeddata="onVideoLoad"
            @seeked="onVideoSeeked"
          />
          <canvas
            v-show="videoUrl"
            ref="canvasRef"
            :width="canvasWidth"
            :height="canvasHeight"
            class="roi-canvas"
            :style="{ cursor: canvasCursor }"
            @mousedown="onPointerDown"
            @mousemove="onPointerMove"
            @mouseup="onPointerUp"
            @mouseleave="onPointerUp"
            @touchstart="onPointerDown"
            @touchmove="onPointerMove"
            @touchend="onPointerUp"
          />
          <div v-if="!videoUrl" class="video-placeholder">
            <i></i>
            <span>首帧 ROI 选择</span>
          </div>
          <div v-if="roi.width" class="roi-readout">
            ROI: ({{ roi.x }}, {{ roi.y }}) {{ roi.width }}×{{ roi.height }}
            <span class="roi-hint">拖拽角点调整 · Delete清除</span>
          </div>
        </div>

        <!-- Result area -->
        <div class="video-panel result-panel">
          <video
            v-if="resultVideoUrl"
            :src="resultVideoUrl"
            class="result-video"
            controls
          />
          <div v-else class="video-placeholder compact">
            <i></i>
            <span>{{ step === 'running' ? '分析中...' : '结果视频回放' }}</span>
          </div>
        </div>
      </div>

      <aside class="task-panel">
        <h3 class="panel-title">任务进度</h3>
        <p class="task-muted">processed / total</p>
        <div class="progress-track">
          <i :style="{ width: `${progress}%` }"></i>
        </div>
        <span class="task-status" :style="{ color: statusColor, borderColor: statusColor }">
          {{ statusText || '等待上传' }}
        </span>
        <div class="task-summary">
          <p>任务：{{ taskId ? `#${taskId}` : '--' }}</p>
          <p>帧数：{{ processedFrames }} / {{ totalFrames || '--' }}</p>
          <p>疑似事件：{{ events.length }}</p>
          <p>最高置信度：{{ events[0]?.confidence ?? '--' }}</p>
          <p>状态：{{ taskStatus || '--' }}</p>
        </div>
        <el-button
          type="primary"
          class="analyze-btn"
          :loading="analyzing"
          :disabled="step !== 'configure' || !roi.width"
          @click="doAnalyze"
        >
          开始分析
        </el-button>
        <p v-if="taskStatus === 'failed'" class="error-msg">{{ taskError }}</p>

        <!-- Event list with actions -->
        <div v-if="events.length" class="event-mini-list">
          <h4 class="event-mini-title">检出事件</h4>
          <div v-for="evt in events" :key="evt.id" class="event-mini-row">
            <img
              v-if="snapshotUrls[evt.id]"
              :src="snapshotUrls[evt.id]"
              class="event-snapshot"
              @click="openPreview(snapshotUrls[evt.id])"
              title="点击查看大图"
            />
            <div class="event-mini-info">
              <span class="event-mini-id">#{{ evt.track_id }}</span>
              <span class="event-mini-conf">{{ (evt.confidence * 100).toFixed(0) }}%</span>
              <el-tag :type="eventTagType(evt.status)" size="small">{{ evt.status }}</el-tag>
            </div>
            <div v-if="evt.status === 'unconfirmed'" class="event-mini-actions">
              <el-button size="small" type="success" plain @click="onConfirmEvent(evt.id)">确认</el-button>
              <el-button size="small" type="info" plain @click="onFalseAlarm(evt.id)">误报</el-button>
            </div>
          </div>
        </div>

        <el-button v-if="step === 'done'" class="new-btn" @click="reset">分析新视频</el-button>
      </aside>
    </section>

    <!-- Preview overlay -->
    <div v-if="previewUrl" class="preview-overlay" @click="closePreview">
      <img :src="previewUrl" class="preview-image" @click.stop />
    </div>
  </div>
</template>

<style scoped>
.analysis-page {
  max-width: 1080px;
  outline: none;
}

.page-heading {
  margin: 4px 0 24px;
  color: #eaf6ff;
  font-size: 30px;
  font-weight: 700;
}

.analysis-grid {
  display: grid;
  grid-template-columns: 320px 1fr 180px;
  gap: 32px;
  align-items: start;
}

.left-column,
.center-column {
  display: grid;
  gap: 24px;
}

.panel,
.task-panel {
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
}

.upload-panel {
  height: 230px;
  padding: 24px;
}

.params-panel {
  height: 164px;
  padding: 24px;
}

.panel-title {
  color: #eaf6ff;
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 18px;
}

.upload-box {
  height: 66px;
  display: grid;
  place-items: center;
  margin-bottom: 12px;
  background: #0d1a2b;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  cursor: pointer;
}

.upload-hint,
.file-size,
.task-muted,
.param-text {
  color: #91a8c7;
  font-size: 14px;
}

.file-name {
  max-width: 230px;
  color: #eaf6ff;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.button-row {
  display: flex;
  gap: 10px;
}

.slider-track,
.progress-track {
  height: 8px;
  margin-top: 18px;
  background: #1e3a5f;
  border-radius: 99px;
  overflow: hidden;
}

.slider-track i {
  display: block;
  width: 45%;
  height: 100%;
  background: #00d8ff;
}

.video-panel {
  position: relative;
  background: #050b14;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  overflow: hidden;
}

.hidden-video {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.roi-panel {
  height: 330px;
}

.result-panel {
  height: 250px;
}

.roi-canvas {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  touch-action: none;
}

.video-placeholder {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: #91a8c7;
  font-size: 16px;
}

.video-placeholder i {
  width: 136px;
  height: 56px;
  margin-bottom: 58px;
  border-radius: 50%;
  background: rgba(0, 216, 255, 0.18);
  filter: blur(1px);
}

.video-placeholder span {
  position: absolute;
}

.video-placeholder.compact i {
  height: 45px;
  margin-bottom: 42px;
}

.roi-readout {
  position: absolute;
  left: 12px;
  top: 12px;
  padding: 4px 10px;
  color: #00d8ff;
  background: rgba(7, 17, 31, 0.88);
  border: 1px solid #1e3a5f;
  border-radius: 6px;
  font-size: 12px;
  pointer-events: none;
}

.roi-hint {
  color: #52657f;
  margin-left: 8px;
}

.result-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
}

/* Progress panel */
.progress-panel {
  padding: 20px 24px;
}

.progress-panel :deep(.el-progress-bar__outer) {
  background: #1e3a5f;
}

.progress-panel :deep(.el-progress-bar__inner) {
  background: #00d8ff;
}

.progress-panel :deep(.el-progress--success .el-progress-bar__inner) {
  background: #00ffb2;
}

.progress-panel :deep(.el-progress--exception .el-progress-bar__inner) {
  background: #ff4d4f;
}

.progress-detail {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  color: #91a8c7;
  font-size: 13px;
}

.task-status-tag {
  display: inline-flex;
  padding: 2px 10px;
  border: 1px solid;
  border-radius: 99px;
  font-size: 12px;
  font-weight: 700;
}

/* Task panel */
.task-panel {
  min-height: 614px;
  padding: 24px;
}

.progress-track i {
  display: block;
  height: 100%;
  background: #00d8ff;
  transition: width 0.2s ease;
}

.task-status {
  display: inline-flex;
  margin: 20px 0 28px;
  padding: 6px 14px;
  border: 1px solid #00d8ff;
  border-radius: 99px;
  font-size: 12px;
  font-weight: 700;
}

.task-summary {
  display: grid;
  gap: 7px;
  margin-bottom: 26px;
  color: #eaf6ff;
  font-size: 14px;
}

.analyze-btn,
.new-btn {
  width: 100%;
  margin-top: 10px;
}

.error-msg {
  color: #ff4d4f;
  font-size: 13px;
  margin-top: 12px;
}

/* Event mini list */
.event-mini-list {
  margin-top: 18px;
  border-top: 1px solid #1e3a5f;
  padding-top: 14px;
}

.event-mini-title {
  color: #91a8c7;
  font-size: 13px;
  margin-bottom: 10px;
}

.event-mini-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 0;
  border-bottom: 1px solid #1e3a5f;
}

.event-mini-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.event-mini-id {
  color: #00d8ff;
  font-weight: 700;
  font-size: 13px;
}

.event-mini-conf {
  color: #eaf6ff;
  font-size: 12px;
}

.event-snapshot {
  width: 100%;
  height: auto;
  max-height: 120px;
  object-fit: contain;
  border-radius: 4px;
  border: 1px solid #1e3a5f;
  cursor: pointer;
  margin-bottom: 6px;
  background: #050b14;
}

.event-mini-actions {
  display: flex;
  gap: 6px;
}

/* Preview overlay */
.preview-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.preview-image {
  max-width: 90vw;
  max-height: 90vh;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 0 60px rgba(0, 216, 255, 0.15);
  cursor: default;
}
</style>
