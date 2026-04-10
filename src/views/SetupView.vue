<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'

const router = useRouter()
const settings = useSettingsStore()

const step = ref(0)
const loading = ref(false)
const error = ref('')

// Detection state
const ollamaRunning = ref(false)
const ollamaModels = ref<string[]>([])

// User choices
const provider = ref('ollama')
const apiKey = ref('')
const selectedOllamaModel = ref('')
const pullingModel = ref(false)
const pullProgress = ref('')
const newModelName = ref('gemma3')

const connectionTested = ref(false)
const connectionOk = ref(false)
const connectionMessage = ref('')

const steps = ['Welcome', 'Choose Provider', 'Configure', 'Test & Finish']

const providerOptions = [
  { id: 'ollama', name: 'Ollama (Local)', desc: 'Fully private. Runs on your machine. No API key needed.', icon: '🏠', recommended: true },
  { id: 'google', name: 'Google Gemini', desc: 'Powerful cloud models. Requires a Google API key.', icon: '🌐' },
  { id: 'openai', name: 'OpenAI GPT-4o', desc: 'Industry standard. Requires an OpenAI API key.', icon: '🤖' },
  { id: 'anthropic', name: 'Anthropic Claude', desc: 'Safety-focused. Requires an Anthropic API key.', icon: '🧠' },
]

const needsApiKey = computed(() => ['google', 'openai', 'anthropic'].includes(provider.value))

onMounted(async () => {
  try {
    const res = await fetch(`${settings.apiUrl}/api/setup/status`)
    const data = await res.json()
    if (data.setup_complete) {
      router.replace('/')
      return
    }
    ollamaRunning.value = data.ollama_running
    ollamaModels.value = data.ollama_models || []
    if (ollamaModels.value.length > 0) {
      selectedOllamaModel.value = ollamaModels.value[0]
    }
  } catch {
    // Backend not ready yet, stay on setup
  }
})

function next() {
  error.value = ''
  if (step.value < steps.length - 1) step.value++
}
function back() {
  error.value = ''
  connectionTested.value = false
  if (step.value > 0) step.value--
}

