<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadVideo, analyzeTask, fetchTask } from '../api/videos'

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
    // Build object URL for video preview
    videoUrl.value = URL.createObjectURL(selectedFile.value)
    step.value = 'configure'
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

// ── ROI drawing ──
const roi = ref({ x: 0, y: 0, width: null, height: null })
const drawing = ref(false)
const drawStart = ref({ x: 0, y: 0 })
const canvasWidth = ref(640)
const canvasHeight = ref(360)

function onVideoLoad() {
  const v = videoRef.value
  if (!v) return
  canvasWidth.value = v.videoWidth || 640
  canvasHeight.value = v.videoHeight || 360
  drawVideoFrame()
}

function drawVideoFrame() {
  const v = videoRef.value
  const c = canvasRef.value
  if (!v || !c) return
  const ctx = c.getContext('2d')
  ctx.drawImage(v, 0, 0, c.width, c.height)
  if (roi.value.width && roi.value.height) {
    ctx.strokeStyle = '#00d8ff'
    ctx.lineWidth = 2
    ctx.strokeRect(roi.value.x, roi.value.y, roi.value.width, roi.value.height)
  }
}

function getCanvasPos(e) {
  const rect = canvasRef.value.getBoundingClientRect()
  const scaleX = canvasWidth.value / rect.width
  const scaleY = canvasHeight.value / rect.height
  return {
    x: Math.round((e.clientX - rect.left) * scaleX),
    y: Math.round((e.clientY - rect.top) * scaleY),
  }
}

function onMouseDown(e) {
  drawing.value = true
  drawStart.value = getCanvasPos(e)
  roi.value = { x: drawStart.value.x, y: drawStart.value.y, width: null, height: null }
}

function onMouseMove(e) {
  if (!drawing.value) return
  const pos = getCanvasPos(e)
  roi.value = {
    x: Math.min(drawStart.value.x, pos.x),
    y: Math.min(drawStart.value.y, pos.y),
    width: Math.abs(pos.x - drawStart.value.x),
    height: Math.abs(pos.y - drawStart.value.y),
  }
  drawVideoFrame()
}

function onMouseUp() {
  drawing.value = false
  if (roi.value.width && roi.value.width < 10) {
    roi.value = { x: 0, y: 0, width: null, height: null }
    drawVideoFrame()
  }
}

// ── Analysis ──
const analyzing = ref(false)
const progress = ref(0)
const taskStatus = ref('')
const taskError = ref('')
const events = ref([])
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
      progress.value = t.progress || 0
      taskStatus.value = t.status
      events.value = t.events || []
      if (t.status === 'success' || t.status === 'failed') {
        clearInterval(pollTimer)
        pollTimer = null
        step.value = 'done'
        taskError.value = t.error_message || ''
        if (t.status === 'success') {
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

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (videoUrl.value) URL.revokeObjectURL(videoUrl.value)
})

// ── Status text ──
const statusText = computed(() => {
  const map = { pending: '等待中', running: '分析中', success: '已完成', failed: '失败' }
  return map[taskStatus.value] || taskStatus.value
})

const statusColor = computed(() => {
  const map = { running: '#00d8ff', success: '#00ffb2', failed: '#ff4d4f' }
  return map[taskStatus.value] || '#91a8c7'
})

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
  uploadProgress.value = 0
  if (videoUrl.value) { URL.revokeObjectURL(videoUrl.value); videoUrl.value = null }
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}
</script>

