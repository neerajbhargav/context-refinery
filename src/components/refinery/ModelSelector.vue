<script setup lang="ts">
import { useWorkbenchStore } from '@/stores/workbench'
import { useSettingsStore } from '@/stores/settings'
import { useRefineryAPI } from '@/composables/useRefineryAPI'
import { onMounted } from 'vue'

const workbench = useWorkbenchStore()
const settingsStore = useSettingsStore()
const { fetchLocalModels } = useRefineryAPI()

const staticModels = [
  { value: 'gemini-pro', label: 'Gemini Pro', provider: 'google' },
  { value: 'gemini-flash', label: 'Gemini Flash', provider: 'google' },
  { value: 'gpt-4o', label: 'GPT-4o', provider: 'openai' },
  { value: 'claude-sonnet', label: 'Claude Sonnet', provider: 'anthropic' },
]

onMounted(() => {
  fetchLocalModels()
})
</script>

<template>
  <div class="flex flex-col gap-2">
    <label class="text-xs font-semibold text-cr-text" for="model-select">
      Target Model
    </label>
    <div class="relative">
      <select
        id="model-select"
        :value="workbench.targetModel"
        @change="workbench.setTargetModel(($event.target as HTMLSelectElement).value)"
        class="input-field pr-10 cursor-pointer appearance-none"
        aria-label="Select target model"
      >
        <optgroup label="Cloud Models">
          <option v-for="model in staticModels" :key="model.value" :value="model.value">
            {{ model.label }}
          </option>
        </optgroup>

        <optgroup v-if="settingsStore.localModels.length > 0" label="Local Models (Ollama)">
          <option v-for="model in settingsStore.localModels" :key="model.name" :value="`ollama:${model.name}`">
            {{ model.name }}
          </option>
        </optgroup>
      </select>

      <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
        <svg class="w-4 h-4 text-cr-text-dim" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
      </div>
    </div>
  </div>
</template>
