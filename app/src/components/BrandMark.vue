<template>
  <span class="brand" :class="{ 'brand--mark': !showText }">
    <svg class="brand-symbol" viewBox="0 0 48 48" width="100%" height="100%" aria-hidden="true">
      <circle cx="24" cy="24" r="22" fill="var(--color-accent)" />
      <!-- 爪垫（纸色），构成品牌"爪印"记忆点 -->
      <g fill="var(--color-surface)">
        <ellipse cx="24" cy="30" rx="9" ry="7" />
        <circle cx="15" cy="20" r="3" />
        <circle cx="20" cy="16" r="3.2" />
        <circle cx="28" cy="16" r="3.2" />
        <circle cx="33" cy="20" r="3" />
      </g>
      <!-- 两只圆点眼，赋予爪印"表情" -->
      <g fill="var(--color-ink)">
        <circle cx="21" cy="29.5" r="1.3" />
        <circle cx="27" cy="29.5" r="1.3" />
      </g>
    </svg>
    <span v-if="showText" class="brand-word">Petwise</span>
  </span>
</template>

<script setup>
defineProps({
  showText: { type: Boolean, default: true }
})
</script>

<style scoped>
.brand {
  display: inline-flex;
  align-items: center;
  gap: 9px;
}
.brand-symbol {
  width: 34px;
  height: 34px;
  display: block;
}
.brand-word {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 22px;
  letter-spacing: -0.02em;
  color: var(--color-ink);
}
.brand--mark .brand-symbol {
  width: 100%;
  height: 100%;
}
</style>
