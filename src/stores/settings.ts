import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  const apiUrl = ref('http://127.0.0.1:8741')
  const llmProvider = ref('google')
  const sidecarConnected = ref(false)
  const localModels = ref<any[]>([]) 
  const theme = ref<'light' | 'dark'>(localStorage.getItem('cr-theme') as any || 'dark')

  function toggleTheme() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    localStorage.setItem('cr-theme', theme.value)
    document.documentElement.className = theme.value
  }

  function setApiUrl(url: string) {
    apiUrl.value = url
  }

  function setSidecarConnected(connected: boolean) {
    sidecarConnected.value = connected
  }

  function setLocalModels(models: any[]) {
    localModels.value = models
  }

  return {
    apiUrl,
    llmProvider,
    sidecarConnected,
    localModels,
    theme,
    toggleTheme,
    setApiUrl,
    setSidecarConnected,
    setLocalModels,
  }
})
