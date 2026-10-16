<template>
  <section class="screen account">
    <!-- 头部：返回 + 标题 -->
    <header class="acc-head" v-reveal>
      <button class="back" type="button" aria-label="返回" @click="router.back()">
        <AppIcon name="back" :size="22" />
      </button>
      <div>
        <p class="eyebrow">ACCOUNT</p>
        <h1 class="title">账号管理</h1>
      </div>
    </header>

    <!-- 账号概览卡：安全等级一眼可见 -->
    <article class="acc-card" v-reveal="{ delay: 60 }">
      <span class="acc-ava">{{ user.initials }}</span>
      <div class="acc-info">
        <h2 class="acc-name">{{ user.name }}</h2>
        <p class="acc-phone num">{{ maskedPhone }}</p>
      </div>
      <span class="acc-level" :class="secLevel.cls">
        <AppIcon name="shield" :size="13" />{{ secLevel.label }}
      </span>
    </article>

    <!-- 账号与安全 -->
    <section class="group" v-reveal="{ delay: 100 }">
      <h2 class="group-t">账号与安全</h2>
      <div class="rows">
        <button class="row" type="button" @click="openPhone">
          <span class="row-ic sage"><AppIcon name="phone" :size="18" /></span>
          <span class="row-label">手机号</span>
          <span class="row-value num">{{ maskedPhone }}</span>
          <AppIcon name="back" :size="15" class="row-arrow" />
        </button>
        <button class="row" type="button" @click="openPwd">
          <span class="row-ic coral"><AppIcon name="eye-off" :size="18" /></span>
          <span class="row-label">登录密码</span>
          <span class="row-value">已设置</span>
          <AppIcon name="back" :size="15" class="row-arrow" />
        </button>
      </div>
    </section>

    <!-- 账号绑定 -->
    <section class="group" v-reveal="{ delay: 130 }">
      <h2 class="group-t">账号绑定</h2>
      <div class="rows">
        <button class="row" type="button" @click="toggleBind('wechat')">
          <span class="row-ic ok"><AppIcon name="wechat" :size="18" /></span>
          <span class="row-label">微信</span>
          <span class="row-value" :class="{ ok: prefs.binds.wechat }">
            {{ prefs.binds.wechat ? '已绑定' : '未绑定' }}
          </span>
          <span class="switch" :class="{ on: prefs.binds.wechat }" role="switch" :aria-checked="prefs.binds.wechat"></span>
        </button>
        <button class="row" type="button" @click="toggleBind('apple')">
          <span class="row-ic ink"><AppIcon name="award" :size="18" /></span>
          <span class="row-label">Apple ID</span>
          <span class="row-value" :class="{ ok: prefs.binds.apple }">
            {{ prefs.binds.apple ? '已绑定' : '未绑定' }}
          </span>
          <span class="switch" :class="{ on: prefs.binds.apple }" role="switch" :aria-checked="prefs.binds.apple"></span>
        </button>
      </div>
      <p class="group-note">绑定后可用于一键登录；解绑不影响账号本身使用</p>
    </section>

    <!-- 隐私管理 -->
    <section class="group" v-reveal="{ delay: 160 }">
      <h2 class="group-t">隐私管理</h2>
      <div class="rows">
        <button class="row" type="button" @click="togglePersonalized">
          <span class="row-ic sage"><AppIcon name="sparkle" :size="18" /></span>
          <span class="row-label">个性化推荐</span>
          <span class="switch" :class="{ on: prefs.personalized }" role="switch" :aria-checked="prefs.personalized"></span>
        </button>
        <button class="row" type="button" @click="visOpen = true">
          <span class="row-ic peach"><AppIcon name="eye" :size="18" /></span>
          <span class="row-label">社区动态可见范围</span>
          <span class="row-value">{{ visibilityLabel }}</span>
          <AppIcon name="back" :size="15" class="row-arrow" />
        </button>
        <button class="row" type="button" @click="openBlacklist">
          <span class="row-ic coral"><AppIcon name="ban" :size="18" /></span>
          <span class="row-label">黑名单管理</span>
          <span class="row-value num">{{ blocked.length }} 人</span>
          <AppIcon name="back" :size="15" class="row-arrow" />
        </button>
        <button class="row" type="button" @click="collectOpen = true">
          <span class="row-ic sand"><AppIcon name="file" :size="18" /></span>
          <span class="row-label">个人信息收集清单</span>
          <AppIcon name="back" :size="15" class="row-arrow" />
        </button>
      </div>
      <p class="group-note">关闭个性化推荐后，社区内容将按热度而非你的兴趣展示</p>
    </section>

    <!-- 危险区：注销账号（主流 App 均置于设置末端，红色警示） -->
    <section class="group danger" v-reveal="{ delay: 220 }">
      <div class="rows">
        <button class="row danger-row" type="button" @click="delStep = 1">
          <span class="row-ic danger"><AppIcon name="alert" :size="18" /></span>
          <span class="row-label">注销账号</span>
          <span class="row-value">数据不可恢复</span>
          <AppIcon name="back" :size="15" class="row-arrow" />
        </button>
      </div>
      <p class="group-note">注销将清空全部个人数据且不可恢复，请谨慎操作</p>
    </section>

    <p class="version">Petwise v1.0 · 账号数据存储于服务端，注销后不可恢复</p>

    <!-- ================= 弹层：更换手机号 ================= -->
    <transition name="sheet">
      <div v-if="phoneOpen" class="sheet-mask" @click.self="phoneOpen = false">
        <div class="sheet">
          <div class="sheet-grip" aria-hidden="true"></div>
          <h3 class="sheet-title">更换手机号</h3>
          <p class="sheet-sub">当前手机号 {{ maskedPhone }}，更换后需使用新手机号登录</p>
          <label class="f-field">
            <span>新手机号</span>
            <input
              v-model="phoneForm.phone"
              class="f-input"
              type="tel"
              inputmode="numeric"
              maxlength="11"
              placeholder="请输入新手机号"
              @input="phoneForm.phone = phoneForm.phone.replace(/\D/g, '')"
            />
          </label>
          <div class="mt">
            <CodeInput v-model="phoneForm.code" :error="!!phoneError" />
          </div>
          <div class="code-foot">
            <button
              class="f-action"
              type="button"
              :disabled="phoneCounting || !phoneOk || phoneSendUsed >= SMS_DAILY_MAX"
              @click="sendPhoneCode"
            >{{ phoneCounting ? `${phoneCountdown}s 后重发` : phoneSendUsed >= SMS_DAILY_MAX ? '今日发送已达上限' : '获取验证码' }}</button>
            <span class="code-tip">验证码 5 分钟内有效 · 请勿转发他人</span>
          </div>
          <p v-if="phoneError" class="f-error">{{ phoneError }}</p>
          <button class="fb-submit" type="button" @click="submitPhone">确认更换</button>
        </div>
      </div>
    </transition>

    <!-- ================= 弹层：修改密码（自「我的」页迁入，全站唯一实现） ================= -->
    <transition name="sheet">
      <div v-if="pwdOpen" class="sheet-mask" @click.self="pwdOpen = false">
        <div class="sheet">
          <div class="sheet-grip" aria-hidden="true"></div>
          <h3 class="sheet-title">修改密码</h3>
          <p class="sheet-sub">为保护账号安全，新密码至少 6 位，建议字母 + 数字组合</p>
          <label class="f-field">
            <span>当前密码</span>
            <input v-model="pwd.old" class="f-input" type="password" placeholder="请输入当前密码" />
          </label>
          <label class="f-field mt">
            <span>新密码</span>
            <input v-model="pwd.n1" class="f-input" type="password" placeholder="至少 6 位" />
          </label>
          <label class="f-field mt">
            <span>确认新密码</span>
            <input v-model="pwd.n2" class="f-input" type="password" placeholder="再输一次新密码" />
          </label>
          <p v-if="pwdError" class="f-error">{{ pwdError }}</p>
          <button class="fb-submit" type="button" @click="submitPwd">确认修改</button>
        </div>
      </div>
    </transition>

    <!-- ================= 弹层：可见范围 ================= -->
    <transition name="sheet">
      <div v-if="visOpen" class="sheet-mask" @click.self="visOpen = false">
        <div class="sheet">
          <div class="sheet-grip" aria-hidden="true"></div>
          <h3 class="sheet-title">社区动态可见范围</h3>
          <p class="sheet-sub">谁可以看到你发布的社区动态</p>
          <button
            v-for="v in visibilityOptions"
            :key="v.value"
            class="pick-row"
            type="button"
            :class="{ on: prefs.visibility === v.value }"
            @click="setVisibility(v.value)"
          >
            <span class="pick-label">{{ v.label }}</span>
            <span class="pick-desc">{{ v.desc }}</span>
            <AppIcon v-if="prefs.visibility === v.value" name="check" :size="18" class="pick-check" />
          </button>
        </div>
      </div>
    </transition>

    <!-- ================= 弹层：黑名单 ================= -->
    <transition name="sheet">
      <div v-if="blOpen" class="sheet-mask" @click.self="blOpen = false">
        <div class="sheet">
          <div class="sheet-grip" aria-hidden="true"></div>
          <h3 class="sheet-title">黑名单管理</h3>
          <p class="sheet-sub">被拉黑的用户将无法关注你、评论或私信你</p>
          <div class="bl-list">
            <div v-for="u in blocked" :key="u.id" class="bl-row">
              <span class="bl-ava">{{ u.name.slice(0, 1) }}</span>
              <div class="bl-info">
                <b>{{ u.name }}</b>
              </div>
              <button class="bl-out" type="button" @click="unblock(u)">解除</button>
            </div>
            <p v-if="!blocked.length" class="bl-empty">黑名单空空如也，世界真美好</p>
          </div>
        </div>
      </div>
    </transition>

    <!-- ================= 弹层：个人信息收集清单 ================= -->
    <transition name="sheet">
      <div v-if="collectOpen" class="sheet-mask" @click.self="collectOpen = false">
        <div class="sheet">
          <div class="sheet-grip" aria-hidden="true"></div>
          <h3 class="sheet-title">个人信息收集清单</h3>
          <p class="sheet-sub">依据《个人信息保护法》向你公示收集的信息与用途</p>
          <ul class="collect-list">
            <li v-for="c in collectList" :key="c.name">
              <AppIcon name="check" :size="14" />
              <div>
                <b>{{ c.name }}</b>
                <span>{{ c.use }}</span>
              </div>
            </li>
          </ul>
          <p class="collect-foot">以上数据仅存储于本机（演示环境），卸载应用即彻底删除</p>
        </div>
      </div>
    </transition>

    <!-- ================= 注销流程：全屏四步 ================= -->
    <transition name="fade">
      <div v-if="delStep" class="del-mask">
        <div class="del-page">
          <header class="del-head">
            <button v-if="delStep > 1" class="back" type="button" aria-label="上一步" @click="delStep -= 1">
              <AppIcon name="back" :size="22" />
            </button>
            <button v-else class="back" type="button" aria-label="关闭" @click="closeDelete">
              <AppIcon name="x" :size="22" />
            </button>
            <div class="del-head-t">
              <h2>注销账号</h2>
              <span class="del-steps num">步骤 {{ delStep }} / 3</span>
            </div>
          </header>

          <div class="del-body">
            <!-- 步骤 1：条件检查（余额与进行中问诊单均为真实数据） -->
            <template v-if="delStep === 1">
              <p class="del-lead">注销前需要满足以下条件（与主流平台一致）：</p>
              <div class="chk-list">
                <div v-for="c in deleteChecks" :key="c.label" class="chk" :class="{ ok: c.ok }">
                  <span class="chk-ic"><AppIcon :name="c.ok ? 'check' : 'alert'" :size="15" /></span>
                  <div class="chk-body">
                    <b>{{ c.label }}</b>
                    <span v-if="!c.ok">{{ c.hint }}</span>
                  </div>
                  <button v-if="!c.ok" class="chk-fix" type="button" @click="fixCheck(c)">去处理</button>
                </div>
              </div>
              <button class="chk-confirm" type="button" :class="{ on: backupConfirmed }" @click="backupConfirmed = !backupConfirmed">
                <span class="chk-box"><AppIcon v-if="backupConfirmed" name="check" :size="13" /></span>
                重要数据已备份（问诊报告、宠物档案建议先导出）
              </button>
            </template>

            <!-- 步骤 2：风险明示 + 原因 -->
            <template v-else-if="delStep === 2">
              <div class="risk-card">
                <p class="risk-title"><AppIcon name="alert" :size="16" />注销后以下数据将立即永久删除，无法恢复</p>
                <ul class="risk-list">
                  <li v-for="r in riskItems" :key="r">{{ r }}</li>
                </ul>
              </div>
              <p class="del-lead">注销原因（帮助我们改进）：</p>
              <div class="reason-chips">
                <button
                  v-for="r in deleteReasons"
                  :key="r"
                  class="reason-chip"
                  type="button"
                  :class="{ on: delReason === r }"
                  @click="delReason = r"
                >{{ r }}</button>
              </div>
              <button class="chk-confirm" type="button" :class="{ on: riskAgreed }" @click="riskAgreed = !riskAgreed">
                <span class="chk-box"><AppIcon v-if="riskAgreed" name="check" :size="13" /></span>
                我已了解上述风险，仍要注销账号
              </button>
            </template>

            <!-- 步骤 3：最终确认（服务端即时删除，不可恢复） -->
            <template v-else-if="delStep === 3">
              <div class="risk-card">
                <p class="risk-title"><AppIcon name="alert" :size="16" />最后确认</p>
                <ul class="risk-list">
                  <li>账号 {{ maskedPhone }} 及全部个人数据将被立即删除</li>
                  <li>删除后无法恢复，也无法用该手机号重新注册找回数据</li>
                  <li>如仅想暂时停用，可直接退出登录</li>
                </ul>
              </div>
              <p v-if="delError" class="f-error">{{ delError }}</p>
            </template>

            <!-- 完成：账号已注销 -->
            <template v-else>
              <div class="done-wrap">
                <span class="done-ic"><AppIcon name="check" :size="34" /></span>
                <h3 class="done-title">账号已注销</h3>
                <p class="done-sub">全部个人数据已删除，感谢你曾经使用 Petwise</p>
              </div>
            </template>
          </div>

          <!-- 底部主操作 -->
          <footer class="del-foot">
            <button
              v-if="delStep === 1"
              class="del-btn"
              type="button"
              :disabled="!deleteReady"
              @click="delStep = 2"
            >下一步</button>
            <button
              v-else-if="delStep === 2"
              class="del-btn"
              type="button"
              :disabled="!riskAgreed"
              @click="delStep = 3"
            >下一步</button>
            <button
              v-else-if="delStep === 3"
              class="del-btn danger"
              type="button"
              :disabled="delSubmitting"
              @click="submitDelete"
            >{{ delSubmitting ? '注销中…' : '确认注销（不可恢复）' }}</button>
            <button v-else class="del-btn" type="button" @click="finishDelete">退出登录</button>
          </footer>
        </div>
      </div>
    </transition>
  </section>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'
