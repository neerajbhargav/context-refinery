<script setup lang="ts">
import { useRefineryStore } from '@/stores/refinery'
import { computed } from 'vue'

const refinery = useRefineryStore()

interface ScoreItem {
  label: string
  value: number
  color: string
}

const scores = computed<ScoreItem[]>(() => {
  if (!refinery.evalScores) return []
  return [
    { label: 'Grounding', value: refinery.evalScores.contextGrounding, color: '#10b981' },
    { label: 'Density', value: refinery.evalScores.informationDensity, color: '#7c3aed' },
    { label: 'Budget', value: refinery.evalScores.budgetUtilization, color: '#f59e0b' },
    { label: 'Overall', value: refinery.evalScores.overallScore, color: '#6b8ce0' },
  ]
})

function getCircumference(): number {
  return 2 * Math.PI * 28
}
function getOffset(value: number): number {
  return getCircumference() * (1 - value)
}
</script>

<template>
  <div v-if="refinery.evalScores">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-xs font-semibold text-cr-text">Evaluation</h3>
      <span
        class="text-xs font-medium px-2.5 py-0.5 rounded-full"
        :class="refinery.evalScores.passed
          ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
          : 'bg-amber-500/10 text-amber-600 dark:text-amber-400'"
      >
        {{ refinery.evalScores.passed ? 'Pass' : 'Needs refinement' }}
      </span>
    </div>

    <div class="grid grid-cols-4 gap-2">
      <div
        v-for="score in scores"
        :key="score.label"
        class="flex flex-col items-center"
      >
        <div class="score-ring w-14 h-14">
          <svg class="w-14 h-14 -rotate-90" viewBox="0 0 64 64">
            <circle
              cx="32" cy="32" r="28"
              fill="none"
              class="stroke-cr-surface-variant"
              stroke-width="3"
            />
            <circle
              cx="32" cy="32" r="28"
              fill="none"
              :stroke="score.color"
              stroke-width="3"
              stroke-linecap="round"
              :stroke-dasharray="getCircumference()"
              :stroke-dashoffset="getOffset(score.value)"
            />
          </svg>
          <span class="absolute text-[11px] font-semibold text-cr-text">
            {{ Math.round(score.value * 100) }}
          </span>
        </div>
        <span class="text-[10px] text-cr-text-dim mt-1">{{ score.label }}</span>
      </div>
    </div>
  </div>
</template>
