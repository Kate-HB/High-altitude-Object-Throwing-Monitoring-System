<script setup>
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadVideo, analyzeTask, fetchTask } from '../api/videos'
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
  if (v.readyState >= 2) {
    try {
      v.currentTime = 0
    } catch {
      drawVideoFrame()
    }
  }
}

function onVideoSeeked() {
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
const processedFrames = ref(0)
const resultVideoPath = ref('')
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
      events.value = t.events || []
      processedFrames.value = t.processed_frames || 0
      resultVideoPath.value = t.result_video_path || ''
      if (t.status === 'success' || t.status === 'failed') {
        clearInterval(pollTimer)
        pollTimer = null
        step.value = 'done'
        taskError.value = t.error_message || ''
        if (t.status === 'success') {
          await loadResultVideo(t.result_video_path)
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

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (videoUrl.value) URL.revokeObjectURL(videoUrl.value)
  if (resultVideoUrl.value) URL.revokeObjectURL(resultVideoUrl.value)
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
  processedFrames.value = 0
  resultVideoPath.value = ''
  uploadProgress.value = 0
  if (videoUrl.value) { URL.revokeObjectURL(videoUrl.value); videoUrl.value = null }
  if (resultVideoUrl.value) { URL.revokeObjectURL(resultVideoUrl.value); resultVideoUrl.value = null }
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}
</script>

<template>
  <div class="analysis-page">
    <h2 class="page-heading">视频分析</h2>

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
            @mousedown="onMouseDown"
            @mousemove="onMouseMove"
            @mouseup="onMouseUp"
            @mouseleave="onMouseUp"
          />
          <div v-if="!videoUrl" class="video-placeholder">
            <i></i>
            <span>首帧 ROI 选择</span>
          </div>
          <div v-if="roi.width" class="roi-readout">
            ROI: ({{ roi.x }}, {{ roi.y }}) {{ roi.width }}×{{ roi.height }}
          </div>
        </div>

        <div class="video-panel result-panel">
          <video
            v-if="resultVideoUrl"
            :src="resultVideoUrl"
            class="result-video"
            controls
          />
          <div v-else class="video-placeholder compact">
            <i></i>
            <span>结果视频回放</span>
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
        <el-button v-if="step === 'done'" class="new-btn" @click="reset">分析新视频</el-button>
      </aside>
    </section>
  </div>
</template>

<style scoped>
.analysis-page {
  max-width: 1080px;
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
  cursor: crosshair;
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
  left: 16px;
  bottom: 14px;
  padding: 5px 10px;
  color: #00d8ff;
  background: rgba(7, 17, 31, 0.82);
  border: 1px solid #1e3a5f;
  border-radius: 6px;
  font-size: 12px;
}

.result-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
}

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
}

.new-btn {
  margin-top: 10px;
}

.error-msg {
  color: #ff4d4f;
  font-size: 13px;
  margin-top: 12px;
}
</style>