import CodeInput from '@/components/CodeInput.vue'
import {
  fetchUser, fetchConsultOrders, logoutUser, smsSendCount, bumpSmsSend, SMS_DAILY_MAX,
  sendSmsCode, fetchPreferences, savePreferences, fetchBlocked, removeBlocked,
  changePassword, changePhone, setBinding, deactivateAccount
} from '@/api/data'
import { getCachedUser } from '@/api/client'
import { showToast } from '@shared/toast'

const router = useRouter()

/* ---------- 账号概览 ---------- */

const EMPTY_USER = { name: '', initials: '', handle: '', phone: '', balance: 0 }

const user = ref({ ...EMPTY_USER })
const orders = ref([])

onMounted(async () => {
  try {
    const [u, os] = await Promise.all([fetchUser(), fetchConsultOrders()])
    user.value = u || { ...EMPTY_USER }
    orders.value = Array.isArray(os) ? os : os?.list || []
  } catch (e) {
    showToast(e?.message || '账号信息加载失败', { type: 'error' })
  }
  loadPrefs()
  // 黑名单计数（列表打开时再拉全量）
  fetchBlocked()
    .then((r) => { blocked.value = r?.list || [] })
    .catch(() => { /* 静默：打开弹层时会重试 */ })
})

const cachedPhone = ref(getCachedUser()?.phone || '')
const maskedPhone = computed(() => {
  const p = user.value.phone || cachedPhone.value
  return p ? `${p.slice(0, 3)}****${p.slice(-4)}` : ''
})
const secLevel = computed(() => {
  // 演示：按绑定与偏好给一个粗略的安全等级
  const score = (prefs.value.binds.wechat ? 1 : 0) + (prefs.value.binds.apple ? 1 : 0) + 1
  if (score >= 3) return { label: '安全等级：高', cls: 'high' }
  if (score === 2) return { label: '安全等级：中', cls: 'mid' }
  return { label: '安全等级：低', cls: 'low' }
})

