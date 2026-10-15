<template>
  <section class="screen profile">
    <header class="screen-head" v-reveal>
      <div>
        <p class="eyebrow">PROFILE</p>
        <h1 class="title">我的</h1>
      </div>
      <button class="icon-btn" type="button" aria-label="设置">
        <AppIcon name="bell" :size="22" />
      </button>
    </header>

    <!-- 用户卡 -->
    <article class="user-card" v-reveal="{ delay: 80 }">
      <span class="user-avatar">{{ user.initials }}</span>
      <div class="user-info">
        <h2 class="user-name">{{ user.name }}</h2>
        <p class="user-handle">{{ maskedPhone }}</p>
        <p class="user-bio">{{ user.bio }}</p>
      </div>
      <button class="edit-btn" type="button" @click="openEdit">编辑</button>
    </article>

    <div class="stats" v-reveal="{ delay: 120 }">
      <div class="stat">
        <b class="num">{{ pets.length }}</b><span>宠物</span>
      </div>
      <div class="stat">
        <b class="num">{{ user.followers }}</b><span>粉丝</span>
      </div>
      <div class="stat">
        <b class="num">{{ user.following }}</b><span>关注</span>
      </div>
    </div>

    <!-- 我的宠物 -->
    <section class="block" v-reveal="{ delay: 160 }">
      <div class="block-head">
        <h3 class="block-title">我的宠物</h3>
        <router-link to="/recognize" class="block-hint">＋ 添加</router-link>
      </div>
      <div class="pet-grid">
        <router-link v-for="p in pets" :key="p.id" :to="`/pet/${p.id}`" class="pet-tile">
          <PetAvatar :species="p.species" :name="p.name" :size="56" />
          <div class="pet-tile-info">
            <span class="pet-tile-name">{{ p.name }}</span>
            <span class="pet-tile-breed">{{ p.breed }}</span>
          </div>
          <span class="pet-tile-score num">{{ p.healthScore }}</span>
        </router-link>
      </div>
    </section>

    <!-- 功能菜单 -->
    <section class="block" v-reveal="{ delay: 200 }">
      <div class="menu">
        <button class="menu-row" type="button" @click="openWallet">
          <span class="menu-ic sage"><AppIcon name="wallet" :size="20" /></span>
          <span class="menu-label">我的钱包</span>
          <span class="menu-balance num">¥{{ walletInfo.balance.toFixed(2) }}</span>
          <AppIcon name="back" :size="16" class="menu-arrow" />
        </button>
        <router-link to="/account" class="menu-row">
          <span class="menu-ic coral"><AppIcon name="shield" :size="20" /></span>
          <span class="menu-label">账号管理</span>
          <span class="menu-badge num">安全 · 隐私 · 注销</span>
          <AppIcon name="back" :size="16" class="menu-arrow" />
        </router-link>
        <router-link to="/community" class="menu-row">
          <span class="menu-ic peach"><AppIcon name="paw" :size="20" /></span>
          <span class="menu-label">我的社区主页</span>
          <span class="menu-badge num">{{ user.followers }} 粉丝</span>
          <AppIcon name="back" :size="16" class="menu-arrow" />
        </router-link>
        <router-link to="/records" class="menu-row">
          <span class="menu-ic sage"><AppIcon name="stethoscope" :size="20" /></span>
          <span class="menu-label">问诊记录</span>
          <span class="menu-badge num">{{ consultRecords.length }}</span>
          <AppIcon name="back" :size="16" class="menu-arrow" />
        </router-link>
        <router-link to="/favorites" class="menu-row">
          <span class="menu-ic peach"><AppIcon name="bookmark" :size="20" /></span>
          <span class="menu-label">我的收藏</span>
          <span class="menu-badge num">{{ favorites.length + customFavCount }}</span>
          <AppIcon name="back" :size="16" class="menu-arrow" />
        </router-link>
        <router-link to="/schedule" class="menu-row">
          <span class="menu-ic sand"><AppIcon name="calendar" :size="20" /></span>
          <span class="menu-label">提醒与日程</span>
          <AppIcon name="back" :size="16" class="menu-arrow" />
        </router-link>
        <button class="menu-row" type="button" @click="clearCache">
          <span class="menu-ic ink"><AppIcon name="refresh" :size="20" /></span>
          <span class="menu-label">清除本地缓存</span>
          <span class="menu-badge num">{{ cacheSize }}</span>
          <AppIcon name="back" :size="16" class="menu-arrow" />
        </button>
        <button class="menu-row" type="button" @click="fbOpen = true">
          <span class="menu-ic coral"><AppIcon name="comment" :size="20" /></span>
          <span class="menu-label">意见反馈</span>
          <AppIcon name="back" :size="16" class="menu-arrow" />
        </button>
        <button class="menu-row" type="button" @click="aboutPetwise">
          <span class="menu-ic ink"><AppIcon name="sparkle" :size="20" /></span>
          <span class="menu-label">关于 Petwise</span>
          <AppIcon name="back" :size="16" class="menu-arrow" />
        </button>
      </div>

      <button class="logout" type="button" @click="onLogout">
        <AppIcon name="logout" :size="17" />
        退出登录
      </button>
    </section>

    <p class="version">Petwise v0.1 · 计算机视觉 × 大模型</p>

    <!-- 意见反馈弹层 -->
    <transition name="sheet">
      <div v-if="fbOpen" class="sheet-mask" @click.self="fbOpen = false">
        <div class="sheet">
          <div class="sheet-grip" aria-hidden="true"></div>
          <h3 class="sheet-title">意见反馈</h3>
          <p class="sheet-sub">你的建议会直达运营团队，处理后可在管理端看到状态</p>
          <div class="type-chips">
            <button
              v-for="t in fbTypes"
              :key="t.value"
              type="button"
              class="type-chip"
              :class="{ on: fbType === t.value }"
              @click="fbType = t.value"
            >{{ t.label }}</button>
          </div>
          <textarea v-model="fbText" class="fb-input" rows="4" placeholder="说说你遇到的问题或想加的功能…"></textarea>
          <button class="fb-submit" type="button" :disabled="!fbText.trim()" @click="sendFeedback">
            提交反馈
          </button>
        </div>
      </div>
    </transition>

    <!-- 钱包弹层 -->
    <transition name="sheet">
      <div v-if="walletOpen" class="sheet-mask" @click.self="walletOpen = false">
        <div class="sheet tall">
          <div class="sheet-grip" aria-hidden="true"></div>
          <div class="w-card">
            <span class="w-label">账户余额（元）</span>
            <b class="w-balance num">{{ walletInfo.balance.toFixed(2) }}</b>
            <span class="w-note">可用于问诊付费与商城消费</span>
          </div>
          <div class="w-actions">
            <button
              v-for="amt in rechargeAmounts"
              :key="amt"
              class="w-amt"
              type="button"
              @click="recharge(amt)"
            >充 {{ amt }}</button>
          </div>
          <h4 class="w-h">交易明细</h4>
          <div v-if="walletInfo.txns.length" class="w-list">
            <div v-for="t in walletInfo.txns" :key="t.id" class="w-row">
              <span class="w-ic" :class="t.type"><AppIcon :name="t.type === 'recharge' ? 'plus' : 'back'" :size="14" /></span>
              <div class="w-row-body">
                <b>{{ t.note }}</b>
                <span class="num">{{ t.time }}</span>
              </div>
              <span class="w-amt-num num" :class="t.type">{{ t.type === 'recharge' ? '+' : '-' }}{{ t.amount.toFixed(2) }}</span>
            </div>
          </div>
          <p v-else class="w-empty">暂无交易记录</p>
          <button class="fb-submit ghost" type="button" @click="withdraw">提现到微信</button>
        </div>
      </div>
    </transition>

    <!-- 编辑资料弹层 -->
    <transition name="sheet">
      <div v-if="editOpen" class="sheet-mask" @click.self="editOpen = false">
        <div class="sheet">
          <div class="sheet-grip" aria-hidden="true"></div>
          <h3 class="sheet-title">编辑资料</h3>
          <p class="sheet-sub">昵称与简介展示在社区主页</p>
          <label class="f-field">
            <span>昵称</span>
            <input v-model="editForm.name" class="f-input" type="text" maxlength="12" placeholder="怎么称呼你" />
          </label>
          <label class="f-field mt">
            <span>简介</span>
            <input v-model="editForm.bio" class="f-input" type="text" maxlength="30" placeholder="一句话介绍自己" />
          </label>
          <button class="fb-submit" type="button" :disabled="!editForm.name.trim()" @click="submitEdit">保存</button>
        </div>
      </div>
    </transition>
  </section>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import PetAvatar from '@/components/PetAvatar.vue'
