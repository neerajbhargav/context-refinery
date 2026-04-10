<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import { useRefineryAPI } from '@/composables/useRefineryAPI'
import { onMounted, ref } from 'vue'

const router = useRouter()
const settingsStore = useSettingsStore()
const { healthCheck } = useRefineryAPI()
const checking = ref(false)

async function retryConnection() {
  checking.value = true
  await healthCheck()
  checking.value = false
}

onMounted(async () => {
  await healthCheck()
  setInterval(() => healthCheck(), 15000)
})
</script>

<template>
  <header class="h-14 flex items-center justify-between px-5 bg-cr-surface border-b border-cr-border select-none" data-tauri-drag-region>
    <!-- Left: Logo -->
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 rounded-xl bg-accent-600 flex items-center justify-center">
        <svg class="w-4.5 h-4.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z" />
          <path d="M12 12l8-4.5" />
          <path d="M12 12v9" />
        </svg>
      </div>
      <div>
        <h1 class="text-sm font-semibold text-cr-text">Context<span class="text-accent-500">Refinery</span></h1>
        <p class="text-[10px] text-cr-text-dim font-medium">Context Orchestration Engine</p>
      </div>
    </div>

    <!-- Right: Controls -->
    <div class="flex items-center gap-2">
      <!-- Connection Status -->
      <div class="flex items-center gap-2 px-3 py-1.5 rounded-full" :class="settingsStore.sidecarConnected ? 'bg-emerald-500/10' : 'bg-red-500/10'">
        <div
          class="w-2 h-2 rounded-full"
          :class="settingsStore.sidecarConnected ? 'bg-emerald-500' : 'bg-red-500'"
        ></div>
        <span class="text-xs font-medium" :class="settingsStore.sidecarConnected ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'">
          {{ settingsStore.sidecarConnected ? 'Connected' : 'Offline' }}
        </span>
        <button
          v-if="!settingsStore.sidecarConnected"
          @click="retryConnection"
          class="btn-icon !p-1"
          :class="{ 'animate-spin': checking }"
          title="Retry Connection"
        >
          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M23 4v6h-6"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
        </button>
      </div>

      <div class="w-px h-5 bg-cr-border mx-1" />

      <!-- Theme Toggle -->
      <button
        @click="settingsStore.toggleTheme()"
        class="btn-icon"
        :title="`Switch to ${settingsStore.theme === 'dark' ? 'Light' : 'Dark'} Mode`"
      >
        <svg v-if="settingsStore.theme === 'dark'" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
        <svg v-else class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>
      </button>

      <!-- Settings -->
      <button
        class="btn-icon"
        @click="router.push('/settings')"
        title="Settings"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
      </button>
    </div>
  </header>
</template>
