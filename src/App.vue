<script setup lang="ts">
import AppHeader from '@/components/common/AppHeader.vue'
import StatusBar from '@/components/common/StatusBar.vue'
import { useSettingsStore } from '@/stores/settings'
import { useRoute } from 'vue-router'
import { onMounted, computed } from 'vue'

const settings = useSettingsStore()
const route = useRoute()
const isSetup = computed(() => route.name === 'setup')

onMounted(() => {
  document.documentElement.className = settings.theme
})
</script>

<template>
  <div class="flex flex-col h-screen overflow-hidden bg-cr-bg">
    <AppHeader v-if="!isSetup" />
    <main class="flex-1 overflow-hidden">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <StatusBar v-if="!isSetup" />
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
