<template>
  <section class="settings">
    <!-- 模型与服务配置 -->
    <article class="card" v-reveal>
      <h2 class="sec-title">模型与服务配置</h2>
      <p class="sec-sub">用户端识别与问诊所依赖的 AI 服务参数（保存后即时生效，演示为本地存储）</p>

      <div class="cfg-grid">
        <label class="cfg">
          <div>
            <b>CV 置信度阈值</b>
            <span>低于该值的识别结果进入人工复核队列</span>
          </div>
          <select v-model.number="cfg.confThreshold">
            <option :value="0.5">0.50</option>
            <option :value="0.6">0.60</option>
            <option :value="0.7">0.70</option>
          </select>
        </label>

        <label class="cfg">
          <div>
            <b>问诊大模型</b>
            <span>图文问诊走视觉模型，纯文本走对话模型</span>
          </div>
          <select v-model="cfg.llm">
            <option>GLM-4V（图文）</option>
            <option>GLM-4（纯文本）</option>
          </select>
        </label>

        <label class="cfg">
          <div>
            <b>医疗免责声明</b>
            <span>问诊底部强制展示"不能替代执业兽医诊断"</span>
          </div>
          <button
            class="switch"
            :class="{ on: cfg.disclaimer }"
            type="button"
            role="switch"
            :aria-checked="cfg.disclaimer"
            @click="cfg.disclaimer = !cfg.disclaimer"
          >
            <span class="knob"></span>
          </button>
        </label>

        <label class="cfg">
          <div>
            <b>新用户注册</b>
            <span>临时关闭注册用于系统维护</span>
          </div>
          <button
            class="switch"
            :class="{ on: cfg.register }"
            type="button"
            role="switch"
            :aria-checked="cfg.register"
            @click="cfg.register = !cfg.register"
          >
            <span class="knob"></span>
          </button>
        </label>
      </div>

      <button class="btn primary save" @click="saveCfg">保存配置</button>
    </article>

    <div class="two-col">
      <!-- 敏感词库 -->
      <article class="card" v-reveal="{ delay: 60 }">
        <h2 class="sec-title">敏感词库</h2>
        <p class="sec-sub">内容审核自动初筛依据，命中后进入人工审核队列</p>

        <form class="word-add" @submit.prevent="addWord">
          <input v-model.trim="newWord" type="text" placeholder="输入敏感词，回车添加" />
          <button class="btn primary sm" type="submit">添加</button>
        </form>

        <div class="word-list">
          <span v-for="(w, i) in words" :key="w" class="word">
            {{ w }}
            <button type="button" class="word-del" :aria-label="`删除 ${w}`" @click="delWord(i)">
              <AppIcon name="x" :size="12" />
            </button>
          </span>
          <span v-if="!words.length" class="empty-sm">词库为空</span>
        </div>
      </article>

      <!-- 管理员与角色 -->
      <article class="card" v-reveal="{ delay: 120 }">
        <h2 class="sec-title">管理员与角色</h2>
        <p class="sec-sub">最小权限原则：内容审核仅审核员与超管可操作</p>

        <table class="table admins">
          <thead>
            <tr><th>账号</th><th>角色</th><th>权限</th></tr>
          </thead>
          <tbody>
            <tr v-for="a in admins" :key="a.name">
              <td><b>{{ a.name }}</b></td>
              <td><span class="badge" :class="a.role === '超级管理员' ? 'ink' : 'neutral'">{{ a.role }}</span></td>
              <td class="perm">{{ a.perm }}</td>
            </tr>
          </tbody>
        </table>
        <p class="empty-sm foot-note">演示数据 · 接入后端后由账号体系接管</p>
      </article>
    </div>
  </section>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { showToast } from '@/composables/toast'

// ---- 模型配置（localStorage 持久化演示） ----
const cfg = reactive({
  confThreshold: 0.6,
  llm: 'GLM-4V（图文）',
  disclaimer: true,
  register: true
})

onMounted(() => {
  try {
    const saved = JSON.parse(localStorage.getItem('petwise_admin_cfg') || '{}')
    Object.assign(cfg, saved)
  } catch { /* 忽略损坏数据 */ }
})

