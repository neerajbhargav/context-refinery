<script setup lang="ts">
import { useRefineryStore } from '@/stores/refinery'
import { ref, watch, nextTick } from 'vue'

const refinery = useRefineryStore()
const streamContainer = ref<HTMLElement | null>(null)

watch(
  () => refinery.messages.length,
  async () => {
    await nextTick()
    if (streamContainer.value) {
      streamContainer.value.scrollTop = streamContainer.value.scrollHeight
    }
  }
)

const stepIcons: Record<string, string> = {
  thinking: '🧠',
  retrieving: '🔍',
  refining: '🔧',
  evaluating: '📊',
  complete: '✅',
  error: '❌',
}

const stepColors: Record<string, string> = {
  thinking: 'text-accent-500',
  retrieving: 'text-blue-500 dark:text-blue-400',
  refining: 'text-violet-500 dark:text-violet-400',
  evaluating: 'text-emerald-500 dark:text-emerald-400',
  complete: 'text-emerald-500 dark:text-emerald-400',
  error: 'text-red-500 dark:text-red-400',
}
</script>

<template>
  <div class="flex flex-col h-full">
    <div class="flex items-center justify-between px-4 py-2.5 border-b border-cr-border">
      <span class="text-xs font-semibold text-cr-text">Agent Activity</span>
      <div v-if="refinery.isRunning" class="flex items-center gap-2 text-xs text-accent-500 font-medium">
        <div class="flex gap-1">
          <span class="thinking-dot w-1.5 h-1.5 rounded-full bg-accent-500"></span>
          <span class="thinking-dot w-1.5 h-1.5 rounded-full bg-accent-500"></span>
          <span class="thinking-dot w-1.5 h-1.5 rounded-full bg-accent-500"></span>
        </div>
        Processing
      </div>
    </div>

    <div ref="streamContainer" class="flex-1 overflow-y-auto p-3 space-y-1">
      <div
        v-if="refinery.messages.length === 0 && !refinery.isRunning"
        class="flex flex-col items-center justify-center h-full text-cr-text-dim"
      >
        <svg class="w-10 h-10 mb-3 opacity-20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z" />
          <path d="M12 12l8-4.5" />
          <path d="M12 12v9" />
          <path d="M12 12L4 7.5" />
        </svg>
        <p class="text-xs">Agent thinking will appear here</p>
      </div>

      <TransitionGroup name="list" tag="div" class="space-y-2">
        <div
          v-for="(msg, i) in refinery.messages"
          :key="i"
          class="flex items-start gap-3 px-2 py-2 rounded-xl hover:bg-cr-surface-variant transition-colors"
        >
          <div class="w-7 h-7 rounded-lg bg-cr-surface-variant flex items-center justify-center flex-shrink-0 text-sm">
            {{ stepIcons[msg.stepType] || '💬' }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between mb-0.5">
              <span class="text-xs font-semibold" :class="stepColors[msg.stepType] || 'text-cr-text'">
                {{ msg.agentName }}
              </span>
              <span class="text-[9px] font-mono text-cr-text-dim">
                {{ new Date(msg.timestamp * 1000).toLocaleTimeString() }}
              </span>
            </div>
            <p class="text-xs text-cr-text leading-relaxed whitespace-pre-wrap">
              {{ msg.content }}
            </p>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<style scoped>
.list-enter-active {
  transition: all 0.2s ease-out;
}
.list-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
</style>
