<script setup lang="ts">
import { computed } from 'vue'
import { useWorkbenchStore } from '@/stores/workbench'

const workbench = useWorkbenchStore()

const budgetLabel = computed(() => {
  const b = workbench.tokenBudget
  if (b >= 1000) return `${(b / 1000).toFixed(b % 1000 === 0 ? 0 : 1)}K`
  return b.toString()
})

function sliderToTokens(val: number): number {
  const minLog = Math.log(512)
  const maxLog = Math.log(32768)
  return Math.round(Math.exp(minLog + (val / 100) * (maxLog - minLog)))
}

function tokensToSlider(tokens: number): number {
  const minLog = Math.log(512)
  const maxLog = Math.log(32768)
  return Math.round(((Math.log(tokens) - minLog) / (maxLog - minLog)) * 100)
}

const sliderValue = computed({
  get: () => tokensToSlider(workbench.tokenBudget),
  set: (val: number) => workbench.setTokenBudget(sliderToTokens(val)),
})

const fillPercent = computed(() => sliderValue.value)
</script>

<template>
  <div class="space-y-2">
    <div class="flex items-center justify-between">
      <label class="text-xs font-semibold text-cr-text" id="token-budget-label">
        Token Budget
      </label>
      <span class="text-sm font-mono font-semibold text-accent-500">
        {{ budgetLabel }}
      </span>
    </div>

    <div class="relative">
      <input
        type="range"
        min="0"
        max="100"
        step="1"
        v-model.number="sliderValue"
        class="slider-input w-full"
        aria-labelledby="token-budget-label"
        :aria-valuenow="workbench.tokenBudget"
        aria-valuemin="512"
        aria-valuemax="32768"
      />
      <div
        class="absolute top-1/2 left-0 h-1 rounded-full bg-accent-500 pointer-events-none -translate-y-1/2"
        :style="{ width: fillPercent + '%' }"
      />
    </div>

    <div class="flex justify-between text-[10px] text-cr-text-dim px-0.5">
      <span>512</span>
      <span>2K</span>
      <span>8K</span>
      <span>32K</span>
    </div>
  </div>
</template>

<style scoped>
.slider-input {
  -webkit-appearance: none;
  appearance: none;
  height: 4px;
  border-radius: 2px;
  background: hsl(var(--color-cr-outline));
  outline: none;
  position: relative;
  z-index: 1;
}

.slider-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #7c3aed;
  border: 2px solid white;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transition: box-shadow 0.15s, transform 0.1s;
}

.slider-input::-webkit-slider-thumb:hover {
  box-shadow: 0 0 0 6px rgba(124, 58, 237, 0.15);
}

.slider-input::-webkit-slider-thumb:active {
  transform: scale(0.95);
}

.slider-input::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #7c3aed;
  border: 2px solid white;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}
</style>
