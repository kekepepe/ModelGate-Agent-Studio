import { expect, test } from '@playwright/test'

test('Handoff Manager creates, accepts and completes a structured handoff', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-1440', 'Run the stateful handoff flow once.')
  await page.goto('/handoffs')
  await page.getByRole('button', { name: '演示交接' }).click()
  await page.getByRole('button', { name: '创建并继续' }).click()
  await expect(page.getByRole('heading', { name: 'Generate Handoff' })).toBeVisible()
  await page.getByPlaceholder('补充当前上下文、失败原因或接手要求...').fill('Playwright verifies structured responsibility transfer.')
  await page.getByRole('button', { name: '确认交接' }).click()

  await expect(page.getByRole('heading', { name: /Handoff #/ })).toBeVisible()
  await expect(page.getByText('Handoff Summary')).toBeVisible()
  await page.getByRole('button', { name: 'Accept Handoff' }).click()
  await expect(page.getByRole('button', { name: '保存结果' })).toBeVisible({ timeout: 10_000 })
  await page.getByPlaceholder('结果备注').fill('Accepted worker continued with preserved context.')
  await page.getByRole('button', { name: '保存结果' }).click()
  await expect(page.getByText('成功', { exact: true }).last()).toBeVisible({ timeout: 10_000 })
})

test('Knowledge Source sync exposes documents and can be disabled', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-1440', 'Run the stateful knowledge flow once.')
  const sourceName = `Playwright README ${Date.now()}`
  await page.goto('/evolution')
  await page.getByLabel('Knowledge source name').fill(sourceName)
  await page.getByLabel('Knowledge source path').fill('README.md')
  await page.getByLabel('Knowledge source scope').fill('README.md')
  await page.getByLabel('Knowledge source type').selectOption('project_document')
  await page.getByRole('button', { name: 'Connect source' }).click()

  const source = page.getByRole('article').filter({ hasText: sourceName })
  await expect(source).toBeVisible()
  await source.getByRole('button', { name: 'Sync' }).click()
  await expect(source.getByText(/Sync complete:/)).toBeVisible({ timeout: 15_000 })
  await source.getByRole('button', { name: 'View documents' }).click()
  const documentRow = source.getByRole('button', { name: /README\.md/ })
  await expect(documentRow).toBeVisible()
  await documentRow.click()
  await expect(source.getByText(/Chunk 0/)).toBeVisible()
  await source.getByRole('button', { name: 'Disable' }).click()
  await expect(source.getByText('disabled', { exact: true })).toBeVisible({ timeout: 10_000 })
})
