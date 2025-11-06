<template>
  <a-card title="拨测信息">
    <div style="margin-bottom: 16px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
      <a-alert v-if="!selectedMsId" type="warning" message="请先在项目菜单选择项目" show-icon />
      <a-button type="primary" :loading="syncing" @click="onSync" :disabled="!selectedMsId">同步拨测信息</a-button>
      <a-button @click="loadData" :loading="loading" :disabled="!selectedMsId">刷新</a-button>
    </div>

    <a-empty v-if="!probe && !loading" description="暂无拨测信息" />

    <a-skeleton :loading="loading" active v-else-if="loading" />

    <a-descriptions v-else :column="2" bordered size="small">
      <a-descriptions-item label="拨测名称">{{ probe?.name }}</a-descriptions-item>
      <a-descriptions-item label="拨测ID">{{ probe?.scenario_id }}</a-descriptions-item>
      <a-descriptions-item label="优先级">{{ probe?.priority }}</a-descriptions-item>
      <a-descriptions-item label="状态">{{ probe?.status }}</a-descriptions-item>
      <a-descriptions-item label="步骤数">{{ probe?.step_total }}</a-descriptions-item>
      <a-descriptions-item label="请求通过率">{{ probe?.request_pass_rate }}</a-descriptions-item>
      <a-descriptions-item label="最近报告状态">{{ probe?.last_report_status }}</a-descriptions-item>
      <a-descriptions-item label="最近报告ID">{{ probe?.last_report_id }}</a-descriptions-item>
      <a-descriptions-item label="编号">{{ probe?.num }}</a-descriptions-item>
      <a-descriptions-item label="环境">{{ probe?.environment_name }}</a-descriptions-item>
      <a-descriptions-item label="定时开启">{{ probe?.schedule_enable ? '是' : '否' }}</a-descriptions-item>
      <a-descriptions-item label="Cron">
        <template v-if="probe?.schedule_cron">
          <a-tooltip :title="humanizeCron(probe?.schedule_cron)">
            <span>{{ probe?.schedule_cron }}</span>
          </a-tooltip>
          <span style="color:#999; margin-left:8px;">{{ humanizeCron(probe?.schedule_cron) }}</span>
        </template>
        <template v-else>-</template>
      </a-descriptions-item>
      <a-descriptions-item label="下次执行时间">{{ fmtDatetime(probe?.next_trigger_time) }}</a-descriptions-item>
      <a-descriptions-item label="创建时间">{{ fmtDatetime(probe?.create_time) }}</a-descriptions-item>
      <a-descriptions-item label="更新时间">{{ fmtDatetime(probe?.update_time) }}</a-descriptions-item>
    </a-descriptions>
  </a-card>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import axios from 'axios'
import { message } from 'ant-design-vue'
import { useProjectStore } from '../stores/projects'

const projectStore = useProjectStore()
const loading = ref(false)
const syncing = ref(false)
const selectedMsId = ref('')
const probe = ref(null)

function fmtDatetime(v) {
  if (!v) return '-'
  try { return new Date(v).toLocaleString() } catch { return v }
}

function humanizeCron(expr) {
  if (!expr || typeof expr !== 'string') return '无'
  const parts = expr.trim().split(/\s+/)
  // Quartz: seconds minutes hours day-of-month month day-of-week [year]
  if (parts.length < 6) return '无法解析'
  const [sec, min, hour, dom, mon, dow] = parts

  // Every N minutes (Quartz): 0 */N * * * ?
  const minStep = /^\*\/(\d+)$/.exec(min)
  if (sec === '0' && minStep && (hour === '*' || hour === '*/1') && dom === '*' && mon === '*' && (dow === '?' || dow === '*')) {
    return `每${minStep[1]}分钟`
  }

  // Every N hours (Quartz): 0 0 */N * * ?
  const hourStep = /^\*\/(\d+)$/.exec(hour)
  if (sec === '0' && (min === '0' || min === '00') && hourStep && dom === '*' && mon === '*' && (dow === '?' || dow === '*')) {
    return `每${hourStep[1]}小时`
  }

  // Every N hours starting at HH:MM (Quartz): 0 MM HH/N * * ?
  const hourStepStart = /^(\d+)$/.exec(min) && /^\d+\/(\d+)$/.exec(hour)
  if (sec === '0' && hourStepStart && dom === '*' && mon === '*' && (dow === '?' || dow === '*')) {
    const mm = min.padStart(2, '0')
    const step = /^\d+\/(\d+)$/.exec(hour)[1]
    return `每${step}小时（起始于每天 ${hour.split('/')[0].padStart(2,'0')}:${mm}）`
  }

  // Daily fixed time: 0 mm HH * * ?
  if (sec === '0' && /^\d+$/.test(min) && /^\d+$/.test(hour) && dom === '*' && mon === '*' && (dow === '?' || dow === '*')) {
    const hh = String(hour).padStart(2, '0')
    const mm = String(min).padStart(2, '0')
    return `每天 ${hh}:${mm}`
  }

  // Hourly fixed minute: 0 mm * * * ?
  if (sec === '0' && /^\d+$/.test(min) && hour === '*' && dom === '*' && mon === '*' && (dow === '?' || dow === '*')) {
    const mm = String(min).padStart(2, '0')
    return `每小时的 ${mm} 分`
  }

  // Fallback for patterns like 0 0 0/1 * * ?
  if (sec === '0' && (min === '0' || min === '00') && /^\d+\/(\d+)$/.test(hour)) {
    const start = hour.split('/')[0].padStart(2,'0')
    const step = hour.split('/')[1]
    return `每${step}小时（起始于每天 ${start}:00）`
  }

  return '无法解析'
}

async function loadData() {
  // Resolve ms_id from selected project (may be numeric internal id)
  const msId = await resolveSelectedMsId()
  selectedMsId.value = msId
  if (!msId) return
  loading.value = true
  try {
    const { data } = await axios.get('/probe', { params: { project_ms_id: msId } })
    probe.value = data || null
  } finally {
    loading.value = false
  }
}

async function onSync() {
  // Resolve ms_id from selected project (may be numeric internal id)
  const msId = await resolveSelectedMsId()
  selectedMsId.value = msId
  if (!msId) return
  syncing.value = true
  try {
    const { data } = await axios.post('/probe/sync', { project_ms_id: msId })
    probe.value = data || null
    message.success('同步完成')
  } catch (e) {
    message.error('同步失败')
  } finally {
    syncing.value = false
  }
}

onMounted(async () => {
  selectedMsId.value = await resolveSelectedMsId()
  if (selectedMsId.value) await loadData()
})

async function resolveSelectedMsId() {
  const sel = projectStore.selectedProjectId
  if (!sel) return ''
  if (!projectStore.projects?.length) {
    try { await projectStore.fetchProjects() } catch { /* ignore */ }
  }
  const projects = projectStore.projects || []
  // If sel already equals an ms_id
  const direct = projects.find(p => String(p.ms_id) === String(sel))
  if (direct) return String(direct.ms_id)
  // Otherwise treat sel as internal numeric id
  const byId = projects.find(p => String(p.id) === String(sel))
  return byId ? String(byId.ms_id) : ''
}

watch(
  () => projectStore.selectedProjectId,
  async () => {
    selectedMsId.value = await resolveSelectedMsId()
    if (selectedMsId.value) {
      await loadData()
    } else {
      probe.value = null
    }
  }
)
</script>


