import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface AgentMessage {
  stepType: string
  agentName: string
  content: string
  timestamp: number
  metadata?: Record<string, any>
}

export interface EvalScores {
  contextGrounding: number
  budgetUtilization: number
  informationDensity: number
  overallScore: number
  passed: boolean
}

export const useRefineryStore = defineStore('refinery', () => {
  // State
  const isRunning = ref(false)
  const messages = ref<AgentMessage[]>([])
  const refinedPrompt = ref('')
  const promptTokenCount = ref(0)
  const evalScores = ref<EvalScores | null>(null)
  const currentStep = ref('')
  const iteration = ref(0)
  const error = ref<string | null>(null)

  // Getters
  const hasResult = computed(() => refinedPrompt.value.length > 0)
  const isPassed = computed(() => evalScores.value?.passed ?? false)
  const latestMessage = computed(() =>
    messages.value.length > 0 ? messages.value[messages.value.length - 1] : null
  )

  // Actions
  function startRefining() {
    isRunning.value = true
    messages.value = []
    refinedPrompt.value = ''
    promptTokenCount.value = 0
    evalScores.value = null
    currentStep.value = 'starting'
    iteration.value = 0
    error.value = null
  }

  function addMessage(msg: AgentMessage) {
    messages.value.push(msg)
  }

  function setResult(prompt: string, tokenCount: number, iter: number) {
    refinedPrompt.value = prompt
    promptTokenCount.value = tokenCount
    iteration.value = iter
  }

  function setEvalScores(scores: EvalScores) {
    evalScores.value = scores
  }

  function setStep(step: string) {
    currentStep.value = step
  }

  function setError(err: string) {
    error.value = err
    isRunning.value = false
  }

  function finishRefining() {
    isRunning.value = false
    currentStep.value = 'complete'
  }

  function reset() {
    isRunning.value = false
    messages.value = []
    refinedPrompt.value = ''
    promptTokenCount.value = 0
    evalScores.value = null
    currentStep.value = ''
    iteration.value = 0
    error.value = null
  }

  return {
    // State
    isRunning,
    messages,
    refinedPrompt,
    promptTokenCount,
    evalScores,
    currentStep,
    iteration,
    error,
    // Getters
    hasResult,
    isPassed,
    latestMessage,
    // Actions
    startRefining,
    addMessage,
    setResult,
    setEvalScores,
    setStep,
    setError,
    finishRefining,
    reset,
  }
})
