<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import { useRefineryAPI } from '@/composables/useRefineryAPI'
import { onMounted, ref } from 'vue'

const router = useRouter()
const settingsStore = useSettingsStore()
const { fetchLocalModels, pullModel, deleteModel } = useRefineryAPI()

const newModelName = ref('')
const isPulling = ref(false)
const pullStatus = ref('')
const pullProgress = ref(0)
const loading = ref(false)

async function refreshModels() {
  loading.value = true
  await fetchLocalModels()
  loading.value = false
}

async function handlePullModel() {
  if (!newModelName.value.trim()) return

  isPulling.value = true
  pullStatus.value = 'Initializing...'
  pullProgress.value = 0

  try {
    const stream = await pullModel(newModelName.value.trim())
    if (!stream) throw new Error('Failed to start stream')

    const reader = stream.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const text = decoder.decode(value)
      const lines = text.split('\n')

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const event = JSON.parse(line.slice(6))
          if (event.event_type === 'progress') {
            const { status, completed, total } = event.data
            pullStatus.value = status
            if (total) pullProgress.value = Math.round((completed / total) * 100)
          } else if (event.event_type === 'done') {
            pullStatus.value = 'Complete!'
            pullProgress.value = 100
          } else if (event.event_type === 'error') {
            throw new Error(event.data.error)
          }
        } catch (e) {
          // skip malformed lines
        }
      }
    }

    await refreshModels()
    newModelName.value = ''
  } catch (err: any) {
    pullStatus.value = `Error: ${err.message}`
  } finally {
    setTimeout(() => {
      isPulling.value = false
      pullStatus.value = ''
      pullProgress.value = 0
    }, 3000)
  }
}

async function handleDelete(name: string) {
  if (!confirm(`Delete model "${name}"?`)) return
  try {
    await deleteModel(name)
    await refreshModels()
  } catch (err: any) {
    alert(`Failed to delete: ${err.message}`)
  }
}

function formatSize(bytes: number) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

onMounted(() => {
  refreshModels()
})
</script>

