<template>
  <!-- 6 位验证码分格输入：自动前进 / 粘贴分发 / 退格回跳。
       Login 与账号管理（更换手机号、注销验证）共用这一份实现。 -->
  <div class="code-row" :class="{ bad: error }">
    <input
      v-for="(d, i) in digits"
      :key="i"
      :ref="(el) => setRef(el, i)"
      v-model="digits[i]"
      class="code-box"
      type="text"
      inputmode="numeric"
      autocomplete="one-time-code"
      maxlength="1"
      :aria-label="`验证码第 ${i + 1} 位`"
      @input="onInput(i)"
      @keydown.delete="onBack(i, $event)"
      @paste="onPaste($event)"
      @focus="($event.target.select())"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => ['', '', '', '', '', ''] },
  error: { type: Boolean, default: false }
})
const emit = defineEmits(['update:modelValue'])

const digits = ref([...props.modelValue])
const refs = []

function sync() {
  emit('update:modelValue', [...digits.value])
}

function setRef(el, i) {
  if (el) refs[i] = el
}

function onInput(i) {
  // 只保留一位数字；粘进来的多位自动分发到后续格子
  const raw = String(digits.value[i] || '').replace(/\D/g, '')
  if (raw.length > 1) {
    distribute(raw, i)
    return
  }
  digits.value[i] = raw
  sync()
  if (raw && i < 5) refs[i + 1]?.focus()
}

function onBack(i, e) {
  if (!digits.value[i] && i > 0) {
    refs[i - 1]?.focus()
  }
}

function onPaste(e) {
  e.preventDefault()
  const text = (e.clipboardData?.getData('text') || '').replace(/\D/g, '').slice(0, 6)
  if (text) distribute(text, 0)
}

function distribute(text, from) {
  const next = [...digits.value]
  let idx = from
  for (const ch of text) {
    if (idx > 5) break
    next[idx] = ch
    idx += 1
  }
  digits.value = next
  sync()
  refs[Math.min(idx, 5)]?.focus()
}

function clear() {
  digits.value = ['', '', '', '', '', '']
  sync()
}

defineExpose({ clear, focus: () => refs[0]?.focus() })
</script>

<style scoped>
.code-row {
  display: flex;
  gap: 8px;
}
.code-row.bad .code-box { border-color: var(--color-alert); }
.code-box {
  flex: 1;
  min-width: 0;
  height: 52px;
  text-align: center;
  font-family: var(--font-display);
  font-size: 21px;
  font-weight: 700;
  color: var(--color-ink);
  background: var(--color-surface);
  border: 1px solid var(--hairline-strong);
  border-radius: var(--radius-md);
  outline: none;
  transition: border-color var(--dur-fast), box-shadow var(--dur-fast);
}
.code-box:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px var(--color-accent-soft);
}
</style>
