<template>
  <svg
    class="app-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    :fill="isFilled ? 'currentColor' : 'none'"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    v-html="path"
  ></svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 24 },
  strokeWidth: { type: [Number, String], default: 1.7 }
})

// 单文件图标库：线性风格统一，paw/signal/battery/sparkle 为实心
const ICONS = {
  home: '<path d="M3 11.4 12 4l9 7.4"/><path d="M5 10v9.5h14V10"/>',
  camera:
    '<path d="M3 8.6A2 2 0 0 1 5 6.6h2l1.3-2h4.4L17 6.6h2a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/><circle cx="12" cy="13" r="3.4"/>',
  paw: '<ellipse cx="12" cy="15.2" rx="4.3" ry="3.4"/><circle cx="6.8" cy="11" r="1.7"/><circle cx="10" cy="8.2" r="1.7"/><circle cx="14" cy="8.2" r="1.7"/><circle cx="17.2" cy="11" r="1.7"/>',
  chat: '<path d="M20 14a2 2 0 0 1-2 2H8l-4 3v-3a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2Z"/>',
  user: '<circle cx="12" cy="8" r="3.4"/><path d="M5 20a7 7 0 0 1 14 0"/>',
  stethoscope:
    '<path d="M6 3v5a4 4 0 0 0 8 0V3"/><path d="M10 16a4 4 0 0 0 8 0v-1.5"/><circle cx="18" cy="12" r="2.2"/><path d="M4.5 3h1M14.5 3h1"/>',
  heart:
    '<path d="M12 20s-7-4.6-9-9a4.5 4.5 0 0 1 8-2.5A4.5 4.5 0 0 1 21 11c-2 4.4-9 9-9 9Z"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  send: '<path d="M21 3 10.5 13.5M21 3l-7 18-4-7-7-4 18-7Z"/>',
  search: '<circle cx="11" cy="11" r="6"/><path d="m20 20-3.6-3.6"/>',
  bell: '<path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6Z"/><path d="M10 19a2 2 0 0 0 4 0"/>',
  signal:
    '<rect x="3" y="14" width="3" height="6" rx="1"/><rect x="8.5" y="10" width="3" height="10" rx="1"/><rect x="14" y="6" width="3" height="14" rx="1"/><rect x="19.5" y="3" width="3" height="17" rx="1"/>',
  battery:
    '<rect x="2" y="8" width="18" height="9" rx="2.5"/><rect x="4" y="10" width="12" height="5" rx="1" fill="currentColor" stroke="none"/><path d="M21 11v3" stroke-width="2.4"/>',
  sparkle: '<path d="M12 3l1.9 5.4L19 10l-5.1 1.6L12 17l-1.9-5.4L5 10l5.1-1.6Z"/>',
  comment: '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-5.2A8 8 0 1 1 21 12Z"/>',
  image:
    '<rect x="3" y="4" width="18" height="16" rx="2.5"/><circle cx="8.5" cy="9.5" r="1.8"/><path d="m4 18 5-5 4 4 3-3 4 4"/>',
  phone:
    '<path d="M5 4h3l2 5-2 1c1 2.2 3.2 4.4 5.4 5.4l1-2 5 2v3a2 2 0 0 1-2 2C11 20 4 13 3 6a2 2 0 0 1 2-2Z"/>',
  check: '<path d="m5 12 4.5 4.5L19 7"/>',
  back: '<path d="M15 6l-6 6 6 6"/>',
  bookmark: '<path d="M6 4h12v16l-6-4-6 4Z"/>',
  'heart-o': '<path d="M12 20s-7-4.6-9-9a4.5 4.5 0 0 1 8-2.5A4.5 4.5 0 0 1 21 11c-2 4.4-9 9-9 9Z"/>',
  x: '<path d="M6 6l12 12M18 6 6 18"/>',
  'calendar-check': '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 9.5h16M8 3v4M16 3v4"/><path d="m9 15 2 2 4-4"/>',
  scale: '<path d="M12 4v16M7 8h10M5 8l-2 5a3 3 0 0 0 6 0L7 8Zm14 0-2 5a3 3 0 0 0 6 0l-2-5Z"/><path d="M5 8h14"/>',
  pill: '<rect x="3.5" y="8" width="17" height="8" rx="4" transform="rotate(-45 12 12)"/><path d="M9 9l6 6"/>',
  notes: '<path d="M5 4h11l3 3v13H5Z"/><path d="M9 10h6M9 14h6"/>',
  refresh: '<path d="M20 11a8 8 0 1 0-1.5 5"/><path d="M20 5v6h-6"/>',
  location:
    '<path d="M12 21s-7-6.5-7-12a7 7 0 0 1 14 0c0 5.5-7 12-7 12Z"/><circle cx="12" cy="9" r="2.4"/>',
  calendar: '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 9.5h16M8 3v4M16 3v4"/>',
  flame:
    '<path d="M12 3c1 3-2 4-2 7a2 2 0 0 0 4 0c2 2 3 4 3 6a5 5 0 0 1-10 0c0-4 5-5.5 5-13Z"/>',
  mic: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>',
  share: '<circle cx="6" cy="12" r="2.4"/><circle cx="18" cy="6" r="2.4"/><circle cx="18" cy="18" r="2.4"/><path d="m8.1 10.9 7.8-3.8M8.1 13.1l7.8 3.8"/>'
}

const FILLED = new Set(['paw', 'signal', 'battery', 'sparkle'])

const path = computed(() => ICONS[props.name] || '')
const isFilled = computed(() => FILLED.has(props.name))
</script>

<style scoped>
.app-icon {
  display: block;
  flex-shrink: 0;
}
</style>
