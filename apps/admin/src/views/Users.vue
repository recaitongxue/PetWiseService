<template>
  <section>
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
            <th>用户</th><th>手机号</th><th>宠物数</th><th>注册时间</th><th>状态</th><th class="ta-r">操作</th>
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

    <!-- 用户详情抽屉：账号治理视角，含名下宠物档案 -->
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
                <button class="btn sm ghost" @click="showToast('重置密码邮件已发送（演示）')">重置密码</button>
                <button class="btn sm ghost" @click="showToast('已导出该用户全部数据（演示）')">导出数据</button>
              </div>
            </section>
          </div>
        </aside>
      </div>
    </transition>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import AppIcon from '@/components/icons/AppIcon.vue'
import { users, pets } from '@/data/admin'
import { showToast } from '@/composables/toast'

const kw = ref('')
const f = ref('all')
const detail = ref(null)
const rows = ref(users.map((u) => ({ ...u })))

const list = computed(() =>
  rows.value.filter((u) => {
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
  showToast(u.state === 'active' ? `已恢复「${u.name}」` : `已冻结「${u.name}」`, {
    type: u.state === 'active' ? 'success' : 'default'
  })
}
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
.filters { display: flex; gap: 8px; }
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
.row-actions { display: inline-flex; gap: 8px; justify-content: flex-end; }
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
</style>
