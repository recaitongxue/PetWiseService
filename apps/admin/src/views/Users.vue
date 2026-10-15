<template>
  <section>
    <!-- 双 Tab：普通用户 / 兽医账号 -->
    <div class="tabs" v-reveal>
      <button class="tab" :class="{ on: tab === 'users' }" @click="tab = 'users'">
        <AppIcon name="users" :size="15" /> 普通用户
        <span class="tab-num num">{{ allUsers.length }}</span>
      </button>
      <button class="tab" :class="{ on: tab === 'doctors' }" @click="tab = 'doctors'">
        <AppIcon name="stethoscope" :size="15" /> 兽医账号
        <span class="tab-num num">{{ allDoctors.length }}</span>
      </button>
      <button class="btn sm primary add-btn" @click="openCreate">
        <AppIcon name="plus" :size="14" /> 新增{{ tab === 'users' ? '用户' : '兽医' }}
      </button>
    </div>

    <!-- ============ 普通用户 ============ -->
    <template v-if="tab === 'users'">
      <div class="toolbar" v-reveal>
        <label class="search">
          <AppIcon name="search" :size="16" />
          <input v-model.trim="kw" type="search" placeholder="搜索昵称 / 手机号…" />
        </label>
        <div class="filters">
          <button class="btn sm" :class="{ ghost: f !== 'all', primary: f === 'all' }" @click="f = 'all'">全部</button>
          <button class="btn sm" :class="{ ghost: f !== 'active', primary: f === 'active' }" @click="f = 'active'">正常</button>
          <button class="btn sm" :class="{ ghost: f !== 'frozen', primary: f === 'frozen' }" @click="f = 'frozen'">已冻结</button>
        </div>
      </div>

      <article class="card" v-reveal="{ delay: 60 }">
        <table class="table">
          <thead>
            <tr>
              <th>用户</th><th>手机号</th><th>宠物数</th><th>注册时间</th><th>来源</th><th>状态</th><th class="ta-r">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in list" :key="u.id">
              <td>
                <div class="cell-user">
                  <span class="u-ava">{{ u.name.slice(0, 1) }}</span>
                  <div>
                    <b>{{ u.name }}</b>
                    <span v-if="u.role" class="u-role">{{ u.role }}</span>
                  </div>
                </div>
              </td>
              <td class="num">{{ u.phone }}</td>
              <td class="num">{{ petCount(u.name) }}</td>
              <td class="num">{{ u.joined }}</td>
              <td>
                <span class="badge" :class="u.custom ? 'ink' : 'neutral'">
                  {{ u.custom ? '管理端新增' : 'App 注册' }}
                </span>
              </td>
              <td>
                <span class="badge" :class="u.state === 'active' ? 'good' : 'neutral'">
                  {{ u.state === 'active' ? '正常' : '已冻结' }}
                </span>
              </td>
              <td class="ta-r">
                <div class="row-actions">
                  <button class="btn sm ghost" @click="openDetail(u)">详情</button>
                  <button class="btn sm" :class="u.state === 'active' ? 'danger' : 'primary'" @click="toggle(u)">
                    {{ u.state === 'active' ? '冻结' : '恢复' }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!list.length" class="empty">没有匹配的用户</p>
      </article>
    </template>

    <!-- ============ 兽医账号 ============ -->
    <template v-else>
      <div class="toolbar" v-reveal>
        <label class="search">
          <AppIcon name="search" :size="16" />
          <input v-model.trim="dkw" type="search" placeholder="搜索姓名 / 医院 / 科室…" />
        </label>
        <div class="filters">
          <button class="btn sm" :class="{ ghost: df !== 'all', primary: df === 'all' }" @click="df = 'all'">全部科室</button>
          <button class="btn sm" :class="{ ghost: df !== 'online', primary: df === 'online' }" @click="df = 'online'">在线接诊</button>
          <button class="btn sm" :class="{ ghost: df !== 'frozen', primary: df === 'frozen' }" @click="df = 'frozen'">已冻结</button>
        </div>
      </div>

      <div class="doc-grid" v-reveal="{ delay: 60 }">
        <article v-for="d in docList" :key="d.id" class="card doc" :class="{ off: d.state !== 'active' }">
          <header class="doc-head">
            <span class="d-ava"><AppIcon name="stethoscope" :size="20" /></span>
            <div class="doc-id">
              <b>{{ d.name }}</b>
              <span class="d-dept">{{ d.dept }} · {{ d.hospital }}</span>
            </div>
            <span class="badge" :class="d.state === 'active' ? 'good' : 'neutral'">
              {{ d.state === 'active' ? (d.online ? '在线接诊' : '离线') : '已冻结' }}
            </span>
          </header>
          <dl class="doc-meta">
            <div><dt>电话</dt><dd class="num">{{ d.phone }}</dd></div>
            <div><dt>累计问诊</dt><dd class="num">{{ d.consults }}</dd></div>
            <div><dt>评分</dt><dd class="num">{{ d.rating.toFixed(1) }}</dd></div>
            <div><dt>入驻</dt><dd class="num">{{ d.joined }}</dd></div>
          </dl>
          <footer class="doc-foot">
            <button class="btn sm ghost" @click="toggleOnline(d)">
              <AppIcon name="refresh" :size="13" /> {{ d.online ? '设为离线' : '设为在线' }}
            </button>
            <button class="btn sm" :class="d.state === 'active' ? 'danger' : 'primary'" @click="toggleDoc(d)">
              {{ d.state === 'active' ? '冻结' : '恢复' }}
            </button>
            <button class="btn sm ghost" @click="removeDoc(d)">
              <AppIcon name="ban" :size="13" /> 删除
            </button>
          </footer>
        </article>
      </div>
      <p v-if="!docList.length" class="empty">没有匹配的兽医账号</p>
    </template>

    <!-- ============ 用户详情抽屉 ============ -->
    <transition name="drawer">
      <div v-if="detail" class="drawer-mask" @click.self="detail = null">
        <aside class="drawer">
          <header class="drawer-head">
            <div class="cell-user">
              <span class="u-ava lg">{{ detail.name.slice(0, 1) }}</span>
              <div>
                <b class="d-name">{{ detail.name }}</b>
                <span class="d-sub num">{{ detail.phone }} · 注册于 {{ detail.joined }}</span>
              </div>
            </div>
            <button class="btn sm ghost" @click="detail = null">关闭</button>
          </header>

          <div class="drawer-body">
            <section class="d-sec">
              <h3 class="d-title">账号状态</h3>
              <div class="d-row">
                <span class="badge" :class="detail.state === 'active' ? 'good' : 'neutral'">
                  {{ detail.state === 'active' ? '正常' : '已冻结' }}
                </span>
                <span v-if="detail.role" class="badge ink">{{ detail.role }}</span>
                <span class="badge" :class="detail.custom ? 'ink' : 'neutral'">
                  {{ detail.custom ? '管理端新增' : 'App 注册' }}
                </span>
                <span class="d-note">ID {{ detail.id }}</span>
              </div>
            </section>

            <section class="d-sec">
              <h3 class="d-title">名下宠物（{{ petCount(detail.name) }}）</h3>
              <div v-if="userPets(detail.name).length" class="pet-cards">
                <div v-for="p in userPets(detail.name)" :key="p.id" class="pet-card">
                  <div class="pc-head">
                    <b>{{ p.name }}</b>
                    <span class="badge" :class="p.state === 'good' ? 'good' : 'watch'">
                      {{ p.state === 'good' ? '良好' : '需关注' }}
                    </span>
                  </div>
                  <p class="pc-line">{{ p.species }} · {{ p.breed }} · {{ p.age }} 岁 · {{ p.weight }} kg</p>
                  <p class="pc-score">健康分 <b class="num" :class="p.state">{{ p.score }}</b></p>
                </div>
              </div>
              <p v-else class="empty-sm">该账号名下暂无宠物档案</p>
            </section>

            <section class="d-sec">
              <h3 class="d-title">治理操作</h3>
              <div class="d-row">
                <button
                  class="btn sm"
                  :class="detail.state === 'active' ? 'danger' : 'primary'"
                  @click="toggle(detail)"
                >
                  {{ detail.state === 'active' ? '冻结账号' : '恢复账号' }}
                </button>
                <button class="btn sm ghost" @click="resetPwd(detail)">重置密码</button>
                <button class="btn sm ghost" @click="showToast('已导出该用户全部数据（演示）')">导出数据</button>
                <button v-if="detail.custom" class="btn sm danger" @click="removeUser(detail)">删除账号</button>
              </div>
              <p v-if="!detail.custom" class="d-hint">演示内置账号不可删除，可冻结或导出数据</p>
            </section>
          </div>
        </aside>
      </div>
    </transition>

    <!-- ============ 新增弹层（用户 / 兽医共用） ============ -->
    <transition name="modal">
      <div v-if="creating" class="modal-mask" @click.self="creating = false">
        <div class="modal" v-reveal>
          <header class="m-head">
            <h2 class="m-title">新增{{ tab === 'users' ? '用户' : '兽医账号' }}</h2>
            <button class="btn sm ghost" @click="creating = false">取消</button>
          </header>
          <form class="m-body" @submit.prevent="submitCreate">
            <label class="field">
              <span class="f-label">昵称 / 姓名 <i>*</i></span>
              <input v-model.trim="form.name" type="text" maxlength="12" placeholder="2–12 个字符" />
            </label>
            <label class="field">
              <span class="f-label">手机号 <i>*</i></span>
              <input v-model.trim="form.phone" type="tel" maxlength="11" placeholder="11 位手机号，作为登录账号" />
            </label>
            <template v-if="tab === 'users'">
              <label class="field">
                <span class="f-label">初始密码 <i>*</i></span>
                <input v-model.trim="form.pwd" type="text" maxlength="16" placeholder="至少 6 位，用户首次登录后可修改" />
              </label>
              <label class="field">
                <span class="f-label">名下宠物数</span>
                <input v-model.number="form.pets" type="number" min="0" max="20" />
              </label>
            </template>
            <template v-else>
              <label class="field">
                <span class="f-label">科室 <i>*</i></span>
                <select v-model="form.dept">
                  <option v-for="d in DEPTS" :key="d" :value="d">{{ d }}</option>
                </select>
              </label>
              <label class="field">
                <span class="f-label">执业医院 <i>*</i></span>
                <input v-model.trim="form.hospital" type="text" maxlength="20" placeholder="如：爱诺德动物医院" />
              </label>
              <label class="field check">
                <input v-model="form.online" type="checkbox" />
                <span>创建后立即上线接诊</span>
              </label>
            </template>
            <p v-if="formErr" class="f-err">
              <AppIcon name="alert" :size="13" /> {{ formErr }}
            </p>
            <button class="btn primary m-submit" type="submit">
              <AppIcon name="check" :size="15" /> 确认新增
            </button>
          </form>
        </div>
      </div>
    </transition>

    <!-- ============ 重置密码结果 ============ -->
    <transition name="modal">
      <div v-if="pwdModal" class="modal-mask" @click.self="pwdModal = null">
        <div class="modal slim" v-reveal>
          <header class="m-head">
            <h2 class="m-title">密码已重置</h2>
          </header>
          <div class="m-body">
            <p class="pwd-tip">已为「{{ pwdModal.name }}」生成新密码，请抄送并提醒用户妥善保管：</p>
            <div class="pwd-box num">{{ pwdModal.pwd }}</div>
            <div class="pwd-actions">
              <button class="btn sm ghost" @click="copyPwd">复制密码</button>
              <button class="btn sm primary" @click="pwdModal = null">完成</button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { users, pets, doctors } from '@/data/admin'
import { showToast } from '@/composables/toast'

// ---- 持久化：管理端新增的用户 / 兽医（与 App 演示域共享 localStorage 根 ----
const USER_KEY = 'petwise_admin_users'
const DOCTOR_KEY = 'petwise_admin_doctors'
function load(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || '[]')
  } catch (e) {
    return []
  }
}
const customUsers = ref(load(USER_KEY))
const customDoctors = ref(load(DOCTOR_KEY))
function saveUsers() {
  localStorage.setItem(USER_KEY, JSON.stringify(customUsers.value))
}
function saveDoctors() {
  localStorage.setItem(DOCTOR_KEY, JSON.stringify(customDoctors.value))
}

