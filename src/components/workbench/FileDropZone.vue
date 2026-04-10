<script setup lang="ts">
import { ref } from 'vue'
import { useWorkbenchStore, type SourceFile } from '@/stores/workbench'

const workbench = useWorkbenchStore()
const isDragging = ref(false)

function onDragOver(e: DragEvent) {
  e.preventDefault()
  isDragging.value = true
}

function onDragLeave() {
  isDragging.value = false
}

async function onDrop(e: DragEvent) {
  e.preventDefault()
  isDragging.value = false

  const items = e.dataTransfer?.files
  if (!items) return

  const files: SourceFile[] = []

  for (let i = 0; i < items.length; i++) {
    const file = items[i]
    try {
      const content = await file.text()
      const ext = file.name.split('.').pop() || 'txt'
      const language = getLanguage(ext)
      const tokenCount = Math.ceil(content.length / 4)

      files.push({
        path: file.name,
        filename: file.name,
        language,
        content,
        tokenCount,
        selected: true,
      })
    } catch (err) {
      console.warn(`Could not read file: ${file.name}`, err)
    }
  }

  if (files.length > 0) {
    workbench.addFiles(files)
  }
}

function getLanguage(ext: string): string {
  const map: Record<string, string> = {
    py: 'python', js: 'javascript', ts: 'typescript',
    jsx: 'javascript', tsx: 'typescript', vue: 'vue',
    rs: 'rust', go: 'go', java: 'java', cpp: 'cpp',
    c: 'c', h: 'c', md: 'markdown', txt: 'text',
    json: 'json', yaml: 'yaml', yml: 'yaml',
    html: 'html', css: 'css', sql: 'sql',
    sh: 'bash', ps1: 'powershell',
  }
  return map[ext.toLowerCase()] || 'text'
}

async function openFolderDialog() {
  try {
    const { invoke } = await import('@tauri-apps/api/core')
    const folderPath = await invoke<string | null>('open_folder_dialog')
    if (folderPath) {
      console.log('Selected folder:', folderPath)
    }
  } catch {
    const input = document.createElement('input')
    input.type = 'file'
    input.multiple = true
    input.accept = '.py,.js,.ts,.jsx,.tsx,.vue,.rs,.go,.java,.md,.txt,.json,.yaml,.yml,.html,.css'
    input.onchange = async () => {
      if (!input.files) return
      const files: SourceFile[] = []
      for (const file of Array.from(input.files)) {
        const content = await file.text()
        const ext = file.name.split('.').pop() || 'txt'
        files.push({
          path: file.name,
          filename: file.name,
          language: getLanguage(ext),
          content,
          tokenCount: Math.ceil(content.length / 4),
          selected: true,
        })
      }
      workbench.addFiles(files)
    }
    input.click()
  }
}
</script>

<template>
  <div
    class="relative flex flex-col items-center justify-center p-5 rounded-2xl border-2 border-dashed transition-all duration-200 cursor-pointer min-h-[120px]"
    :class="isDragging
      ? 'border-accent-500 bg-accent-500/5'
      : 'border-cr-outline bg-cr-surface hover:border-accent-400 hover:bg-accent-500/[0.02]'"
    @dragover="onDragOver"
    @dragleave="onDragLeave"
    @drop="onDrop"
    @click="openFolderDialog"
    role="button"
    tabindex="0"
    aria-label="Drop files here or click to browse"
  >
    <div class="mb-2" :class="isDragging ? 'animate-bounce' : ''">
      <svg class="w-8 h-8" :class="isDragging ? 'text-accent-500' : 'text-cr-text-dim'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </svg>
    </div>

    <p class="text-sm font-medium" :class="isDragging ? 'text-accent-500' : 'text-cr-text'">
      {{ isDragging ? 'Drop files here' : 'Drag & drop files' }}
    </p>
    <p class="text-xs text-cr-text-dim mt-0.5">
      or click to browse
    </p>

    <div v-if="workbench.fileCount > 0" class="absolute top-2 right-2 badge-info">
      {{ workbench.fileCount }} file{{ workbench.fileCount !== 1 ? 's' : '' }}
    </div>
  </div>
</template>
