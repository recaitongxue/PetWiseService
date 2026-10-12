<template>
  <section class="login">
    <div class="login-card">
      <span class="mark"><AppIcon name="paw" :size="30" /></span>
      <h1 class="word">Petwise 管理端</h1>
      <p class="sub">宠物智能服务平台 · 运营控制台</p>

      <form class="form" @submit.prevent="submit">
        <label class="field">
          <span>账号</span>
          <input v-model.trim="account" type="text" placeholder="admin" autocomplete="username" />
        </label>
        <label class="field">
          <span>密码</span>
          <input v-model.trim="pwd" type="password" placeholder="••••••••" autocomplete="current-password" />
        </label>
        <p v-if="err" class="err">{{ err }}</p>
        <button class="btn accent submit" type="submit">登录控制台</button>
        <p class="hint">演示账号：admin / petwise</p>
      </form>
    </div>
    <p class="foot">CV 识别 · 大模型问诊 · 社区运营 —— 三位一体管理</p>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '@/components/icons/AppIcon.vue'

const router = useRouter()
const account = ref('')
const pwd = ref('')
const err = ref('')

function submit() {
  // 演示鉴权：接入后端后替换为登录接口
  if (account.value === 'admin' && pwd.value === 'petwise') {
    localStorage.setItem('petwise_admin_auth', '1')
    router.replace('/dashboard')
  } else {
    err.value = '账号或密码不正确（演示：admin / petwise）'
  }
}
</script>

<style scoped>
.login {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 26px;
  padding: 24px;
  background:
    radial-gradient(40rem 30rem at 12% -8%, rgba(232, 85, 43, 0.14), transparent 60%),
    radial-gradient(36rem 28rem at 100% 10%, rgba(126, 155, 120, 0.2), transparent 58%),
    var(--color-bg);
  position: relative;
  z-index: 1;
}
.login-card {
  width: min(400px, 100%);
  background: var(--color-surface);
  border-radius: 24px;
  box-shadow: var(--shadow-3);
  padding: 38px 34px 30px;
  text-align: center;
}
.mark {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  display: inline-grid;
  place-items: center;
  color: #fff;
  background: linear-gradient(150deg, #f4a987, #d6502a);
  box-shadow: 0 12px 28px rgba(214, 80, 42, 0.35);
}
.word {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 26px;
  letter-spacing: -0.01em;
  margin-top: 16px;
}
.sub {
  font-size: 13px;
  color: var(--color-muted);
  margin-top: 4px;
}
.form {
  margin-top: 26px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  text-align: left;
}
.field { display: flex; flex-direction: column; gap: 6px; }
.field span {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-faint);
}
.field input {
  height: 46px;
  border-radius: 13px;
  border: none;
  outline: none;
  background: var(--color-surface-2);
  box-shadow: inset 0 0 0 1px var(--color-border);
  padding: 0 16px;
  font: inherit;
  font-size: 15px;
  color: var(--color-ink);
}
.field input:focus-visible { box-shadow: inset 0 0 0 2px var(--color-accent); }
.err {
  font-size: 13px;
  color: var(--color-alert);
  background: var(--color-accent-soft);
  border-radius: 10px;
  padding: 9px 12px;
}
.submit {
  height: 48px;
  border-radius: var(--radius-pill);
  font-size: 15px;
  justify-content: center;
  margin-top: 4px;
}
.hint {
  text-align: center;
  font-size: 12px;
  color: var(--color-faint);
}
.foot {
  font-size: 12px;
  letter-spacing: 0.08em;
  color: var(--color-muted);
}
</style>
