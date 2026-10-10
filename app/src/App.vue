<template>
  <div class="app-atmosphere"></div>

  <div class="app-shell">
    <!-- 拟真状态栏 -->
    <div class="status-bar">
      <span class="num">{{ clock }}</span>
      <span class="sb-right">
        <span>5G</span>
        <AppIcon name="signal" :size="16" />
        <AppIcon name="battery" :size="22" />
      </span>
    </div>

    <main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- 底部导航：仅非启动页显示 -->
    <AppNav v-show="!isBare" />

    <!-- 全局轻提示 -->
    <ToastHost />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import AppNav from '@/components/AppNav.vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import ToastHost from '@/components/ToastHost.vue'

const route = useRoute()
const isBare = computed(() => route.meta.bare === true)

const clock = ref('09:41')
let timer = null
function tick() {
  const d = new Date()
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  clock.value = `${hh}:${mm}`
}
onMounted(() => {
  tick()
  timer = setInterval(tick, 30000)
})
onUnmounted(() => clearInterval(timer))
</script>
