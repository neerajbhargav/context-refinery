<script setup lang="ts">
import { useWorkbenchStore } from '@/stores/workbench'

const workbench = useWorkbenchStore()

const langColors: Record<string, string> = {
  python: 'text-yellow-500 dark:text-yellow-400',
  javascript: 'text-yellow-500 dark:text-yellow-300',
  typescript: 'text-blue-500 dark:text-blue-400',
  vue: 'text-emerald-500 dark:text-emerald-400',
  rust: 'text-orange-500 dark:text-orange-400',
  go: 'text-cyan-500 dark:text-cyan-400',
  java: 'text-red-500 dark:text-red-400',
  markdown: 'text-cr-text-dim',
  json: 'text-amber-500 dark:text-amber-400',
  text: 'text-cr-text-dim',
}

function getColor(lang: string): string {
  return langColors[lang] || 'text-cr-text-dim'
}

function formatTokens(tokens: number): string {
  if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}K`
  return tokens.toString()
}
</script>

<template>
  <div class="flex flex-col h-full">
    <div class="flex items-center justify-between px-3 py-2 border-b border-cr-border">
      <span class="text-xs font-semibold text-cr-text">Files</span>
      <div class="flex gap-1">
        <button class="btn-ghost text-[10px] !px-2 !py-0.5" @click="workbench.selectAll()" :disabled="workbench.fileCount === 0">All</button>
        <button class="btn-ghost text-[10px] !px-2 !py-0.5" @click="workbench.deselectAll()" :disabled="workbench.fileCount === 0">None</button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto py-1">
      <div v-if="workbench.fileCount === 0" class="flex items-center justify-center h-full text-xs text-cr-text-dim">
        No files loaded
      </div>

      <div
        v-for="file in workbench.files"
        :key="file.path"
        class="group flex items-center gap-2 px-3 py-1.5 hover:bg-cr-surface-variant cursor-pointer transition-colors rounded-lg mx-1"
        @click="workbench.toggleFile(file.path)"
      >
        <div
          class="w-4 h-4 rounded border-2 flex items-center justify-center transition-all flex-shrink-0"
          :class="file.selected
            ? 'bg-accent-600 border-accent-600'
            : 'border-cr-outline group-hover:border-cr-text-dim'"
        >
          <svg v-if="file.selected" class="w-2.5 h-2.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>

        <span class="text-xs flex-shrink-0" :class="getColor(file.language)">
          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        </span>

        <span class="text-xs truncate flex-1" :class="file.selected ? 'text-cr-text' : 'text-cr-text-dim'">{{ file.filename }}</span>

        <span class="text-[10px] text-cr-text-dim font-mono flex-shrink-0">{{ formatTokens(file.tokenCount) }}</span>

        <button
          class="opacity-0 group-hover:opacity-100 text-cr-text-dim hover:text-red-500 transition-all p-0.5"
          @click.stop="workbench.removeFile(file.path)"
          aria-label="Remove file"
        >
          <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
    </div>

    <div class="px-3 py-2 border-t border-cr-border text-[10px] text-cr-text-dim font-medium">
      {{ workbench.totalTokens.toLocaleString() }} tokens selected
    </div>
  </div>
</template>
