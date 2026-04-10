<script setup lang="ts">
import { useWorkbenchStore } from '@/stores/workbench'
import { useRefineryStore } from '@/stores/refinery'
import { useSettingsStore } from '@/stores/settings'
import { computed } from 'vue'

const workbench = useWorkbenchStore()
const refinery = useRefineryStore()
const settings = useSettingsStore()

const budgetDisplay = computed(() => {
  const count = refinery.promptTokenCount
  const budget = workbench.tokenBudget
  const pct = budget > 0 ? Math.round((count / budget) * 100) : 0
  return { count, budget, pct }
})
</script>

<template>
  <footer class="h-8 flex items-center justify-between px-5 bg-cr-surface border-t border-cr-border text-xs text-cr-text-dim select-none">
    <!-- Left -->
    <div class="flex items-center gap-4">
      <div class="flex items-center gap-1.5">
        <div class="w-1.5 h-1.5 rounded-full" :class="settings.sidecarConnected ? 'bg-emerald-500' : 'bg-cr-outline'"></div>
        <span class="font-medium">{{ settings.sidecarConnected ? 'Connected' : 'Offline' }}</span>
      </div>
      <span class="text-cr-outline">|</span>
      <span><span class="text-cr-text font-medium">{{ workbench.fileCount }}</span> files</span>
      <span><span class="text-cr-text font-medium">{{ workbench.selectedFiles.length }}</span> selected</span>
      <span class="font-mono text-accent-500 font-medium">{{ workbench.totalTokens.toLocaleString() }} tokens</span>
    </div>

    <!-- Center: Eval -->
    <div v-if="refinery.evalScores" class="flex items-center gap-3 px-3 py-0.5 rounded-full bg-accent-500/5">
      <span class="font-semibold text-[10px]" :class="refinery.evalScores.passed ? 'text-emerald-500' : 'text-accent-500'">
        {{ refinery.evalScores.passed ? 'OPTIMAL' : 'REFINING' }}
      </span>
      <div class="flex items-center gap-3 font-mono text-[10px]">
        <span>G:{{ Math.round(refinery.evalScores.contextGrounding * 100) }}%</span>
        <span>D:{{ Math.round(refinery.evalScores.informationDensity * 100) }}%</span>
        <span>B:{{ budgetDisplay.pct }}%</span>
      </div>
    </div>

    <!-- Right -->
    <div class="flex items-center gap-3">
      <div v-if="refinery.isRunning" class="flex items-center gap-1.5 text-accent-500 font-medium text-[10px]">
        <div class="flex gap-1">
          <span class="thinking-dot w-1 h-1 rounded-full bg-accent-500"></span>
          <span class="thinking-dot w-1 h-1 rounded-full bg-accent-500"></span>
          <span class="thinking-dot w-1 h-1 rounded-full bg-accent-500"></span>
        </div>
        {{ refinery.currentStep }}
      </div>
      <span class="font-medium text-accent-500">{{ settings.llmProvider.toUpperCase() }}</span>
      <span class="text-[10px] font-mono opacity-40">v0.1.0</span>
    </div>
  </footer>
</template>
