const { chromium } = require('D:/Node/node_global/node_modules/openclaw/node_modules/playwright-core')

const CHROME = 'C:/Users/32501/.agent-browser/browsers/chrome-155.0.8059.39/chrome.exe'
const BASE = 'http://localhost:5173/#'
const wait = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const b = await chromium.launch({ executablePath: CHROME })
  const p = await b.newPage({ viewport: { width: 430, height: 900 } })
  const errs = []
  p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()) })
  p.on('pageerror', (e) => errs.push('PAGEERROR: ' + e.message))

  const ok = (label, cond, extra = '') =>
    console.log(`${cond ? 'PASS' : 'FAIL'}  ${label}${extra ? ' — ' + extra : ''}`)

  // 登录
  await p.goto(BASE + '/login', { waitUntil: 'networkidle' })
  await p.fill('input[autocomplete="tel"]', '13800001111')
  await p.fill('input[autocomplete="one-time-code"]', '123456')
  await p.click('.lg-submit')
  await wait(1400)

  // 1. AI 问诊页结构
  await p.goto(BASE + '/consult', { waitUntil: 'networkidle' })
  await wait(500)
  ok('问诊页：宠物选择器', (await p.locator('.pet-chip').count()) >= 2)
  ok('问诊页：免费额度条', await p.locator('.quota').isVisible())
  ok('问诊页：症状标签分组', (await p.locator('.sym-row').count()) === 4)
  ok('问诊页：找医生入口', await p.locator('.find-doc').isVisible())

  // 2. 症状标签联动
  await p.locator('.sym-chip', { hasText: '呼吸异常' }).first().click()
  await wait(200)
  const inputVal = await p.locator('.composer-input').inputValue()
  ok('症状标签带入输入框', inputVal.includes('呼吸异常'), inputVal)

  // 3. 触发急诊分诊
  await p.fill('.composer-input', '狗狗突然呼吸困难，张嘴喘气')
  await p.click('.composer-send')
  await wait(2200)
  ok('急诊告警条出现', await p.locator('.er-bar').isVisible())
  ok('结构化分诊卡出现', await p.locator('.triage').isVisible())
  const lvl = await p.locator('.triage').first().getAttribute('class')
  ok('分诊级别为 emergency', lvl.includes('emergency'), lvl)
  ok('分诊卡含可能原因', (await p.locator('.t-causes li').count()) > 0)
  ok('分诊卡含建议动作', (await p.locator('.t-actions li').count()) > 0)

  const quotaLeft = await p.locator('.quota b').textContent()
  ok('额度已扣减', quotaLeft.trim() === '2/3', quotaLeft.trim())

  // 4. 转真人医生（携带病例摘要）
  await p.locator('.er-btn').click()
  await wait(900)
  const url1 = p.url()
  ok('跳转到医生列表并带急诊科室', url1.includes('/doctors') && url1.includes('dept=er'), url1)
  ok('医生页显示 AI 病例摘要卡', await p.locator('.case-card').isVisible())
  ok('急诊科室有医生', (await p.locator('.doc').count()) > 0)

  // 5. 医生详情 + 选择问诊方式
  await p.locator('.doc').first().click()
  await wait(900)
  ok('进入医生详情', p.url().includes('/doctor/'), p.url())
  ok('详情页显示病例摘要', await p.locator('.summary').isVisible())
  ok('三种问诊方式', (await p.locator('.mode').count()) === 3)
  ok('医生评价可见', (await p.locator('.rv').count()) > 0)

  await p.locator('.mode').nth(2).click() // 视频
  await wait(200)
  const price = await p.locator('.pay-n').textContent()
  ok('选择视频后价格更新为 59', price.trim() === '¥59', price.trim())

  // 6. 下单进入问诊室
  await p.click('.pay-btn')
  await wait(1200)
  ok('进入真人问诊室', p.url().includes('/consultation/'), p.url())
  ok('问诊室显示病例摘要', await p.locator('.summary').isVisible())
  ok('视频方式显示通话卡', await p.locator('.call-card').isVisible())

  // 等待医生首条回复（脚本 setTimeout 1500 + 1200）
  await wait(3200)
  ok('医生自动接诊回复', (await p.locator('.bubble.them').count()) > 0)

  // 7. 追问推进到处方
  await p.fill('.composer-input', '需要用什么药吗？')
  await p.click('.composer-send')
  await wait(2600)
  await p.fill('.composer-input', '好的，还需要线下检查吗')
  await p.click('.composer-send')
  await wait(3600)
  const rx = await p.locator('.rx').count()
  ok('医生开具处方建议卡', rx > 0, `rx=${rx}`)

  // 8. 结束并评价
  await p.click('.end-btn')
  await wait(600)
  ok('评价弹层打开', await p.locator('.sheet').isVisible())
  await p.locator('.star').nth(4).click()
  await p.locator('.rate-tag').first().click()
  await p.click('.sheet-submit')
  await wait(1200)
  ok('评价后生成真人问诊报告', p.url().includes('/report/'), p.url())
  ok('报告类型标签为真人医生', (await p.locator('.cover-kind').textContent()).includes('真人'))
  ok('报告含医生建议', (await p.locator('.advice li').count()) > 0)
  ok('报告含用药方案', (await p.locator('.rx').count()) > 0)

  // 真人报告同样支持回流闭环
  await p.locator('.bar-ic').first().click()
  await wait(700)
  ok('真人报告可存入档案', (await p.locator('.bar-ic').first().textContent()).includes('已存档'))

  // 9. 问诊记录页回流
  await p.goto(BASE + '/records', { waitUntil: 'networkidle' })
  await wait(700)
  const all = await p.locator('.rec').count()
  ok('记录页含历史 + 新订单', all >= 6, `${all} 条`)
  await p.locator('.tab').nth(2).click()
  await wait(400)
  const human = await p.locator('.rec').count()
  ok('真人医生筛选生效', human >= 3, `${human} 条`)
  ok('记录页有找医生入口', await p.locator('.cta.solid').isVisible())

  await p.screenshot({ path: 'E:/毕业设计/PetWiseService/.workbuddy/records.png', fullPage: true })
  await p.goto(BASE + '/doctors', { waitUntil: 'networkidle' })
  await wait(600)
  await p.screenshot({ path: 'E:/毕业设计/PetWiseService/.workbuddy/doctors.png', fullPage: true })

  console.log('\n控制台错误数:', errs.length)
  errs.slice(0, 5).forEach((e) => console.log('  -', e.slice(0, 120)))
  await b.close()
})()
