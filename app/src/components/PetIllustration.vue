<template>
  <svg
    class="pet-illu"
    :class="'tone-' + tone"
    viewBox="0 0 120 120"
    role="img"
    :aria-label="label || (species === 'dog' ? '狗狗' : '猫咪')"
    :style="toneVars"
  >
    <defs>
      <radialGradient :id="bgId" cx="36%" cy="28%" r="82%">
        <stop offset="0%" :stop-color="tints[tone].hi" />
        <stop offset="100%" :stop-color="tints[tone].lo" />
      </radialGradient>
    </defs>

    <!-- 柔光圆形底 -->
    <circle cx="60" cy="60" r="60" :fill="`url(#${bgId})`" />
    <!-- 顶部一抹高光，增加体积感 -->
    <ellipse cx="44" cy="30" rx="26" ry="16" fill="#ffffff" opacity="0.18" />

    <!-- 猫 -->
    <g v-if="species === 'cat'" class="sil">
      <path d="M30 40 L23 11 L52 31 Z" />
      <path d="M90 40 L97 11 L68 31 Z" />
      <circle cx="60" cy="55" r="31" />
      <path d="M20 122 C20 89 39 75 60 75 C81 75 100 89 100 122 Z" />
    </g>
    <g v-else-if="species === 'dog'" class="sil">
      <ellipse cx="29" cy="56" rx="16" ry="27" transform="rotate(-14 29 56)" />
      <ellipse cx="91" cy="56" rx="16" ry="27" transform="rotate(14 91 56)" />
      <circle cx="60" cy="52" r="28" />
      <ellipse cx="60" cy="67" rx="19" ry="16" />
      <path d="M22 122 C22 92 40 78 60 78 C80 78 98 92 98 122 Z" />
    </g>

    <!-- 五官（浅色，模拟剪影留白） -->
    <g class="feat">
      <template v-if="species === 'cat'">
        <ellipse class="eye" cx="49" cy="51" rx="3.4" ry="4.2" />
        <ellipse class="eye" cx="71" cy="51" rx="3.4" ry="4.2" />
        <path class="nose" d="M56 58 L64 58 L60 63 Z" />
        <path class="whisker" d="M58 60 L40 55 M58 62 L40 64 M62 60 L80 55 M62 62 L80 64" />
      </template>
      <template v-else>
        <ellipse class="eye" cx="49" cy="49" rx="3.6" ry="4.2" />
        <ellipse class="eye" cx="71" cy="49" rx="3.6" ry="4.2" />
        <ellipse class="nose" cx="60" cy="63" rx="5.2" ry="3.8" />
        <path class="mouth" d="M60 67 Q53 73 47 70 M60 67 Q67 73 73 70" />
      </template>
    </g>
  </svg>
</template>

<script setup>
let uidCounter = 0
const props = defineProps({
  species: { type: String, default: 'cat' },
  tone: { type: String, default: 'sage' }, // sage | peach | ink | coral
  label: { type: String, default: '' }
})

const bgId = `petbg-${(uidCounter += 1)}-${Math.random().toString(36).slice(2, 7)}`

// 每种色调：圆形底亮色（hi/lo）+ 剪影深色调（sil/feat）
const tints = {
  sage: { hi: '#e9f0e6', lo: '#c9ddc6', sil: '#34503f', feat: '#86a681' },
  peach: { hi: '#fceede', lo: '#f1cca2', sil: '#a9622e', feat: '#e3ac7c' },
  ink: { hi: '#e4ece5', lo: '#bccdc2', sil: '#1d2c24', feat: '#5b7563' },
  coral: { hi: '#fbe5dc', lo: '#f3bfae', sil: '#c8431f', feat: '#f0a083' }
}

const toneVars = {
  '--sil': tints[props.tone]?.sil || tints.sage.sil,
  '--feat': tints[props.tone]?.feat || tints.sage.feat
}
</script>

<style scoped>
.pet-illu {
  width: 100%;
  height: 100%;
  display: block;
}
.sil path,
.sil circle,
.sil ellipse {
  fill: var(--sil);
}
.feat .eye {
  fill: var(--feat);
}
.feat .nose {
  fill: var(--color-peach);
}
.feat .whisker {
  fill: none;
  stroke: var(--feat);
  stroke-width: 1.4;
  stroke-linecap: round;
  opacity: 0.7;
}
.feat .mouth {
  fill: none;
  stroke: var(--feat);
  stroke-width: 1.6;
  stroke-linecap: round;
}
</style>
