import axios from 'axios'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api'

const request = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

// 请求拦截器：注入token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：统一解包 {code, data, message} → 只返回data，非200抛错
request.interceptors.response.use(
  (response) => {
    const body = response.data
    // FastAPI HTTPException 返回 {"detail": {...}}，直接放行
    if (body && 'detail' in body && !('code' in body)) {
      return response
    }
    // 后端统一格式 {code, data, message}
    if (body && body.code !== undefined) {
      if (body.code === 200) {
        return { ...response, data: body.data }
      }
      // 业务错误
      const err = new Error(body.message || '请求失败')
      err.response = response
      return Promise.reject(err)
    }
    return response
  },
  (error) => {
    // HTTP 401 → 清除token跳转登录
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('token_expire')
      const router = window.__router__
      if (router && router.currentRoute.value.path !== '/login') {
        router.push('/login')
      }
    }
    return Promise.reject(error)
  }
)

export default request