/* ---------- 隐私与绑定偏好（真实接口：GET/PUT /users/preferences） ---------- */

const DEFAULT_PREFS = {
  personalized: true,
  visibility: 'public', // public / followers / private
  binds: { wechat: true, apple: false }
}
const prefs = ref({ ...DEFAULT_PREFS })

const visibilityOptions = [
  { value: 'public', label: '公开', desc: '所有人可见你的社区动态' },
  { value: 'followers', label: '仅关注者', desc: '只有关注你的人可见' },
  { value: 'private', label: '仅自己', desc: '动态仅自己可见' }
]
const visibilityLabel = computed(
  () => visibilityOptions.find((v) => v.value === prefs.value.visibility)?.label || '公开'
)

async function loadPrefs() {
  try {
    const p = await fetchPreferences()
    prefs.value = {
      personalized: p.personalized ?? DEFAULT_PREFS.personalized,
      visibility: p.visibility || DEFAULT_PREFS.visibility,
      binds: { ...DEFAULT_PREFS.binds, ...(p.binds || {}) }
    }
  } catch (e) {
    showToast(e?.message || '偏好加载失败', { type: 'error' })
  }
}

async function togglePersonalized() {
  const next = !prefs.value.personalized
  try {
    const p = await savePreferences({ personalized: next })
    prefs.value = { ...prefs.value, personalized: p.personalized ?? next }
    showToast(next ? '已开启个性化推荐' : '已关闭个性化推荐，内容将按热度展示')
  } catch (e) {
    showToast(e?.message || '设置失败', { type: 'error' })
  }
}
async function setVisibility(v) {
  try {
    const p = await savePreferences({ visibility: v })
    prefs.value = { ...prefs.value, visibility: p.visibility || v }
    visOpen.value = false
    showToast('可见范围已更新')
  } catch (e) {
    showToast(e?.message || '设置失败', { type: 'error' })
  }
}
async function toggleBind(kind) {
  const bound = !prefs.value.binds[kind]
  try {
    const p = await setBinding(kind, { bound })
    prefs.value = { ...prefs.value, binds: { ...prefs.value.binds, ...(p.binds || { [kind]: bound }) } }
    const name = kind === 'wechat' ? '微信' : 'Apple ID'
    showToast(bound ? `已绑定${name}` : `已解绑${name}`)
  } catch (e) {
    showToast(e?.message || '操作失败', { type: 'error' })
  }
}

