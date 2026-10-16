/**
 * 布局铁律验收（移植自旧 check-nav.cjs，本机路径 + 断言版）：
 * 1. 滚动 .app-main 时底部 Dock 不位移（静态 flex 项，非悬浮）
 * 2. window 本身不滚动（滚动容器是 .app-main 不是 window）
 * 3. body 不可滚动（外壳 height:100dvh 锁死）
 * 运行：node .workbuddy/e2e_layout.cjs
 */
const { chromium } = require('C:/Users/admin/.workbuddy/binaries/node/workspace/node_modules/playwright-core')

const CHROME = 'C:/Users/admin/.agent-browser/browsers/chrome-155.0.8059.39/chrome.exe'
const BASE = 'http://localhost:5173'

const PAGES = [
  ['/#/home', '首页'],
  ['/#/community', '社区'],
  ['/#/chat', '消息'],
  ['/#/schedule', '日程'],
  ['/#/consult/ai', 'AI 问诊'],
  ['/#/records', '记录'],
  ['/#/profile', '我的']
]

const errors = []

;(async () => {
  const browser = await chromium.launch({ executablePath: CHROME })
  const page = await browser.newPage({ viewport: { width: 430, height: 900 } })

  // 登录
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

  for (const [hash, name] of PAGES) {
    try {
      await page.goto(BASE + hash, { waitUntil: 'networkidle' })
      await page.waitForTimeout(1600)

      const probe = () => page.evaluate(() => {
        const dock = document.querySelector('.dock')
        const main = document.querySelector('.app-main')
        const r = dock ? dock.getBoundingClientRect() : null
        return {
          pageScrollY: window.scrollY,
          bodyScrollable: document.body.scrollHeight > document.body.clientHeight + 1,
          mainScrollTop: main ? main.scrollTop : null,
          mainScrollable: main ? main.scrollHeight > main.clientHeight + 1 : null,
          dockTop: r ? Math.round(r.top) : null,
          dockBottom: r ? Math.round(r.bottom) : null
        }
      })

      const before = await probe()
      await page.evaluate(() => {
        const main = document.querySelector('.app-main')
        if (main) main.scrollTop = main.scrollHeight
        window.scrollTo(0, 99999)
      })
      await page.waitForTimeout(500)
      const after = await probe()

      const problems = []
      if (before.dockTop === null) problems.push('找不到 .dock')
      if (after.dockTop !== before.dockTop) {
        problems.push(`Dock 随滚动位移 ${after.dockTop - before.dockTop}px（应为 0，静态 flex 项）`)
      }
      if (after.pageScrollY !== 0) problems.push(`window 被滚动(pageScrollY=${after.pageScrollY})，滚动容器应为 .app-main`)
      if (after.bodyScrollable) problems.push('body 可滚动，外壳未用 height 锁死')
      if (!before.mainScrollable) {
        console.log(`OK   ${name}（内容不足一屏，跳过滚动项；dockTop=${before.dockTop} 稳定）`)
        continue
      }
      if (after.mainScrollTop === 0) problems.push('.app-main 未滚动（滚动事件被 window 吃了？）')

      if (problems.length) {
        console.log(`FAIL ${name}: ${problems.join('；')}`)
        errors.push(`${name}: ${problems.join('；')}`)
      } else {
        console.log(`OK   ${name}（dock 位移 0，window 未滚，main 滚 ${after.mainScrollTop}px）`)
      }
    } catch (e) {
      console.log(`FAIL ${name}: ${e.message}`)
      errors.push(`${name}: ${e.message}`)
    }
  }

  await browser.close()
  console.log('\n========== 结果 ==========')
  console.log(`布局错误 ${errors.length} 个`)
  if (errors.length) errors.forEach((e) => console.log(' ', e))
  process.exit(errors.length ? 1 : 0)
})()
