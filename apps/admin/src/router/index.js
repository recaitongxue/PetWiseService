import { createRouter, createWebHashHistory } from 'vue-router'
import { getAuth } from '@shared/token'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { bare: true }
  },
  {
    path: '/',
    component: () => import('@/layout/AdminLayout.vue'),
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', name: 'dashboard', component: () => import('@/views/Dashboard.vue'), meta: { title: '数据看板' } },
      { path: 'users', name: 'users', component: () => import('@/views/Users.vue'), meta: { title: '用户管理' } },
      { path: 'records', name: 'records', component: () => import('@/views/Records.vue'), meta: { title: '识别记录' } },
      { path: 'moderation', name: 'moderation', component: () => import('@/views/Moderation.vue'), meta: { title: '内容审核' } },
      { path: 'consults', name: 'consults', component: () => import('@/views/Consults.vue'), meta: { title: '问诊记录' } },
      { path: 'announce', name: 'announce', component: () => import('@/views/Announce.vue'), meta: { title: '公告管理' } },
      { path: 'feedback', name: 'feedback', component: () => import('@/views/Feedback.vue'), meta: { title: '用户反馈' } },
      { path: 'settings', name: 'settings', component: () => import('@/views/Settings.vue'), meta: { title: '系统设置' } }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 登录守卫：以 accessToken 为准（token 里带 admin 角色，后端 /admin/* 会再次校验）
router.beforeEach((to) => {
  const authed = !!getAuth()?.accessToken
  if (to.name !== 'login' && !authed) return { name: 'login' }
  if (to.name === 'login' && authed) return { name: 'dashboard' }
  return true
})

export default router
