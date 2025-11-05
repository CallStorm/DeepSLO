<template>
  <template v-if="isAuthed">
    <a-layout style="min-height: 100vh">
      <a-layout-sider v-model:collapsed="collapsed" collapsible :style="{ display: 'flex', flexDirection: 'column', position: 'relative' }">
      <div class="logo">
        <appstore-outlined class="logo-icon" />
        <span v-if="!collapsed" class="logo-text">DeepSLO</span>
      </div>
      <div class="project-switch">
        <a-select v-model:value="selectedProject" style="width: 100%" :options="projectOptions" />
      </div>
        <a-menu theme="dark" mode="inline" :selectedKeys="[selectedKey]" @click="onMenu" :style="{ flex: 1, overflow: 'auto' }">
        <a-menu-item key="probe">
          <template #icon><dashboard-outlined /></template>
          拨测信息
        </a-menu-item>
        <a-menu-item key="slo-screen">
          <template #icon><fund-outlined /></template>
          SLO大屏
        </a-menu-item>
        <a-menu-item key="slo-analysis">
          <template #icon><line-chart-outlined /></template>
          SLO分析
        </a-menu-item>
        <a-menu-item key="slo-settings">
          <template #icon><setting-outlined /></template>
          SLO设置
        </a-menu-item>
        <a-sub-menu v-if="me?.is_admin" key="system">
          <template #title>
            <span>
              <tool-outlined />
              <span v-if="!collapsed" class="submenu-title-text">系统管理</span>
            </span>
          </template>
          <a-menu-item key="sys-users">
            <template #icon><team-outlined /></template>
            用户管理
          </a-menu-item>
          <a-menu-item key="sys-projects">
            <template #icon><project-outlined /></template>
            项目管理
          </a-menu-item>
          <a-menu-item key="sys-ai">
            <template #icon><robot-outlined /></template>
            AI模型配置
          </a-menu-item>
          <a-menu-item key="sys-ms">
            <template #icon><tool-outlined /></template>
            metersphere配置
          </a-menu-item>
        </a-sub-menu>
        </a-menu>
        <template #trigger>
          <div class="ant-layout-sider-trigger user-trigger" :style="{ display: 'flex', alignItems: 'center', gap: '8px', padding: '0 16px' }">
            <a-dropdown :open="userMenuOpen" placement="top">
              <a class="user-footer-trigger" @click.stop.prevent="toggleUserMenu">
                <span class="user-left">
                  <user-outlined />
                  <span v-if="!collapsed" class="user-name">{{ me?.name || '未登录' }}</span>
                </span>
              </a>
              <template #overlay>
                <a-menu @click="onUserMenu">
                  <a-menu-item key="about">
                    <template #icon><info-circle-outlined /></template>
                    关于
                  </a-menu-item>
                  <a-menu-item key="help">
                    <template #icon><question-circle-outlined /></template>
                    帮助
                  </a-menu-item>
                  <a-menu-item key="change-password">
                    <template #icon><key-outlined /></template>
                    修改密码
                  </a-menu-item>
                  <a-menu-item key="logout">
                    <template #icon><logout-outlined /></template>
                    退出登录
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
            <span class="collapse-toggle" @click.stop="toggleCollapse">
              <menu-unfold-outlined v-if="collapsed" />
              <menu-fold-outlined v-else />
            </span>
          </div>
        </template>
      </a-layout-sider>
      <a-layout>
        <a-layout-header style="background:#fff; padding: 0 16px">
          <div class="app-header">
            <appstore-outlined class="header-logo" />
            <span class="header-title">DeepSLO</span>
          </div>
        </a-layout-header>
        <a-layout-content style="margin: 16px">
          <router-view />
        </a-layout-content>
      </a-layout>
    </a-layout>
    <a-modal v-model:open="changePwdOpen" title="修改密码" :okText="'提交'" :cancelText="'取消'" @ok="submitChangePwd">
      <a-form layout="vertical">
        <a-form-item label="原密码">
          <a-input-password v-model:value="changePwd.old" placeholder="输入原密码" />
        </a-form-item>
        <a-form-item label="新密码">
          <a-input-password v-model:value="changePwd.pwd" placeholder="输入新密码" />
        </a-form-item>
        <a-form-item label="确认新密码">
          <a-input-password v-model:value="changePwd.confirm" placeholder="再次输入新密码" />
        </a-form-item>
      </a-form>
    </a-modal>
  </template>
  <template v-else>
    <router-view />
  </template>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useProjectStore } from './stores/projects'
