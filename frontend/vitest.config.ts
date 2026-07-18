import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    exclude: ['e2e/**', 'node_modules/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      include: [
        'src/components/FinalOutputPanel.tsx',
        'src/components/PlanOverviewPanel.tsx',
        'src/components/TaskCard.tsx',
        'src/components/TaskDetailPanel.tsx',
        'src/utils/workspaceViewModel.ts',
      ],
      thresholds: {
        lines: 80,
        functions: 75,
        statements: 75,
        branches: 60,
      },
    },
  },
})
