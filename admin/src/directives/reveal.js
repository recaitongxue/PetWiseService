// v-reveal：IntersectionObserver 入场动效（与用户端一致）
const observed = new WeakMap()

export const revealDirective = {
  mounted(el, binding) {
    el.classList.add('reveal')
    const delay = binding.value?.delay || 0
    el.style.setProperty('--d', `${delay}ms`)
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            el.classList.add('in')
            io.unobserve(el)
          }
        })
      },
      { threshold: 0.08 }
    )
    io.observe(el)
    observed.set(el, io)
  },
  unmounted(el) {
    observed.get(el)?.disconnect()
    observed.delete(el)
  }
}
