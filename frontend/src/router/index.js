import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const Login = () => import('../views/Login.vue')
const Dashboard = () => import('../views/Dashboard.vue')
const Probe = () => import('../views/Probe.vue')
const SLOScreen = () => import('../views/SLOScreen.vue')
const SLOAnalysis = () => import('../views/SLOAnalysis.vue')
const SLOSettings = () => import('../views/SLOSettings.vue')
const SysUsers = () => import('../views/system/Users.vue')
const SysProjects = () => import('../views/system/Projects.vue')
const SysAIModels = () => import('../views/system/AIModels.vue')
const SysMS = () => import('../views/system/Metersphere.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: Login },
    { path: '/', component: Dashboard },
    { path: '/probe', component: Probe },
    { path: '/slo-screen', component: SLOScreen },
    { path: '/slo-analysis', component: SLOAnalysis },
    { path: '/slo-settings', component: SLOSettings },
    { path: '/system/users', component: SysUsers },
    { path: '/system/projects', component: SysProjects },
    { path: '/system/ai-models', component: SysAIModels },
    { path: '/system/metersphere', component: SysMS },
  ]
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.path !== '/login' && !auth.isAuthenticated) {
    return '/login'
  }
})

export default router


