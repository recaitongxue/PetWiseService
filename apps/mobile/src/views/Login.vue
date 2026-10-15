<template>
  <section class="login">
    <!-- 品牌区 -->
    <header class="lg-brand">
      <div class="lg-mark"><BrandMark :show-text="false" /></div>
      <h1 class="lg-word">Petwise</h1>
      <p class="lg-slogan">登录后同步你的宠物档案、识别与问诊记录</p>
    </header>

    <!-- 登录方式切换 -->
    <div class="lg-tabs" role="tablist">
      <button
        class="lg-tab"
        :class="{ on: mode === 'code' }"
        type="button"
        role="tab"
        @click="switchMode('code')"
      >验证码登录</button>
      <button
        class="lg-tab"
        :class="{ on: mode === 'password' }"
        type="button"
        role="tab"
        @click="switchMode('password')"
      >密码登录</button>
    </div>

    <!-- 表单 -->
    <form class="lg-form" @submit.prevent="submit">
      <label class="field" :class="{ bad: errors.phone }">
        <span class="f-prefix">+86</span>
        <input
          v-model.trim="form.phone"
          class="f-control"
          type="tel"
          inputmode="numeric"
          autocomplete="tel"
          maxlength="11"
          placeholder="请输入手机号"
          @input="form.phone = form.phone.replace(/\D/g, ''); clearError('phone')"
        />
      </label>
      <p v-if="errors.phone" class="f-error">{{ errors.phone }}</p>

      <!-- 验证码：6 位分格输入（共享组件 CodeInput：自动前进 / 粘贴分发 / 退格回跳） -->
      <template v-if="mode === 'code'">
        <CodeInput ref="codeInputRef" v-model="codeDigits" :error="!!errors.code" />
        <p v-if="errors.code" class="f-error">{{ errors.code }}</p>
        <div class="code-foot">
          <button
            class="f-action"
            type="button"
            :disabled="counting || !phoneOk || sendUsed >= SMS_DAILY_MAX"
            @click="sendCode"
          >{{ counting ? `${countdown}s 后重发` : sendUsed >= SMS_DAILY_MAX ? '今日发送已达上限' : '获取验证码' }}</button>
          <span class="code-tip">验证码 5 分钟内有效 · 请勿转发他人</span>
        </div>
      </template>

      <!-- 密码 -->
      <template v-else>
        <label class="field" :class="{ bad: errors.pwd }">
          <input
            v-model="form.pwd"
            class="f-control"
            :type="showPwd ? 'text' : 'password'"
            autocomplete="current-password"
            placeholder="请输入密码"
            @input="clearError('pwd')"
          />
          <button
            class="f-icon"
            type="button"
            :aria-label="showPwd ? '隐藏密码' : '显示密码'"
            @click="showPwd = !showPwd"
          >
            <AppIcon :name="showPwd ? 'eye-off' : 'eye'" :size="18" />
          </button>
        </label>
        <p v-if="errors.pwd" class="f-error">{{ errors.pwd }}</p>
        <!-- 密码强度：引导用户设置更安全的密码 -->
        <div v-if="form.pwd" class="pwd-meter">
          <div class="pm-bars">
            <span v-for="s in 3" :key="s" class="pm-bar" :class="{ on: pwdScore >= s, [pwdLevel]: pwdScore >= s }"></span>
          </div>
          <span class="pm-label" :class="pwdLevel">{{ pwdLevelLabel }}</span>
        </div>
      </template>

      <button class="lg-submit" type="submit" :disabled="loading">
        <span v-if="!loading">登 录</span>
        <span v-else class="spinner" aria-label="登录中"></span>
      </button>
    </form>

    <!-- 协议 -->
    <label class="agree" :class="{ warn: agreeWarn }">
      <input v-model="agreed" type="checkbox" class="agree-box" />
      <span class="agree-text">
        已阅读并同意
        <button type="button" class="lnk" @click.stop="openDoc('用户协议')">《用户协议》</button>
        和
        <button type="button" class="lnk" @click.stop="openDoc('隐私政策')">《隐私政策》</button>
      </span>
    </label>

    <!-- 辅助入口 -->
    <div class="lg-aux">
      <button type="button" class="aux" @click="goRegister">注册新账号</button>
      <span class="aux-sep"></span>
      <button type="button" class="aux" @click="goReset">忘记密码</button>
    </div>

    <!-- 第三方登录 -->
    <div class="lg-third">
      <span class="third-label">其他登录方式</span>
      <button class="third-btn" type="button" @click="wechatLogin">
        <span class="third-ic"><AppIcon name="wechat" :size="20" /></span>
        微信
      </button>
    </div>

    <p class="lg-hint">演示环境：输入任意 11 位手机号，验证码填 888888 即可登录</p>
  </section>
</template>