const today = () => {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

const tab = ref('users')
const kw = ref('')
const f = ref('all')
const detail = ref(null)

// ---- 用户列表：管理端新增在前，内置演示账号在后 ----
const allUsers = computed(() => [...customUsers.value, ...users])
const list = computed(() =>
  allUsers.value.filter((u) => {
    const hitKw = !kw.value || u.name.includes(kw.value) || u.phone.includes(kw.value)
    const hitF = f.value === 'all' || u.state === f.value
    return hitKw && hitF
  })
)

function userPets(owner) {
  return pets.filter((p) => p.owner === owner)
}
function petCount(owner) {
  return userPets(owner).length
}
function openDetail(u) {
  detail.value = u
}
function toggle(u) {
  u.state = u.state === 'active' ? 'frozen' : 'active'
  if (u.custom) saveUsers()
  showToast(u.state === 'active' ? `已恢复「${u.name}」` : `已冻结「${u.name}」`, {
    type: u.state === 'active' ? 'success' : 'default'
  })
}
function removeUser(u) {
  if (!u.custom) return
  customUsers.value = customUsers.value.filter((x) => x.id !== u.id)
  saveUsers()
  detail.value = null
  showToast(`已删除账号「${u.name}」`, { type: 'default' })
}

// ---- 重置密码：生成 6 位随机密码并展示 ----
const pwdModal = ref(null)
function resetPwd(u) {
  const pwd = String(Math.floor(100000 + Math.random() * 900000))
  pwdModal.value = { name: u.name, pwd }
  showToast(`已重置「${u.name}」的登录密码`, { type: 'success' })
}
async function copyPwd() {
  try {
    await navigator.clipboard.writeText(pwdModal.value.pwd)
    showToast('密码已复制到剪贴板', { type: 'success' })
  } catch (e) {
    showToast('复制失败，请手动抄录', { type: 'default' })
  }
}

// ---- 兽医管理 ----
const DEPTS = ['猫科内科', '犬科内科', '外科', '皮肤科', '异宠专科', '影像科', '预防兽医']
const dkw = ref('')
const df = ref('all')
const allDoctors = computed(() => [...customDoctors.value, ...doctors])
const docList = computed(() =>
  allDoctors.value.filter((d) => {
    const hitKw =
      !dkw.value ||
      d.name.includes(dkw.value) ||
      d.hospital.includes(dkw.value) ||
      d.dept.includes(dkw.value)
    const hitF =
      df.value === 'all' ||
      (df.value === 'online' && d.online && d.state === 'active') ||
      (df.value === 'frozen' && d.state !== 'active')
    return hitKw && hitF
  })
)
function toggleOnline(d) {
  d.online = !d.online
  if (d.custom) saveDoctors()
  showToast(`${d.name} 已${d.online ? '上线接诊' : '转为离线'}`, { type: 'default' })
}
function toggleDoc(d) {
  d.state = d.state === 'active' ? 'frozen' : 'active'
  if (d.state !== 'active') d.online = false
  if (d.custom) saveDoctors()
  showToast(d.state === 'active' ? `已恢复「${d.name}」` : `已冻结「${d.name}」`, {
    type: d.state === 'active' ? 'success' : 'default'
  })
}
function removeDoc(d) {
  if (!d.custom) {
    showToast('演示内置兽医不可删除，可冻结账号', { type: 'default' })
    return
  }
  customDoctors.value = customDoctors.value.filter((x) => x.id !== d.id)
  saveDoctors()
  showToast(`已删除兽医「${d.name}」`, { type: 'default' })
}

// ---- 新增表单 ----
const creating = ref(false)
const formErr = ref('')
const blankForm = () => ({
  name: '',
  phone: '',
  pwd: '',
  pets: 1,
  dept: DEPTS[0],
  hospital: '',
  online: true
})
const form = ref(blankForm())

function openCreate() {
  form.value = blankForm()
  formErr.value = ''
  creating.value = true
}
function submitCreate() {
  const name = form.value.name
  const phone = form.value.phone
  if (name.length < 2) {
    formErr.value = '昵称至少 2 个字符'
    return
  }
  if (!/^1[3-9]\d{9}$/.test(phone)) {
    formErr.value = '手机号格式不正确（11 位，1 开头）'
    return
  }
  const dup = [...allUsers.value, ...allDoctors.value].some((x) => x.phone === phone)
  if (dup) {
    formErr.value = '该手机号已存在，请更换'
    return
  }
  if (tab.value === 'users') {
    if (form.value.pwd.length < 6) {
      formErr.value = '初始密码至少 6 位'
      return
    }
    customUsers.value.unshift({
      id: 'cu' + Date.now(),
      name,
      phone,
      pets: Math.max(0, Math.min(20, Number(form.value.pets) || 0)),
      joined: today(),
      state: 'active',
      custom: true
    })
    saveUsers()
    showToast(`已新增用户「${name}」，初始密码 ${form.value.pwd}`, { type: 'success' })
  } else {
    if (!form.value.hospital) {
      formErr.value = '请填写执业医院'
      return
    }
    customDoctors.value.unshift({
      id: 'cd' + Date.now(),
      name,
      dept: form.value.dept,
      hospital: form.value.hospital,
      phone,
      online: form.value.online,
      consults: 0,
      rating: 5,
      state: 'active',
      joined: today(),
      custom: true
    })
    saveDoctors()
    showToast(`已新增兽医「${name}」（${form.value.dept}）`, { type: 'success' })
  }
  creating.value = false
}
</script>

<style scoped>
/* ---------- Tab 栏 ---------- */
.tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}
.tab {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 9px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  background: var(--color-surface);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink-2);
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease-out);
}
.tab:hover { border-color: var(--color-border-strong); }
.tab.on {
  background: var(--color-ink);
  border-color: var(--color-ink);
  color: #fff;
}
.tab.on .app-icon { color: var(--color-accent); }
.tab-num {
  font-size: 12px;
  padding: 1px 8px;
  border-radius: var(--radius-pill);
  background: var(--color-surface-2);
  color: var(--color-muted);
}
.tab.on .tab-num { background: rgba(255, 255, 255, 0.16); color: #fff; }
.add-btn { margin-left: auto; }

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.filters { display: flex; gap: 8px; flex-wrap: wrap; }
.cell-user { display: flex; align-items: center; gap: 10px; }
.u-ava {
  width: 34px;
  height: 34px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 15px;
  background: var(--grad-sand, linear-gradient(150deg, #efe6d2, #d8c6a3));
  flex-shrink: 0;
}
.u-ava.lg { width: 48px; height: 48px; border-radius: 15px; font-size: 20px; }
.u-role {
  display: block;
  font-size: 11px;
  color: var(--color-accent-ink);
  font-weight: 700;
}
.ta-r { text-align: right; }
.row-actions { display: inline-flex; gap: 8px; justify-content: flex-end; flex-wrap: wrap; }
.empty { text-align: center; color: var(--color-muted); padding: 26px 0; font-size: 14px; }

/* ---------- 兽医卡片网格 ---------- */
.doc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 14px;
}
.doc {
  display: flex;
  flex-direction: column;
  gap: 14px;
  transition: opacity var(--dur-fast) var(--ease-out);
}
.doc.off { opacity: 0.62; }
.doc-head { display: flex; align-items: flex-start; gap: 12px; }
.d-ava {
  width: 42px;
  height: 42px;
  border-radius: 13px;
  display: grid;
  place-items: center;
  background: var(--color-sage-soft);
  color: var(--color-sage);
  flex-shrink: 0;
}
.doc-id { flex: 1; min-width: 0; }
.doc-id b { display: block; font-size: 15px; }
.d-dept {
  display: block;
  font-size: 12px;
  color: var(--color-muted);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.doc-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 16px;
  margin: 0;
  padding: 12px 14px;
  background: var(--color-surface-2);
  border-radius: var(--radius-md);
}
.doc-meta dt { font-size: 11px; color: var(--color-faint); }
.doc-meta dd { margin: 2px 0 0; font-size: 14px; font-weight: 600; color: var(--color-ink); }
.doc-foot { display: flex; gap: 8px; flex-wrap: wrap; }

/* ---------- 详情抽屉 ---------- */
.drawer-mask {
  position: fixed;
  inset: 0;
  background: rgba(27, 42, 34, 0.4);
  z-index: 60;
  display: flex;
  justify-content: flex-end;
}
.drawer {
  width: min(420px, 92vw);
  height: 100%;
  background: var(--color-bg);
  box-shadow: var(--shadow-3);
  display: flex;
  flex-direction: column;
}
.drawer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 22px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
}
.d-name {
  display: block;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 18px;
  line-height: 1.2;
}
.d-sub { font-size: 12px; color: var(--color-muted); }
.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  gap: 22px;
}
.d-sec { display: flex; flex-direction: column; gap: 10px; }
.d-title {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-faint);
}
.d-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.d-note { font-size: 12px; color: var(--color-faint); }
.d-hint { font-size: 12px; color: var(--color-faint); }
.pet-cards { display: flex; flex-direction: column; gap: 10px; }
.pet-card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-soft);
  padding: 14px 16px;
}
.pc-head { display: flex; align-items: center; justify-content: space-between; }
.pc-head b { font-size: 15px; }
.pc-line { font-size: 13px; color: var(--color-ink-2); margin-top: 4px; }
.pc-score { font-size: 12px; color: var(--color-muted); margin-top: 6px; }
.pc-score b { font-family: var(--font-display); font-size: 16px; margin-left: 4px; }
.pc-score b.good { color: var(--color-good); }
.pc-score b.watch { color: var(--color-watch); }
.empty-sm { font-size: 13px; color: var(--color-faint); }

