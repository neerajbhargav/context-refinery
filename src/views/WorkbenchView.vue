<script setup lang="ts">
import FileDropZone from '@/components/workbench/FileDropZone.vue'
import FileTree from '@/components/workbench/FileTree.vue'
import GoalEditor from '@/components/workbench/GoalEditor.vue'
import ModelSelector from '@/components/refinery/ModelSelector.vue'
import TokenBudgetSlider from '@/components/common/TokenBudgetSlider.vue'
import AgentThinkingStream from '@/components/refinery/AgentThinkingStream.vue'
import PromptPreview from '@/components/refinery/PromptPreview.vue'
import EvalDashboard from '@/components/eval/EvalDashboard.vue'

import { useWorkbenchStore } from '@/stores/workbench'
import { useRefineryStore } from '@/stores/refinery'
import { useSSE } from '@/composables/useSSE'
import { ref, onMounted, onUnmounted } from 'vue'

const workbench = useWorkbenchStore()
const refinery = useRefineryStore()
const { connect } = useSSE()

const isSidebarCollapsed = ref(false)
const isRightPanelCollapsed = ref(false)

function startRefining() {
  if (!workbench.isReady || refinery.isRunning) return

  const body = {
    goal: workbench.goal,
    files: workbench.selectedFiles.map(f => ({
      path: f.path,
      filename: f.filename,
      content: f.content,
      language: f.language,
    })),
    token_budget: workbench.tokenBudget,
    target_model: workbench.targetModel,
    max_iterations: 3,
  }

  connect('/api/refinery/stream', body)
}

function toggleSidebar() { isSidebarCollapsed.value = !isSidebarCollapsed.value }
function toggleRightPanel() { isRightPanelCollapsed.value = !isRightPanelCollapsed.value }

function handleKeyDown(e: KeyboardEvent) {
  if (e.ctrlKey && e.key === 'Enter') {
    startRefining()
  }
  if (e.ctrlKey && e.key === 'b') {
    e.preventDefault()
    toggleSidebar()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})

const samplePrompts = [
  { label: 'Feature Walkthrough', icon: '📖', goal: 'Summarize the core architecture and create a technical walkthrough of the main entry point.' },
  { label: 'Security Audit', icon: '🔒', goal: 'Analyze the codebase for common security vulnerabilities, focusing on input validation and API endpoints.' },
  { label: 'Refactor Plan', icon: '🔧', goal: 'Identify technical debt and suggest a cleaner, more modular refactoring for the primary service layer.' },
]

function fillSample(goal: string) {
  workbench.setGoal(goal)
}
</script>

