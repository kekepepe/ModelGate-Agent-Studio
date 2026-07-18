import { expect, test } from '@playwright/test'

const API_BASE = process.env.PLAYWRIGHT_API_BASE ?? 'http://127.0.0.1:8000/api/v1'
const HEALTH_URL = `${API_BASE.replace(/\/api\/v1\/?$/, '')}/health`

test('loads the application shell and reaches the backend', async ({ page, request }, testInfo) => {
  const browserErrors: string[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') browserErrors.push(message.text())
  })
  page.on('pageerror', (error) => browserErrors.push(error.message))

  const health = await request.get(HEALTH_URL)
  expect(health.ok()).toBeTruthy()

  await page.goto('/workspace')
  await expect(page.locator('#root')).toBeVisible()
  await expect(page).toHaveTitle(/ModelGate/i)
  await expect(page.getByRole('navigation', { name: 'Primary navigation' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Workspace', exact: true })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Studio', exact: true })).toBeVisible()
  await expect(page.getByRole('article').first()).toBeVisible()
  await page.screenshot({ path: testInfo.outputPath('workspace-overview.png'), fullPage: true })
  expect(browserErrors).toEqual([])
})
