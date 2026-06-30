<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchCameraStatus, startCamera, stopCamera } from '../api/camera'

const running = ref(false)
const status = ref({
  resolution: '1280×720',
  fps: 15,
  device: 'laptop camera',
  mode: 'auxiliary demo',
})
const streamUrl = '/api/camera/stream'

const statusRows = computed(() => [
  `running: ${running.value}`,
  `resolution: ${status.value.resolution}`,
  `fps: ${status.value.fps}`,
  `device: ${status.value.device}`,
  `mode: ${status.value.mode}`,
])

async function refreshStatus() {
  try {
    const res = await fetchCameraStatus()
    const data = res.data || {}
    running.value = data.status === 'online'
  } catch {
    running.value = false
  }
}

async function handleStart() {
  try {
    await startCamera(0, 640, 480)
    running.value = true
  } catch {
    running.value = false
  }
}

async function handleStop() {
  try {
    await stopCamera()
  } finally {
    running.value = false
  }
}

onMounted(refreshStatus)
</script>

<template>
  <div class="monitor-page">
    <section class="control-card">
      <button class="primary-action" @click="handleStart">启动摄像头</button>
      <button class="secondary-action" @click="handleStop">停止摄像头</button>
      <span class="pill cyan">MJPEG流</span>
      <span class="pill yellow">不入库</span>
    </section>

    <section class="monitor-grid">
      <div class="camera-card">
        <img v-if="running" :src="streamUrl" alt="MJPEG camera stream" />
        <template v-else>
          <div class="scan-glow"></div>
          <div class="detect-box cyan-box"></div>
          <div class="detect-box yellow-box"></div>
          <strong>实时摄像头画面 +<br />YOLOv11检测框</strong>
        </template>
      </div>

      <aside class="status-card">
        <h3>摄像头状态</h3>
        <p v-for="row in statusRows" :key="row">{{ row }}</p>
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
  height: 116px;
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

.pill.cyan {
  color: #00d8ff;
  border: 1px solid #00d8ff;
}

.pill.yellow {
  color: #ffb020;
  border: 1px solid #ffb020;
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
  height: 520px;
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

.detect-box {
  position: absolute;
  border-radius: 4px;
}

.cyan-box {
  left: 270px;
  top: 190px;
  width: 150px;
  height: 116px;
  border: 2px solid #00d8ff;
}

.yellow-box {
  left: 520px;
  top: 320px;
  width: 128px;
  height: 92px;
  border: 2px solid #ffb020;
  background: rgba(255, 176, 32, 0.08);
}

.camera-card strong {
  position: absolute;
  left: 430px;
  top: 310px;
  color: #91a8c7;
  font-size: 18px;
  line-height: 1.25;
}

.status-card {
  min-height: 520px;
  padding: 36px 28px;
}

.status-card h3 {
  margin-bottom: 40px;
  color: #eaf6ff;
  font-size: 22px;
}

.status-card p {
  color: #91a8c7;
  font-size: 17px;
  line-height: 1.35;
}
</style>