import { useRouter } from 'vue-router'
import { user, pets, consultRecords, favorites } from '@/data/mock'
import { submitFeedback, logout, getAuth, wallet, walletTransact, customFavorites } from '@/data/ops'
import { showToast } from '@/composables/toast'

const router = useRouter()

/* ---------- 钱包 ---------- */

const walletOpen = ref(false)
const walletInfo = ref(wallet())
const rechargeAmounts = [30, 50, 100, 200]

function openWallet() {
  walletInfo.value = wallet()
  walletOpen.value = true
}
function recharge(amt) {
  walletInfo.value = walletTransact(amt, '余额充值')
  showToast(`充值 ¥${amt} 成功`, { type: 'success' })
}
function withdraw() {
  if (walletInfo.value.balance <= 0) {
    showToast('余额不足，先充一笔', { type: 'info' })
    return
  }
  const all = walletInfo.value.balance
  walletInfo.value = walletTransact(-all, '提现到微信')
  showToast(`已提现 ¥${all.toFixed(2)} 到微信`, { type: 'success' })
}

/* ---------- 编辑资料 ---------- */

const editOpen = ref(false)
const editForm = reactive({ name: user.name, bio: user.bio })

function openEdit() {
  editForm.name = user.name
  editForm.bio = user.bio
  editOpen.value = true
}
function submitEdit() {
  user.name = editForm.name.trim() || user.name
  user.bio = editForm.bio.trim()
  editOpen.value = false
  showToast('资料已更新', { type: 'success' })
}

