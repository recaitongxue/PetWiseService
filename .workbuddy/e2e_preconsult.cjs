/**
 * 预问诊多步向导验收：6 步走完 → 生成问诊报告
 * 运行：node .workbuddy/e2e_preconsult.cjs
 */
const { chromium } = require('C:/Users/admin/.workbuddy/binaries/node/workspace/node_modules/playwright-core')

const CHROME = 'C:/Users/admin/.agent-browser/browsers/chrome-155.0.8059.39/chrome.exe'
const BASE = 'http://localhost:5173'

const errors = []

;(async () => {
  const browser = await chromium.launch({ executablePath: CHROME })
  const page = await browser.newPage({ viewport: { width: 430, height: 900 } })
  page.on('console', (m) => { if (m.type() === 'error') errors.push(`[console] ${m.text().slice(0, 180)}`) })
  page.on('pageerror', (e) => errors.push(`[pageerror] ${e.message.slice(0, 180)}`))

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

  // 进入预问诊
  await page.goto(`${BASE}/#/preconsult`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(2200)

  const stepText = async () => {
    const t = await page.evaluate(() => document.querySelector('#app').innerText)
    const m = t.match(/(\d)\s*\/\s*(\d+)/)
    return m ? { cur: Number(m[1]), total: Number(m[2]) } : null
  }

  let st = await stepText()
  console.log(`起始步骤: ${st ? st.cur + '/' + st.total : 'null'}`)
  if (!st || st.cur !== 1) throw new Error(`起始步骤异常: ${JSON.stringify(st)}`)
  const totalSteps = st.total

  // 最多 totalSteps+2 次点击，走完所有步
  for (let i = 0; i < totalSteps + 2; i++) {
    st = await stepText()
    if (!st) {
      console.log('步骤指示器消失（可能已生成报告并跳转）')
      break
    }
    // 每步先选第一个可选项（部位/症状/时长/严重度/伴随），让「下一步」可点
    const opt = await page.$('.opt:not(.on), .chip:not(.on), .q-opt:not(.on)')
    if (opt) {
      await opt.click()
      await page.waitForTimeout(400)
    }
    const next = await page.$('.nav-next')
    if (!next) throw new Error(`第 ${st.cur} 步找不到下一步按钮`)
    const disabled = await next.isDisabled()
    if (disabled) throw new Error(`第 ${st.cur} 步「下一步」被禁用（选项未生效？）`)
    const label = (await next.innerText()).trim()
    await next.click()
    console.log(`  第 ${st.cur}/${st.total} 步 → ${label}`)
    await page.waitForTimeout(900)

    if (/生成问诊报告/.test(label)) {
      // 提交后等报告页
      await page.waitForTimeout(4000)
      const url = page.url()
      const text = await page.evaluate(() => document.querySelector('#app').innerText)
      if (!url.includes('/report/')) throw new Error(`提交后未跳转报告页: ${url}`)
      if (!/分诊|建议|级别|紧急|观察|就诊/.test(text)) throw new Error('报告页缺少分诊内容')
      console.log('OK   报告已生成并跳转')
      break
    }
  }

  await browser.close()
  console.log('\n========== 结果 ==========')
  console.log(`错误 ${errors.length} 个`)
  if (errors.length) errors.slice(0, 10).forEach((e) => console.log(' ', e))
  process.exit(errors.length ? 1 : 0)
})()
