import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../components/MainLayout.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/home',
    children: [
      { path: 'home', name: 'Home', component: () => import('../views/HomeView.vue') },
      { path: 'analysis', name: 'Analysis', component: () => import('../views/VideoAnalysisView.vue') },
      { path: 'alarms', name: 'Alarms', component: () => import('../views/AlarmCenterView.vue') },
      { path: 'history', name: 'History', component: () => import('../views/HistoryView.vue') },
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/DashboardView.vue') },
      { path: 'settings', name: 'Settings', component: () => import('../views/SettingsView.vue') },
      { path: 'monitor', name: 'Monitor', component: () => import('../views/MonitorView.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const expire = Number(localStorage.getItem('token_expire'))

  if (to.path === '/login') {
    // 已登录 → 跳到首页
    if (token && expire > Date.now()) {
      return next('/')
    }
    return next()
  }

  // 受保护页面：无token或过期
  if (!token || expire <= Date.now()) {
    localStorage.removeItem('token')
    localStorage.removeItem('token_expire')
    return next('/login')
  }

  next()
})

export default router