function saveCfg() {
  localStorage.setItem('petwise_admin_cfg', JSON.stringify({ ...cfg }))
  showToast('配置已保存并生效', { type: 'success' })
}

// ---- 敏感词库 ----
const DEFAULT_WORDS = ['加微信', '低价药', '代刷', '私聊转账']
const words = ref([])
const newWord = ref('')

onMounted(() => {
  try {
    words.value = JSON.parse(localStorage.getItem('petwise_admin_words') || 'null') || [...DEFAULT_WORDS]
  } catch {
    words.value = [...DEFAULT_WORDS]
  }
})
function persistWords() {
  localStorage.setItem('petwise_admin_words', JSON.stringify(words.value))
}
function addWord() {
  const w = newWord.value
  if (!w) return
  if (words.value.includes(w)) {
    showToast('该词已在词库中')
    return
  }
  words.value.push(w)
  newWord.value = ''
  persistWords()
  showToast(`已添加「${w}」`, { type: 'success' })
}
function delWord(i) {
  const [w] = words.value.splice(i, 1)
  persistWords()
  showToast(`已移除「${w}」`)
}

// ---- 管理员角色（演示静态） ----
const admins = [
  { name: '平台运营', role: '超级管理员', perm: '全部模块 + 角色分配' },
  { name: '审核员·阿珂', role: '内容审核员', perm: '内容审核 + 识别复核' },
  { name: '客服·小周', role: '运营专员', perm: '用户查询（只读） + 问诊跟进' }
]
</script>

<style scoped>
.settings { display: flex; flex-direction: column; gap: 16px; }
.sec-title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 17px;
  letter-spacing: -0.01em;
}
.sec-sub { font-size: 12px; color: var(--color-faint); margin-top: 3px; }

.cfg-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 16px;
}
.cfg {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: var(--color-surface-2);
  border-radius: var(--radius-md);
  padding: 14px 16px;
  cursor: pointer;
}
.cfg b { display: block; font-size: 14px; }
.cfg span { font-size: 12px; color: var(--color-muted); }
.cfg select {
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-ink);
  background: var(--color-surface);
  border: none;
  box-shadow: inset 0 0 0 1px var(--color-border-strong);
  border-radius: var(--radius-pill);
  padding: 8px 12px;
  outline: none;
  min-width: 150px;
}

/* 开关 */
.switch {
  width: 46px;
  height: 27px;
  border-radius: 999px;
  background: var(--color-border-strong);
  position: relative;
  transition: background var(--dur-fast);
  flex-shrink: 0;
}
.switch .knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 21px;
  height: 21px;
  border-radius: 50%;
  background: #fff;
  box-shadow: var(--shadow-1);
  transition: transform var(--dur-fast) var(--ease-out);
}
.switch.on { background: var(--color-good); }
.switch.on .knob { transform: translateX(19px); }

.save { margin-top: 16px; }

.two-col {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
  align-items: start;
}

/* 敏感词 */
.word-add { display: flex; gap: 8px; margin-top: 16px; }
.word-add input {
  flex: 1;
  height: 38px;
  border-radius: var(--radius-pill);
  border: none;
  outline: none;
  background: var(--color-surface-2);
  box-shadow: inset 0 0 0 1px var(--color-border);
  padding: 0 16px;
  font: inherit;
  font-size: 13px;
}
.word-add input:focus-visible { box-shadow: inset 0 0 0 2px var(--color-accent); }
.word-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}
.word {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  background: var(--color-accent-soft);
  color: var(--color-accent-ink);
  padding: 6px 8px 6px 12px;
  border-radius: var(--radius-pill);
}
.word-del {
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  color: inherit;
  transition: background var(--dur-fast);
}
.word-del:hover { background: rgba(200, 67, 31, 0.15); }

.admins { margin-top: 16px; }
.perm { font-size: 12px; color: var(--color-muted); }
.foot-note { margin-top: 10px; }
.empty-sm { font-size: 13px; color: var(--color-faint); }

@media (max-width: 1000px) {
  .cfg-grid, .two-col { grid-template-columns: 1fr; }
}
</style>
