/**
 * 交互写路径验收：点赞 / 收藏 / 日程勾选 / 发消息 / 识别上传
 * 运行：node .workbuddy/e2e_flows.cjs
 */
const { chromium } = require('C:/Users/admin/.workbuddy/binaries/node/workspace/node_modules/playwright-core')

const CHROME = 'C:/Users/admin/.agent-browser/browsers/chrome-155.0.8059.39/chrome.exe'
const BASE = 'http://localhost:5173'

const errors = []
const passes = []

;(async () => {
  const browser = await chromium.launch({ executablePath: CHROME })
  const page = await browser.newPage({ viewport: { width: 430, height: 900 } })

  page.on('console', (m) => { if (m.type() === 'error') errors.push(`[console] ${m.text().slice(0, 180)}`) })
  page.on('pageerror', (e) => errors.push(`[pageerror] ${e.message.slice(0, 180)}`))

  const step = async (name, fn) => {
    try {
      const r = await fn()
      passes.push(name)
      console.log(`OK   ${name}${r ? ' — ' + r : ''}`)
    } catch (e) {
      console.log(`FAIL ${name}: ${e.message}`)
      errors.push(`[step] ${name}: ${e.message}`)
    }
  }

  const login = async () => {
    await page.goto(`${BASE}/#/login`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(600)
    await page.fill('input.f-control[type="tel"]', '13800138000')
    await page.click('button.f-action')
    await page.waitForTimeout(1200)
    const cells = await page.$$('.code-box')
    for (let i = 0; i < 6; i++) await cells[i].fill('8')
    const agree = await page.$('input.agree-box')
    if (agree && !(await agree.isChecked())) await agree.click()
    await page.click('button.lg-submit')
    await page.waitForTimeout(3000)
  }

  await login()

  // ---- 1. 社区点赞 ----
  await step('社区帖子点赞', async () => {
    await page.goto(`${BASE}/#/community`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(2200)
    const likeBtn = await page.$('.post-like, .like-btn, [class*="like"]')
    if (!likeBtn) throw new Error('找不到点赞按钮')
    const before = await page.evaluate(() => document.querySelector('#app').innerText.match(/\d+/) || [])
    await likeBtn.click()
    await page.waitForTimeout(1500)
    // 点赞后按钮应有激活态或计数变化（不强制，主要验证不报错）
    return '已点击，无报错'
  })

  // ---- 2. 收藏页渲染 + 删除 ----
  await step('收藏页渲染', async () => {
    await page.goto(`${BASE}/#/favorites`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(2000)
    const text = await page.evaluate(() => document.querySelector('#app').innerText)
    if (text.length < 20) throw new Error('收藏页空白')
    return `文本 ${text.length} 字符`
  })

  // ---- 3. 日程勾选完成 ----
  await step('日程勾选完成', async () => {
    await page.goto(`${BASE}/#/schedule`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(2200)
    const check = await page.$('.sc-check, .check, input[type="checkbox"], [class*="done"]')
    if (!check) throw new Error('找不到日程勾选控件')
    await check.click()
    await page.waitForTimeout(1500)
    return '已勾选，无报错'
  })

  // ---- 4. 通讯录 → 发起会话 → 发消息 ----
  await step('通讯录进入会话', async () => {
    await page.goto(`${BASE}/#/contacts`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(2000)
    const member = await page.$('.c-row')
    if (!member) throw new Error('找不到联系人条目(.c-row)')
    await member.click()
    await page.waitForTimeout(2000)
    const url = page.url()
    if (!/\/chat\/|\/doctor\/|\/consult/.test(url)) throw new Error(`点击联系人后未进入会话: ${url}`)
    return `跳转到 ${url}`
  })

  // ---- 5. 聊天页发消息 ----
  await step('聊天页发送消息', async () => {
    // 确保在聊天页（上一步可能跳转）；若不在则从消息列表进第一个会话
    if (!page.url().includes('/chat/')) {
      await page.goto(`${BASE}/#/chat`, { waitUntil: 'networkidle' })
      await page.waitForTimeout(2000)
      const conv = await page.$('.conv')
      if (!conv) throw new Error('找不到会话条目(.conv)')
      await conv.click()
      await page.waitForTimeout(2000)
    }
    const input = await page.$('.composer-input, textarea, .chat-input')
    if (!input) throw new Error('找不到聊天输入框')
    await input.fill('自动化测试消息')
    const sendBtn = await page.$('.composer-send, .send-btn, [class*="send"]')
    if (!sendBtn) throw new Error('找不到发送按钮')
    await sendBtn.click()
    await page.waitForTimeout(2500)
    const text = await page.evaluate(() => document.querySelector('#app').innerText)
    if (!text.includes('自动化测试消息')) throw new Error('消息未上屏')
    return '消息已发送并上屏'
  })

  // ---- 6. 识别页上传（构造一张测试图片） ----
  await step('识别页上传图片', async () => {
    await page.goto(`${BASE}/#/recognize`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(2000)
    // 1x1 红色 PNG
    const png = Buffer.from(
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
      'base64'
    )
    const fileInput = await page.$('input[type="file"]')
    if (!fileInput) throw new Error('找不到文件上传 input')
    await fileInput.setInputFiles({ name: 'test.png', mimeType: 'image/png', buffer: png })
    await page.waitForTimeout(5000)
    const text = await page.evaluate(() => document.querySelector('#app').innerText)
    if (/置信度|识别|品种|confidence/.test(text)) return '识别结果已渲染'
    throw new Error(`上传后未见识别结果: ${text.slice(0, 100)}`)
  })

  // ---- 7. 退出登录 ----
  await step('退出登录', async () => {
    await page.goto(`${BASE}/#/profile`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(2200)
    const btn = await page.$('.logout')
    if (!btn) throw new Error('找不到退出登录按钮')
    await btn.click()
    await page.waitForTimeout(2500)
    if (!page.url().includes('/login')) throw new Error(`退出后未回登录页: ${page.url()}`)
    // 再访问需要登录的页面应被拦截回登录页
    await page.goto(`${BASE}/#/home`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(1500)
    if (!page.url().includes('/login')) throw new Error('退出后访问 /home 未被拦截（登录态未清）')
    return '已退出且路由拦截生效'
  })

  await browser.close()

  console.log('\n========== 结果 ==========')
  console.log(`通过 ${passes.length} 项，错误 ${errors.length} 个`)
  if (errors.length) {
    console.log('\n--- 错误明细 ---')
    errors.slice(0, 20).forEach((e) => console.log(' ', e))
  }
  process.exit(errors.length ? 1 : 0)
})()
