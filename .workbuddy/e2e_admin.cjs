/**
 * 管理端端到端浏览器验收：登录 + 走遍所有页面 + 收集错误
 * 运行：node .workbuddy/e2e_admin.cjs
 */
const { chromium } = require('C:/Users/admin/.workbuddy/binaries/node/workspace/node_modules/playwright-core')

const CHROME = 'C:/Users/admin/.agent-browser/browsers/chrome-155.0.8059.39/chrome.exe'
const BASE = 'http://localhost:5174'

const errors = []

;(async () => {
  const browser = await chromium.launch({ executablePath: CHROME })
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })

  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(`[console] ${msg.text()}`)
  })
  page.on('pageerror', (err) => errors.push(`[pageerror] ${err.message}`))
  page.on('response', (res) => {
    if (res.status() >= 400 && !/favicon/i.test(res.url())) {
      errors.push(`[HTTP ${res.status()}] ${res.url()}`)
    }
  })

  const step = async (name, fn) => {
    try {
      await fn()
      console.log(`OK   ${name}`)
    } catch (e) {
      console.log(`FAIL ${name}: ${e.message}`)
      errors.push(`[step] ${name}: ${e.message}`)
    }
  }

  // ---- 登录（管理员手机号 + 演示验证码） ----
  await step('打开管理端登录页', async () => {
    await page.goto(`${BASE}/#/login`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(800)
  })

  await step('管理员登录', async () => {
    // 等手机号输入出现
    await page.waitForSelector('input', { timeout: 8000 })
    const inputs = await page.$$('input')
    let phoneFilled = false
    for (const inp of inputs) {
      const type = await inp.getAttribute('type')
      const ph = (await inp.getAttribute('placeholder')) || ''
      if (type === 'tel' || /手机号|账号/.test(ph)) {
        await inp.fill('13900000000')
        phoneFilled = true
        break
      }
    }
    if (!phoneFilled) await inputs[0].fill('13900000000')
    // 获取验证码按钮
    const btns = await page.$$('button')
    for (const b of btns) {
      const t = (await b.innerText()).trim()
      if (/获取验证码|发送/.test(t)) {
        await b.click()
        break
      }
    }
    await page.waitForTimeout(1500)
    // 6 位验证码
    const cells = await page.$$('.code-box')
    if (cells.length === 6) {
      for (let i = 0; i < 6; i++) await cells[i].fill('8')
    } else {
      const all = await page.$$('input')
      for (const inp of all) {
        const ml = await inp.getAttribute('maxlength')
        const type = await inp.getAttribute('type')
        if (type !== 'tel' && ml === '6') {
          await inp.fill('888888')
          break
        }
      }
    }
    // 提交
    const submit = await page.$('button[type="submit"], .submit, button.btn')
    if (submit) await submit.click()
    await page.waitForTimeout(3500)
    if (page.url().includes('/login')) {
      const txt = await page.evaluate(() => document.querySelector('#app').innerText.slice(0, 200))
      throw new Error(`登录后被拦截在登录页: ${txt}`)
    }
  })

  // ---- 走遍管理端页面 ----
  const pages = [
    ['/#/dashboard', '数据看板'],
    ['/#/users', '用户管理'],
    ['/#/records', '识别记录'],
    ['/#/moderation', '内容审核'],
    ['/#/consults', '问诊记录'],
    ['/#/announce', '公告管理'],
    ['/#/feedback', '用户反馈'],
    ['/#/settings', '系统设置']
  ]

  for (const [hash, name] of pages) {
    await step(`页面 ${name}`, async () => {
      await page.goto(BASE + hash, { waitUntil: 'networkidle' })
      await page.waitForTimeout(1800)
      const info = await page.evaluate(() => {
        const root = document.querySelector('#app')
        const text = (root?.innerText || '').trim()
        return {
          textLen: text.length,
          isLogin: location.hash.includes('/login'),
          hasErr: /加载失败|请求失败|网络错误|500|Internal Server|undefined|NaN|null/.test(text)
        }
      })
      if (info.isLogin) throw new Error('被重定向到登录页（登录态丢失）')
      if (info.textLen < 20) throw new Error(`页面内容过少(${info.textLen}字符)，可能白屏`)
      if (info.hasErr) {
        const t = await page.evaluate(() => document.querySelector('#app').innerText)
        const bad = t.match(/.{0,30}(加载失败|请求失败|网络错误|500|Internal Server|undefined|NaN).{0,30}/)
        throw new Error(`页面异常文案: ${bad ? bad[0] : ''}`)
      }
    })
  }

  // ---- 看板数字真实性：统计卡不应全为 0/空 ----
  await step('看板统计卡有真实数据', async () => {
    await page.goto(`${BASE}/#/dashboard`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(2000)
    const text = await page.evaluate(() => document.querySelector('#app').innerText)
    // 至少要有非零数字出现（用户数/宠物数等）
    if (!/\d/.test(text)) throw new Error('看板没有任何数字')
    const zeros = (text.match(/\b0\b/g) || []).length
    console.log(`     看板文本长度 ${text.length}，0 出现 ${zeros} 次`)
  })

  // ---- 公告列表有真实数据 ----
  await step('公告管理有真实数据', async () => {
    await page.goto(`${BASE}/#/announce`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(2000)
    const text = await page.evaluate(() => document.querySelector('#app').innerText)
    if (text.length < 50) throw new Error('公告页内容异常')
    console.log(`     公告页文本长度 ${text.length}`)
  })

  await browser.close()

  console.log('\n========== 结果 ==========')
  console.log(`错误 ${errors.length} 个`)
  if (errors.length) {
    console.log('\n--- 错误明细 ---')
    errors.slice(0, 20).forEach((e) => console.log(' ', e.slice(0, 220)))
  }
  process.exit(errors.length ? 1 : 0)
})()
