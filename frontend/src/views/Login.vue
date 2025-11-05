<template>
  <div class="login-wrap">
    <div class="slo-bg">
      <div class="slo-circles"></div>
      <div class="slo-grid"></div>
      <div class="slo-title">Service Level Objectives</div>
    </div>
    <div class="login-panel">
      <div class="hero-title">DeepSLO</div>
      <a-card title="登录" class="login-card">
        <a-form @finish="onFinish" :model="form">
          <a-form-item name="username" :rules="[{ required: true, message: '请输入账号' }]">
            <a-input v-model:value="form.username" placeholder="账号" />
          </a-form-item>
          <a-form-item name="password" :rules="[{ required: true, message: '请输入密码' }]">
            <a-input-password v-model:value="form.password" placeholder="密码" />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" html-type="submit" block :loading="loading">登录</a-button>
          </a-form-item>
        </a-form>
      </a-card>
    </div>
  </div>
  </template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const form = reactive({ username: 'admin', password: 'admin' })
const loading = ref(false)

async function onFinish() {
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    router.push('/')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap { position: relative; min-height: 100vh; background: radial-gradient(1200px 600px at 10% 20%, rgba(22,119,255,0.15), transparent 60%), linear-gradient(135deg, #f0f5ff 0%, #f6ffed 100%); overflow: hidden; }
.login-panel { position: absolute; top: 50%; left: 66%; transform: translate(-50%, -50%); display: flex; flex-direction: column; align-items: stretch; gap: 16px; padding: 16px; }
.login-card { width: 440px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); backdrop-filter: blur(2px); }
.slo-bg { position: absolute; inset: 0; pointer-events: none; }
.slo-circles { position: absolute; left: -120px; bottom: -120px; width: 480px; height: 480px; background: radial-gradient(circle at center, rgba(82,196,26,0.18), rgba(82,196,26,0.05) 60%, transparent 70%); filter: blur(0.5px); }
.slo-grid { position: absolute; right: 20%; top: 15%; width: 520px; height: 320px; background-image: linear-gradient(rgba(24,144,255,0.12) 1px, transparent 1px), linear-gradient(90deg, rgba(24,144,255,0.12) 1px, transparent 1px); background-size: 24px 24px; border-radius: 12px; transform: rotate(-4deg); }
.slo-title { position: absolute; left: 48px; top: 64px; font-weight: 700; font-size: 24px; color: rgba(0,0,0,0.35); letter-spacing: 1px; }
.hero-title { font-weight: 800; font-size: 40px; letter-spacing: 1px; color: rgba(0,0,0,0.65); text-align: left; }
</style>


