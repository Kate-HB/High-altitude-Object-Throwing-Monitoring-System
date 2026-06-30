<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../api/auth'

const router = useRouter()

const form = ref({ username: '', password: '' })
const errorMsg = ref('')
const loading = ref(false)

async function handleLogin() {
  errorMsg.value = ''
  if (!form.value.username || !form.value.password) {
    errorMsg.value = '请输入账号和密码'
    return
  }
  loading.value = true
  try {
    const res = await login(form.value.username, form.value.password)
    // 响应拦截器已自动解包 {code, data, message}，res.data 即业务数据
    if (res.data?.token) {
      localStorage.setItem('token', res.data.token)
      localStorage.setItem('token_expire', String(Date.now() + 86400000))
      router.push('/')
    } else {
      errorMsg.value = '登录失败'
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || err.message || '无法连接服务器，请检查后端是否启动'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-left">
      <div class="brand">
        <p class="eyebrow">AI PRODUCTION PRACTICE</p>
        <h1>高空抛物监测系统</h1>
        <p class="desc">基于深度学习的智能安防监控平台</p>
      </div>
      <div class="deco-lines">
        <span class="line"></span>
        <span class="line"></span>
      </div>
    </div>

    <div class="login-right">
      <div class="login-card">
        <h2 class="card-title">管理员登录</h2>

        <el-form
          class="login-form"
          @submit.prevent="handleLogin"
        >
          <el-form-item>
            <el-input
              v-model="form.username"
              placeholder="用户名"
              size="large"
            />
          </el-form-item>
          <el-form-item>
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              size="large"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

          <el-button
            type="primary"
            class="login-btn"
            size="large"
            :loading="loading"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  min-height: 100vh;
  background:
    radial-gradient(circle at 20% 20%, rgba(0, 216, 255, 0.16), transparent 30%),
    radial-gradient(circle at 80% 10%, rgba(0, 255, 178, 0.10), transparent 28%),
    #07111f;
}

.login-left {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 80px 60px;
}

.brand {
  max-width: 440px;
}

.eyebrow {
  margin: 0 0 20px;
  color: #6ea9ad;
  font-family: Consolas, monospace;
  font-size: 12px;
  letter-spacing: 0.2em;
}

.brand h1 {
  margin: 0;
  color: #eaf6ff;
  font-size: 46px;
  font-weight: 700;
  line-height: 1.2;
}

.desc {
  margin: 16px 0 0;
  color: #91a8c7;
  font-size: 16px;
}

.deco-lines {
  margin-top: 60px;
  display: flex;
  gap: 12px;
}

.deco-lines .line {
  display: block;
  width: 120px;
  height: 2px;
  background: linear-gradient(90deg, #00d8ff, transparent);
}

.login-right {
  flex: 0 0 480px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 48px 40px;
  background: rgba(16, 31, 51, 0.85);
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
}

.card-title {
  margin: 0 0 32px;
  color: #eaf6ff;
  font-size: 20px;
  font-weight: 600;
  text-align: center;
}

.login-form :deep(.el-input__wrapper) {
  background: #0d1a2b;
  border-color: #1e3a5f;
  box-shadow: none;
}

.login-form :deep(.el-input__wrapper:focus-within) {
  border-color: #00d8ff;
}

.login-form :deep(.el-input__inner) {
  color: #eaf6ff;
}

.error-msg {
  margin: -8px 0 16px;
  color: #ff4d4f;
  font-size: 13px;
  text-align: center;
}

.login-btn {
  width: 100%;
  background: #00d8ff;
  border-color: #00d8ff;
  color: #04101c;
  font-weight: 600;
}

.login-btn:hover {
  background: #33e3ff;
}
</style>
