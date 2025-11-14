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
// 在Docker生产环境中，nginx会代理API请求，使用相对路径（空字符串）
// 在开发环境中，使用环境变量或默认值
let apiBaseURL = ''
if (import.meta.env.PROD) {
    // 生产环境：如果nginx代理API，使用相对路径
    // 否则使用运行时配置或构建时环境变量
    if (typeof window !== 'undefined' && window.__ENV__ && window.__ENV__.VITE_API_BASE_URL) {
        apiBaseURL = window.__ENV__.VITE_API_BASE_URL
    } else if (import.meta.env.VITE_API_BASE_URL) {
        apiBaseURL = import.meta.env.VITE_API_BASE_URL
    }
    // 如果nginx代理了API，apiBaseURL保持为空字符串（相对路径）
} else {
    // 开发环境
    apiBaseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
}
axios.defaults.baseURL = apiBaseURL
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