<template>
  <div class="h-full flex flex-col items-center p-4 overflow-y-auto">
    <div class="w-full max-w-2xl space-y-4 pb-10">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-semibold text-cr-text">Settings</h2>
          <p class="text-sm text-cr-text-dim">Configure your intelligence providers and environment.</p>
        </div>
        <button class="btn-secondary flex items-center gap-2" @click="router.push('/')">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
          Back
        </button>
      </div>

      <!-- Connection Config -->
      <section class="surface-card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-cr-text flex items-center gap-2">
          <svg class="w-4 h-4 text-cr-text-dim" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" /></svg>
          API Configuration
        </h3>

        <div class="space-y-3">
          <div>
            <label class="text-xs font-medium text-cr-text-dim mb-1 block">Sidecar API URL</label>
            <input
              type="text"
              :value="settingsStore.apiUrl"
              @input="settingsStore.setApiUrl(($event.target as HTMLInputElement).value)"
              class="input-field"
              placeholder="http://127.0.0.1:8741"
            />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div class="glass-surface p-4">
            <div class="flex items-center gap-2 mb-2">
              <span class="text-base">🌐</span>
              <span class="text-sm font-medium text-cr-text">Cloud Models</span>
            </div>
            <p class="text-xs text-cr-text-dim mb-3">Gemini, GPT-4o, Claude via API keys.</p>
            <div class="flex flex-wrap gap-1.5">
              <span class="badge-success">Gemini</span>
              <span class="badge text-cr-text-dim bg-cr-surface-variant">Claude</span>
              <span class="badge text-cr-text-dim bg-cr-surface-variant">GPT-4o</span>
            </div>
          </div>
          <div class="glass-surface p-4">
            <div class="flex items-center gap-2 mb-2">
              <span class="text-base">��</span>
              <span class="text-sm font-medium text-cr-text">Local Models</span>
            </div>
            <p class="text-xs text-cr-text-dim mb-3">Private inference via Ollama.</p>
            <div class="flex items-center gap-1.5">
              <div class="w-2 h-2 rounded-full bg-emerald-500"></div>
              <span class="text-[10px] font-medium text-emerald-600 dark:text-emerald-400">Service Active</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Model Manager -->
      <section class="surface-card p-5 space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-semibold text-cr-text flex items-center gap-2">
            <svg class="w-4 h-4 text-cr-text-dim" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
              <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
              <line x1="12" y1="22.08" x2="12" y2="12" />
            </svg>
            Ollama Model Manager
          </h3>
          <button class="btn-icon" @click="refreshModels" :disabled="loading" aria-label="Refresh">
            <svg class="w-4 h-4" :class="loading ? 'animate-spin' : ''" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 2v6h-6" /><path d="M3 12a9 9 0 0 1 15-6.7L21 8" />
              <path d="M3 22v-6h6" /><path d="M21 12a9 9 0 0 1-15 6.7L3 16" />
            </svg>
          </button>
        </div>

        <!-- Pull Model -->
        <div class="space-y-2">
          <div class="flex gap-2">
            <input
              v-model="newModelName"
              type="text"
              placeholder="Model name (e.g. llama3, mistral, gemma3)"
              class="input-field flex-1"
              @keyup.enter="handlePullModel"
              :disabled="isPulling"
            />
            <button class="btn-primary" :disabled="!newModelName.trim() || isPulling" @click="handlePullModel">
              {{ isPulling ? 'Downloading...' : 'Pull' }}
            </button>
          </div>

          <div v-if="isPulling" class="space-y-1 animate-fade-in">
            <div class="flex items-center justify-between text-xs">
              <span class="text-accent-500 font-medium">{{ pullStatus }}</span>
              <span class="text-cr-text-dim">{{ pullProgress }}%</span>
            </div>
            <div class="h-1.5 bg-cr-surface-variant rounded-full overflow-hidden">
              <div
                class="h-full bg-accent-500 transition-all duration-300 rounded-full"
                :style="{ width: `${pullProgress}%` }"
              />
            </div>
          </div>
        </div>

        <!-- Installed Models -->
        <div class="space-y-2">
          <label class="text-xs font-medium text-cr-text-dim">Installed Models</label>
          <div v-if="settingsStore.localModels.length === 0" class="text-center py-6 glass-surface border-dashed">
            <p class="text-xs text-cr-text-dim">No models found. Pull one above to get started.</p>
          </div>
          <div v-else class="space-y-1.5">
            <div
              v-for="model in settingsStore.localModels"
              :key="model.name"
              class="glass-surface p-3 flex items-center justify-between group hover:border-cr-outline transition-colors"
            >
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-accent-500/10 flex items-center justify-center text-sm">🤖</div>
                <div>
                  <div class="text-sm font-medium text-cr-text">{{ model.name }}</div>
                  <div class="text-[10px] text-cr-text-dim flex gap-2">
                    <span>{{ formatSize(model.size) }}</span>
                    <span v-if="model.details?.parameter_size">{{ model.details.parameter_size }} params</span>
                  </div>
                </div>
              </div>
              <button
                class="opacity-0 group-hover:opacity-100 btn-icon !p-1.5 hover:text-red-500 transition-all"
                @click="handleDelete(model.name)"
                aria-label="Delete model"
              >
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 6h18" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Advanced -->
      <section class="surface-card p-5 space-y-4">
        <h3 class="text-sm font-semibold text-cr-text flex items-center gap-2">
          <svg class="w-4 h-4 text-cr-text-dim" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
          Advanced
        </h3>
        <div class="space-y-3">
          <div class="flex items-center justify-between py-2">
            <div>
              <div class="text-sm font-medium text-cr-text">Cross-Encoder Reranking</div>
              <div class="text-xs text-cr-text-dim">Improves retrieval precision, uses more CPU.</div>
            </div>
            <span class="badge-success">Enabled</span>
          </div>
          <div class="border-t border-cr-border"></div>
          <div class="flex items-center justify-between py-2">
            <div>
              <div class="text-sm font-medium text-cr-text">Local Embeddings Path</div>
              <div class="text-xs text-cr-text-dim font-mono">~/.context-refinery/models</div>
            </div>
          </div>
          <div class="border-t border-cr-border"></div>
          <div class="flex items-center justify-between py-2">
            <div>
              <div class="text-sm font-medium text-cr-text">Theme</div>
              <div class="text-xs text-cr-text-dim">Switch between light and dark mode.</div>
            </div>
            <button class="btn-secondary !px-4 !py-2 !text-xs" @click="settingsStore.toggleTheme()">
              {{ settingsStore.theme === 'dark' ? 'Switch to Light' : 'Switch to Dark' }}
            </button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
