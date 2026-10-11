/**
 * 底部导航重构 + 问诊中心 回归测试
 * 覆盖：导航固定性、问诊 tab 位置与高亮、问诊域归属、中心页入口、AI 页上下文
 */
const { chromium } = require('D:/Node/node_global/node_modules/openclaw/node_modules/playwright-core')
const CHROME = 'C:/Users/32501/.agent-browser/browsers/chrome-155.0.8059.39/chrome.exe'
const BASE = 'http://localhost:5173'
const wait = (ms) => new Promise((r) => setTimeout(r, ms))

let pass = 0
let fail = 0
function ok(label, cond, extra = '') {
  if (cond) {
    pass++
    console.log(`  PASS  ${label}${extra ? ' — ' + extra : ''}`)
  } else {
    fail++
    console.log(`  FAIL  ${label}${extra ? ' — ' + extra : ''}`)
  }
}

;(async () => {
  const browser = await chromium.launch({ executablePath: CHROME })
  const page = await browser.newPage({ viewport: { width: 430, height: 900 } })
  const errors = []
  page.on('console', (m) => {
    if (m.type() === 'error') errors.push(m.text())
  })

  // ---- 登录 ----
  await page.goto(`${BASE}/#/login`, { waitUntil: 'networkidle' })
  await page.fill('input[autocomplete="tel"]', '13800001111')
  await page.fill('input[autocomplete="one-time-code"]', '123456')
  await page.click('.lg-submit')
  await wait(1400)

  // ---- 1. 导航结构 ----
  await page.goto(`${BASE}/#/home`, { waitUntil: 'networkidle' })
  await wait(600)
  const labels = await page.locator('.dock-item .dock-label').allInnerTexts()
  ok('底部 tab 数量为 4（+1 中央核心入口）', labels.length === 4, labels.join('/'))
  ok('tab 均带文字标签（非纯图标）', labels.every((x) => x.trim().length > 0), labels.join('/'))

  const fabText = (await page.locator('.dock-fab').innerText()).trim()
  ok('中央核心入口为「问诊」且带文字', fabText.includes('问诊'), fabText)

  // ---- 2. tab 数量在 3~5 规范内 ----
  const total = labels.length + 1
  ok('一级目的地总数在 3~5 规范区间', total >= 3 && total <= 5, `${total} 个`)

  // ---- 3. 高亮互斥 ----
  const homeOn = await page.locator('.dock-item').first().getAttribute('class')
  const fabOnHome = await page.locator('.dock-fab').getAttribute('class')
  ok('首页时「今日」高亮', homeOn.includes('on'))
  ok('首页时问诊不误高亮', !fabOnHome.includes('on'))

  // ---- 4. 点击中央入口进入问诊中心 ----
  await page.click('.dock-fab')
  await wait(800)
  ok('点击中央入口跳转 /consult', page.url().includes('#/consult'), page.url().split('#')[1])
  const fabOn = await page.locator('.dock-fab').getAttribute('class')
  ok('问诊中心时中央入口高亮', fabOn.includes('on'))

  const hubTitle = await page.locator('.hub .title').innerText()
  ok('中心页标题为「问诊」', hubTitle.trim() === '问诊', hubTitle.trim())

  // ---- 5. 中心页三大入口 ----
  const entries = await page.locator('.entry').count()
  ok('中心页含 3 个主入口', entries === 3, `${entries} 个`)
  const hrefs = await page.locator('.entry').evaluateAll((els) => els.map((e) => e.getAttribute('href')))
  ok(
    '入口覆盖 预问诊 / AI 问诊 / 找医生',
    hrefs.some((h) => h.includes('/preconsult')) &&
      hrefs.some((h) => h.includes('/consult/ai')) &&
      hrefs.some((h) => h.includes('/doctors')),
    hrefs.join(' , ')
  )
  const quotaTxt = await page.locator('.quota').innerText()
  ok('中心页显示 AI 免费额度', /剩余\s*\d+\/\d+/.test(quotaTxt), quotaTxt.replace(/\n/g, ' ').trim())

  // ---- 6. 问诊域子路由持续高亮 ----
  for (const [path, name] of [
    ['/preconsult', '结构化预问诊'],
    ['/consult/ai', 'AI 智能问诊'],
    ['/doctors', '医生列表'],
    ['/records', '问诊记录']
  ]) {
    await page.goto(`${BASE}/#${path}`, { waitUntil: 'networkidle' })
    await wait(450)
    const cls = await page.locator('.dock-fab').getAttribute('class')
    ok(`${name} 页面时问诊 tab 保持高亮`, cls.includes('on'), path)
  }

  // ---- 7. AI 页未被 hub 顶掉 ----
  await page.goto(`${BASE}/#/consult/ai`, { waitUntil: 'networkidle' })
  await wait(500)
  const hasInput = await page.locator('.consult textarea, .consult input[type="text"]').count()
  ok('AI 问诊页仍可直接输入症状', hasInput > 0, `${hasInput} 个输入框`)

  // ---- 8. 识别结果上下文仍可带入 ----
  await page.goto(`${BASE}/#/consult/ai?pet=%E8%B1%86%E8%B1%86&note=%E8%AF%86%E5%88%AB%E7%BB%93%E6%9E%9C`, {
    waitUntil: 'networkidle'
  })
  await wait(500)
  const ctx = await page.locator('.ctx-banner').count()
  ok('拍照/品种识别结果可带入 AI 问诊', ctx > 0, `${ctx} 个上下文横幅`)

  // ---- 9. 导航固定性（滚动不动） ----
  await page.goto(`${BASE}/#/home`, { waitUntil: 'networkidle' })
  await wait(600)
  const before = await page.locator('.dock').boundingBox()
  await page.evaluate(() => {
    document.querySelector('.app-main').scrollTop = 99999
  })
  await wait(500)
  const after = await page.locator('.dock').boundingBox()
  const dy = Math.abs(after.y - before.y)
  ok('内容滚动时底部导航不位移', dy < 1, `位移 ${dy.toFixed(1)}px`)

  const shellH = await page.evaluate(() => document.querySelector('.app-shell').getBoundingClientRect().height)
  ok('外壳高度锁定（未突破视口）', Math.abs(shellH - 900) < 2, `${shellH}px`)

  ok('无控制台报错', errors.filter((e) => !e.includes('fonts.g')).length === 0, errors.slice(0, 2).join(' | '))

  console.log(`\n  结果：${pass} 通过 / ${fail} 失败`)
  await browser.close()
  process.exit(fail ? 1 : 0)
})()
