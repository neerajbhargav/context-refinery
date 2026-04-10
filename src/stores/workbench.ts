import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface SourceFile {
  path: string
  filename: string
  language: string
  content: string
  tokenCount: number
  selected: boolean
}

export const useWorkbenchStore = defineStore('workbench', () => {
  // State
  const files = ref<SourceFile[]>([])
  const goal = ref('')
  const tokenBudget = ref(4096)
  const targetModel = ref<string>('gemini-pro')
  const projectName = ref('')
  const isIndexing = ref(false)

  // Getters
  const selectedFiles = computed(() => files.value.filter(f => f.selected))
  const totalTokens = computed(() => selectedFiles.value.reduce((sum, f) => sum + f.tokenCount, 0))
  const fileCount = computed(() => files.value.length)
  const isReady = computed(() => goal.value.trim().length >= 10 && selectedFiles.value.length > 0)

  // Actions
  function addFiles(newFiles: SourceFile[]) {
    for (const file of newFiles) {
      if (!files.value.find(f => f.path === file.path)) {
        files.value.push({ ...file, selected: true })
      }
    }
  }

  function removeFile(path: string) {
    files.value = files.value.filter(f => f.path !== path)
  }

  function toggleFile(path: string) {
    const file = files.value.find(f => f.path === path)
    if (file) file.selected = !file.selected
  }

  function selectAll() {
    files.value.forEach(f => f.selected = true)
  }

  function deselectAll() {
    files.value.forEach(f => f.selected = false)
  }

  function clearWorkbench() {
    files.value = []
    goal.value = ''
  }

  function setGoal(newGoal: string) {
    goal.value = newGoal
  }

  function setTokenBudget(budget: number) {
    tokenBudget.value = Math.max(512, Math.min(32768, budget))
  }

  function setTargetModel(model: string) {
    targetModel.value = model
  }

  return {
    // State
    files,
    goal,
    tokenBudget,
    targetModel,
    projectName,
    isIndexing,
    // Getters
    selectedFiles,
    totalTokens,
    fileCount,
    isReady,
    // Actions
    addFiles,
    removeFile,
    toggleFile,
    selectAll,
    deselectAll,
    clearWorkbench,
    setGoal,
    setTokenBudget,
    setTargetModel,
  }
})