async function testConnection() {
  loading.value = true
  error.value = ''
  connectionTested.value = false
  try {
    const body: any = { provider: provider.value }
    if (needsApiKey.value) body.api_key = apiKey.value
    if (provider.value === 'ollama') body.ollama_model = selectedOllamaModel.value

    const res = await fetch(`${settings.apiUrl}/api/setup/test-connection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await res.json()
    connectionTested.value = true
    connectionOk.value = data.success
    connectionMessage.value = data.message || data.error
  } catch (e: any) {
    connectionTested.value = true
    connectionOk.value = false
    connectionMessage.value = 'Cannot reach backend. Is it running?'
  } finally {
    loading.value = false
  }
}

async function pullModel() {
  pullingModel.value = true
  pullProgress.value = 'Starting download...'
  try {
    const res = await fetch(`${settings.apiUrl}/api/models/ollama/pull`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model_name: newModelName.value }),
    })
    const reader = res.body?.getReader()
    const decoder = new TextDecoder()
    if (!reader) return

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const text = decoder.decode(value, { stream: true })
      for (const line of text.split('\n')) {
        if (!line.startsWith('data: ')) continue
        try {
          const event = JSON.parse(line.slice(6))
          if (event.event_type === 'progress') {
            const d = event.data
            if (d.total && d.completed) {
              const pct = Math.round((d.completed / d.total) * 100)
              pullProgress.value = `${d.status}: ${pct}%`
            } else {
              pullProgress.value = d.status || 'Downloading...'
            }
          } else if (event.event_type === 'done') {
            pullProgress.value = 'Download complete!'
            selectedOllamaModel.value = newModelName.value
            ollamaModels.value.push(newModelName.value)
          } else if (event.event_type === 'error') {
            pullProgress.value = `Error: ${event.data.error}`
          }
        } catch { /* skip */ }
      }
    }
  } catch (e: any) {
    pullProgress.value = `Error: ${e.message}`
  } finally {
    pullingModel.value = false
  }
}

async function finishSetup() {
  loading.value = true
  error.value = ''
  try {
    const body: any = {
      provider: provider.value,
      embedding_provider: provider.value === 'ollama' ? 'sentence-transformers' : provider.value === 'google' ? 'google' : 'sentence-transformers',
    }
    if (needsApiKey.value) body.api_key = apiKey.value
    if (provider.value === 'ollama') body.ollama_model = selectedOllamaModel.value

    const res = await fetch(`${settings.apiUrl}/api/setup/save-config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await res.json()
    if (data.success) {
      settings.llmProvider = provider.value
      router.replace('/')
    } else {
      error.value = data.error || 'Failed to save configuration'
    }
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="h-full flex items-center justify-center p-8 overflow-auto">
    <div class="w-full max-w-2xl">
      <!-- Progress indicator -->
      <div class="flex items-center justify-center gap-2 mb-10">
        <template v-for="(_s, i) in steps" :key="i">
          <div
            class="flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold transition-all duration-300"
            :class="i <= step ? 'bg-accent-600 text-white' : 'bg-cr-surface-variant text-cr-text-dim'"
          >{{ i + 1 }}</div>
          <div v-if="i < steps.length - 1" class="w-12 h-0.5 transition-all duration-300"
               :class="i < step ? 'bg-accent-600' : 'bg-cr-surface-variant'" />
        </template>
      </div>

      <!-- Step 0: Welcome -->
      <div v-if="step === 0" class="text-center space-y-6 animate-fade-in">
        <div class="text-6xl mb-2">&#x1f48e;</div>
        <h1 class="text-3xl font-bold text-cr-text">Welcome to ContextRefinery</h1>
        <p class="text-cr-text-dim text-lg max-w-md mx-auto leading-relaxed">
          Transform your codebase into LLM-optimized prompts.
          Let's get you set up in under a minute.
        </p>
        <button @click="next" class="btn-primary text-base px-10 py-4 mt-4">
          Get Started
        </button>
      </div>

      <!-- Step 1: Choose Provider -->
      <div v-else-if="step === 1" class="space-y-6 animate-fade-in">
        <div class="text-center mb-2">
          <h2 class="text-2xl font-bold text-cr-text">Choose Your AI Provider</h2>
          <p class="text-cr-text-dim mt-2">You can change this later in Settings.</p>
        </div>

        <div class="grid gap-3">
          <button
            v-for="opt in providerOptions" :key="opt.id"
            @click="provider = opt.id"
            class="surface-card p-5 text-left transition-all duration-200 cursor-pointer group"
            :class="provider === opt.id
              ? 'ring-2 ring-accent-500 border-accent-500'
              : 'hover:border-cr-outline'"
          >
            <div class="flex items-start gap-4">
              <span class="text-2xl mt-0.5">{{ opt.icon }}</span>
              <div class="flex-1">
                <div class="flex items-center gap-2">
                  <span class="font-semibold text-cr-text">{{ opt.name }}</span>
                  <span v-if="opt.recommended" class="badge-success text-[10px] px-2 py-0">RECOMMENDED</span>
                  <span v-if="opt.id === 'ollama' && ollamaRunning" class="badge-info text-[10px] px-2 py-0">DETECTED</span>
                </div>
                <p class="text-sm text-cr-text-dim mt-1">{{ opt.desc }}</p>
              </div>
              <div class="w-5 h-5 rounded-full border-2 flex items-center justify-center mt-1 transition-colors"
                   :class="provider === opt.id ? 'border-accent-500 bg-accent-500' : 'border-cr-outline'">
                <svg v-if="provider === opt.id" class="w-3 h-3 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
              </div>
            </div>
          </button>
        </div>

        <div class="flex justify-between pt-4">
          <button @click="back" class="btn-ghost">Back</button>
          <button @click="next" class="btn-primary">Continue</button>
        </div>
      </div>

      <!-- Step 2: Configure -->
      <div v-else-if="step === 2" class="space-y-6 animate-fade-in">
        <div class="text-center mb-2">
          <h2 class="text-2xl font-bold text-cr-text">Configure {{ providerOptions.find(o => o.id === provider)?.name }}</h2>
        </div>

        <!-- Ollama config -->
        <div v-if="provider === 'ollama'" class="space-y-5">
          <div v-if="!ollamaRunning" class="surface-card p-5 border-amber-500/50 space-y-3">
            <p class="text-amber-400 font-semibold">Ollama not detected</p>
            <p class="text-cr-text-dim text-sm">
              Install Ollama from <span class="text-accent-400 font-mono">ollama.com</span>, start it, then come back here.
            </p>
          </div>

          <div v-if="ollamaRunning && ollamaModels.length > 0" class="space-y-3">
            <label class="text-sm font-semibold text-cr-text">Select a model</label>
            <select v-model="selectedOllamaModel" class="input-field">
              <option v-for="m in ollamaModels" :key="m" :value="m">{{ m }}</option>
            </select>
          </div>

          <div v-if="ollamaRunning && ollamaModels.length === 0" class="surface-card p-5 space-y-3">
            <p class="text-cr-text-dim text-sm">No models found. Pull one to get started:</p>
          </div>

          <div v-if="ollamaRunning" class="surface-card p-5 space-y-3">
            <label class="text-sm font-semibold text-cr-text">Pull a new model</label>
            <div class="flex gap-2">
              <input v-model="newModelName" class="input-field flex-1" placeholder="e.g. gemma3, llama3.2, qwen3" />
              <button @click="pullModel" :disabled="pullingModel || !newModelName" class="btn-primary whitespace-nowrap">
                {{ pullingModel ? 'Pulling...' : 'Pull Model' }}
              </button>
            </div>
            <p v-if="pullProgress" class="text-sm text-cr-text-dim font-mono">{{ pullProgress }}</p>
          </div>
        </div>

        <!-- API key config -->
        <div v-if="needsApiKey" class="space-y-4">
          <div>
            <label class="text-sm font-semibold text-cr-text block mb-2">API Key</label>
            <input
              v-model="apiKey"
              type="password"
              class="input-field font-mono"
              :placeholder="provider === 'google' ? 'AIza...' : provider === 'openai' ? 'sk-...' : 'sk-ant-...'"
            />
          </div>
          <p class="text-xs text-cr-text-dim">
            Your key is stored locally in <span class="font-mono">src-backend/.env</span> and never sent anywhere except the provider's API.
          </p>
        </div>

        <p v-if="error" class="text-red-400 text-sm">{{ error }}</p>

        <div class="flex justify-between pt-4">
          <button @click="back" class="btn-ghost">Back</button>
          <button @click="next" class="btn-primary"
                  :disabled="(needsApiKey && !apiKey) || (provider === 'ollama' && !ollamaRunning)">
            Continue
          </button>
        </div>
      </div>

      <!-- Step 3: Test & Finish -->
      <div v-else-if="step === 3" class="space-y-6 animate-fade-in">
        <div class="text-center mb-2">
          <h2 class="text-2xl font-bold text-cr-text">Almost There</h2>
          <p class="text-cr-text-dim mt-2">Let's verify everything works.</p>
        </div>

        <div class="surface-card p-6 space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="font-semibold text-cr-text">{{ providerOptions.find(o => o.id === provider)?.name }}</p>
              <p class="text-sm text-cr-text-dim" v-if="provider === 'ollama'">Model: {{ selectedOllamaModel || 'default' }}</p>
            </div>
            <button @click="testConnection" :disabled="loading" class="btn-secondary">
              {{ loading ? 'Testing...' : 'Test Connection' }}
            </button>
          </div>

          <div v-if="connectionTested" class="flex items-center gap-2 p-3 rounded-xl"
               :class="connectionOk ? 'bg-emerald-500/10' : 'bg-red-500/10'">
            <span>{{ connectionOk ? '&#x2705;' : '&#x274c;' }}</span>
            <span class="text-sm" :class="connectionOk ? 'text-emerald-400' : 'text-red-400'">
              {{ connectionMessage }}
            </span>
          </div>
        </div>

        <p v-if="error" class="text-red-400 text-sm">{{ error }}</p>

        <div class="flex justify-between pt-4">
          <button @click="back" class="btn-ghost">Back</button>
          <button @click="finishSetup" :disabled="loading" class="btn-primary text-base px-8 py-3">
            {{ loading ? 'Saving...' : 'Launch ContextRefinery' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeSlideIn 0.3s var(--ease-emphasized) both;
}
@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
