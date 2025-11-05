<template>
  <a-card title="用户管理">
    <a-space style="margin-bottom: 12px">
      <a-button type="primary" @click="openCreate">新增用户</a-button>
    </a-space>
    <a-table :dataSource="users" :columns="columns" rowKey="id">
      <template #bodyCell="{ column, record, text }">
        <template v-if="column.dataIndex === 'is_admin'">{{ text ? '是' : '否' }}</template>
        <template v-else-if="column.dataIndex === 'is_active'">
          <a-switch :checked="record.is_active" @change="(checked) => toggleActive(record, checked)" />
        </template>
        <template v-else-if="column.key === 'actions'">
          <a-button type="link" v-if="auth.user?.is_admin" @click="openEdit(record)">编辑</a-button>
        </template>
      </template>
    </a-table>

    <a-modal v-model:open="modalOpen" title="用户" @ok="submit">
      <a-form :model="form">
        <a-form-item label="姓名"><a-input v-model:value="form.name" /></a-form-item>
        <a-form-item label="账号"><a-input v-model:value="form.username" :disabled="!!form.id" /></a-form-item>
        <a-form-item label="邮箱"><a-input v-model:value="form.email" /></a-form-item>
        <a-form-item label="密码"><a-input-password v-model:value="form.password" /></a-form-item>
        <a-form-item label="管理员"><a-switch v-model:checked="form.is_admin" /></a-form-item>
        <a-form-item label="启用"><a-switch v-model:checked="form.is_active" /></a-form-item>
      </a-form>
    </a-modal>
  </a-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useAuthStore } from '../../stores/auth'
import axios from 'axios'

const users = ref([])
const modalOpen = ref(false)
const form = reactive({ id: null, name: '', username: '', email: '', password: '', is_admin: false, is_active: true })
const auth = useAuthStore()

const columns = [
  { title: 'ID', dataIndex: 'id' },
  { title: '姓名', dataIndex: 'name' },
  { title: '账号', dataIndex: 'username' },
  { title: '邮箱', dataIndex: 'email' },
  { title: '管理员', dataIndex: 'is_admin' },
  { title: '启用', dataIndex: 'is_active' },
  { title: '操作', key: 'actions' },
]

async function load() {
  const { data } = await axios.get('/system/users')
  users.value = data
}

function openCreate() {
  Object.assign(form, { id: null, name: '', username: '', email: '', password: '', is_admin: false, is_active: true })
  modalOpen.value = true
}

function openEdit(record) {
  Object.assign(form, {
    id: record.id,
    name: record.name,
    username: record.username,
    email: record.email,
    password: '',
    is_admin: record.is_admin,
    is_active: record.is_active,
  })
  modalOpen.value = true
}

async function toggleActive(record, checked) {
  const original = record.is_active
  record.is_active = checked
  try {
    await axios.put(`/system/users/${record.id}`, { is_active: checked })
  } catch (e) {
    record.is_active = original
  }
}

async function submit() {
  if (form.id) {
    const payload = { name: form.name, email: form.email, is_admin: form.is_admin, is_active: form.is_active }
    if (form.password) payload.password = form.password
    await axios.put(`/system/users/${form.id}`, payload)
  } else {
    await axios.post('/system/users', { name: form.name, username: form.username, email: form.email, password: form.password, is_admin: form.is_admin, is_active: form.is_active })
  }
  modalOpen.value = false
  await load()
}

onMounted(load)
</script>