/* ---------- 黑名单（真实接口：GET/POST/DELETE /users/blocked） ---------- */

const blOpen = ref(false)
const visOpen = ref(false)
const collectOpen = ref(false)
const blocked = ref([])
async function openBlacklist() {
  blOpen.value = true
  try {
    const r = await fetchBlocked()
    blocked.value = r?.list || []
  } catch (e) {
    showToast(e?.message || '黑名单加载失败', { type: 'error' })
  }
}
async function unblock(u) {
  try {
    const r = await removeBlocked(u.id)
    blocked.value = r?.list || []
    showToast(`已解除「${u.name}」的拉黑`, { type: 'success' })
  } catch (e) {
    showToast(e?.message || '操作失败', { type: 'error' })
  }
}

/* ---------- 更换手机号 ---------- */

const PHONE_RE = /^1[3-9]\d{9}$/
const phoneOpen = ref(false)
const phoneForm = reactive({ phone: '', code: ['', '', '', '', '', ''] })
const phoneError = ref('')
const phoneCountdown = ref(0)
const phoneSendUsed = ref(smsSendCount())
let phoneTimer = null
const phoneOk = computed(() => PHONE_RE.test(phoneForm.phone))
const phoneCounting = computed(() => phoneCountdown.value > 0)

function openPhone() {
  phoneForm.phone = ''
  phoneForm.code = ['', '', '', '', '', '']
  phoneError.value = ''
  phoneOpen.value = true
}
async function sendPhoneCode() {
  if (!phoneOk.value) {
    phoneError.value = '请输入正确的 11 位手机号'
    return
  }
  if (phoneSendUsed.value >= SMS_DAILY_MAX) {
    showToast('今日验证码发送次数已达上限，请明天再试', { type: 'warn' })
    return
  }
  try {
    await sendSmsCode(phoneForm.phone, 'rebind')
    phoneSendUsed.value = bumpSmsSend()
    phoneCountdown.value = 60
    phoneTimer = setInterval(() => {
      phoneCountdown.value -= 1
      if (phoneCountdown.value <= 0) clearInterval(phoneTimer)
    }, 1000)
    showToast(`验证码已发送至 ${phoneForm.phone.slice(0, 3)}****${phoneForm.phone.slice(-4)}`, { type: 'success' })
  } catch (e) {
    showToast(e?.message || '验证码发送失败', { type: 'error' })
  }
}
async function submitPhone() {
  phoneError.value = ''
  if (!phoneOk.value) {
    phoneError.value = '请输入正确的 11 位手机号'
    return
  }
  if (phoneForm.code.join('').length < 6) {
    phoneError.value = '请输入 6 位验证码'
    return
  }
  try {
    const u = await changePhone({ phone: phoneForm.phone, code: phoneForm.code.join('') })
    user.value = { ...user.value, ...(u || {}) }
    phoneOpen.value = false
    showToast('手机号已更换，请使用新手机号登录', { type: 'success' })
  } catch (e) {
    phoneError.value = e?.message || '更换失败，请重试'
  }
}

