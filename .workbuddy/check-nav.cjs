// 验证底部导航是否随页面滚动：滚动 .app-main 前后对比 dock 位置
const { chromium } = require('D:/Node/node_global/node_modules/openclaw/node_modules/playwright-core')

const CHROME = 'C:/Users/32501/.agent-browser/browsers/chrome-155.0.8059.39/chrome.exe'

;(async () => {
  const browser = await chromium.launch({ executablePath: CHROME })
  const page = await browser.newPage({ viewport: { width: 430, height: 900 } })
  await page.goto('http://localhost:5173/#/home', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1200)

  const probe = async () => {
    return page.evaluate(() => {
      const dock = document.querySelector('.dock')
      const main = document.querySelector('.app-main')
      const shell = document.querySelector('.app-shell')
      const r = dock ? dock.getBoundingClientRect() : null
      return {
        pageScrollY: window.scrollY,
        bodyScrollable: document.body.scrollHeight > document.body.clientHeight,
        mainScrollTop: main ? main.scrollTop : null,
        mainScrollable: main ? main.scrollHeight > main.clientHeight : null,
        shellHeight: shell ? Math.round(shell.getBoundingClientRect().height) : null,
        viewportH: window.innerHeight,
        dockTop: r ? Math.round(r.top) : null,
        dockBottom: r ? Math.round(r.bottom) : null
      }
    })
  }

  const before = await probe()

  // 把主内容区滚到底
  await page.evaluate(() => {
    const main = document.querySelector('.app-main')
    if (main) main.scrollTop = main.scrollHeight
    window.scrollTo(0, 99999)
  })
  await page.waitForTimeout(600)
  const after = await probe()

  console.log('BEFORE', JSON.stringify(before, null, 2))
  console.log('AFTER ', JSON.stringify(after, null, 2))
  console.log('dock 位移(px):', before.dockTop === null ? 'n/a' : after.dockTop - before.dockTop)

  await page.screenshot({ path: 'E:/毕业设计/PetWiseService/.workbuddy/nav-scrolled.png' })
  await browser.close()
})()
