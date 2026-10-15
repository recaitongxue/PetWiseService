/**
 * data.js —— 前端「数据门面」：把原 data/mock.js + data/ops.js 的同步调用，
 * 统一收敛到真实后端接口（@/api/index.js）之上。
 *
 * 设计原则：
 * 1. 对外暴露的函数尽量返回与原 mock 一致的字段形状，降低各视图改动量。
 * 2. 纯静态配置（quickActions / tips / consultSeed / consultSuggestions /
 *    departments / consultModes / bodyParts / durations / severities /
 *    accompanyOptions / symptomGroups / triageRules / aiSchedulePlan /
 *    galleryPool / recognitionSamples）仍留在 @/data/mock，视图继续从那里取。
 * 3. 纯客户端能力（短信频控 / 钱包流水 / 登录态）在 @/api/client.js。
 *
 * 视图里的典型改法（以 Home 为例）：
 *   旧：import { pets, petTrends } from '@/data/mock'
 *       const pets = pets            // 同步
 *   新：import { fetchPets, fetchPetTrend } from '@/api/data'
 *       const pets = ref([])
 *       onMounted(async () => { pets.value = await fetchPets() })
 */
import {
  authApi, petsApi, scheduleApi, homeApi, contentApi, recognitionApi,
  consultApi, communityApi, imApi, fileApi, contactsApi, memoApi
} from './index'
import { setTokens, clearAuth } from './token'
import {
  smsSendCount, bumpSmsSend, SMS_DAILY_MAX, walletTransactions, addWalletTransaction, isAuthed
} from './client'

/* 透传客户端助手，方便视图只 import 一个模块 */
export { smsSendCount, bumpSmsSend, SMS_DAILY_MAX, walletTransactions, addWalletTransaction, isAuthed }

/* ============================================================
   鉴权
   ============================================================ */
export async function loginWithCode(phone, code) {
  const r = await authApi.login({ mode: 'sms', phone, code })
  setTokens({ accessToken: r.accessToken, refreshToken: r.refreshToken, user: r.user })
  return r.user
}

export async function sendSmsCode(phone, scene = 'login') {
  return authApi.sendCode(phone, scene)
}

export async function logoutUser() {
  try {
    await authApi.logout()
  } catch {
    /* 无状态登出，忽略网络错误 */
  }
  clearAuth()
}

export const fetchUser = () => authApi.me()

/* ============================================================
   宠物
   ============================================================ */
export const fetchPets = () => petsApi.list()
export const fetchPet = (id) => petsApi.detail(id)
export async function fetchPetTrend(petId) {
  const r = await petsApi.trend(petId)
  return r.points || []
}
export const fetchPetReminders = (petId) => petsApi.reminders(petId)
export async function fetchPetSchedule() {
  const items = await scheduleApi.list()
  const map = {}
  for (const it of items) {
    ;(map[it.petId] = map[it.petId] || []).push(it)
  }
  return map
}
export const fetchScheduleTypes = () => scheduleApi.types()
export const createSchedule = (body) => scheduleApi.create(body)
export const updateSchedule = (id, body) => scheduleApi.update(id, body)
export const toggleScheduleDone = (id, done) => scheduleApi.toggleDone(id, done)
export const removeSchedule = (id) => scheduleApi.remove(id)

/* ============================================================
   首页聚合
   ============================================================ */
export const fetchHome = (petId) => homeApi.summary(petId)

/* ============================================================
   公告 / 收藏 / 品种
   ============================================================ */
export const fetchAnnouncements = (active = true) => contentApi.announcements(active)
export const dismissAnnouncement = (id) => contentApi.dismissAnnouncement(id)
export const fetchFavorites = (kind) => contentApi.favorites(kind)
export async function addFavorite(kind, targetId, meta = {}) {
  return contentApi.addFavorite(kind, targetId, meta)
}
export const removeFavorite = (kind, targetId) => contentApi.removeFavorite(kind, targetId)
export const fetchBreedLibrary = (params) => contentApi.breeds(params)
export const fetchBreed = (id) => contentApi.breed(id)

/* ============================================================
   社区
   ============================================================ */
export async function fetchFeed(params) {
  const r = await communityApi.posts(params)
  return r.list || []
}
export async function fetchPostComments(postId) {
  const r = await communityApi.comments(postId)
  return r.list || []
}
export const publishPost = (body) => communityApi.publish(body)
export const likePost = (id) => communityApi.like(id)
export const unlikePost = (id) => communityApi.unlike(id)
export const commentPost = (id, text) => communityApi.comment(id, text)
export const reportPost = (id, body) => communityApi.report(id, body)

/* ============================================================
   即时消息
   ============================================================ */
export const fetchConversations = () => imApi.conversations()
export async function fetchMessages(convId, params) {
  const r = await imApi.messages(convId, params)
  return r.list || []
}
export const createConversation = (contactId) => imApi.create({ contactId })
export const sendMessage = (convId, body) => imApi.send(convId, body)
export const readConversation = (convId) => imApi.read(convId)

/* ============================================================
   通讯录
   ============================================================ */
export const fetchContactGroups = (q) => contactsApi.list(q)

/* ============================================================
   医生
   ============================================================ */
