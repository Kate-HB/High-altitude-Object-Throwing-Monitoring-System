<script setup>
import { useRoute, useRouter } from 'vue-router'
import { SwitchButton } from '@element-plus/icons-vue'

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

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('token_expire')
  router.push('/login')
}
</script>

<template>
  <el-container class="main-layout">
    <el-header class="top-bar" height="64px">
      <div class="top-left">
        <span class="system-name">高空抛物监测系统</span>
      </div>
      <div class="top-right">
        <div class="status-group">
          <span class="status-item" :class="{ online: true }">
            后端在线
          </span>
          <span class="status-item">
            GPU Ready
          </span>
        </div>
        <span class="user-tag">用户：admin</span>
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
      <el-aside class="side-bar" width="228px">
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
  padding: 0 28px;
  background: #0b1728;
}

.top-left {
  display: flex;
  align-items: baseline;
  gap: 20px;
}

.system-name {
  color: #eaf6ff;
  font-size: 20px;
  font-weight: 700;
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
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 14px;
  color: #00d8ff;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid #00d8ff;
  border-radius: 99px;
  background: rgba(0, 216, 255, 0.13);
}

.status-item.online {
  color: #00ffb2;
  border-color: #00ffb2;
  background: rgba(0, 255, 178, 0.13);
}

.user-tag {
  color: #91a8c7;
  font-size: 13px;
}

.logout-btn {
  color: #91a8c7;
}

.body-area {
  height: calc(100vh - 64px);
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
  height: 40px;
  margin: 14px 18px;
  border-radius: 8px;
}

.side-menu :deep(.el-menu-item:hover) {
  background: rgba(0, 216, 255, 0.08);
  color: #eaf6ff;
}

.side-menu :deep(.el-menu-item.is-active) {
  background: rgba(0, 216, 255, 0.14);
  color: #00d8ff;
  border: 1px solid #00d8ff;
}

.main-content {
  padding: 36px 32px;
  background: #07111f;
  overflow-y: auto;
}
</style>
