import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'workbench',
      component: () => import('@/views/WorkbenchView.vue'),
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue'),
    },
    {
      path: '/setup',
      name: 'setup',
      component: () => import('@/views/SetupView.vue'),
    },
  ],
})

// Redirect to setup on first run
let setupChecked = false
router.beforeEach(async (to) => {
  if (to.name === 'setup' || setupChecked) return
  try {
    const res = await fetch('http://127.0.0.1:8741/api/setup/status')
    const data = await res.json()
    setupChecked = true
    if (!data.setup_complete) return { name: 'setup' }
  } catch {
    // Backend not available — skip guard, app will show connection error
    setupChecked = true
  }
})

export default router
