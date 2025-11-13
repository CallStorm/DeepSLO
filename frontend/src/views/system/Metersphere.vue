<template>
  <a-card title="MeterSphere 配置">
    <a-space direction="vertical" style="width: 720px">
      <a-form :model="form" layout="vertical">
        <a-row :gutter="12">
          <a-col :span="10">
            <a-form-item label="URL">
              <a-input v-model:value="form.url" placeholder="http://10.73.2.118:8000" />
            </a-form-item>
          </a-col>
          <a-col :span="7">
            <a-form-item label="AK">
              <a-input v-model:value="form.ak" />
            </a-form-item>
          </a-col>
          <a-col :span="7">
            <a-form-item label="SK">
              <a-input v-model:value="form.sk" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="12">
          <a-col :span="6">
            <a-form-item label="Active">
              <a-switch
                v-model:checked="form.active"
                checked-children="启用"
                un-checked-children="停用"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-space>
          <a-button type="primary" @click="save">保存</a-button>
          <a-button @click="load">刷新</a-button>
        </a-space>
      </a-form>
    </a-space>
  </a-card>
</template>

<script setup>
import { reactive, onMounted } from 'vue'
import axios from 'axios'

const form = reactive({ id: null, url: '', ak: '', sk: '', active: true })

async function load() {
  const { data } = await axios.get('/system/config/metersphere')
  const first = Array.isArray(data) ? data[0] : data
  if (first) {
    form.id = first.id
    form.url = first.url || ''
    form.ak = first.ak || ''
    form.sk = first.sk || ''
    form.active = typeof first.active === 'boolean' ? first.active : true
  } else {
    form.id = null
    form.url = ''
    form.ak = ''
    form.sk = ''
    form.active = true
  }
}

async function save() {
  const payload = { url: form.url, ak: form.ak, sk: form.sk, active: form.active }
  await axios.put('/system/config/metersphere', payload)
  await load()
}

onMounted(load)
</script>


