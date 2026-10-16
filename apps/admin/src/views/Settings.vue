<template>
  <section class="settings">
    <!-- 模型与服务配置 -->
    <article class="card" v-reveal>
      <h2 class="sec-title">模型与服务配置</h2>
      <p class="sec-sub">用户端识别与问诊所依赖的 AI 服务参数（保存后即时生效，写入后端平台设置）</p>

      <div class="cfg-grid">
        <label class="cfg">
          <div>
            <b>每日 AI 免费额度</b>
            <span>每用户每天可免费调用识别 / 问诊的次数</span>
          </div>
          <select v-model.number="settings.aiDailyFree">
            <option :value="1">1 次</option>
            <option :value="3">3 次</option>
            <option :value="5">5 次</option>
            <option :value="10">10 次</option>
          </select>
        </label>

        <label class="cfg">
          <div>
            <b>维护公告</b>
            <span>留空表示当前无公告，填写后 App 端首屏提示</span>
          </div>
          <input v-model.trim="settings.maintenanceNotice" type="text" placeholder="例：今晚 23:00 例行维护" />
        </label>

        <label class="cfg">
          <div>
            <b>在线问诊</b>
            <span>关闭后用户端无法发起新的问诊单</span>
          </div>
          <button
            class="switch"
            :class="{ on: settings.consultEnabled }"
            type="button"
            role="switch"
            :aria-checked="settings.consultEnabled"
            @click="settings.consultEnabled = !settings.consultEnabled"
          >
            <span class="knob"></span>
          </button>
        </label>

        <label class="cfg">
          <div>
            <b>社区功能</b>
            <span>临时关闭社区用于内容治理</span>
          </div>
          <button
            class="switch"
            :class="{ on: settings.communityEnabled }"
            type="button"
            role="switch"
            :aria-checked="settings.communityEnabled"
            @click="settings.communityEnabled = !settings.communityEnabled"
          >
            <span class="knob"></span>
          </button>
        </label>

        <label class="cfg">
          <div>
            <b>品种识别</b>
            <span>关闭后用户端拍照识别入口置灰</span>
          </div>
          <button
            class="switch"
            :class="{ on: settings.recognizeEnabled }"
            type="button"
            role="switch"
            :aria-checked="settings.recognizeEnabled"
            @click="settings.recognizeEnabled = !settings.recognizeEnabled"
          >
            <span class="knob"></span>
          </button>
        </label>

        <label class="cfg">
          <div>
            <b>公告自动发布</b>
            <span>运营新建公告后免审核直接发布</span>
          </div>
          <button
            class="switch"
            :class="{ on: settings.autoPublishAnnouncement }"
            type="button"
            role="switch"
            :aria-checked="settings.autoPublishAnnouncement"
            @click="settings.autoPublishAnnouncement = !settings.autoPublishAnnouncement"
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
import { adminApi } from '@/api'
import { showToast } from '@shared/toast'

// ---- 平台配置：后端 GET /admin/settings + PUT /admin/settings ----
const settings = reactive({
  aiDailyFree: 3,
  consultEnabled: true,
  communityEnabled: true,
  recognizeEnabled: true,
  autoPublishAnnouncement: false,
  maintenanceNotice: ''
})

// 载入时的基线快照，保存时只提交与快照不同的键
let baseline = { ...settings }

onMounted(async () => {
  try {
    const data = await adminApi.settings()
    Object.assign(settings, data || {})
  } catch (e) {
    showToast(e?.message || '平台设置加载失败', { type: 'warn' })
  }
  baseline = { ...settings }
})

async function saveCfg() {
  const patch = {}
  Object.keys(settings).forEach((k) => {
    if (settings[k] !== baseline[k]) patch[k] = settings[k]
  })
  if (!Object.keys(patch).length) {
    showToast('没有需要保存的修改')
    return
  }
  try {
    const merged = await adminApi.updateSettings(patch)
    Object.assign(settings, merged || {})
    baseline = { ...settings }
    showToast('配置已保存并生效', { type: 'success' })
  } catch (e) {
    showToast(e?.message || '配置保存失败', { type: 'warn' })
  }
}

// ---- 敏感词库（后端暂无词库接口，仅保存在当前会话，刷新即还原） ----
const DEFAULT_WORDS = ['加微信', '低价药', '代刷', '私聊转账']
const words = ref([...DEFAULT_WORDS])
const newWord = ref('')

function addWord() {
  const w = newWord.value
  if (!w) return
  if (words.value.includes(w)) {
    showToast('该词已在词库中')
    return
  }
  words.value.push(w)
  newWord.value = ''
  showToast(`已添加「${w}」`, { type: 'success' })
}
function delWord(i) {
  const [w] = words.value.splice(i, 1)
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
.cfg select,
.cfg input {
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
.cfg input { font-weight: 400; min-width: 180px; }

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
