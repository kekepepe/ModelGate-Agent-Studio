import { expect, test, type APIRequestContext, type Page } from '@playwright/test'

const API_BASE = process.env.PLAYWRIGHT_API_BASE ?? 'http://127.0.0.1:8000/api/v1'

function captureBrowserErrors(page: Page) {
  const errors: string[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text())
  })
  page.on('pageerror', (error) => errors.push(error.message))
  return errors
}

async function createStartedGoal(request: APIRequestContext, title: string) {
  const created = await request.post(`${API_BASE}/goals`, {
    data: { title, execution_mode: 'mock', max_parallel_tasks: 3 },
  })
  expect(created.ok()).toBeTruthy()
  const payload = (await created.json()).data
  const goalId = payload.goal_id as string
  const runId = payload.run_id as string
  const started = await request.post(`${API_BASE}/goals/${goalId}/start`)
  expect(started.ok()).toBeTruthy()
  return { goalId, runId }
}

test('Goal, replan, Card/Pixel, refresh, execution and final output stay consistent', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-1440', 'Run the stateful core flow once; layout smoke covers every viewport.')
  const browserErrors = captureBrowserErrors(page)
  const title = `E2E status summary ${Date.now()}`

  await page.goto('/workspace/new?team=code-delivery')
  await page.getByPlaceholder('描述你的目标...').fill(title)
  await page.getByRole('button', { name: /Run Config/ }).click()
  await page.locator('.workspace-config-form select').selectOption('mock')
  await page.getByRole('button', { name: '开始' }).click()

  await expect(page.getByRole('region', { name: 'Active execution plan' })).toBeVisible({ timeout: 20_000 })
  await expect(page.getByText('Rule fallback plan')).toBeVisible()
  await page.getByRole('button', { name: /Modify/ }).click()
  const objective = `Produce a concise E2E summary ${Date.now()}`
  await page.locator('.plan-edit-list input').first().fill(objective)
  await page.getByRole('button', { name: 'Save & confirm' }).click()
  await expect(page.locator('.plan-version-badge')).toHaveText('v2', { timeout: 15_000 })

  await page.getByText(objective, { exact: true }).first().click()
  const detail = page.getByRole('dialog', { name: new RegExp(objective) })
  await expect(detail).toBeVisible()
  await detail.getByRole('button', { name: 'Context' }).click()
  await expect(detail.getByText(/尚未建立可继承上下文|当前 Worker 接收到的上下文/)).toBeVisible()
  await detail.getByRole('button', { name: 'Tools' }).click()
  await expect(detail.getByText('Tool access')).toBeVisible()
  await detail.getByRole('button', { name: 'History' }).click()
  await expect(detail.getByText(/尚未执行模型路由|选择理由/)).toBeVisible()
  await detail.getByRole('button', { name: '关闭详情' }).click()

  await page.getByRole('button', { name: 'Pixel Office' }).click()
  await expect(page.getByRole('region', { name: 'Pixel Office' })).toContainText(objective)
  await page.getByRole('button', { name: 'Card Flow' }).click()
  await expect(page.getByRole('region', { name: 'Agent Flow' })).toContainText(objective)

  const runId = new URL(page.url()).pathname.split('/').at(-1)
  expect(runId).toBeTruthy()
  const runResponse = await page.request.get(`${API_BASE}/runs/${runId}`)
  const goalId = (await runResponse.json()).data.goal_id as string
  expect(goalId).toBeTruthy()
  await expect(page.getByRole('navigation', { name: 'Primary navigation' })).toBeVisible()
  await page.getByRole('link', { name: 'Logs' }).first().click()
  await expect(page).toHaveURL(new RegExp(`/logs\\?runId=${runId}`))
  await expect(page.getByRole('link', { name: '返回当前 Workspace' })).toBeVisible()
  await page.goBack()
  await expect(page).toHaveURL(new RegExp(`/workspace/runs/${runId}`))
  await page.reload()
  await expect(page.locator('.plan-version-badge')).toHaveText('v2')
  await expect(page.getByText(objective, { exact: true }).first()).toBeVisible()

  await page.getByRole('button', { name: 'Run', exact: true }).click()
  await expect.poll(async () => {
    const response = await page.request.get(`${API_BASE}/runtime/status/${goalId}`)
    return (await response.json()).data.goal_status
  }, { timeout: 30_000 }).toBe('completed')
  await expect(page.getByText('已完成', { exact: true }).first()).toBeVisible({ timeout: 10_000 })

  await page.getByRole('button', { name: /Console summary/ }).click()
  const finalOutput = page.getByTestId('workspace-final-output')
  await expect(finalOutput).toContainText('执行完成，交付内容如下')
  await expect(finalOutput).toContainText('Final Output')
  await expect(finalOutput).toContainText('运行总结')
  await page.screenshot({ path: testInfo.outputPath('workspace-completed.png'), fullPage: true })
  expect(browserErrors).toEqual([])
})