/* ---------- 清除缓存 ---------- */

const customFavCount = computed(() => customFavorites().length)

const cacheSize = computed(() => {
  let bytes = 0
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i)
      if (k && k.startsWith('petwise_')) bytes += (localStorage.getItem(k) || '').length
    }
  } catch (e) { /* ignore */ }
  return bytes > 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${bytes} B`
})

function clearCache() {
  const keys = []
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i)
      if (k && k.startsWith('petwise_') && k !== 'petwise_auth') keys.push(k)
    }
  } catch (e) { /* ignore */ }
  keys.forEach((k) => localStorage.removeItem(k))
  showToast(`已清除 ${keys.length} 项本地数据（保留登录态）`, { type: 'success' })
}

/* ---------- 意见反馈 ---------- */

const fbOpen = ref(false)
const fbType = ref('suggestion')
const fbText = ref('')
const fbTypes = [
  { value: 'bug', label: '遇到问题' },
  { value: 'suggestion', label: '功能建议' },
  { value: 'other', label: '其他' }
]

function sendFeedback() {
  if (!fbText.value.trim()) return
  submitFeedback({ user: user.name, type: fbType.value, text: fbText.value.trim() })
  fbText.value = ''
  fbOpen.value = false
  showToast('反馈已提交，感谢你的建议', { type: 'success' })
}

function aboutPetwise() {
  showToast('Petwise v0.1 · 计算机视觉 × 大模型', { type: 'info' })
}

// 用户卡展示当前登录手机号（脱敏）
const authPhone = getAuth()?.phone || ''
const maskedPhone = authPhone
  ? `${authPhone.slice(0, 3)}****${authPhone.slice(-4)}`
  : user.handle

// 退出登录：清登录态后回到登录页，并禁止返回上一个已登录页面
function onLogout() {
  logout()
  showToast('已退出登录')
  router.replace('/login')
}
</script>

<style scoped>
.title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: var(--fs-2xl);
  letter-spacing: -0.02em;
  line-height: 1;
}
.icon-btn {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-ink);
}
.user-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 18px;
  box-shadow: var(--shadow-1);
}
.user-avatar {
  width: 60px;
  height: 60px;
  border-radius: 30%;
  display: grid;
  place-items: center;
  font-size: 32px;
  background: linear-gradient(150deg, #f6e7d3, #e7d3b8);
  flex-shrink: 0;
}
.user-info { flex: 1; min-width: 0; }
.user-name { font-family: var(--font-display); font-weight: 700; font-size: var(--fs-lg); }
.user-handle { font-size: 13px; color: var(--color-muted); }
.user-bio { font-size: 13px; color: var(--color-ink-2); margin-top: 4px; }
.edit-btn {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-ink);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-pill);
  padding: 7px 16px;
}
.stats {
  display: flex;
  margin: 16px 0 4px;
  gap: 10px;
}
.stat {
  flex: 1;
  text-align: center;
  background: var(--color-surface-2);
  border-radius: var(--radius-md);
  padding: 14px 0;
}
.stat b { display: block; font-family: var(--font-display); font-size: var(--fs-xl); line-height: 1; }
.stat span { font-size: 12px; color: var(--color-muted); }

.block { margin-top: 28px; }
.block-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 14px;
}
.block-title { font-family: var(--font-display); font-weight: 700; font-size: var(--fs-lg); }
.block-hint { font-size: 13px; font-weight: 700; color: var(--color-accent-ink); }

.pet-grid { display: flex; flex-direction: column; gap: 12px; }
.pet-tile {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  transition: transform var(--dur-fast) var(--ease-out);
}
.pet-tile:active { transform: scale(0.98); }
.pet-tile-info { flex: 1; display: flex; flex-direction: column; }
.pet-tile-name { font-weight: 700; font-size: 16px; }
.pet-tile-breed { font-size: 13px; color: var(--color-muted); }
.pet-tile-score {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 22px;
  color: var(--color-good);
}

.menu {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}
.menu-row {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  padding: 16px;
  border-bottom: 1px solid var(--color-border);
  transition: background var(--dur-fast);
}
.menu-row:last-child { border-bottom: none; }
.menu-row:active { background: var(--color-surface-2); }
.menu-ic {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  color: #fff;
}
.menu-ic.sage { background: var(--color-sage); }
.menu-ic.peach { background: var(--color-peach); }
.menu-ic.sand { background: var(--color-sand); color: var(--color-ink); }
.menu-ic.ink { background: var(--color-ink); }
.menu-ic.coral { background: var(--color-accent); }

/* ---------- 意见反馈弹层 ---------- */
.sheet-mask {
  position: fixed;
  inset: 0;
  z-index: 60;
  background: rgba(27, 42, 34, 0.4);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: flex-end;
}
.sheet {
  width: 100%;
  background: var(--color-surface);
  border-radius: 28px 28px 0 0;
  padding: 14px 22px calc(22px + env(safe-area-inset-bottom));
}
.sheet-grip {
  width: 40px;
  height: 4px;
  border-radius: 2px;
  background: var(--color-border-strong);
  margin: 0 auto 16px;
}
.sheet-title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: var(--fs-lg);
}
.sheet-sub {
  font-size: 12.5px;
  color: var(--color-muted);
  margin-top: 4px;
}
.type-chips { display: flex; gap: 8px; margin: 16px 0 12px; }
.type-chip {
  padding: 8px 16px;
  border-radius: var(--radius-pill);
  font-size: 13px;
  font-weight: 700;
  color: var(--color-muted);
  box-shadow: inset 0 0 0 1px var(--color-border);
  transition: all var(--dur-fast) var(--ease-out);
}
.type-chip.on {
  color: var(--color-accent-ink);
  background: var(--color-accent-soft);
  box-shadow: inset 0 0 0 1px transparent;
}
.fb-input {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 12px 14px;
  font-size: 14px;
  font-family: inherit;
  background: var(--color-surface-2);
  color: var(--color-ink);
  resize: none;
}
.fb-submit {
  margin-top: 14px;
  width: 100%;
  height: 50px;
  border-radius: 18px;
  background: var(--color-accent);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.04em;
  box-shadow: 0 10px 24px rgba(232, 85, 43, 0.28);
}
.fb-submit:disabled {
  background: var(--color-border-strong);
  box-shadow: none;
  color: var(--color-faint);
}
.sheet-enter-active,
.sheet-leave-active { transition: opacity var(--dur-base) var(--ease-out); }
.sheet-enter-active .sheet,
.sheet-leave-active .sheet { transition: transform var(--dur-base) var(--ease-out); }
.sheet-enter-from,
.sheet-leave-to { opacity: 0; }
.sheet-enter-from .sheet,
.sheet-leave-to .sheet { transform: translateY(40%); }
.menu-label { flex: 1; text-align: left; font-weight: 700; font-size: 15px; }
.menu-balance {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-accent-ink);
  padding-right: 4px;
}

/* ---------- 钱包 ---------- */
.sheet.tall { max-height: 84dvh; overflow-y: auto; }
.w-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 20px 18px;
  border-radius: var(--radius-lg);
  background: linear-gradient(140deg, var(--color-ink), #2e4a3c);
  color: #fff;
}
.w-label { font-size: 12px; opacity: 0.75; }
.w-balance {
  font-family: var(--font-display);
  font-size: 34px;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.1;
}
.w-note { font-size: 11px; opacity: 0.6; }
.w-actions {
  display: flex;
  gap: 8px;
  margin-top: 14px;
}
.w-amt {
  flex: 1;
  padding: 12px 0;
  border-radius: var(--radius-md);
  background: var(--color-accent-soft);
  border: 1px solid color-mix(in srgb, var(--color-accent) 25%, transparent);
  color: var(--color-accent-ink);
  font-size: 14px;
  font-weight: 700;
  transition: transform var(--dur-fast) var(--ease-out);
}
.w-amt:active { transform: scale(0.95); }
.w-h {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-muted);
  margin: 20px 0 10px;
}
.w-list { display: flex; flex-direction: column; gap: 2px; }
.w-row {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 12px 2px;
  border-bottom: 1px solid var(--hairline);
}
.w-row:last-child { border-bottom: none; }
.w-ic {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  background: var(--color-sage-soft);
  color: var(--color-good);
}
.w-ic.withdraw { background: var(--color-surface-2); color: var(--color-muted); transform: rotate(180deg); }
.w-row-body { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.w-row-body b { font-size: 14px; }
.w-row-body span { font-size: 11px; color: var(--color-faint); }
.w-amt-num { font-size: 15px; font-weight: 700; color: var(--color-good); }
.w-amt-num.withdraw { color: var(--color-muted); }
.w-empty {
  text-align: center;
  font-size: 13px;
  color: var(--color-faint);
  padding: 22px 0;
}

/* ---------- 表单（改密 / 编辑资料） ---------- */
.f-field { display: flex; flex-direction: column; gap: 6px; }
.f-field.mt { margin-top: 12px; }
.f-field span { font-size: 12px; font-weight: 700; color: var(--color-muted); }
.f-input {
  width: 100%;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--hairline-strong);
  background: var(--color-bg);
  font: inherit;
  font-size: 15px;
  color: var(--color-ink);
  outline: none;
}
.f-input:focus { outline: 2px solid var(--color-accent); outline-offset: -1px; }
.f-error {
  margin-top: 10px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--color-alert);
}
.fb-submit.ghost {
  margin-top: 16px;
  background: var(--color-surface-2);
  color: var(--color-ink);
  box-shadow: none;
}

/* 退出登录：与菜单分离，弱化但不隐藏 */
.logout {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  width: 100%;
  margin-top: 14px;
  padding: 13px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  font-size: 14px;
  font-weight: 700;
  color: var(--color-accent-ink);
  transition: transform var(--dur-fast) var(--ease-out);
}
.logout:active { transform: scale(0.978); }
/* 菜单右侧计数：弱化处理，避免制造"未读红点"式的焦虑感 */
.menu-badge {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-faint);
  padding-right: 4px;
}
.menu-arrow { color: var(--color-muted); transform: rotate(180deg); opacity: 0.5; }

.version {
  text-align: center;
  font-size: 12px;
  color: var(--color-faint);
  margin-top: 32px;
  letter-spacing: 0.04em;
}
</style>
