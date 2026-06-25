<script setup>
import { onMounted, ref } from 'vue'
import { fetchHealth } from '../api/health'
import { fetchSystemStatus } from '../api/system'

const backendOnline = ref(false)
const algoOnline = ref(false)
const dbOnline = ref(false)
const systemStatus = ref(null)
const loading = ref(true)

const statCards = [
  { label: '今日报警', value: '--' },
  { label: '累计事件', value: '--' },
  { label: '未确认事件', value: '--' },
]

onMounted(async () => {
  // 健康检查
  try {
    const h = await fetchHealth()
    backendOnline.value = h.status === 'ok'
  } catch {
    backendOnline.value = false
  }

  // 系统状态
  try {
    const s = await fetchSystemStatus()
    // 响应拦截器已自动解包，s.data 即业务数据
    systemStatus.value = s.data
    algoOnline.value = s.data.algorithm?.status === 'ready'
    dbOnline.value = s.data.database?.status === 'connected'
  } catch {
    algoOnline.value = false
    dbOnline.value = false
  }

  loading.value = false
})
</script>

<template>
  <div class="home-page">
    <h2 class="page-heading">系统首页</h2>

    <!-- 服务状态 -->
    <section class="status-row">
      <div class="status-card" :class="{ online: backendOnline, offline: !backendOnline }">
        <span class="status-label">后端服务</span>
        <span class="status-text">{{ backendOnline ? '在线' : '离线' }}</span>
        <i class="status-indicator"></i>
      </div>
      <div class="status-card" :class="{ online: algoOnline, offline: !algoOnline }">
        <span class="status-label">算法状态</span>
        <span class="status-text">{{ algoOnline ? '就绪' : '未就绪' }}</span>
        <i class="status-indicator"></i>
      </div>
      <div class="status-card" :class="{ online: dbOnline, offline: !dbOnline }">
        <span class="status-label">数据库</span>
        <span class="status-text">{{ dbOnline ? '正常' : '异常' }}</span>
        <i class="status-indicator"></i>
      </div>
      <div class="status-card online">
        <span class="status-label">设备状态</span>
        <span class="status-text">正常</span>
        <i class="status-indicator"></i>
      </div>
    </section>

    <!-- 统计卡片 -->
    <section class="stat-row">
      <div v-for="card in statCards" :key="card.label" class="stat-card">
        <span class="stat-label">{{ card.label }}</span>
        <span class="stat-value">{{ card.value }}</span>
      </div>
    </section>

    <!-- 最近事件占位 -->
    <section class="section-card">
      <h3 class="section-title">最近事件</h3>
      <el-empty description="暂无报警事件" />
    </section>
  </div>
</template>

<style scoped>
.home-page {
  max-width: 1200px;
}

.page-heading {
  margin: 0 0 20px;
  color: #eaf6ff;
  font-size: 20px;
  font-weight: 600;
}

.status-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.status-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 20px 24px;
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
  position: relative;
}

.status-label {
  font-size: 13px;
  color: #91a8c7;
}

.status-text {
  font-size: 18px;
  font-weight: 600;
}

.status-card.online .status-text {
  color: #00ffb2;
}

.status-card.offline .status-text {
  color: #ff4d4f;
}

.status-indicator {
  position: absolute;
  top: 12px;
  right: 16px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.status-card.online .status-indicator {
  color: #00ffb2;
  box-shadow: 0 0 12px #00ffb2;
}

.status-card.offline .status-indicator {
  color: #ff4d4f;
  box-shadow: 0 0 12px #ff4d4f;
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 24px;
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
}

.stat-label {
  font-size: 13px;
  color: #91a8c7;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #00d8ff;
  font-family: "DIN Alternate", Consolas, monospace;
}

.section-card {
  padding: 24px;
  background: #101f33;
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
}

.section-title {
  margin: 0 0 16px;
  padding-left: 12px;
  border-left: 3px solid #00d8ff;
  color: #eaf6ff;
  font-size: 16px;
  font-weight: 600;
}

.section-card :deep(.el-empty__description) {
  color: #52657f;
}
</style>