<template>
  <div class="analysis-page">
    <h2 class="page-heading">视频分析</h2>

    <!-- Step 1: Upload -->
    <section v-if="step === 'upload'" class="upload-section">
      <div class="upload-card" @click="fileInput?.click()">
        <input
          ref="fileInput"
          type="file"
          accept=".mp4,.avi,.mov,.mkv"
          style="display:none"
          @change="onFileChange"
        />
        <template v-if="!selectedFile">
          <el-icon :size="48" color="#52657f"><i class="el-icon-upload" /></el-icon>
          <p class="upload-hint">点击选择视频文件</p>
          <p class="upload-formats">支持 .mp4 .avi .mov .mkv</p>
        </template>
        <template v-else>
          <p class="file-name">{{ selectedFile.name }}</p>
          <p class="file-size">{{ (selectedFile.size / 1024 / 1024).toFixed(1) }} MB</p>
        </template>
      </div>
      <div class="upload-actions" v-if="selectedFile">
        <el-button
          type="primary"
          size="large"
          :loading="uploadLoading"
          @click="doUpload"
        >
          {{ uploadLoading ? `上传中 ${uploadProgress}%` : '上传视频' }}
        </el-button>
        <el-button size="large" @click="reset">取消</el-button>
      </div>
    </section>

    <!-- Step 2: Configure ROI -->
    <section v-if="step === 'configure'" class="configure-section">
      <div class="preview-panel">
        <h3 class="section-title">视频预览 — 拖动鼠标绘制ROI区域</h3>
        <div class="video-wrapper">
          <video
            ref="videoRef"
            :src="videoUrl"
            style="display:none"
            @loadeddata="onVideoLoad"
          />
          <canvas
            ref="canvasRef"
            :width="canvasWidth"
            :height="canvasHeight"
            class="roi-canvas"
            @mousedown="onMouseDown"
            @mousemove="onMouseMove"
            @mouseup="onMouseUp"
            @mouseleave="onMouseUp"
          />
        </div>
        <div class="roi-info">
          <span v-if="roi.width">ROI: ({{ roi.x }}, {{ roi.y }}) {{ roi.width }}×{{ roi.height }}</span>
          <span v-else class="roi-hint">请在画面上拖动鼠标绘制ROI矩形区域</span>
        </div>
      </div>
      <div class="configure-actions">
        <el-button
          type="primary"
          size="large"
          :loading="analyzing"
          :disabled="!roi.width"
          @click="doAnalyze"
        >
          开始分析
        </el-button>
        <el-button size="large" @click="reset">重新上传</el-button>
      </div>
    </section>

    <!-- Step 3-4: Running / Done -->
    <section v-if="step === 'running' || step === 'done'" class="result-section">
      <div class="result-card">
        <h3 class="section-title">分析进度</h3>
        <div class="status-row">
          <span class="status-badge" :style="{ color: statusColor }">{{ statusText }}</span>
          <span class="frame-info">任务 #{{ taskId }} | {{ totalFrames }} 帧</span>
        </div>
        <el-progress
          :percentage="progress"
          :status="taskStatus === 'failed' ? 'exception' : taskStatus === 'success' ? 'success' : undefined"
          :stroke-width="16"
          class="progress-bar"
        />
        <p v-if="taskStatus === 'failed'" class="error-msg">{{ taskError }}</p>

        <!-- Events -->
        <div v-if="events.length" class="events-panel">
          <h4>检测事件 ({{ events.length }})</h4>
          <div v-for="evt in events" :key="evt.id" class="event-row">
            <span>Track #{{ evt.track_id }}</span>
            <span>置信度 {{ evt.confidence?.toFixed(2) }}</span>
            <el-tag size="small" :type="evt.status === 'confirmed' ? 'success' : 'info'">
              {{ evt.status === 'unconfirmed' ? '待确认' : evt.status === 'confirmed' ? '已确认' : '误报' }}
            </el-tag>
          </div>
        </div>
      </div>
      <div class="result-actions">
        <el-button type="primary" size="large" @click="reset">分析新视频</el-button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.analysis-page {
  max-width: 960px;
  margin: 0 auto;
}

.page-heading {
  margin: 0 0 20px;
  color: #eaf6ff;
  font-size: 20px;
  font-weight: 600;
}

/* ── Upload ── */
.upload-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.upload-card {
  width: 100%;
  max-width: 500px;
  padding: 60px 40px;
  background: #101f33;
  border: 2px dashed #1e3a5f;
  border-radius: 12px;
  cursor: pointer;
  text-align: center;
  transition: border-color 0.2s;
}

.upload-card:hover {
  border-color: #00d8ff;
}

.upload-hint {
  margin: 12px 0 4px;
  color: #91a8c7;
  font-size: 15px;
}

.upload-formats {
  color: #52657f;
  font-size: 12px;
}

.file-name {
  color: #eaf6ff;
  font-size: 16px;
  margin-bottom: 4px;
  word-break: break-all;
}

.file-size {
  color: #91a8c7;
  font-size: 13px;
}

.upload-actions {
  display: flex;
  gap: 12px;
}

/* ── Configure ── */
.configure-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.preview-panel {
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  padding: 20px;
}

.section-title {
  margin: 0 0 12px;
  padding-left: 12px;
  border-left: 3px solid #00d8ff;
  color: #eaf6ff;
  font-size: 16px;
  font-weight: 600;
}

.video-wrapper {
  position: relative;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.roi-canvas {
  display: block;
  width: 100%;
  height: auto;
  cursor: crosshair;
}

.roi-info {
  margin-top: 10px;
  color: #91a8c7;
  font-size: 13px;
}

.roi-hint {
  color: #52657f;
}

.configure-actions {
  display: flex;
  gap: 12px;
}

/* ── Result ── */
.result-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.result-card {
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  padding: 24px;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.status-badge {
  font-size: 18px;
  font-weight: 700;
}

.frame-info {
  color: #52657f;
  font-size: 13px;
}

.progress-bar {
  margin-bottom: 16px;
}

.progress-bar :deep(.el-progress-bar__outer) {
  background: #1e3a5f;
}

.error-msg {
  color: #ff4d4f;
  font-size: 14px;
  margin-top: 8px;
}

.events-panel {
  margin-top: 20px;
  border-top: 1px solid #1e3a5f;
  padding-top: 16px;
}

.events-panel h4 {
  color: #91a8c7;
  font-size: 14px;
  margin: 0 0 12px;
}

.event-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 12px;
  background: #0b1728;
  border-radius: 6px;
  margin-bottom: 8px;
  color: #91a8c7;
  font-size: 13px;
}

.result-actions {
  display: flex;
  justify-content: center;
}
</style>
