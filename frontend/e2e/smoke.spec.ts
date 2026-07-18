import { expect, test } from '@playwright/test'

const API_BASE = process.env.PLAYWRIGHT_API_BASE ?? 'http://127.0.0.1:8000/api/v1'
const HEALTH_URL = `${API_BASE.replace(/\/api\/v1\/?$/, '')}/health`

test('loads the application shell and reaches the backend', async ({ page, request }) => {
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
  await expect(page.getByRole('button', { name: 'Card Flow' })).toBeVisible()
  await page.getByRole('button', { name: 'Pixel Office' }).click()
  await expect(page.getByRole('region', { name: 'Pixel Office' })).toBeVisible()
  expect(browserErrors).toEqual([])
})
