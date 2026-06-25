<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, SwitchButton } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const menuItems = [
  { path: '/home', label: '系统首页', icon: 'home' },
  { path: '/analysis', label: '视频分析', icon: 'video' },
  { path: '/alarms', label: '报警中心', icon: 'bell' },
  { path: '/history', label: '历史事件', icon: 'clock' },
  { path: '/dashboard', label: '数据看板', icon: 'data' },
  { path: '/settings', label: '参数设置', icon: 'setting' },
  { path: '/monitor', label: '实时监控', icon: 'monitor' },
]

const pageTitle = computed(() => {
  const item = menuItems.find((m) => m.path === route.path)
  return item ? item.label : ''
})

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('token_expire')
  router.push('/login')
}
</script>

<template>
  <el-container class="main-layout">
    <!-- 顶部栏 -->
    <el-header class="top-bar" height="60px">
      <div class="top-left">
        <span class="system-name">高空抛物监测系统</span>
        <span class="page-title">{{ pageTitle }}</span>
      </div>
      <div class="top-right">
        <div class="status-group">
          <span class="status-item" :class="{ online: true }">
            <i class="status-dot"></i>后端在线
          </span>
          <span class="status-item">
            <i class="status-dot"></i>算法就绪
          </span>
          <span class="status-item">
            <i class="status-dot"></i>数据库正常
          </span>
        </div>
        <span class="user-tag">admin</span>
        <el-button
          :icon="SwitchButton"
          text
          class="logout-btn"
          @click="logout"
        >
          退出
        </el-button>
      </div>
    </el-header>

    <el-container class="body-area">
      <!-- 侧边栏 -->
      <el-aside class="side-bar" width="220px">
        <el-menu
          :default-active="route.path"
          class="side-menu"
          router
        >
          <el-menu-item
            v-for="item in menuItems"
            :key="item.path"
            :index="item.path"
          >
            <span>{{ item.label }}</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.main-layout {
  min-height: 100vh;
  background: #07111f;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #0b1728;
  border-bottom: 1px solid #1e3a5f;
}

.top-left {
  display: flex;
  align-items: baseline;
  gap: 20px;
}

.system-name {
  color: #eaf6ff;
  font-size: 18px;
  font-weight: 700;
}

.page-title {
  color: #91a8c7;
  font-size: 14px;
}

.top-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-group {
  display: flex;
  gap: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #52657f;
  font-size: 12px;
}

.status-item.online {
  color: #00ffb2;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 8px currentColor;
}

.user-tag {
  color: #91a8c7;
  font-size: 13px;
}

.logout-btn {
  color: #91a8c7;
}

.body-area {
  height: calc(100vh - 60px);
}

.side-bar {
  background: #0b1728;
  border-right: 1px solid #1e3a5f;
  overflow-y: auto;
}

.side-menu {
  border-right: none;
  background: transparent;
}

.side-menu :deep(.el-menu-item) {
  color: #91a8c7;
  font-size: 14px;
  margin: 4px 8px;
  border-radius: 8px;
}

.side-menu :deep(.el-menu-item:hover) {
  background: rgba(0, 216, 255, 0.08);
  color: #eaf6ff;
}

.side-menu :deep(.el-menu-item.is-active) {
  background: rgba(0, 216, 255, 0.14);
  color: #eaf6ff;
  border-left: 3px solid #00d8ff;
}

.main-content {
  padding: 20px;
  background: #07111f;
  overflow-y: auto;
}
</style>
