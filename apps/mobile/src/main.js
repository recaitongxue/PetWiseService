import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './styles/tokens.css'
import './styles/base.css'

const app = createApp(App)

// 编排入场动效：进入视口时添加 .in。支持 --d 自定义错峰延迟
app.directive('reveal', {
  mounted(el, binding) {
    el.classList.add('reveal')
    if (binding.value && binding.value.delay) {
      el.style.setProperty('--d', `${binding.value.delay}ms`)
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            el.classList.add('in')
            io.unobserve(el)
          }
        })
      },
      { threshold: 0.12, rootMargin: '0px 0px -8% 0px' }
    )
    io.observe(el)
  }
})

app.use(router)
app.mount('#app')
