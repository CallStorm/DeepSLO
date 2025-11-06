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

  <a-card title="拨测报告同步配置" style="margin-top:16px;">
    <div v-if="!selectedMsId">
      <a-alert type="info" message="请先选择项目后再配置同步" show-icon />
    </div>
    <template v-else>
      <a-space direction="vertical" style="width:100%">
        <a-space>
          <a-switch v-model:checked="syncCfg.enabled" :loading="cfgLoading" />
          <span>开启同步</span>
          <a-button size="small" @click="saveCfg" :loading="cfgSaving">保存配置</a-button>
          <a-button size="small" @click="runNow" :loading="runLoading">立即同步</a-button>
          <a-button size="small" @click="openResults">查看结果</a-button>
          <a-button size="small" @click="loadCfg" :loading="cfgLoading" :disabled="!selectedMsId">刷新</a-button>
        </a-space>
        <a-form layout="inline">
          <a-form-item label="起始时间">
            <a-date-picker v-model:value="syncCfg.start_time" valueFormat="YYYY-MM-DD HH:mm:ss" show-time style="width:220px" />
          </a-form-item>
          <a-form-item label="同步间隔(秒)">
            <a-input-number v-model:value="syncCfg.interval_seconds" :min="30" :step="30" style="width:160px" />
          </a-form-item>
        </a-form>
        <a-descriptions :column="3" bordered size="small" v-if="cfgOut">
          <a-descriptions-item label="上次运行时间">{{ fmtDatetime(cfgOut.last_run_at) }}</a-descriptions-item>
          <a-descriptions-item label="状态">{{ cfgOut.last_status || '-' }}</a-descriptions-item>
          <a-descriptions-item label="指针起始时间">{{ fmtDatetime(cfgOut.last_synced_start) }}</a-descriptions-item>
          <a-descriptions-item label="错误">{{ cfgOut.last_error || '-' }}</a-descriptions-item>
        </a-descriptions>
      </a-space>
    </template>
  </a-card>

  <a-modal v-model:open="resultsOpen" title="拨测结果" width="900px" :footer="null">
    <a-space style="margin-bottom:8px;">
      <a-select v-model:value="resultStatus" style="width:160px" allow-clear placeholder="状态过滤">
        <a-select-option value="ERROR">ERROR</a-select-option>
        <a-select-option value="SUCCESS">SUCCESS</a-select-option>
        <a-select-option value="FAKE_ERROR">FAKE_ERROR</a-select-option>
        <a-select-option value="PENDING">PENDING</a-select-option>
      </a-select>
      <a-select v-model:value="resultValid" style="width:160px" allow-clear placeholder="有效性过滤">
        <a-select-option :value="true">有效</a-select-option>
        <a-select-option :value="false">无效</a-select-option>
      </a-select>
      <a-button size="small" @click="loadResults">刷新</a-button>
    </a-space>
    <a-table :data-source="results" :loading="resultsLoading" :pagination="false" row-key="id" size="small">
      <a-table-column title="名称" dataIndex="name" key="name" />
      <a-table-column title="开始时间" key="start">
        <template #default="{ record }">{{ fmtDatetime(record.start_time) }}</template>
      </a-table-column>
      <a-table-column title="耗时(ms)" dataIndex="request_duration_ms" key="dur" />
      <a-table-column title="状态" dataIndex="status" key="status" />
      <a-table-column title="错误数" dataIndex="error_count" key="ec" />
      <a-table-column title="成功数" dataIndex="success_count" key="sc" />
      <a-table-column title="有效性" key="valid">
        <template #default="{ record }">
          <a-select v-model:value="record.is_valid" size="small" style="width:100px">
            <a-select-option :value="true">有效</a-select-option>
            <a-select-option :value="false">无效</a-select-option>
          </a-select>
        </template>
      </a-table-column>
      <a-table-column title="原因标注" key="reason">
        <template #default="{ record }">
          <a-space>
            <a-input v-model:value="record.reason_label" size="small" style="width:160px" />
            <a-button size="small" type="link" @click="saveReason(record)">保存</a-button>
          </a-space>
        </template>
      </a-table-column>
    </a-table>
    <div style="margin-top:8px; text-align:right;">
      <a-pagination
        :current="resultsPage"
        :pageSize="resultsPageSize"
        :total="resultsTotal"
        @change="onResultsPage"
        @showSizeChange="onResultsSize"
        :showSizeChanger="true"
      />
    </div>
  </a-modal>
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

