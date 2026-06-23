<script setup>
import { onMounted, ref } from 'vue'
import { fetchHealth } from './api/health'

const status = ref('正在连接后端…')
const online = ref(false)

onMounted(async () => {
  try {
    const result = await fetchHealth()
    online.value = result.status === 'ok'
    status.value = online.value ? '后端服务在线' : '后端状态异常'
  } catch {
    status.value = '后端服务离线'
  }
})
</script>

<template>
  <main class="shell">
    <section class="status-card">
      <p class="eyebrow">AI PRODUCTION PRACTICE</p>
      <h1>高空抛物监测系统</h1>
      <p class="description">系统框架运行状态</p>
      <div
        class="status"
        :class="{ online }"
        role="status"
        aria-live="polite"
      >
        <span class="status-dot" aria-hidden="true"></span>
        {{ status }}
      </div>
    </section>
  </main>
</template>
