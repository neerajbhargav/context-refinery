<script setup lang="ts">
import { useRefineryStore } from '@/stores/refinery'
import { useWorkbenchStore } from '@/stores/workbench'
import { ref, computed } from 'vue'

const refinery = useRefineryStore()
const workbench = useWorkbenchStore()
const copied = ref(false)
const selectedFormat = ref<'markdown' | 'xml' | 'json'>('markdown')

const utilizationPct = computed(() => {
  if (workbench.tokenBudget === 0) return 0
  return Math.round((refinery.promptTokenCount / workbench.tokenBudget) * 100)
})

const formattedPrompt = computed(() => {
  const prompt = refinery.refinedPrompt
  if (selectedFormat.value === 'xml') {
    return `<prompt>\n  <goal>${workbench.goal}</goal>\n  <content>\n${prompt}\n  </content>\n</prompt>`
  }
  if (selectedFormat.value === 'json') {
    return JSON.stringify({
      goal: workbench.goal,
      prompt: prompt,
      metrics: {
        tokens: refinery.promptTokenCount,
        budget: workbench.tokenBudget,
        model: workbench.targetModel
      }
    }, null, 2)
  }
  return prompt
})

async function copyToClipboard() {
  try {
    await navigator.clipboard.writeText(formattedPrompt.value)
    copied.value = true
    setTimeout(() => copied.value = false, 2000)
  } catch (err) {
    console.error('Copy failed:', err)
  }
}
</script>

<template>
  <div class="flex flex-col h-full overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between px-5 py-3 border-b border-cr-border">
      <div class="flex items-center gap-4">
        <span class="text-xs font-semibold text-cr-text">Refined Output</span>

        <div v-if="refinery.hasResult" class="flex p-0.5 bg-cr-surface-variant rounded-full">
          <button
            v-for="fmt in ['markdown', 'xml', 'json']"
            :key="fmt"
            @click="selectedFormat = fmt as any"
            class="px-3 py-1 text-[10px] font-semibold rounded-full transition-all"
            :class="selectedFormat === fmt ? 'bg-accent-600 text-white shadow-sm' : 'text-cr-text-dim hover:text-cr-text'"
          >
            {{ fmt.toUpperCase() }}
          </button>
        </div>
      </div>

      <div class="flex items-center gap-4" v-if="refinery.hasResult">
        <div class="flex flex-col items-end gap-1 min-w-[100px]">
          <span class="text-[11px] font-mono font-semibold" :class="utilizationPct > 100 ? 'text-red-500' : 'text-cr-text'">
            {{ refinery.promptTokenCount.toLocaleString() }}
            <span class="text-cr-text-dim text-[9px] ml-0.5">/ {{ workbench.tokenBudget.toLocaleString() }}</span>
          </span>
          <div class="w-full h-1 bg-cr-surface-variant rounded-full overflow-hidden">
            <div
              class="h-full transition-all duration-500 rounded-full"
              :class="utilizationPct > 100 ? 'bg-red-500' : 'bg-accent-500'"
              :style="{ width: `${Math.min(utilizationPct, 100)}%` }"
            ></div>
          </div>
        </div>

        <button
          class="btn-primary !px-5 !py-2 !text-xs flex items-center gap-1.5"
          @click="copyToClipboard"
          :aria-label="copied ? 'Copied!' : 'Copy to clipboard'"
        >
          <svg v-if="!copied" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
          </svg>
          <svg v-else class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          {{ copied ? 'Copied!' : 'Copy' }}
        </button>
      </div>
    </div>

    <!-- Body -->
    <div class="flex-1 overflow-hidden relative">
      <div
        v-if="!refinery.hasResult && !refinery.isRunning"
        class="flex flex-col items-center justify-center h-full text-cr-text-dim text-center px-10"
      >
        <svg class="w-16 h-16 mb-4 opacity-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
        <p class="text-xs text-cr-text-dim">Waiting for synthesis</p>
      </div>

      <div v-else-if="!refinery.hasResult && refinery.isRunning" class="p-6 space-y-4">
        <div class="h-4 rounded-lg shimmer" v-for="n in 10" :key="n" :style="{ width: `${40 + Math.random() * 50}%` }" />
      </div>

      <div v-else class="h-full p-5 overflow-auto">
        <pre class="code-block w-full whitespace-pre-wrap text-sm leading-relaxed">{{ formattedPrompt }}</pre>

        <div v-if="copied" class="absolute inset-0 pointer-events-none flex items-center justify-center bg-cr-bg/50 animate-fade-in">
          <div class="bg-accent-600 text-white px-6 py-2.5 rounded-full font-semibold text-sm shadow-lg">
            Copied to clipboard
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
