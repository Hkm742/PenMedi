<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import AppNavbar from './components/AppNavbar.vue'

const route = useRoute()
const authStore = useAuthStore()

const showNavbar = computed(() => {
  return authStore.isAuthenticated && route.name !== 'login'
})
</script>

<template>
  <div class="pm-app-layout">
    <AppNavbar v-if="showNavbar" />
    <main class="pm-main-content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.pm-app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--pm-bg-canvas);
}

.pm-main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>
