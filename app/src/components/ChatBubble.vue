<template>
  <div class="bubble-row" :class="role">
    <span v-if="role === 'them'" class="b-avatar">{{ initial }}</span>
    <div class="b-col">
      <div class="bubble" :class="role">{{ text }}</div>
      <span v-if="time" class="b-time num">{{ time }}</span>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  role: { type: String, default: 'them' }, // me | them
  text: { type: String, required: true },
  time: { type: String, default: '' },
  name: { type: String, default: '问' }
})
const initial = (props.name || '问').slice(0, 1)
</script>

<style scoped>
.bubble-row {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  max-width: 100%;
}
.bubble-row.me {
  flex-direction: row-reverse;
}
.b-avatar {
  width: 36px;
  height: 36px;
  border-radius: 30%;
  display: grid;
  place-items: center;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 17px;
  color: var(--color-ink);
  background: var(--grad-sand);
  flex-shrink: 0;
  align-self: flex-end;
}
.b-col {
  display: flex;
  flex-direction: column;
  max-width: 76%;
}
.bubble-row.me .b-col {
  align-items: flex-end;
}
.bubble {
  padding: 11px 15px;
  border-radius: 18px;
  font-size: 15px;
  line-height: 1.55;
  word-break: break-word;
}
.bubble.them {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-ink);
  border-bottom-left-radius: 6px;
}
.bubble.me {
  background: linear-gradient(140deg, var(--color-accent), var(--color-accent-ink));
  color: #fff;
  border-bottom-right-radius: 6px;
}
.b-time {
  font-size: 11px;
  color: var(--color-faint);
  margin-top: 4px;
}
</style>
