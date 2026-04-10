import { useSettingsStore } from '@/stores/settings'

/**
 * Composable for non-streaming API calls to the FastAPI sidecar.
 */
export function useRefineryAPI() {
  const settingsStore = useSettingsStore()

  async function healthCheck(): Promise<boolean> {
    try {
      const res = await fetch(`${settingsStore.apiUrl}/api/health`)
      const data = await res.json()
      settingsStore.setSidecarConnected(data.status === 'ok')
      return data.status === 'ok'
    } catch {
      settingsStore.setSidecarConnected(false)
      return false
    }
  }

  async function indexProject(projectName: string, folderPath: string) {
    const res = await fetch(`${settingsStore.apiUrl}/api/workbench/index`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_name: projectName,
        folder_path: folderPath,
      }),
    })
    if (!res.ok) throw new Error(`Indexing failed: ${res.statusText}`)
    return res.json()
  }

  async function countTokens(text: string, model: string = 'gpt-4o') {
    const res = await fetch(`${settingsStore.apiUrl}/api/workbench/count-tokens`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, model }),
    })
    if (!res.ok) throw new Error(`Token count failed: ${res.statusText}`)
    return res.json()
  }

  async function getSettings() {
    const res = await fetch(`${settingsStore.apiUrl}/api/settings`)
    return res.json()
  }

  // ── Model Management ─────────────────────────────────────────────

  async function fetchLocalModels() {
    const res = await fetch(`${settingsStore.apiUrl}/api/models/ollama/tags`)
    const data = await res.json()
    if (data.status === 'online') {
      settingsStore.setLocalModels(data.models)
    }
    return data
  }

  async function pullModel(modelName: string) {
    const res = await fetch(`${settingsStore.apiUrl}/api/models/ollama/pull`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model_name: modelName }),
    })
    if (!res.ok) throw new Error(`Pull failed: ${res.statusText}`)
    return res.body // Returns stream
  }

  async function deleteModel(modelName: string) {
    const res = await fetch(`${settingsStore.apiUrl}/api/models/ollama/${modelName}`, {
      method: 'DELETE',
    })
    if (!res.ok) throw new Error(`Delete failed: ${res.statusText}`)
    return res.json()
  }

  return {
    healthCheck,
    indexProject,
    countTokens,
    getSettings,
    fetchLocalModels,
    pullModel,
    deleteModel,
  }
}
