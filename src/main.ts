import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import { createPinia } from 'pinia'
import routes from 'virtual:generated-pages'
import App from './App.vue'

import '@unocss/reset/tailwind.css'
import './styles/main.css'
import 'uno.css'

const app = createApp(App)
const pinia = createPinia()

const router = createRouter({
  // 改成 Hash 模式
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes,
})

app.use(pinia)
app.use(router)
app.mount('#app')