<script setup>
import { ref, reactive, computed, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import BrandMark from '@/components/BrandMark.vue'
import CodeInput from '@/components/CodeInput.vue'
import { smsSendCount, bumpSmsSend, SMS_DAILY_MAX } from '@/api/client'
import { loginWithCode, sendSmsCode } from '@/api/data'
import { showToast } from '@/composables/toast'

const route = useRoute()
const router = useRouter()

const mode = ref('code')
const loading = ref(false)
const showPwd = ref(false)
const agreed = ref(true)
const agreeWarn = ref(false)

const form = reactive({ phone: '', code: '', pwd: '' })
const errors = reactive({ phone: '', code: '', pwd: '' })

const countdown = ref(0)
const counting = computed(() => countdown.value > 0)
let timer = null

const PHONE_RE = /^1[3-9]\d{9}$/
const phoneOk = computed(() => PHONE_RE.test(form.phone))

/* ---------- 验证码：6 位分格（共享组件 CodeInput） ---------- */

const codeDigits = ref(['', '', '', '', '', ''])
const codeInputRef = ref(null)

// 输入即清除验证码错误（与原分格实现的行为一致）
watch(codeDigits, () => {
  if (errors.code) errors.code = ''
})

function clearCode() {
  codeInputRef.value?.clear()
}

/* ---------- 验证码发送频控（ops 共享实现，账号管理页同源） ---------- */

const sendUsed = ref(smsSendCount())

function clearError(k) {
  errors[k] = ''
}

function switchMode(m) {
  mode.value = m
  errors.code = ''
  errors.pwd = ''
  clearCode()
}

async function sendCode() {
  if (!phoneOk.value) {
    errors.phone = '请输入正确的 11 位手机号'
    return
  }
  if (sendUsed.value >= SMS_DAILY_MAX) {
    showToast('今日验证码发送次数已达上限，请明天再试', { type: 'warn' })
    return
  }
  try {
    await sendSmsCode(form.phone)
    bumpSmsSend()
    sendUsed.value = smsSendCount()
    countdown.value = 60
    timer = setInterval(() => {
      countdown.value -= 1
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)
    showToast(`验证码已发送至 ${form.phone.slice(0, 3)}****${form.phone.slice(-4)}（演示验证码 888888）`, { type: 'success' })
  } catch (e) {
    showToast(e?.message || '验证码发送失败', { type: 'error' })
  }
}

function openDoc(name) {
  showToast(`《${name}》为演示占位`, { type: 'info' })
}

function goRegister() {
  showToast('注册流程为演示占位', { type: 'info' })
}

function goReset() {
  showToast('重置密码为演示占位', { type: 'info' })
}

/* ---------- 密码强度 ---------- */

const pwdScore = computed(() => {
  const p = form.pwd
  if (!p) return 0
  let s = 0
  if (p.length >= 6) s += 1
  if (p.length >= 10) s += 1
  if (/[A-Z]/.test(p) && /[a-z]/.test(p)) s += 1
  if (/\d/.test(p)) s += 1
  if (/[^A-Za-z0-9]/.test(p)) s += 1
  return Math.min(3, Math.ceil(s / 2))
})
const pwdLevel = computed(() => (['weak', 'mid', 'strong'])[pwdScore.value - 1] || 'weak')
const pwdLevelLabel = computed(() =>
  ({ weak: '强度偏弱：建议字母 + 数字 + 符号', mid: '强度中等：再加几位更安全', strong: '强度很好' })[pwdLevel.value]
)

function validate() {
  let ok = true
  if (!phoneOk.value) {
    errors.phone = '请输入正确的 11 位手机号'
    ok = false
  }
  if (mode.value === 'code') {
    form.code = codeDigits.value.join('')
    if (!/^\d{6}$/.test(form.code)) {
      errors.code = '请输入完整的 6 位数字验证码'
      ok = false
    }
  } else if (form.pwd.length < 6) {
    errors.pwd = '密码不少于 6 位'
    ok = false
  }
  return ok
}

async function submit() {
  agreeWarn.value = false
  if (!validate()) return
  if (!agreed.value) {
    agreeWarn.value = true
    showToast('请先勾选并同意用户协议', { type: 'warn' })
    return
  }
  if (mode.value === 'password') {
    showToast('演示环境仅支持验证码登录', { type: 'warn' })
    return
  }
  loading.value = true
  try {
    await loginWithCode(form.phone, form.code)
    showToast(`欢迎回来，${form.phone.slice(0, 3)}****${form.phone.slice(-4)}`, { type: 'success' })
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/home'
    router.replace(redirect)
  } catch (e) {
    showToast(e?.message || '登录失败，请重试', { type: 'error' })
  } finally {
    loading.value = false
  }
}

function wechatLogin() {
  if (!agreed.value) {
    agreeWarn.value = true
    showToast('请先勾选并同意用户协议', { type: 'warn' })
    return
  }
  showToast('微信授权为演示占位，请先用手机号登录', { type: 'info' })
}

onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.login {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  padding: 12px 24px 28px;
}

/* ---------- 品牌区 ---------- */
.lg-brand { text-align: center; padding: 18px 0 26px; }
.lg-mark { width: 62px; height: 62px; margin: 0 auto 14px; }
.lg-word {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 34px;
  letter-spacing: -0.03em;
  line-height: 1;
}
.lg-slogan {
  margin-top: 10px;
  font-size: 13px;
  color: var(--color-muted);
  line-height: 1.6;
}

/* ---------- 方式切换 ---------- */
.lg-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  border-radius: var(--radius-pill);
  background: var(--color-surface-2);
  margin-bottom: 22px;
}
.lg-tab {
  flex: 1;
  padding: 10px 0;
  border-radius: var(--radius-pill);
  font-size: 14px;
  font-weight: 700;
  color: var(--color-muted);
  transition: all var(--dur-fast) var(--ease-out);
}
.lg-tab.on {
  color: var(--color-ink);
  background: var(--color-surface);
  box-shadow: var(--shadow-soft);
}

/* ---------- 表单 ---------- */
.lg-form { display: flex; flex-direction: column; gap: 14px; }
.field {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 52px;
  padding: 0 14px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--hairline-strong);
  transition: border-color var(--dur-fast) var(--ease-out);
}
.field:focus-within { border-color: var(--color-accent); }
.field.bad { border-color: var(--color-alert); }
.f-prefix {
  font-size: 15px;
  font-weight: 700;
  color: var(--color-ink);
  padding-right: 10px;
  border-right: 1px solid var(--hairline);
  flex-shrink: 0;
}
.f-control {
  flex: 1;
  min-width: 0;
  border: none;
  background: none;
  font: inherit;
  font-size: 15px;
  color: var(--color-ink);
}
.f-control::placeholder { color: var(--color-faint); }
.f-control:focus { outline: none; }
.f-action {
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-accent-ink);
  padding: 6px 2px;
}
.f-action:disabled { color: var(--color-faint); }
.f-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: var(--color-muted);
}
.f-icon:active { background: var(--color-surface-2); }
.f-error {
  margin-top: -8px;
  font-size: 12px;
  color: var(--color-alert);
  padding-left: 2px;
}

