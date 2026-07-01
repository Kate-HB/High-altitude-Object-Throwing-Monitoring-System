import { test, expect } from '@playwright/test'

test.describe('首页', () => {
  test.beforeEach(async ({ page }) => {
    // 设置模拟登录 token，跳过登录页
    await page.goto('/login')
    await page.evaluate(() => {
      localStorage.setItem('token', 'mock-token-1234567890abcdef1234567890abcdef')
      localStorage.setItem('token_expire', String(Date.now() + 3600000))
    })

    // Mock后端API
    await page.route('**/api/health', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'ok', time: new Date().toISOString() }),
      })
    })
    await page.route('**/api/system/status', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          code: 200,
          data: {
            backend: { status: 'running', version: '0.1.0' },
            database: { status: 'connected', driver: 'SQLite' },
            algorithm: { status: 'not_ready', model: 'YOLOv11', device: 'CPU' },
            device: { cpu_count: 8, memory_total: '16GB' },
          },
        }),
      })
    })
    await page.route('**/api/statistics/overview', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          code: 200,
          data: {
            today_event_count: 5,
            total_event_count: 128,
            daily_trend: [
              { date: '06-20', count: 2 },
              { date: '06-21', count: 5 },
              { date: '06-22', count: 3 },
              { date: '06-23', count: 8 },
              { date: '06-24', count: 4 },
              { date: '06-25', count: 6 },
            ],
            recent_events: [
              { id: 1, created_at: '2026-06-26 10:30', confidence: 0.92, status: 'confirmed' },
              { id: 2, created_at: '2026-06-26 09:15', confidence: 0.88, status: 'unconfirmed' },
            ],
          },
        }),
      })
    })
  })

  test('显示系统首页标题', async ({ page }) => {
    await page.goto('/home')
    await expect(page.locator('.flow-title')).toHaveText('主演示闭环')
  })

  test('显示4个统计卡片', async ({ page }) => {
    await page.goto('/home')
    await expect(page.locator('.stat-card')).toHaveCount(4)
  })

  test('显示今日事件和累计事件', async ({ page }) => {
    await page.goto('/home')
    // 卡片值应在mock数据加载后显示
    await expect(page.locator('.stat-card').first()).toContainText('今日事件')
    // 第二个卡片应显示累计事件
    await expect(page.locator('.stat-card').nth(1)).toContainText('累计事件')
  })

  test('显示事件趋势柱状图', async ({ page }) => {
    await page.goto('/home')
    await expect(page.locator('.bar-chart')).toBeVisible()
    // 应有趋势柱
    await expect(page.locator('.trend-bar').first()).toBeVisible()
  })

  test('显示主演示闭环', async ({ page }) => {
    await page.goto('/home')
    await expect(page.locator('.flow-card')).toBeVisible()
    await expect(page.locator('.flow-card p')).toContainText('登录')
  })

  test('无登录态跳转到登录页', async ({ page }) => {
    // 清除登录状态
    await page.goto('/login')
    await page.evaluate(() => localStorage.clear())
    await page.goto('/home')
    await expect(page).toHaveURL('/login')
  })
})
