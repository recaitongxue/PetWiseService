<template>
  <span
    class="pet-avatar"
    :class="{ ring }"
    :style="{ width: size + 'px', height: size + 'px' }"
  >
    <PetIllustration :species="species" :tone="tone" :label="name" />
  </span>
</template>

<script setup>
import PetIllustration from './PetIllustration.vue'

const props = defineProps({
  species: { type: String, default: 'cat' },
  name: { type: String, default: '' },
  size: { type: Number, default: 44 },
  ring: { type: Boolean, default: true },
  // 显式色调；缺省按物种给：猫=苔绿，狗=蜜桃
  tone: { type: String, default: '' }
})

const tone = props.tone || (props.species === 'dog' ? 'peach' : 'sage')
</script>

<style scoped>
.pet-avatar {
  display: inline-block;
  position: relative;
  border-radius: 50%;
  overflow: hidden;
  background: var(--color-surface);
  box-shadow: var(--shadow-soft);
  flex-shrink: 0;
}
.pet-avatar.ring {
  padding: 3px;
  background: var(--color-surface);
  box-shadow:
    0 0 0 1px var(--color-border-strong),
    var(--shadow-soft);
}
.pet-avatar :deep(.pet-illu) {
  border-radius: 50%;
}
</style>
