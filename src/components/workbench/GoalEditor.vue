<script setup lang="ts">
import { useWorkbenchStore } from '@/stores/workbench'

const workbench = useWorkbenchStore()
</script>

<template>
  <div class="flex flex-col gap-3">
    <div class="flex items-center justify-between">
      <label class="text-xs font-semibold text-cr-text" for="goal-editor">
        Refinement Goal
      </label>
      <div
        class="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-medium transition-all"
        :class="workbench.goal.length >= 10
          ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
          : 'bg-cr-surface-variant text-cr-text-dim'"
      >
        <div class="w-1.5 h-1.5 rounded-full" :class="workbench.goal.length >= 10 ? 'bg-emerald-500' : 'bg-cr-outline'"></div>
        {{ workbench.goal.length >= 10 ? 'Ready' : 'Describe your goal' }}
      </div>
    </div>

    <textarea
      id="goal-editor"
      v-model="workbench.goal"
      class="input-field min-h-[100px] resize-none leading-relaxed"
      placeholder="e.g. Analyze the codebase for security vulnerabilities, focusing on input validation and API endpoints..."
      aria-label="Goal description"
    />

    <div class="flex items-center justify-between text-[10px] text-cr-text-dim px-1">
      <span>{{ workbench.goal.length }} characters</span>
      <span>min 10 chars</span>
    </div>
  </div>
</template>