test('a 100-task DAG remains readable and state survives Card/Pixel switching', async ({ page, request }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-1440', 'Run the large-DAG fixture once; viewport smoke is separate.')
  const { goalId, runId } = await createStartedGoal(request, `Long DAG QA ${Date.now()}`)
  const stateResponse = await request.get(`${API_BASE}/workspace/${goalId}/state`)
  const state = (await stateResponse.json()).data
  const tasks = Array.from({ length: 100 }, (_, index) => ({
    client_task_id: `dag-${index + 1}`,
    objective: `Long DAG task ${String(index + 1).padStart(2, '0')} with enough text to verify wrapping and overflow behavior`,
    task_type: 'direct',
    required_capabilities: ['direct'],
    required_tools: [],
    dependencies: index === 0 ? [] : [`dag-${index}`],
    acceptance_criteria: [],
    risk_level: 'low',
    parallel_safe: false,
    context_query: `context-${index + 1}`,
    approval_required: false,
  }))
  const replanned = await request.post(`${API_BASE}/goals/${goalId}/replan`, {
    data: {
      trigger: 'user_change',
      reason: 'Playwright long DAG layout fixture',
      plan: {
        plan_id: state.active_plan.plan_id,
        task_mode: 'sequential_multi_agent',
        goal_summary: 'Validate a long dependency graph in the real Workspace UI.',
        assumptions: [],
        required_context: [],
        activation_reason: 'Large DAG visual QA',
        tasks,
        final_acceptance_criteria: [],
        human_approval_points: [],
        estimated_cost: {},
      },
    },
  })
  expect(replanned.ok()).toBeTruthy()

  await page.goto(`/workspace/runs/${runId}`)
  await expect(page.getByText('100 active tasks')).toBeVisible()
  await expect(page.getByText(/100 个 Task/)).toBeAttached()
  await expect(page.getByText('Long DAG task 100 with enough text to verify wrapping and overflow behavior', { exact: true }).first()).toBeVisible()
  await page.getByRole('button', { name: 'Pixel Office' }).click()
  await expect(page.getByRole('region', { name: 'Pixel Office' })).toBeVisible()
  await page.getByRole('button', { name: 'Card Flow' }).click()
  await expect(page.getByText('100 active tasks')).toBeVisible()
  await page.screenshot({ path: testInfo.outputPath('long-dag.png'), fullPage: true })
})

test('unified navigation preserves run context and controls planning lifecycle', async ({ page, request }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-1440', 'Run the navigation lifecycle once at the primary desktop viewport.')
  const { goalId, runId } = await createStartedGoal(request, `Workspace navigation ${Date.now()}`)

  await page.goto(`/workspace/runs/${runId}`)
  await expect(page.getByRole('navigation', { name: 'Primary navigation' })).toBeVisible()
  await expect(page.getByRole('region', { name: 'Workspace run header' })).toContainText(runId.slice(0, 12))

  await page.getByRole('button', { name: 'Pixel Office' }).click()
  await page.reload()
  await expect(page.getByRole('region', { name: 'Pixel Office' })).toBeVisible()

  const primaryNav = page.getByRole('navigation', { name: 'Primary navigation' })
  await primaryNav.getByRole('link', { name: 'Workspace' }).click()
  await expect(page).toHaveURL(/\/workspace$/)
  await expect(page.getByRole('link', { name: /进入 Workspace/ }).first()).toBeVisible()
  const stillPlanning = await request.get(`${API_BASE}/runtime/status/${goalId}`)
  expect((await stillPlanning.json()).data.goal_status).toBe('planning')
  await page.goBack()
  await expect(page).toHaveURL(new RegExp(`/workspace/runs/${runId}`))

  await page.getByRole('link', { name: 'Logs' }).first().click()
  await expect(page).toHaveURL(new RegExp(`/logs\\?runId=${runId}`))
  await page.getByRole('link', { name: '返回当前 Workspace' }).click()
  await page.getByRole('link', { name: 'Evolution' }).first().click()
  await expect(page).toHaveURL(new RegExp(`/evolution\\?runId=${runId}&goalId=${goalId}`))
  await page.getByRole('link', { name: '返回当前 Workspace' }).click()
  await page.getByRole('link', { name: 'Assets' }).first().click()
  await expect(page).toHaveURL(new RegExp(`/assets\\?runId=${runId}`))
  await page.getByRole('link', { name: '返回当前 Workspace' }).click()

  await page.getByRole('button', { name: 'Pause' }).click()
  await expect.poll(async () => (await (await request.get(`${API_BASE}/runtime/status/${goalId}`)).json()).data.goal_status).toBe('paused')
  await page.getByRole('button', { name: 'Resume' }).click()
  await expect.poll(async () => (await (await request.get(`${API_BASE}/runtime/status/${goalId}`)).json()).data.goal_status).toBe('planning')

  page.once('dialog', (dialog) => dialog.accept())
  await page.getByRole('button', { name: 'Stop' }).click()
  await expect.poll(async () => (await (await request.get(`${API_BASE}/runtime/status/${goalId}`)).json()).data.goal_status).toBe('cancelled')

  await page.goto('/workspace/runs/not-a-real-run')
  await expect(page.getByRole('heading', { name: '无法打开这个 Run' })).toBeVisible()
  await expect(page.getByRole('link', { name: '返回 Workspace' })).toBeVisible()
  await page.screenshot({ path: testInfo.outputPath('run-not-found.png'), fullPage: true })
})