// sync config states
const cfgLoading = ref(false)
const cfgSaving = ref(false)
const runLoading = ref(false)
const cfgOut = ref(null)
const syncCfg = ref({ enabled: false, start_time: undefined, interval_seconds: 300 })

// results modal states
const resultsOpen = ref(false)
const resultsLoading = ref(false)
const results = ref([])
const resultsTotal = ref(0)
const resultsPage = ref(1)
const resultsPageSize = ref(10)
const resultStatus = ref(undefined)
const resultValid = ref(undefined)

function fmtDatetime(v) {
  if (!v) return '-'
  try {
    const str = typeof v === 'string' ? v : String(v)
    const hasTz = /[zZ]|[+-]\d{2}:?\d{2}$/.test(str)
    const iso = hasTz ? str : `${str}Z`
    const d = new Date(iso)
    return d.toLocaleString('zh-CN', { hour12: false, timeZone: 'Asia/Shanghai' })
  } catch {
    try { return new Date(v).toLocaleString('zh-CN', { hour12: false, timeZone: 'Asia/Shanghai' }) } catch { return String(v) }
  }
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
  if (selectedMsId.value) await loadCfg()
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
      await loadCfg()
    } else {
      probe.value = null
      cfgOut.value = null
    }
  }
)

async function loadCfg() {
  if (!selectedMsId.value) return
  cfgLoading.value = true
  try {
    const { data } = await axios.get('/probe/sync-config', { params: { project_ms_id: selectedMsId.value } })
    cfgOut.value = data || null
    if (cfgOut.value) {
      syncCfg.value.enabled = !!cfgOut.value.enabled
      syncCfg.value.start_time = cfgOut.value.start_time || (probe.value?.create_time || undefined)
      syncCfg.value.interval_seconds = cfgOut.value.interval_seconds || 300
    }
  } finally {
    cfgLoading.value = false
  }
}

async function saveCfg() {
  if (!selectedMsId.value) return
  cfgSaving.value = true
  try {
    const payload = { project_ms_id: selectedMsId.value, ...syncCfg.value }
    const { data } = await axios.post('/probe/sync-config', payload)
    cfgOut.value = data
    message.success('已保存同步配置')
  } catch (e) {
    message.error('保存失败')
  } finally {
    cfgSaving.value = false
  }
}

async function runNow() {
  if (!selectedMsId.value) return
  runLoading.value = true
  try {
    await axios.post('/probe/sync/run-now', null, { params: { project_ms_id: selectedMsId.value } })
    message.success('已触发同步')
    await loadCfg()
  } catch (e) {
    message.error('触发失败')
  } finally {
    runLoading.value = false
  }
}

function openResults() {
  resultsOpen.value = true
  resultsPage.value = 1
  loadResults()
}

async function loadResults() {
  if (!selectedMsId.value) return
  resultsLoading.value = true
  try {
    const params = {
      project_ms_id: selectedMsId.value,
      current: resultsPage.value,
      pageSize: resultsPageSize.value,
    }
    if (resultStatus.value) params.status = resultStatus.value
    if (resultValid.value !== undefined) params.is_valid = resultValid.value
    const { data } = await axios.get('/probe/results', { params })
    results.value = data.list || []
    resultsTotal.value = data.total || 0
  } finally {
    resultsLoading.value = false
  }
}

async function onResultsPage(p, ps) {
  resultsPage.value = p
  resultsPageSize.value = ps
  await loadResults()
}

async function onResultsSize(p, ps) {
  resultsPage.value = p
  resultsPageSize.value = ps
  await loadResults()
}

async function saveReason(record) {
  try {
    const { data } = await axios.patch(`/probe/results/${record.id}`, null, { params: { reason_label: record.reason_label, is_valid: record.is_valid } })
    Object.assign(record, data)
    message.success('已保存原因标注')
  } catch (e) {
    message.error('保存原因失败')
  }
}
</script>


