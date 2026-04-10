import { ref, onUnmounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useRefineryStore } from '@/stores/refinery'

/**
 * Composable for Server-Sent Events (SSE) connection to the FastAPI sidecar.
 * Parses streaming events from the refinery pipeline and updates the store.
 */
export function useSSE() {
  const settingsStore = useSettingsStore()
  const refineryStore = useRefineryStore()
  const eventSource = ref<EventSource | null>(null)
  const isConnected = ref(false)

  function connect(endpoint: string, body: Record<string, any>) {
    // SSE via fetch + ReadableStream (POST not supported by EventSource)
    const url = `${settingsStore.apiUrl}${endpoint}`

    refineryStore.startRefining()

    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
      .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        if (!response.body) throw new Error('No response body')

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        isConnected.value = true

        function pump(): Promise<void> {
          return reader.read().then(({ done, value }) => {
            if (done) {
              isConnected.value = false
              refineryStore.finishRefining()
              return
            }

            const text = decoder.decode(value, { stream: true })
            const lines = text.split('\n')

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const event = JSON.parse(line.slice(6))
                  handleEvent(event)
                } catch (e) {
                  console.warn('Failed to parse SSE event:', line)
                }
              }
            }

            return pump()
          })
        }

        return pump()
      })
      .catch(err => {
        console.error('SSE connection error:', err)
        refineryStore.setError(err.message)
        isConnected.value = false
      })
  }

  function handleEvent(event: any) {
    const { event_type, data, timestamp } = event

    switch (event_type) {
      case 'agent_message':
        refineryStore.addMessage({
          stepType: data.step_type,
          agentName: data.agent_name,
          content: data.content,
          timestamp: timestamp,
          metadata: data.metadata,
        })
        break

      case 'progress':
        refineryStore.setStep(data.step || data.message)
        break

      case 'result':
        refineryStore.setResult(
          data.refined_prompt,
          data.token_count,
          data.iteration
        )
        break

      case 'eval':
        refineryStore.setEvalScores({
          contextGrounding: data.context_grounding,
          budgetUtilization: data.budget_utilization,
          informationDensity: data.information_density,
          overallScore: data.overall_score,
          passed: data.passed,
        })
        break

      case 'error':
        refineryStore.setError(data.error)
        break

      case 'done':
        refineryStore.finishRefining()
        isConnected.value = false
        break
    }
  }

  function disconnect() {
    if (eventSource.value) {
      eventSource.value.close()
      eventSource.value = null
    }
    isConnected.value = false
  }

  onUnmounted(() => disconnect())

  return {
    connect,
    disconnect,
    isConnected,
  }
}