/* ---------- 修改密码（自 Profile.vue 迁入，全站唯一实现） ---------- */

const pwdOpen = ref(false)
const pwdError = ref('')
const pwd = reactive({ old: '', n1: '', n2: '' })

function openPwd() {
  pwd.old = ''
  pwd.n1 = ''
  pwd.n2 = ''
  pwdError.value = ''
  pwdOpen.value = true
}
async function submitPwd() {
  pwdError.value = ''
  if (pwd.old.length < 6) {
    pwdError.value = '请输入当前密码（至少 6 位）'
    return
  }
  if (pwd.n1.length < 6) {
    pwdError.value = '新密码至少 6 位'
    return
  }
  if (pwd.n1 !== pwd.n2) {
    pwdError.value = '两次输入的新密码不一致'
    return
  }
  if (pwd.n1 === pwd.old) {
    pwdError.value = '新密码不能与当前密码相同'
    return
  }
  try {
    await changePassword({ oldPassword: pwd.old, newPassword: pwd.n1 })
    pwdOpen.value = false
    showToast('密码已修改，请牢记新密码', { type: 'success' })
  } catch (e) {
    pwdError.value = e?.message || '修改失败，请重试'
  }
}

/* ---------- 注销流程 ---------- */

const collectList = [
  { name: '账号信息', use: '手机号、昵称、头像，用于登录与身份识别' },
  { name: '宠物档案', use: '品种、年龄、体重、健康记录，用于生成养护建议' },
  { name: '问诊数据', use: '主诉、分诊结论、处方，用于问诊连续性与复盘' },
  { name: '社区内容', use: '发布的动态、评论、点赞，用于社区展示' },
  { name: '设备信息', use: '机型与系统版本，用于故障排查与安全防护' }
]
const riskItems = [
  '宠物档案与全部健康记录',
  '问诊报告、处方与聊天记录',
  '社区动态、评论与点赞',
  '收藏、日程提醒与备忘录',
  '钱包余额与交易流水',
  '账号本身（删除后无法登录）'
]
const deleteReasons = ['不再需要养宠记录', '体验不符合预期', '担心隐私安全', '找到了替代产品', '想换个账号重新开始', '其他原因']

const delStep = ref(0)
const delReason = ref('')
const delSubmitting = ref(false)
const delError = ref('')
const backupConfirmed = ref(false)
const riskAgreed = ref(false)

const deleteChecks = computed(() => {
  const bal = Number(user.value.balance) || 0
  const activeOrders = orders.value.filter((o) => o.state !== 'closed')
  return [
    { label: '账号状态正常，无安全风险', ok: true, hint: '', fix: null },
    {
      label: '钱包余额已清零',
      ok: bal <= 0,
      hint: `当前余额 ¥${bal.toFixed(2)}，请先提现`,
      fix: 'wallet'
    },
    {
      label: '无进行中的问诊单',
      ok: activeOrders.length === 0,
      hint: `还有 ${activeOrders.length} 单问诊未结束`,
      fix: 'orders'
    }
  ]
})
const deleteReady = computed(() => deleteChecks.value.every((c) => c.ok) && backupConfirmed.value)

