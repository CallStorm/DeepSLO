import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import axios from 'axios'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(Antd)

// Configure API base URL and restore auth header on reload
// 在 Docker 环境中，前端和后端在同一个容器，使用相对路径
// 在开发环境中，使用环境变量或默认值
axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://127.0.0.1:8000' : '')
const storedToken = localStorage.getItem('token')
if (storedToken) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`
}

// Add response interceptor to handle 401 Unauthorized
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid, clear auth and redirect to login
      const authStore = useAuthStore()
      authStore.logout()
      router.push('/login')
    }
    return Promise.reject(error)
  }
)

app.mount('#app')


