const { chromium } = require('D:/Node/node_global/node_modules/openclaw/node_modules/playwright-core')

const CHROME = 'C:/Users/32501/.agent-browser/browsers/chrome-155.0.8059.39/chrome.exe'
const BASE = 'http://localhost:5173/#'
const wait = (ms) => new Promise((r) => setTimeout(r, ms))
const ok = (l, c, e = '') => console.log(`${c ? 'PASS' : 'FAIL'}  ${l}${e ? ' — ' + e : ''}`)

async function nextStep(p) {
  await p.locator('.nav-next').click()
  await wait(350)
}

;(async () => {
  const b = await chromium.launch({ executablePath: CHROME })
  const p = await b.newPage({ viewport: { width: 430, height: 900 } })
  const errs = []
  p.on('pageerror', (e) => errs.push('PAGEERROR: ' + e.message))
  p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()) })

  // 登录
  await p.goto(BASE + '/login', { waitUntil: 'networkidle' })
  await p.fill('input[autocomplete="tel"]', '13800001111')
  await p.fill('input[autocomplete="one-time-code"]', '123456')
  await p.click('.lg-submit')
  await wait(1400)

  /* ========== 路径 A：普通症状 → 加权评分 ========== */
  await p.goto(BASE + '/consult', { waitUntil: 'networkidle' })
  await wait(500)
  ok('问诊页显示结构化问诊入口', await p.locator('.guide-cta').isVisible())

  await p.click('.guide-cta')
  await wait(700)
  ok('进入预问诊向导', p.url().includes('/preconsult'), p.url())
  ok('步骤进度显示 1/7', (await p.locator('.h-step').textContent()).trim() === '1/7')
  ok('首步下一步禁用（未选宠物）', await p.locator('.nav-next').isDisabled() === false) // 有默认选中

  // Step1 选宠物（默认已选麻薯）
  await p.locator('.opt.pet').first().click()
  await nextStep(p)

  // Step2 部位
  await p.locator('.chip', { hasText: '消化系统' }).click()
  await nextStep(p)

  // Step3 症状
  await p.locator('.opt', { hasText: '呕吐' }).first().click()
  await nextStep(p)

  // Step4 持续时长
  await p.locator('.opt', { hasText: '超过一周' }).click()
  await nextStep(p)

  // Step5 严重程度
  await p.locator('.opt', { hasText: '精神差' }).click()
  await nextStep(p)

  // Step6 伴随症状
  await p.locator('.opt', { hasText: '精神萎靡' }).click()
  await nextStep(p)

  // Step7 补充
  ok('到达最后一步 7/7', (await p.locator('.h-step').textContent()).trim() === '7/7')
  await p.fill('.note', '吐的是黄水，一天两次，精神比平时差')
  await p.locator('.attach').click()
  await wait(300)
  await p.locator('.nav-next').click()
  await wait(900)

  ok('生成报告并跳转', p.url().includes('/report/rp'), p.url())
  ok('报告封面显示', await p.locator('.cover-title').isVisible())
  ok('报告类型标签为 AI', (await p.locator('.cover-kind').textContent()).includes('AI'))
  ok('主诉含症状 chip', (await p.locator('.cv-chip').count()) > 0)
  ok('分诊结论卡存在', await p.locator('.triage').isVisible())
  ok('评分依据区块存在', await p.locator('.score').isVisible())

  const scoreTxt = await p.locator('.score-n').textContent()
  const score = parseInt(scoreTxt)
  ok('加权评分正确（时长3+严重4+伴随3=10）', score === 10, scoreTxt.trim())
  const factors = await p.locator('.factors li').count()
  ok('评分依据列出加分项', factors >= 3, `${factors} 项`)
  const triageCls = await p.locator('.triage').first().getAttribute('class')
  ok('分级为 urgent', triageCls.includes('urgent'), triageCls)

  // 闭环 1：存入健康档案
  await p.locator('.bar-ic').first().click()
  await wait(700)
  ok('存档后按钮变为已存档', (await p.locator('.bar-ic').first().textContent()).includes('已存档'))

  // 闭环 2：用药 / 复查提醒
  await p.locator('.bar-ic').nth(1).click()
  await wait(700)
  ok('提醒后按钮变为已设提醒', (await p.locator('.bar-ic').nth(1).textContent()).includes('已设提醒'))

  // 验证档案页真的有这条记录
  await p.goto(BASE + '/pet/mochi', { waitUntil: 'networkidle' })
  await wait(800)
  const bodyTxt = await p.locator('body').innerText()
  ok('健康档案出现问诊报告记录', bodyTxt.includes('问诊报告'))

  // 验证日程页真的有提醒
  await p.goto(BASE + '/schedule', { waitUntil: 'networkidle' })
  await wait(800)
  const schedTxt = await p.locator('body').innerText()
  ok('日程页出现复查提醒', schedTxt.includes('复查') || schedTxt.includes('复诊'))

  /* ========== 路径 B：高危症状 → 红旗中断 ========== */
  await p.goto(BASE + '/preconsult', { waitUntil: 'networkidle' })
  await wait(500)
  await p.locator('.opt.pet').first().click()
  await nextStep(p)
  await p.locator('.chip', { hasText: '呼吸循环' }).click()
  await nextStep(p)
  await p.locator('.opt', { hasText: '张嘴呼吸' }).click()
  await wait(400)
  ok('高危信号即时告警条出现', await p.locator('.rf').isVisible())
  ok('高危症状被标记为高危', (await p.locator('.opt.danger').count()) > 0)
  await nextStep(p)
  await p.locator('.opt', { hasText: '今天刚开始' }).click()
  await nextStep(p)
  await p.locator('.opt', { hasText: '轻微' }).click()
  await nextStep(p)
  await nextStep(p) // 跳过伴随
  await p.locator('.nav-next').click()
  await wait(900)

  const triageCls2 = await p.locator('.triage').first().getAttribute('class')
  ok('红旗症状判为 emergency', triageCls2.includes('emergency'), triageCls2)
  const fText = await p.locator('.factors').innerText()
  ok('评分依据标注高危信号', fText.includes('高危信号'), fText.split('\n')[0])

  /* ========== 路径 C：记录页可回溯报告 ========== */
  await p.goto(BASE + '/records', { waitUntil: 'networkidle' })
  await wait(700)
  const recCount = await p.locator('.rec').count()
  ok('记录页包含生成的报告', recCount >= 7, `${recCount} 条`)
  await p.locator('.rec').first().click()
  await wait(700)
  ok('点击记录可打开报告', p.url().includes('/report/'), p.url())

  await p.screenshot({ path: 'E:/毕业设计/PetWiseService/.workbuddy/report.png', fullPage: true })

  console.log('\n控制台错误数:', errs.length)
  errs.slice(0, 5).forEach((e) => console.log('  -', e.slice(0, 120)))
  await b.close()
})()