function closeDelete() {
  delStep.value = 0
  delReason.value = ''
  delError.value = ''
  backupConfirmed.value = false
  riskAgreed.value = false
}

function fixCheck(c) {
  if (c.fix === 'wallet') {
    closeDelete()
    showToast('请先到「我的 → 我的钱包」完成提现', { type: 'info' })
    router.push('/profile')
  } else if (c.fix === 'orders') {
    closeDelete()
    showToast('请先结束进行中的问诊单', { type: 'info' })
    router.push('/records')
  }
}

async function submitDelete() {
  delError.value = ''
  delSubmitting.value = true
  try {
    await deactivateAccount({ reason: delReason.value })
    delStep.value = 4
    showToast('账号已注销', { type: 'success' })
  } catch (e) {
    delError.value = e?.message || '注销失败，请稍后再试'
  } finally {
    delSubmitting.value = false
  }
}

// 清除本机账号数据（注销后退出登录用）：清除所有 petwise_ 前缀的本地键
function clearLocalAccountData() {
  const removed = []
  try {
    for (let i = localStorage.length - 1; i >= 0; i--) {
      const k = localStorage.key(i)
      if (k && k.startsWith('petwise_')) {
        removed.push(k)
        localStorage.removeItem(k)
      }
    }
  } catch (e) { /* ignore */ }
  return removed
}
</script>

<style scoped>
/* ---------- 头部 ---------- */
.acc-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 10px 0 18px;
}
.back {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-ink);
  flex-shrink: 0;
}
.back:active { transform: scale(0.94); }
.title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: var(--fs-2xl);
  letter-spacing: -0.02em;
  line-height: 1;
  margin-top: 4px;
}

/* ---------- 账号概览卡 ---------- */
.acc-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  box-shadow: var(--shadow-soft);
}
.acc-ava {
  width: 52px;
  height: 52px;
  border-radius: 30%;
  display: grid;
  place-items: center;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 21px;
  color: #fff;
  background: var(--grad-ink);
  flex-shrink: 0;
}
.acc-info { flex: 1; min-width: 0; }
.acc-name { font-size: 17px; font-weight: 700; }
.acc-phone { font-size: 13px; color: var(--color-muted); margin-top: 3px; }
.acc-level {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  padding: 5px 10px;
  border-radius: var(--radius-pill);
  flex-shrink: 0;
}
.acc-level.high { background: var(--color-sage-soft); color: var(--color-good); }
.acc-level.mid { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.acc-level.low { background: var(--color-surface-2); color: var(--color-muted); }

/* ---------- 分组行 ---------- */
.group { margin-top: 22px; }
.group-t {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 0.04em;
  color: var(--color-muted);
  margin-bottom: 8px;
  padding-left: 2px;
}
.group-note {
  font-size: 11.5px;
  color: var(--color-faint);
  line-height: 1.6;
  margin-top: 8px;
  padding-left: 2px;
}
.rows {
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
  box-shadow: var(--shadow-soft);
  overflow: hidden;
}
.row {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 14px;
  text-align: left;
  transition: background var(--dur-fast);
}
.row + .row, .row.device + .row.device { border-top: 1px solid var(--hairline); }
.row:active { background: var(--color-surface-2); }
.row-ic {
  width: 34px;
  height: 34px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  background: var(--color-sage-soft);
  color: var(--color-good);
}
.row-ic.coral { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.row-ic.sand { background: var(--color-sand); color: var(--color-ink); }
.row-ic.ink { background: var(--color-ink); color: var(--color-surface); }
.row-ic.peach { background: var(--color-peach); color: var(--color-ink); }
.row-ic.ok { background: var(--color-sage-soft); color: var(--color-good); }
.row-ic.danger { background: var(--color-accent-soft); color: var(--color-accent-ink); }
.row-label { flex: 1; min-width: 0; font-weight: 700; font-size: 14.5px; }
.row-label small {
  display: block;
  font-weight: 600;
  font-size: 11.5px;
  color: var(--color-faint);
  margin-top: 2px;
}
.row-value { font-size: 12.5px; color: var(--color-muted); flex-shrink: 0; }
.row-value.ok { color: var(--color-good); font-weight: 700; }
.row-arrow { color: var(--color-faint); transform: rotate(180deg); flex-shrink: 0; }

/* 开关 */
.switch {
  width: 46px;
  height: 27px;
  border-radius: 999px;
  background: var(--color-border-strong);
  position: relative;
  flex-shrink: 0;
  transition: background var(--dur-fast) var(--ease-out);
}
.switch::after {
  content: '';
  position: absolute;
  top: 2.5px;
  left: 2.5px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 4px rgba(27, 42, 34, 0.25);
  transition: transform var(--dur-fast) var(--ease-out);
}
.switch.on { background: var(--color-good); }
.switch.on::after { transform: translateX(19px); }

/* 设备下线按钮 */
.device-out {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-accent-ink);
  padding: 7px 12px;
  border-radius: var(--radius-pill);
  background: var(--color-accent-soft);
  flex-shrink: 0;
}
.device-out:active { transform: scale(0.95); }

/* 危险区 */
.group.danger .rows { border-color: rgba(200, 67, 31, 0.22); }
.danger-row .row-label { color: var(--color-accent-ink); }

/* ---------- 弹层（与 Profile 一致的底部 Sheet） ---------- */
.sheet-mask {
  position: fixed;
  inset: 0;
  z-index: 60;
  background: rgba(27, 42, 34, 0.4);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.sheet {
  width: min(var(--shell-max), 100%);
  max-height: 86%;
  overflow-y: auto;
  background: var(--color-bg);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  padding: 10px 20px calc(24px + env(safe-area-inset-bottom, 0px));
}
.sheet-grip {
  width: 40px;
  height: 4px;
  border-radius: 999px;
  background: var(--color-border-strong);
  margin: 0 auto 14px;
}
.sheet-title { font-family: var(--font-display); font-size: var(--fs-lg); font-weight: 700; }
.sheet-sub { font-size: 12.5px; color: var(--color-muted); margin-top: 6px; line-height: 1.6; }
.mt { margin-top: 14px; }

.f-field { display: block; margin-top: 14px; }
.f-field > span {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-muted);
  margin-bottom: 6px;
}
.f-input {
  width: 100%;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: 12px 14px;
  font: inherit;
  font-size: 15px;
  color: var(--color-ink);
  outline: none;
}
.f-input:focus { border-color: var(--color-accent); }
.f-error { font-size: 12px; color: var(--color-alert); margin-top: 10px; }
.f-action {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-accent-ink);
  padding: 8px 2px;
}
.f-action:disabled { color: var(--color-faint); }
.code-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 10px;
}
.code-tip { font-size: 11px; color: var(--color-faint); }
.fb-submit {
  width: 100%;
  margin-top: 18px;
  padding: 14px;
  border-radius: var(--radius-md);
  background: var(--grad-ink);
  color: var(--color-surface);
  font-weight: 700;
  font-size: 15px;
}
.fb-submit:active { transform: scale(0.978); }
.fb-submit:disabled { opacity: 0.5; }

