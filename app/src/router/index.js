import { createRouter, createWebHashHistory } from 'vue-router'

// 哈希路由：便于静态托管与 Capacitor 打包（file:// 也可运行）
const routes = [
  { path: '/', name: 'splash', component: () => import('@/views/Splash.vue'), meta: { bare: true } },
  { path: '/home', name: 'home', component: () => import('@/views/Home.vue') },
  { path: '/recognize', name: 'recognize', component: () => import('@/views/Recognize.vue') },
  { path: '/consult', name: 'consult', component: () => import('@/views/Consult.vue') },
  { path: '/community', name: 'community', component: () => import('@/views/Community.vue') },
  { path: '/chat', name: 'chat', component: () => import('@/views/ChatList.vue') },
  { path: '/chat/:id', name: 'chatroom', component: () => import('@/views/ChatRoom.vue') },
  { path: '/profile', name: 'profile', component: () => import('@/views/Profile.vue') },
  { path: '/pet/:id', name: 'pet', component: () => import('@/views/PetProfile.vue') },
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

export default router
