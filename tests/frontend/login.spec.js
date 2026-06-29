import { test, expect } from '@playwright/test'

test.describe('登录页', () => {
  test.beforeEach(async ({ page }) => {
    // 清除登录状态
    await page.goto('/login')
    await page.evaluate(() => localStorage.clear())
    await page.reload()
  })

  test('显示登录表单', async ({ page }) => {
    await expect(page.locator('.card-title')).toHaveText('管理员登录')
    await expect(page.locator('input[placeholder="用户名"]')).toBeVisible()
    await expect(page.locator('input[placeholder="密码"]')).toBeVisible()
    await expect(page.locator('.login-btn')).toBeVisible()
  })

  test('空表单提交显示提示', async ({ page }) => {
    await page.click('.login-btn')
    await expect(page.locator('.error-msg')).toContainText('请输入账号和密码')
  })

  test('仅输入用户名提交显示提示', async ({ page }) => {
    await page.fill('input[placeholder="用户名"]', 'admin')
    await page.click('.login-btn')
    await expect(page.locator('.error-msg')).toContainText('请输入账号和密码')
  })

  test('Mock登录成功跳转首页', async ({ page }) => {
    // 拦截登录API，处理CORS预检+POST
    await page.route('**/api/auth/login', (route) => {
      if (route.request().method() === 'OPTIONS') {
        return route.fulfill({
          status: 204,
          headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
          },
        })
      }
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify({
          code: 200,
          data: { token: 'mock-token-1234567890abcdef1234567890abcdef', username: 'admin', role: 'admin' },
          message: '登录成功',
        }),
      })
    })

    await page.fill('input[placeholder="用户名"]', 'admin')
    await page.fill('input[placeholder="密码"]', 'admin123')

    // 等待mock拦截的POST响应
    const loginResp = page.waitForResponse(
      resp => resp.url().includes('/api/auth/login') && resp.request().method() === 'POST',
      { timeout: 10000 }
    )
    await page.locator('.login-btn').click()
    await loginResp

    // 等待SPA导航完成
    await page.waitForURL('/home', { timeout: 10000 })
    // token应存入localStorage
    await expect.poll(() =>
      page.evaluate(() => localStorage.getItem('token'))
    ).toBeTruthy()
  })

  test('Mock登录失败显示错误', async ({ page }) => {
    // 拦截登录API，返回失败
    await page.route('**/api/auth/login', (route) => {
      route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: '账号或密码错误' }),
      })
    })

    await page.fill('input[placeholder="用户名"]', 'admin')
    await page.fill('input[placeholder="密码"]', 'wrong')
    await page.click('.login-btn')

    await expect(page.locator('.error-msg')).toContainText('账号或密码错误')
  })

  test('Mock网络错误显示提示', async ({ page }) => {
    // 拦截登录API，模拟网络错误
    await page.route('**/api/auth/login', (route) => {
      route.abort('failed')
    })

    await page.fill('input[placeholder="用户名"]', 'admin')
    await page.fill('input[placeholder="密码"]', 'admin123')
    await page.click('.login-btn')

    await expect(page.locator('.error-msg')).toBeVisible()
  })
})