/* 可见范围选项 */
.pick-row {
  display: block;
  width: 100%;
  text-align: left;
  padding: 14px 2px;
  border-bottom: 1px solid var(--hairline);
  position: relative;
}
.pick-row:last-child { border-bottom: none; }
.pick-label { font-weight: 700; font-size: 15px; display: block; }
.pick-desc { font-size: 12px; color: var(--color-muted); display: block; margin-top: 3px; }
.pick-check { position: absolute; right: 2px; top: 18px; color: var(--color-accent-ink); }

/* 黑名单 */
.bl-list { margin-top: 6px; }
.bl-row { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--hairline); }
.bl-row:last-child { border-bottom: none; }
.bl-ava {
  width: 40px;
  height: 40px;
  border-radius: 30%;
  display: grid;
  place-items: center;
  font-weight: 700;
  background: var(--color-sand);
  flex-shrink: 0;
}
.bl-info { flex: 1; min-width: 0; }
.bl-info b { font-size: 14.5px; display: block; }
.bl-info span { font-size: 11.5px; color: var(--color-muted); display: block; margin-top: 2px; }
.bl-out {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-accent-ink);
  padding: 7px 12px;
  border-radius: var(--radius-pill);
  background: var(--color-accent-soft);
  flex-shrink: 0;
}
.bl-out:active { transform: scale(0.95); }
.bl-empty { text-align: center; color: var(--color-muted); font-size: 13px; padding: 24px 0; }

/* 收集清单 */
.collect-list { list-style: none; margin-top: 8px; }
.collect-list li {
  display: flex;
  gap: 10px;
  padding: 12px 0;
  border-bottom: 1px solid var(--hairline);
  color: var(--color-good);
}
.collect-list li:last-child { border-bottom: none; }
.collect-list b { font-size: 14px; color: var(--color-ink); display: block; }
.collect-list span { font-size: 12px; color: var(--color-muted); display: block; margin-top: 2px; line-height: 1.6; }
.collect-foot { font-size: 11.5px; color: var(--color-faint); margin-top: 12px; line-height: 1.6; }

/* ---------- 注销流程（全屏） ---------- */
.del-mask {
  position: fixed;
  inset: 0;
  z-index: 80;
  background: var(--color-bg);
  display: flex;
  justify-content: center;
}
.del-page {
  width: min(var(--shell-max), 100%);
  height: 100%;
  display: flex;
  flex-direction: column;
}
.del-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: calc(14px + env(safe-area-inset-top, 0px)) 20px 12px;
  border-bottom: 1px solid var(--hairline);
  background: var(--color-surface);
}
.del-head-t { flex: 1; display: flex; align-items: baseline; justify-content: space-between; }
.del-head-t h2 { font-family: var(--font-display); font-size: var(--fs-lg); font-weight: 700; }
.del-steps { font-size: 11px; font-weight: 700; color: var(--color-faint); letter-spacing: 0.08em; }

.del-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.del-lead { font-size: 13.5px; color: var(--color-ink-2); line-height: 1.7; margin-bottom: 14px; }

