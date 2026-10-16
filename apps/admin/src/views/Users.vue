<template>
  <section>
    <!-- 用户管理：后端 GET /admin/users + PATCH /admin/users/{id} -->
    <div class="toolbar" v-reveal>
      <label class="search">
        <AppIcon name="search" :size="16" />
        <input v-model.trim="kw" type="search" placeholder="搜索昵称 / 手机号…" />
      </label>
      <div class="filters">
        <button class="btn sm" :class="{ ghost: f !== 'all', primary: f === 'all' }" @click="f = 'all'">全部</button>
        <button class="btn sm" :class="{ ghost: f !== 'user', primary: f === 'user' }" @click="f = 'user'">普通用户</button>
        <button class="btn sm" :class="{ ghost: f !== 'admin', primary: f === 'admin' }" @click="f = 'admin'">管理员</button>
      </div>
    </div>

    <article class="card" v-reveal="{ delay: 60 }">
      <table class="table">
        <thead>
          <tr>
            <th>用户</th><th>手机号</th><th>宠物数</th><th>注册时间</th><th>余额</th><th>角色</th><th class="ta-r">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in list" :key="u.id">
            <td>
              <div class="cell-user">
                <span class="u-ava">{{ u.name.slice(0, 1) }}</span>
                <div>
                  <b>{{ u.name }}</b>
                  <span v-if="u.role === 'admin'" class="u-role">管理员</span>
                </div>
              </div>
            </td>
            <td class="num">{{ u.phone }}</td>
            <td class="num">{{ u.petCount }}</td>
            <td class="num">{{ u.joined }}</td>
            <td class="num">{{ u.balance }}</td>
            <td>
              <span class="badge" :class="u.role === 'admin' ? 'ink' : 'neutral'">
                {{ u.role === 'admin' ? '管理员' : '普通用户' }}
              </span>
            </td>
            <td class="ta-r">
              <div class="row-actions">
                <button class="btn sm ghost" @click="openDetail(u)">详情</button>
                <button class="btn sm" :class="u.role === 'admin' ? 'danger' : 'primary'" @click="toggleRole(u)">
                  {{ u.role === 'admin' ? '取消管理员' : '设为管理员' }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!list.length" class="empty">没有匹配的用户</p>
    </article>

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
                <span class="badge" :class="detail.role === 'admin' ? 'ink' : 'neutral'">
                  {{ detail.role === 'admin' ? '管理员' : '普通用户' }}
                </span>
                <span class="badge neutral">App 注册</span>
                <span class="d-note">ID {{ detail.id }}</span>
              </div>
            </section>

            <section class="d-sec">
              <h3 class="d-title">名下宠物（{{ detail.petCount }}）</h3>
              <p class="empty-sm">用户接口仅返回宠物数量，档案明细暂未开放</p>
            </section>

            <section class="d-sec">
              <h3 class="d-title">编辑资料</h3>
              <label class="field">
                <span class="f-label">昵称</span>
                <input v-model.trim="editForm.nickname" type="text" maxlength="20" />
              </label>
              <label class="field">
                <span class="f-label">简介</span>
                <input v-model.trim="editForm.bio" type="text" maxlength="60" placeholder="未填写" />
              </label>
              <div class="d-row">
                <button class="btn sm primary" @click="saveProfile">保存资料</button>
              </div>
            </section>

            <section class="d-sec">
              <h3 class="d-title">治理操作</h3>
              <div class="d-row">
                <button
                  class="btn sm"
                  :class="detail.role === 'admin' ? 'danger' : 'primary'"
                  @click="toggleRole(detail)"
                >
                  {{ detail.role === 'admin' ? '取消管理员' : '设为管理员' }}
                </button>
              </div>
              <p class="d-hint">后端暂未提供删除 / 冻结账号接口，可通过角色与资料进行调整</p>
            </section>
          </div>
        </aside>
      </div>
    </transition>
  </section>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { adminApi } from '@/api'
import { showToast } from '@shared/toast'

const kw = ref('')
const f = ref('all')
const detail = ref(null)

// ---- 用户列表：后端 GET /admin/users（q 走后端模糊匹配：昵称 / 手机号） ----
const rows = ref([])

function toRow(u) {
  return {
    id: u.id,
    name: u.nickname || u.name || u.phone || '—',
    phone: u.phone || '—',
    role: u.role === 'admin' ? 'admin' : 'user',
    bio: u.bio || '',
    balance: Number(u.balance || 0),
    petCount: Number(u.petCount || 0),
    joined: (u.createdAt || '').slice(0, 10)
  }
}

async function loadUsers() {
  try {
    const res = await adminApi.users(kw.value || undefined)
    rows.value = (res?.list || []).map(toRow)
  } catch (e) {
    showToast(e?.message || '用户列表加载失败', { type: 'warn' })
    rows.value = []
  }
}

// 搜索框输入后防抖重新请求（角色筛选在本地完成）
let timer = null
watch(kw, () => {
  clearTimeout(timer)
  timer = setTimeout(loadUsers, 300)
})

const list = computed(() =>
  rows.value.filter((u) => f.value === 'all' || u.role === f.value)
)

const editForm = ref({ nickname: '', bio: '' })
function openDetail(u) {
  detail.value = u
  editForm.value = { nickname: u.name, bio: u.bio }
}

// 编辑昵称 / 简介：PATCH /admin/users/{id}
async function saveProfile() {
  const u = detail.value
  if (!u) return
  try {
    await adminApi.updateUser(u.id, {
      nickname: editForm.value.nickname,
      bio: editForm.value.bio
    })
    showToast(`已更新「${u.name}」的资料`, { type: 'success' })
    detail.value = null
    await loadUsers()
  } catch (e) {
    showToast(e?.message || '资料保存失败', { type: 'warn' })
  }
}

// 后端账号无「冻结」字段，角色（user / admin）是唯一可管的权限位
async function toggleRole(u) {
  const next = u.role === 'admin' ? 'user' : 'admin'
  try {
    await adminApi.updateUser(u.id, { role: next })
    showToast(
      next === 'admin' ? `已将「${u.name}」设为管理员` : `已取消「${u.name}」的管理员身份`,
      { type: 'success' }
    )
    if (detail.value?.id === u.id) detail.value = null
    await loadUsers()
  } catch (e) {
    showToast(e?.message || '权限调整失败', { type: 'warn' })
  }
}

onMounted(loadUsers)
</script>

<style scoped>
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
.empty-sm { font-size: 13px; color: var(--color-faint); }

.drawer-enter-active,
.drawer-leave-active { transition: opacity var(--dur-base) var(--ease-out); }
.drawer-enter-from,
.drawer-leave-to { opacity: 0; }
.drawer-enter-active .drawer,
.drawer-leave-active .drawer { transition: transform var(--dur-base) var(--ease-out); }
.drawer-enter-from .drawer,
.drawer-leave-to .drawer { transform: translateX(100%); }

/* ---------- 表单 ---------- */
.field { display: flex; flex-direction: column; gap: 6px; }
.f-label { font-size: 12px; font-weight: 700; color: var(--color-ink-2); }
.field input {
  height: 40px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font-size: 14px;
  color: var(--color-ink);
  transition: border-color var(--dur-fast) var(--ease-out);
}
.field input:focus {
  outline: none;
  border-color: var(--color-accent);
}
</style>