import {
  AppstoreOutlined,
  DashboardOutlined,
  FundOutlined,
  LineChartOutlined,
  SettingOutlined,
  TeamOutlined,
  ProjectOutlined,
  RobotOutlined,
  ToolOutlined,
  UserOutlined,
  MenuOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  QuestionCircleOutlined,
  InfoCircleOutlined,
  LogoutOutlined,
  KeyOutlined
} from '@ant-design/icons-vue'
import { Modal, message } from 'ant-design-vue'

const router = useRouter()
const auth = useAuthStore()
const projStore = useProjectStore()

const collapsed = ref(false)
const selectedKey = ref('slo-screen')
const selectedProject = ref(null)
const userMenuOpen = ref(false)

const me = computed(() => auth.user)
const isAuthed = computed(() => auth.isAuthenticated)
const projectOptions = computed(() => projStore.projects.map(p => ({ label: p.ms_name, value: p.id })))

function onMenu({ key }) {
  selectedKey.value = key
  const map = {
    'probe': '/probe',
    'slo-screen': '/slo-screen',
    'slo-analysis': '/slo-analysis',
    'slo-settings': '/slo-settings',
    'sys-users': '/system/users',
    'sys-projects': '/system/projects',
    'sys-ai': '/system/ai-models',
    'sys-ms': '/system/metersphere',
  }
  router.push(map[key] || '/')
}

function onUserMenu({ key }) {
  if (key === 'about') {
    Modal.info({ title: '关于 DeepSLO', content: 'DeepSLO 前端界面' })
  } else if (key === 'help') {
    Modal.info({ title: '帮助', content: '如需帮助，请联系管理员。' })
  } else if (key === 'change-password') {
    changePwdOpen.value = true
  } else if (key === 'logout') {
    logout()
  }
}

function toggleUserMenu() {
  userMenuOpen.value = !userMenuOpen.value
}

function toggleCollapse() {
  collapsed.value = !collapsed.value
}

function logout() {
  auth.logout()
  router.push('/login')
}

onMounted(async () => {
  await auth.fetchMe().catch(() => {})
  await projStore.fetchProjects().catch(() => {})
})

const changePwdOpen = ref(false)
const changePwd = ref({ old: '', pwd: '', confirm: '' })

function submitChangePwd() {
  if (!changePwd.value.pwd || changePwd.value.pwd !== changePwd.value.confirm) {
    message.error('两次输入的密码不一致')
    return
  }
  // TODO: 调用后端修改密码接口
  changePwdOpen.value = false
  changePwd.value = { old: '', pwd: '', confirm: '' }
  message.success('密码修改提交成功')
}
</script>

<style scoped>
.logo { color: #fff; text-align: center; font-weight: bold; padding: 16px 0; display: flex; align-items: center; justify-content: center; gap: 8px; }
.logo-icon { font-size: 20px; }
.logo-text { font-size: 16px; }
.project-switch { padding: 0 12px 12px; }
.user-footer { padding: 12px; color: #fff; cursor: pointer; border-top: 1px solid rgba(255,255,255,0.15); }
.user-footer-trigger { display: inline-flex; align-items: center; gap: 8px; color: inherit; }
.user-left { display: inline-flex; align-items: center; gap: 8px; }
.user-right { margin-left: auto; opacity: 0.85; }
.collapse-toggle { margin-left: auto; display: inline-flex; align-items: center; cursor: pointer; }
.user-name { margin-left: 8px; }
.app-header { display: flex; align-items: center; gap: 8px; }
.header-logo { font-size: 18px; color: #1677ff; }
.header-title { font-weight: 600; }
</style>


