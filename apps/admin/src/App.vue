<template>
  <div class="grain app-root">
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
    <ToastHost />
  </div>
</template>

<script setup>
import ToastHost from '@shared/ToastHost.vue'
</script>

<style>
.app-root {
  height: 100%;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--dur-base) var(--ease-out);
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