/* ---------- 验证码 6 位分格 ---------- */
.code-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: -6px;
}
.code-tip { font-size: 11px; color: var(--color-faint); }

/* ---------- 密码强度 ---------- */
.pwd-meter {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: -4px;
}
.pm-bars { display: flex; gap: 5px; flex: 1; }
.pm-bar {
  flex: 1;
  height: 4px;
  border-radius: 999px;
  background: var(--color-surface-2);
  transition: background var(--dur-fast);
}
.pm-bar.on.weak { background: var(--color-alert); }
.pm-bar.on.mid { background: var(--color-watch); }
.pm-bar.on.strong { background: var(--color-good); }
.pm-label { font-size: 11px; font-weight: 700; color: var(--color-faint); flex-shrink: 0; }
.pm-label.weak { color: var(--color-alert); }
.pm-label.mid { color: var(--color-watch); }
.pm-label.strong { color: var(--color-good); }

.lg-submit {
  height: 52px;
  margin-top: 4px;
  border-radius: var(--radius-pill);
  background: var(--color-ink);
  color: var(--color-surface);
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.08em;
  display: grid;
  place-items: center;
  transition: transform var(--dur-fast) var(--ease-out);
}
.lg-submit:active { transform: scale(0.978); }
.lg-submit:disabled { opacity: 0.7; }
.spinner {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid rgba(251, 246, 236, 0.35);
  border-top-color: var(--color-surface);
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ---------- 协议 ---------- */
.agree {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 16px;
  padding: 2px;
}
.agree.warn .agree-text { color: var(--color-alert); }
.agree-box {
  width: 16px;
  height: 16px;
  margin: 3px 0 0;
  accent-color: var(--color-accent);
  flex-shrink: 0;
}
.agree-text { font-size: 12px; color: var(--color-muted); line-height: 1.6; }
.lnk { font-size: 12px; font-weight: 700; color: var(--color-accent-ink); }

/* ---------- 辅助入口 ---------- */
.lg-aux {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  margin-top: 20px;
}
.aux { font-size: 13px; font-weight: 700; color: var(--color-muted); }
.aux:active { color: var(--color-ink); }
.aux-sep { width: 1px; height: 12px; background: var(--hairline-strong); }

/* ---------- 第三方 ---------- */
.lg-third {
  margin-top: auto;
  padding-top: 28px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}
.third-label {
  position: relative;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--color-faint);
}
.third-btn {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-muted);
}
.third-ic {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  box-shadow: var(--shadow-soft);
  color: var(--color-good);
  transition: transform var(--dur-fast) var(--ease-out);
}
.third-btn:active .third-ic { transform: scale(0.94); }

.lg-hint {
  margin-top: 14px;
  text-align: center;
  font-size: 11px;
  color: var(--color-faint);
}
</style>
