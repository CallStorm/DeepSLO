<template>
  <a-card title="metersphere 配置">
    <a-space direction="vertical" style="width: 480px">
      <a-form :model="form" layout="vertical">
        <a-form-item label="URL"><a-input v-model:value="form.url" placeholder="http://10.73.2.118:8000" /></a-form-item>
        <a-form-item label="AK"><a-input v-model:value="form.ak" /></a-form-item>
        <a-form-item label="SK"><a-input v-model:value="form.sk" /></a-form-item>
        <a-form-item label="启用"><a-switch v-model:checked="form.active" /></a-form-item>
        <a-space>
          <a-button type="primary" @click="save">保存</a-button>
          <a-button @click="load">刷新</a-button>
        </a-space>
      </a-form>
      <a-table :dataSource="items" :columns="columns" rowKey="id">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'actions'">
            <a-button size="small" @click="activate(record.id)" :disabled="record.active">设为当前</a-button>
          </template>
        </template>
      </a-table>
    </a-space>
  </a-card>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import axios from 'axios'

const form = reactive({ url: '', ak: '', sk: '', active: true })
const items = ref([])
const columns = [
  { title: 'ID', dataIndex: 'id' },
  { title: 'URL', dataIndex: 'url' },
  { title: 'AK', dataIndex: 'ak' },
  { title: 'Active', dataIndex: 'active' },
  { title: '操作', key: 'actions' }
]

async function load() {
  const { data } = await axios.get('/system/config/metersphere')
  items.value = data
}

async function save() {
  await axios.post('/system/config/metersphere', form)
  await load()
}

async function activate(id) {
  await axios.post(`/system/config/metersphere/${id}/activate`)
  await load()
}

onMounted(load)
</script>