<template>
  <div class="h-full flex gap-2 p-2 overflow-hidden">
    <!-- LEFT PANEL: Files -->
    <div
      class="flex-shrink-0 flex flex-col gap-2 transition-all duration-300"
      :class="isSidebarCollapsed ? 'w-0 opacity-0 pointer-events-none' : 'w-72'"
    >
      <FileDropZone />
      <div class="surface-card flex-1 overflow-hidden relative">
        <FileTree />
        <button
          @click="toggleSidebar"
          class="absolute top-3 right-3 btn-icon !p-1.5"
          title="Collapse Sidebar (Ctrl+B)"
        >
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="11 17 6 12 11 7"/></svg>
        </button>
      </div>
    </div>

    <!-- Floating sidebar toggle -->
    <button
      v-if="isSidebarCollapsed"
      @click="toggleSidebar"
      class="fixed left-4 top-1/2 -translate-y-1/2 z-50 btn-icon surface-card-elevated !p-3"
    >
      <svg class="w-5 h-5 text-accent-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="13 17 18 12 13 7"/></svg>
    </button>

    <!-- CENTER PANEL -->
    <div class="flex-1 flex flex-col gap-2 min-w-0">
      <!-- Empty State -->
      <div v-if="workbench.fileCount === 0" class="surface-card flex-1 flex flex-col items-center justify-center p-10 space-y-8 text-center">
        <div class="flex flex-col items-center space-y-4">
          <div class="w-16 h-16 rounded-2xl bg-accent-500/10 flex items-center justify-center">
            <svg class="w-8 h-8 text-accent-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z" />
              <path d="M12 12l8-4.5" />
              <path d="M12 12v9" />
              <path d="M12 12L4 7.5" />
            </svg>
          </div>
          <div class="max-w-md space-y-2">
            <h2 class="text-xl font-semibold text-cr-text">Focus Your Context</h2>
            <p class="text-sm text-cr-text-dim leading-relaxed">Transform complex codebases into precise, model-optimized prompts. Drag files or a folder to begin.</p>
          </div>
        </div>

        <!-- Sample Prompts -->
        <div class="w-full max-w-2xl space-y-3">
          <div class="text-xs font-medium text-cr-text-dim uppercase tracking-wider">Quick Start</div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
            <button
              v-for="sample in samplePrompts"
              :key="sample.label"
              @click="fillSample(sample.goal)"
              class="surface-card p-4 text-left hover:border-accent-400 transition-all group"
            >
              <div class="flex items-center gap-2 mb-2">
                <span>{{ sample.icon }}</span>
                <span class="text-xs font-semibold text-cr-text">{{ sample.label }}</span>
              </div>
              <p class="text-xs text-cr-text-dim line-clamp-2 group-hover:text-cr-text transition-colors leading-relaxed">{{ sample.goal }}</p>
            </button>
          </div>
        </div>

        <!-- Steps -->
        <div class="flex items-center gap-8 text-xs font-medium text-cr-text-dim pt-4 border-t border-cr-border">
          <div class="flex items-center gap-2">
            <span class="w-6 h-6 rounded-lg bg-cr-surface-variant flex items-center justify-center text-[10px] font-semibold">1</span>
            <span>Ingest</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="w-6 h-6 rounded-lg bg-cr-surface-variant flex items-center justify-center text-[10px] font-semibold">2</span>
            <span>Define</span>
          </div>
          <div class="flex items-center gap-2 text-accent-500">
            <span class="w-6 h-6 rounded-lg bg-accent-500/10 flex items-center justify-center text-[10px] font-semibold">3</span>
            <span>Refine</span>
          </div>
        </div>
      </div>

      <!-- Content when files exist -->
      <template v-else>
        <div class="surface-card p-5">
          <GoalEditor />
        </div>

        <!-- Controls Row -->
        <div class="surface-card p-4 flex items-end gap-4">
          <div class="flex-1">
            <ModelSelector />
          </div>
          <div class="flex-1">
            <TokenBudgetSlider />
          </div>
          <button
            class="btn-primary flex items-center gap-2 whitespace-nowrap"
            :disabled="!workbench.isReady || refinery.isRunning"
            @click="startRefining"
          >
            <svg v-if="!refinery.isRunning" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z" />
            </svg>
            <svg v-else class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M21 12a9 9 0 1 1-6.219-8.56" />
            </svg>
            {{ refinery.isRunning ? 'Refining...' : 'Refine Prompt' }}
          </button>
        </div>

        <!-- Agent Stream -->
        <div class="surface-card flex-1 overflow-hidden">
          <AgentThinkingStream />
        </div>
      </template>
    </div>

    <!-- RIGHT PANEL: Output -->
    <div
      class="flex-shrink-0 flex flex-col gap-2 transition-all duration-300"
      :class="isRightPanelCollapsed ? 'w-0 opacity-0 pointer-events-none' : 'w-[460px]'"
    >
      <div class="surface-card-elevated flex-1 overflow-hidden relative">
        <PromptPreview />
        <button
          @click="toggleRightPanel"
          class="absolute top-3 left-3 btn-icon !p-1.5"
          title="Collapse Output"
        >
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="13 17 18 12 13 7"/></svg>
        </button>
      </div>

      <div v-if="refinery.evalScores" class="surface-card p-4">
        <EvalDashboard />
      </div>
    </div>

    <!-- Floating right panel toggle -->
    <button
      v-if="isRightPanelCollapsed"
      @click="toggleRightPanel"
      class="fixed right-4 top-1/2 -translate-y-1/2 z-50 btn-icon surface-card-elevated !p-3"
    >
      <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="11 17 6 12 11 7"/></svg>
    </button>
  </div>
</template>
