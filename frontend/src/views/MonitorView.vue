<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { fetchCameraStatus, startCamera, stopCamera } from '../api/camera'

const running = ref(false)
const cameraIndex = ref(0)
const streamUrl = '/api/camera/stream'
const errorMsg = ref('')
let pollTimer = null

async function refreshStatus() {
  try {
    const res = await fetchCameraStatus()
    const data = res.data || {}
    running.value = data.status === 'online'
    cameraIndex.value = data.camera_index ?? 0
  } catch {
    running.value = false
  }
}

async function handleStart() {
  errorMsg.value = ''
  try {
    const res = await startCamera({ camera_index: 0, width: 640, height: 480 })
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
  try {
    await stopCamera()
  } finally {
    running.value = false
  }
}

onMounted(() => {
  refreshStatus()
  pollTimer = setInterval(refreshStatus, 5000)
})

onBeforeUnmount(() => {
  clearInterval(pollTimer)
})
</script>

<template>
  <div class="monitor-page">
    <section class="control-card">
      <button class="primary-action" :disabled="running" @click="handleStart">启动摄像头</button>
      <button class="secondary-action" :disabled="!running" @click="handleStop">停止摄像头</button>
      <span :class="['pill', running ? 'cyan' : 'red']">{{ running ? '运行中' : '已停止' }}</span>
      <span class="pill yellow">不入库</span>
      <span v-if="errorMsg" class="error-text">{{ errorMsg }}</span>
    </section>

    <section class="monitor-grid">
      <div class="camera-card">
        <img v-if="running" :src="streamUrl" :key="streamUrl" alt="MJPEG camera stream" />
        <template v-else>
          <div class="scan-glow"></div>
          <strong>摄像头未启动<br />点击"启动摄像头"开始</strong>
        </template>
      </div>

      <aside class="status-card">
        <h3>摄像头状态</h3>
        <div class="status-list">
          <p><span>运行状态</span><span :class="running ? 'green' : 'red'">{{ running ? '在线' : '离线' }}</span></p>
          <p><span>设备编号</span><span>{{ cameraIndex }}</span></p>
          <p><span>分辨率</span><span>640 × 480</span></p>
          <p><span>流格式</span><span>MJPEG</span></p>
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
  gap: 18px;
  height: 80px;
  padding: 0 28px;
  margin-bottom: 32px;
}

.control-card button {
  min-width: 130px;
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
}

.monitor-grid {
  display: grid;
  grid-template-columns: 1fr 280px;
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

.camera-card img {
  width: 100%;
  height: 100%;
  object-fit: contain;
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

.status-card {
  min-height: 480px;
  padding: 28px 24px;
}

.status-card h3 {
  margin-bottom: 32px;
  color: #eaf6ff;
  font-size: 20px;
}

.status-list p {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #1e3a5f;
  color: #91a8c7;
  font-size: 15px;
}

.status-list p span:last-child {
  color: #d6e4f2;
  font-weight: 600;
}

.green { color: #00ffb2 !important; }
.red { color: #ff4d4f !important; }
</style>
