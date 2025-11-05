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
      <a-form :model="form" layout="vertical">
        <a-form-item label="模型名称">
          <a-input v-model:value="form.name" placeholder="给该模型起一个别名，如：默认对话模型" />
        </a-form-item>
        <a-form-item label="供应商">
          <a-select v-model:value="form.provider" placeholder="选择或输入供应商" :options="providerOptions" allowClear showSearch @change="onProviderChange" />
        </a-form-item>
        <a-form-item label="模型">
          <a-select v-if="modelOptions.length" v-model:value="form.model" :options="modelOptions" placeholder="选择模型" allowClear showSearch />
          <a-input v-else v-model:value="form.model" placeholder="输入模型名" />
        </a-form-item>
        <a-form-item label="API Key">
          <a-input v-model:value="form.api_key" />
        </a-form-item>
        <a-form-item label="Base URL">
          <a-input v-model:value="form.base_url" placeholder="https://..." />
        </a-form-item>
        <a-form-item label="默认">
          <a-switch v-model:checked="form.is_default" />
        </a-form-item>
      </a-form>
    </a-modal>
  </a-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import axios from 'axios'

const items = ref([])
const open = ref(false)
const form = reactive({ name: '', provider: '', model: '', api_key: '', base_url: '', is_default: false })

// 预置供应商与模型
const PRESETS = {
  DeepSeek: {
    base_url: 'https://api.deepseek.com',
    models: ['deepseek-chat']
  },
  火山引擎: {
    base_url: 'https://ark.cn-beijing.volces.com/api/v3',
    models: ['doubao-seed-1-6-250615', 'deepseek-v3-250324']
  }
}

const providerOptions = Object.keys(PRESETS).map(k => ({ label: k, value: k }))
const modelOptions = ref([])

const columns = [
  { title: 'ID', dataIndex: 'id' },
  { title: '模型名称', dataIndex: 'name' },
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
  Object.assign(form, { name: '', provider: '', model: '', api_key: '', base_url: '', is_default: false })
  modelOptions.value = []
  open.value = true
}

async function submit() {
  await axios.post('/system/ai-models', form)
  open.value = false
  await load()
}

function onProviderChange(val) {
  const preset = PRESETS[val]
  if (preset) {
    // 自动填充 Base URL 与模型下拉
    form.base_url = preset.base_url
    modelOptions.value = preset.models.map(m => ({ label: m, value: m }))
    if (!preset.models.includes(form.model)) {
      form.model = ''
    }
  } else {
    modelOptions.value = []
  }
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


