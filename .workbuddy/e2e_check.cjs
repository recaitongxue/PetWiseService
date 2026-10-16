/**
 * 端到端浏览器验收：登录 + 走遍核心页面 + 收集控制台/页面错误
 * 运行：node .workbuddy/e2e_check.cjs
 */
const { chromium } = require('C:/Users/admin/.workbuddy/binaries/node/workspace/node_modules/playwright-core')

const CHROME = 'C:/Users/admin/.agent-browser/browsers/chrome-155.0.8059.39/chrome.exe'
const BASE = 'http://localhost:5173'

const errors = []
const warnings = []

;(async () => {
  const browser = await chromium.launch({ executablePath: CHROME })
  const page = await browser.newPage({ viewport: { width: 430, height: 900 } })

  page.on('console', (msg) => {
    const t = msg.type()
    const text = msg.text()
    if (t === 'error') errors.push(`[console] ${text}`)
    else if (t === 'warning' && !/devtools|Download the Vue|Vue devtools/i.test(text)) {
      warnings.push(`[warn] ${text}`)
    }
  })
  page.on('pageerror', (err) => errors.push(`[pageerror] ${err.message}`))
  page.on('requestfailed', (req) => {
    const url = req.url()
    if (!/favicon|\.js\.map|sourcemap/i.test(url)) {
      errors.push(`[reqfail] ${req.failure()?.errorText || ''} ${url}`)
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

  // ---- 登录 ----
  await step('打开登录页', async () => {
    await page.goto(`${BASE}/#/login`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(800)
  })

  await step('手机号+验证码登录', async () => {
    await page.waitForSelector('input.f-control[type="tel"]', { timeout: 8000 })
    // 手机号
    await page.fill('input.f-control[type="tel"]', '13800138000')
    // 获取验证码
    await page.click('button.f-action')
    await page.waitForTimeout(1500)
    // 6 位分格验证码
    const cells = await page.$$('.code-box')
    if (cells.length !== 6) throw new Error(`验证码分格数异常: ${cells.length}`)
    for (let i = 0; i < 6; i++) await cells[i].fill('8')
    // 勾选协议
    const agree = await page.$('input.agree-box')
    if (agree && !(await agree.isChecked())) await agree.click()
    // 提交
    await page.click('button.lg-submit')
    await page.waitForTimeout(3500)
    const url = page.url()
    if (!url.includes('/home')) {
      const toast = await page.evaluate(() => document.querySelector('#app').innerText.slice(0, 150))
      throw new Error(`登录后未跳转 home，当前: ${url}；页面: ${toast}`)
    }
  })

  // ---- 走遍页面 ----
  const pages = [
    ['/#/home', '首页'],
    ['/#/consult/ai', 'AI 问诊'],
    ['/#/doctors', '医生列表'],
    ['/#/community', '社区'],
    ['/#/messages', '消息列表'],
    ['/#/contacts', '通讯录'],
    ['/#/pets', '宠物档案'],
    ['/#/schedule', '日程'],
    ['/#/records', '问诊记录'],
    ['/#/favorites', '收藏'],
    ['/#/recognize', '拍照识别'],
    ['/#/profile', '我的'],
    ['/#/account', '账号设置']
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
          hasError: /加载失败|请求失败|网络错误|500|Internal Server/i.test(text),
          // 登录页拦截？
          isLogin: location.hash.includes('/login')
        }
      })
      if (info.isLogin) throw new Error('被重定向到登录页（登录态丢失）')
      if (info.textLen < 20) throw new Error(`页面内容过少(${info.textLen}字符)，可能白屏`)
      if (info.hasError) throw new Error(`页面显示错误文案: ${(await page.evaluate(() => document.querySelector('#app').innerText)).slice(0, 120)}`)
    })
  }

  // ---- AI 问诊实际发一次消息（验证 triage 联通） ----
  await step('AI 问诊发送消息', async () => {
    await page.goto(`${BASE}/#/consult/ai`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(1500)
    const input = await page.$('.composer-input')
    if (!input) throw new Error('找不到问诊输入框(.composer-input)')
    await input.fill('狗狗一直挠耳朵是怎么回事')
    await page.waitForTimeout(300)
    const sendBtn = await page.$('.composer-send')
    if (!sendBtn) throw new Error('找不到发送按钮(.composer-send)')
    const disabled = await sendBtn.isDisabled()
    if (disabled) throw new Error('发送按钮处于禁用态（输入未生效？）')
    await sendBtn.click()
    await page.waitForTimeout(5000)
    const text = await page.evaluate(() => document.querySelector('#app').innerText)
    if (!text.includes('狗狗一直挠耳朵')) throw new Error('发送后未见消息上屏')
    if (!/挠耳|耳道|中耳炎|螨虫|建议|医院|就诊|观察/.test(text)) {
      throw new Error('未收到 AI 分诊回复')
    }
    console.log('     问诊回复已渲染')
  })

  await browser.close()

  console.log('\n========== 结果 ==========')
  console.log(`错误 ${errors.length} 个，警告 ${warnings.length} 个`)
  if (errors.length) {
    console.log('\n--- 错误明细 ---')
    errors.slice(0, 25).forEach((e) => console.log(' ', e.slice(0, 220)))
  }
  if (warnings.length) {
    console.log('\n--- 警告明细(前10) ---')
    warnings.slice(0, 10).forEach((w) => console.log(' ', w.slice(0, 180)))
  }
  process.exit(errors.length ? 1 : 0)
})()
