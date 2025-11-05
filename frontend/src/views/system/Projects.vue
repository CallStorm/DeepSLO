<template>
  <a-card title="项目管理">
    <a-space style="margin-bottom: 12px">
      <a-button type="primary" @click="sync" :loading="syncing">同步 metersphere 项目</a-button>
    </a-space>
    <a-table :dataSource="projects" :columns="columns" rowKey="id" />
  </a-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useProjectStore } from '../../stores/projects'

const store = useProjectStore()
const projects = ref([])
const syncing = ref(false)

const columns = [
  { title: 'ID', dataIndex: 'id' },
  { title: '项目名称', dataIndex: 'ms_name' },
  { title: '项目描述', dataIndex: 'ms_description' },
  { title: '创建时间', dataIndex: 'ms_createtime' },
  { title: 'MS ID', dataIndex: 'ms_id' },
]

async function load() {
  await store.fetchProjects()
  projects.value = store.projects
}

async function sync() {
  syncing.value = true
  try { await store.syncProjects() } finally { syncing.value = false }
  await load()
}

onMounted(load)
</script>