.drawer-enter-active,
.drawer-leave-active { transition: opacity var(--dur-base) var(--ease-out); }
.drawer-enter-from,
.drawer-leave-to { opacity: 0; }
.drawer-enter-active .drawer,
.drawer-leave-active .drawer { transition: transform var(--dur-base) var(--ease-out); }
.drawer-enter-from .drawer,
.drawer-leave-to .drawer { transform: translateX(100%); }

/* ---------- 新增 / 重置弹层 ---------- */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(27, 42, 34, 0.44);
  z-index: 70;
  display: grid;
  place-items: center;
  padding: 20px;
}
.modal {
  width: min(460px, 100%);
  max-height: 88vh;
  overflow-y: auto;
  background: var(--color-bg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-3);
}
.modal.slim { width: min(380px, 100%); }
.m-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid var(--color-border);
}
.m-title { font-family: var(--font-display); font-size: 17px; font-weight: 700; }
.m-body { padding: 20px 22px 22px; display: flex; flex-direction: column; gap: 14px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.f-label { font-size: 12px; font-weight: 700; color: var(--color-ink-2); }
.f-label i { font-style: normal; color: var(--color-alert); }
.field input,
.field select {
  height: 40px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font-size: 14px;
  color: var(--color-ink);
  transition: border-color var(--dur-fast) var(--ease-out);
}
.field input:focus,
.field select:focus {
  outline: none;
  border-color: var(--color-accent);
}
.field.check {
  flex-direction: row;
  align-items: center;
  gap: 9px;
  font-size: 13px;
  color: var(--color-ink-2);
}
.field.check input { width: 16px; height: 16px; accent-color: var(--color-accent); }
.f-err {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-alert);
}
.m-submit { justify-content: center; margin-top: 2px; }

.pwd-tip { font-size: 13px; color: var(--color-ink-2); line-height: 1.6; }
.pwd-box {
  padding: 16px;
  text-align: center;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 0.22em;
  background: var(--color-surface-2);
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-md);
  color: var(--color-ink);
}
.pwd-actions { display: flex; gap: 10px; justify-content: flex-end; }

.modal-enter-active,
.modal-leave-active { transition: opacity var(--dur-base) var(--ease-out); }
.modal-enter-from,
.modal-leave-to { opacity: 0; }
.modal-enter-active .modal,
.modal-leave-active .modal { transition: transform var(--dur-base) var(--ease-out); }
.modal-enter-from .modal,
.modal-leave-to .modal { transform: translateY(14px) scale(0.98); }
</style>
