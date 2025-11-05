<template>
  <a-card title="AI 模型配置">
    <a-space style="margin-bottom: 12px">
      <a-button type="primary" @click="openCreate">添加模型</a-button>
    </a-space>
    <a-table :dataSource="items" :columns="columns" rowKey="id">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button size="small" @click="setDefault(record.id)" :disabled="record.is_default">设为默认</a-button>
            <a-button size="small" danger @click="remove(record.id)">删除</a-button>
          </a-space>
        </template>
      </template>
    </a-table>

    <a-modal v-model:open="open" title="AI 模型" @ok="submit">
      <a-form :model="form">
        <a-form-item label="供应商"><a-input v-model:value="form.provider" placeholder="Volcengine/DeepSeek" /></a-form-item>
        <a-form-item label="模型"><a-input v-model:value="form.model" placeholder="模型名" /></a-form-item>
        <a-form-item label="API Key"><a-input v-model:value="form.api_key" /></a-form-item>
        <a-form-item label="Base URL"><a-input v-model:value="form.base_url" /></a-form-item>
        <a-form-item label="默认"><a-switch v-model:checked="form.is_default" /></a-form-item>
      </a-form>
    </a-modal>
  </a-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import axios from 'axios'

const items = ref([])
const open = ref(false)
const form = reactive({ provider: '', model: '', api_key: '', base_url: '', is_default: false })

const columns = [
  { title: 'ID', dataIndex: 'id' },
  { title: '供应商', dataIndex: 'provider' },
  { title: '模型', dataIndex: 'model' },
  { title: '默认', dataIndex: 'is_default' },
  { title: '操作', key: 'actions' }
]

async function load() {
  const { data } = await axios.get('/system/ai-models')
  items.value = data
}

function openCreate() {
  Object.assign(form, { provider: '', model: '', api_key: '', base_url: '', is_default: false })
  open.value = true
}

async function submit() {
  await axios.post('/system/ai-models', form)
  open.value = false
  await load()
}

async function setDefault(id) {
  await axios.post(`/system/ai-models/${id}/set-default`)
  await load()
}

async function remove(id) {
  await axios.delete(`/system/ai-models/${id}`)
  await load()
}

onMounted(load)
</script>


