<script setup lang="ts">
import AppHeader from '@/components/common/AppHeader.vue'
import StatusBar from '@/components/common/StatusBar.vue'
import { useSettingsStore } from '@/stores/settings'
import { onMounted } from 'vue'

const settings = useSettingsStore()

onMounted(() => {
  document.documentElement.className = settings.theme
})
</script>

<template>
  <div class="flex flex-col h-screen overflow-hidden bg-cr-bg">
    <AppHeader />
    <main class="flex-1 overflow-hidden">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <StatusBar />
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