export const fetchDoctors = (params) => consultApi.doctors(params)
export const fetchDoctor = (id) => consultApi.doctor(id)
export const fetchDoctorReviews = (id, params) => consultApi.doctorReviews(id, params)

/* ============================================================
   在线问诊
   ============================================================ */
export const fetchConsultModes = () => consultApi.modes()
export const fetchDepartments = () => consultApi.departments()
export const fetchDictionary = () => consultApi.dictionary()
export const fetchAiQuota = () => consultApi.quota()
export const triageFree = (text) => consultApi.triage({ text })
export const preConsult = (body) => consultApi.preConsult(body)
export const caseSummary = (body) => consultApi.caseSummary(body)
export const fetchConsultOrders = (state) => consultApi.orders(state)
export const fetchOrder = (id) => consultApi.order(id)
export const fetchOrderMessages = (id, params) => consultApi.messages(id, params)
export const sendOrderMessage = (id, body) => consultApi.sendMessage(id, body)
export const callOrder = (id) => consultApi.call(id)
export const closeOrder = (id) => consultApi.close(id)
export const readOrder = (id, lastMessageId) => consultApi.read(id, lastMessageId)
export const rateOrder = (id, body) => consultApi.rate(id, body)
export const createConsultOrder = (body) => consultApi.createOrder(body)

/* ============================================================
   报告
   ============================================================ */
export async function fetchReports(params) {
  const r = await consultApi.reports(params)
  return r.list || []
}
export const fetchReport = (id) => consultApi.report(id)
export const saveReport = (body) => consultApi.saveReport(body)
export const archiveReport = (id) => consultApi.archiveReport(id)
export const remindReport = (id) => consultApi.remindReport(id)

/* ============================================================
   问诊记录（订单 + 报告合并，兼容原 consultRecords 形状）
   ============================================================ */
export async function fetchConsultRecords() {
  const [orders, reports] = await Promise.all([
    consultApi.orders().catch(() => []),
    consultApi.reports().catch(() => ({ list: [] }))
  ])
  const items = []
  for (const r of reports.list || []) {
    items.push({
      id: r.id,
      date: r.date,
      petId: r.petId,
      petName: r.petName,
      title: r.title,
      preview: r.preview,
      type: r.type, // ai | human
      state: 'closed',
      level: (r.triage && r.triage.level) || 'home',
      rated: false,
      mode: null,
      doctorId: r.doctor && r.doctor.id,
      reportId: r.id,
      source: 'report'
    })
  }
  for (const o of orders || []) {
    items.push({
      id: o.id,
      date: (o.createdAt || '').slice(0, 10),
      petId: o.petId,
      petName: o.pet && o.pet.name,
      title: o.summary || '在线问诊',
      preview: o.lastMessage && o.lastMessage.text ? o.lastMessage.text : '',
      type: 'human',
      state: o.state, // pending | replied | closed
      level: 'urgent',
      rated: false,
      mode: o.mode,
      doctorId: o.doctorId,
      orderId: o.id,
      source: 'order'
    })
  }
  items.sort((a, b) => (b.date || '').localeCompare(a.date || ''))
  return items
}

/* ============================================================
   健康记录 / 体重
   ============================================================ */
export async function fetchHealthRecords(petId) {
  const r = await petsApi.records(petId)
  const list = r.list || r || []
  return list.map((x) => ({
    id: x.id,
    petId: x.pet_id,
    kind: x.kind,
    date: x.record_date,
    weight: x.weight,
    note: x.note,
    metrics: x.metrics
  }))
}
export const addHealthRecord = (petId, body) => petsApi.addRecord(petId, body)
export const removeHealthRecord = (recordId) => petsApi.removeRecord(recordId)
export const fetchWeights = (petId) => petsApi.weights(petId)
export const addWeight = (petId, body) => petsApi.addWeight(petId, body)

/* 兼容原 ops 命名 */
export const recordsOf = fetchHealthRecords
export const customRecords = fetchHealthRecords
export const addRecord = addHealthRecord
export const removeRecord = removeHealthRecord

/* ============================================================
   拍照识别
   ============================================================ */
export async function fetchRecognitionHistory(params) {
  const r = await recognitionApi.history(params)
  return r.list || []
}
export const recognizeImage = (formData) => recognitionApi.recognize(formData)
export const correctRecognition = (id, breed) =>
  recognitionApi.correct(id, { breed, corrected: breed })
export const recognitionTask = (taskId) => recognitionApi.task(taskId)

/* ============================================================
   日程（AI 计划 / 批量写入 / 备忘录）
   ============================================================ */
export const aiSchedulePlan = (petId) => scheduleApi.aiPlan({ petId })
export const batchSchedule = (petId, items) => scheduleApi.batch({ petId, items })
export const fetchMemos = (petId) => memoApi.list(petId ? { petId } : undefined)
export const addMemo = (body) => memoApi.add(body)
export const pinMemo = (id, pinned) => memoApi.pin(id, { pinned })
export const removeMemo = (id) => memoApi.remove(id)

/* ============================================================
   反馈 / 资料
   ============================================================ */
export const submitFeedback = (body) => contentApi.submitFeedback(body)
export const updateProfile = (patch) => authApi.updateMe(patch)
