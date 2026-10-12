import { createRouter, createWebHashHistory } from 'vue-router'
import { isAuthed } from '@/data/ops'

// 哈希路由：便于静态托管与 Capacitor 打包（file:// 也可运行）
const routes = [
  {
    path: '/',
    name: 'splash',
    component: () => import('@/views/Splash.vue'),
    meta: { bare: true, public: true }
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { bare: true, public: true }
  },
  { path: '/home', name: 'home', component: () => import('@/views/Home.vue') },
  { path: '/recognize', name: 'recognize', component: () => import('@/views/Recognize.vue') },
  { path: '/consult', name: 'consult', component: () => import('@/views/ConsultHub.vue') },
  { path: '/consult/ai', name: 'consult-ai', component: () => import('@/views/Consult.vue') },
  { path: '/preconsult', name: 'preconsult', component: () => import('@/views/PreConsult.vue') },
  { path: '/report/:id', name: 'report', component: () => import('@/views/Report.vue') },
  { path: '/doctors', name: 'doctors', component: () => import('@/views/Doctors.vue') },
  { path: '/doctor/:id', name: 'doctor', component: () => import('@/views/DoctorDetail.vue') },
  { path: '/consultation/:id', name: 'consultation', component: () => import('@/views/ConsultationRoom.vue') },
  { path: '/community', name: 'community', component: () => import('@/views/Community.vue') },
  { path: '/chat', name: 'chat', component: () => import('@/views/ChatList.vue') },
  { path: '/chat/:id', name: 'chatroom', component: () => import('@/views/ChatRoom.vue') },
  { path: '/profile', name: 'profile', component: () => import('@/views/Profile.vue') },
  { path: '/pet/:id', name: 'pet', component: () => import('@/views/PetProfile.vue') },
  { path: '/schedule', name: 'schedule', component: () => import('@/views/Schedule.vue') },
  { path: '/records', name: 'records', component: () => import('@/views/Records.vue') },
  { path: '/favorites', name: 'favorites', component: () => import('@/views/Favorites.vue') },
  { path: '/breed/:id', name: 'breed', component: () => import('@/views/BreedDetail.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/home' }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// 登录拦截：未登录访问业务页 → 跳转登录页，并带上原目标以便登录后回跳
router.beforeEach((to) => {
  if (to.meta.public) return true
  if (!isAuthed()) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