/* 步骤 1：条件检查 */
.chk-list { display: flex; flex-direction: column; gap: 10px; }
.chk {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 13px 14px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
}
.chk-ic {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  background: var(--color-accent-soft);
  color: var(--color-accent-ink);
}
.chk.ok .chk-ic { background: var(--color-sage-soft); color: var(--color-good); }
.chk-body { flex: 1; min-width: 0; }
.chk-body b { font-size: 14px; display: block; }
.chk-body span { font-size: 11.5px; color: var(--color-accent-ink); display: block; margin-top: 2px; }
.chk-fix {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-accent-ink);
  padding: 7px 12px;
  border-radius: var(--radius-pill);
  background: var(--color-accent-soft);
  flex-shrink: 0;
}
.chk-fix:active { transform: scale(0.95); }
.chk-confirm {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  margin-top: 16px;
  padding: 13px 14px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px dashed var(--hairline-strong);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-muted);
  text-align: left;
  line-height: 1.5;
}
.chk-box {
  width: 20px;
  height: 20px;
  border-radius: 6px;
  border: 1.5px solid var(--color-border-strong);
  display: grid;
  place-items: center;
  flex-shrink: 0;
  color: #fff;
}
.chk-confirm.on { border-style: solid; border-color: var(--color-good); color: var(--color-ink); }
.chk-confirm.on .chk-box { background: var(--color-good); border-color: var(--color-good); }

/* 步骤 2：风险明示 */
.risk-card {
  border-radius: var(--radius-md);
  background: var(--color-accent-soft);
  border: 1px solid rgba(200, 67, 31, 0.25);
  padding: 14px;
}
.risk-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13.5px;
  font-weight: 700;
  color: var(--color-accent-ink);
}
.risk-list { list-style: none; margin-top: 10px; }
.risk-list li {
  font-size: 12.5px;
  color: var(--color-accent-ink);
  line-height: 1.9;
  padding-left: 14px;
  position: relative;
}
.risk-list li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 10px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--color-accent);
}
.reason-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.reason-chip {
  font-size: 12.5px;
  font-weight: 600;
  padding: 8px 13px;
  border-radius: var(--radius-pill);
  background: var(--color-surface);
  box-shadow: inset 0 0 0 1px var(--color-border);
  color: var(--color-muted);
}
.reason-chip.on {
  color: var(--color-accent-ink);
  background: var(--color-accent-soft);
  box-shadow: inset 0 0 0 1px transparent;
}

/* 步骤 3：验证 */
.cool-tip {
  display: flex;
  gap: 8px;
  margin-top: 18px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  background: var(--color-sage-soft);
  color: var(--color-ink-2);
  font-size: 12.5px;
  line-height: 1.7;
}
.cool-tip svg { color: var(--color-good); flex-shrink: 0; margin-top: 2px; }
.cool-tip b { color: var(--color-good); }

/* 步骤 4：完成 */
.done-wrap { text-align: center; padding-top: 24px; }
.done-ic {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  margin: 0 auto 16px;
  background: var(--color-sage-soft);
  color: var(--color-good);
}
.done-title { font-family: var(--font-display); font-size: var(--fs-xl); font-weight: 700; }
.done-sub { font-size: 13px; color: var(--color-muted); margin-top: 8px; }
.cool-card {
  margin-top: 20px;
  text-align: left;
  padding: 16px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--hairline);
}
.cool-card p { font-size: 12.5px; color: var(--color-ink-2); line-height: 2; }
.cool-card p:first-child { color: var(--color-ink); font-size: 13px; }

/* 底部主操作 */
.del-foot {
  flex-shrink: 0;
  display: flex;
  gap: 10px;
  padding: 12px 20px calc(16px + env(safe-area-inset-bottom, 0px));
  border-top: 1px solid var(--hairline);
  background: var(--color-surface);
}
.del-btn {
  flex: 1;
  padding: 14px;
  border-radius: var(--radius-md);
  background: var(--grad-ink);
  color: var(--color-surface);
  font-weight: 700;
  font-size: 15px;
}
.del-btn:active { transform: scale(0.978); }
.del-btn:disabled { opacity: 0.45; }
.del-btn.ghost {
  background: var(--color-surface-2);
  color: var(--color-ink);
  box-shadow: inset 0 0 0 1px var(--color-border);
}
.del-btn.danger { background: linear-gradient(150deg, var(--color-accent), var(--color-accent-ink)); }

.version {
  text-align: center;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--color-faint);
  margin-top: 26px;
}

/* 弹层动画（与全站 sheet 一致） */
.sheet-enter-active,
.sheet-leave-active { transition: opacity var(--dur-base) var(--ease-out); }
.sheet-enter-active .sheet,
.sheet-leave-active .sheet { transition: transform var(--dur-base) var(--ease-out); }
.sheet-enter-from,
.sheet-leave-to { opacity: 0; }
.sheet-enter-from .sheet,
.sheet-leave-to .sheet { transform: translateY(24px); }
.fade-enter-active,
.fade-leave-active { transition: opacity var(--dur-base) var(--ease-out); }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
</style>
