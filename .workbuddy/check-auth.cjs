// 端到端验证：登录拦截 / 登录流程 / 导航固定 / 退出登录
const { chromium } = require('D:/Node/node_global/node_modules/openclaw/node_modules/playwright-core')
const CHROME = 'C:/Users/32501/.agent-browser/browsers/chrome-155.0.8059.39/chrome.exe'
const BASE = 'http://localhost:5173/'
const OUT = 'E:/毕业设计/PetWiseService/.workbuddy/'

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await chromium.launch({ executablePath: CHROME })
  const page = await browser.newPage({ viewport: { width: 430, height: 900 } })

  const errors = []
  page.on('console', (m) => {
    if (m.type() === 'error') errors.push(m.text())
  })
  page.on('pageerror', (e) => errors.push('PAGEERROR: ' + e.message))

  // 1) 未登录直接访问业务页
  await page.goto(BASE + '#/home', { waitUntil: 'networkidle' })
  await sleep(800)
  console.log('1) 未登录访问 #/home  →  实际:', page.url())

  // 2) 登录页渲染
  await page.waitForSelector('.lg-submit')
  await page.screenshot({ path: OUT + 'login.png' })

  // 3) 填表登录（验证码模式）
  await page.fill('input[autocomplete="tel"]', '13800001111')
  await page.fill('input[autocomplete="one-time-code"]', '123456')
  await page.click('.lg-submit')
  await sleep(1400)
  console.log('2) 提交登录后  →  实际:', page.url())

  // 4) 首页 + 导航固定复检
  await page.waitForSelector('.dock', { timeout: 4000 })
  const nav = await page.evaluate(() => {
    const dock = document.querySelector('.dock')
    const main = document.querySelector('.app-main')
    const before = dock.getBoundingClientRect().top
    main.scrollTop = main.scrollHeight
    return new Promise((res) =>
      setTimeout(() => {
        res({
          moved: Math.round(dock.getBoundingClientRect().top - before),
          bodyScrollable: document.body.scrollHeight > document.body.clientHeight
        })
      }, 400)
    )
  })
  console.log('3) 首页滚动后 dock 位移:', nav.moved, 'px | 页面可滚:', nav.bodyScrollable)
  await page.screenshot({ path: OUT + 'home-after-login.png' })

  // 5) 退出登录
  await page.goto(BASE + '#/profile', { waitUntil: 'networkidle' })
  await sleep(700)
  await page.waitForSelector('.logout')
  await page.screenshot({ path: OUT + 'profile.png' })
  await page.click('.logout')
  await sleep(900)
  console.log('4) 退出登录后  →  实际:', page.url())

  // 6) 退出后再访问业务页应被拦截
  await page.goto(BASE + '#/community', { waitUntil: 'networkidle' })
  await sleep(700)
  console.log('5) 退出后访问 #/community → 实际:', page.url())

  console.log('控制台错误:', errors.length ? errors : '无')
  await browser.close()
})()
