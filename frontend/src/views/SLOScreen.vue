<template>
  <div class="slo-screen" v-if="projectStore.selectedProjectId">
    <!-- 顶部横幅区域 -->
    <div class="screen-header">
      <div class="header-left">
        <h1 class="screen-title">{{ projectName }}系统 SLO 健康度监控</h1>
        <div class="update-time">数据更新于：{{ lastUpdated }}</div>
      </div>
      <div class="header-right">
        <div class="status-indicator" :class="`status-${globalStatus}`">
          <div class="status-light"></div>
          <div class="status-text">
            {{ statusText }}
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="screen-content">
      <!-- 左上 - 核心状态区 -->
      <div class="content-card status-card">
        <h2 class="card-title">核心状态</h2>
        <div class="status-content">
          <div class="slo-item">
            <div class="slo-label">SLO名称：拨测</div>
            <div class="slo-targets">
              <div class="target-item">
                <span class="target-label">目标值（月度）：</span>
                <span class="target-value">{{ formatTarget(monthlyData.target) }}</span>
              </div>
              <div class="target-item">
                <span class="target-label">目标值（年度）：</span>
                <span class="target-value">{{ formatTarget(yearlyData.target) }}</span>
              </div>
            </div>
          </div>

          <!-- 月度SLO -->
          <div class="slo-period">
            <h3>本月（{{ monthlyData.period_value }}）</h3>
            <div class="achievement-rate">
              <span class="rate-label">当前周期达成率：</span>
              <span class="rate-value" :class="getRateClass(monthlyData.achievement_rate, monthlyData.target)">
                {{ formatPercent(monthlyData.achievement_rate) }}
              </span>
            </div>
            <div class="error-budget">
              <div class="budget-header">
                <span>误差预算消耗：</span>
                <span class="budget-value">{{ formatPercent(monthlyData.error_budget_consumption) }}</span>
              </div>
              <a-progress
                :percent="monthlyData.error_budget_consumption * 100"
                :stroke-color="getBudgetColor(monthlyData.error_budget_consumption)"
                :show-info="false"
              />
              <div class="budget-footer">
                <span>当月剩余预算：{{ formatPercent(monthlyData.remaining_budget) }}</span>
                <span>周期剩余：{{ formatRemainingTime(monthlyData.remaining_time) }}</span>
              </div>
            </div>
          </div>

          <!-- 年度SLO -->
          <div class="slo-period">
            <h3>本年（{{ yearlyData.period_value }}）</h3>
            <div class="achievement-rate">
              <span class="rate-label">当前周期达成率：</span>
              <span class="rate-value" :class="getRateClass(yearlyData.achievement_rate, yearlyData.target)">
                {{ formatPercent(yearlyData.achievement_rate) }}
              </span>
            </div>
            <div class="error-budget">
              <div class="budget-header">
                <span>误差预算消耗：</span>
                <span class="budget-value">{{ formatPercent(yearlyData.error_budget_consumption) }}</span>
              </div>
              <a-progress
                :percent="yearlyData.error_budget_consumption * 100"
                :stroke-color="getBudgetColor(yearlyData.error_budget_consumption)"
                :show-info="false"
              />
              <div class="budget-footer">
                <span>年度剩余预算：{{ formatPercent(yearlyData.remaining_budget) }}</span>
                <span>周期剩余：{{ formatRemainingTime(yearlyData.remaining_time) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右上 - 趋势与预测区 -->
      <div class="content-card trend-card">
        <h2 class="card-title">趋势与预测</h2>
        <div class="trend-controls">
          <a-select v-model:value="trendMonths" style="width: 120px" @change="loadTrend">
            <a-select-option :value="6">最近6个月</a-select-option>
            <a-select-option :value="12">最近12个月</a-select-option>
            <a-select-option :value="24">最近24个月</a-select-option>
          </a-select>
        </div>
        <div ref="trendChartRef" class="trend-chart"></div>
      </div>

      <!-- 下方 - 关联事件区 -->
      <div class="content-card events-card">
        <h2 class="card-title">关联事件</h2>
        <div class="events-controls">
          <a-range-picker
            v-model:value="eventDateRange"
            show-time
            format="YYYY-MM-DD HH:mm:ss"
            @change="() => { eventsPagination.current = 1; loadEvents() }"
          />
          <a-button @click="loadEvents" :loading="eventsLoading">刷新</a-button>
        </div>
        <a-table
          :data-source="events"
          :loading="eventsLoading"
          :pagination="{
            ...eventsPagination,
            onChange: (page, pageSize) => {
              eventsPagination.current = page
              eventsPagination.pageSize = pageSize
              loadEvents()
            },
            onShowSizeChange: (current, size) => {
              eventsPagination.current = 1
              eventsPagination.pageSize = size
              loadEvents()
            }
          }"
          row-key="id"
          size="small"
          :scroll="{ y: 300 }"
        >
          <a-table-column title="拨测名" data-index="name" key="name" />
          <a-table-column title="时间" key="start_time">
            <template #default="{ record }">
              {{ formatDateTime(record.start_time) }}
            </template>
          </a-table-column>
          <a-table-column title="错误原因" data-index="reason_label" key="reason_label">
            <template #default="{ record }">
              <a-tag v-if="record.reason_label" color="red">{{ record.reason_label }}</a-tag>
              <span v-else>-</span>
            </template>
          </a-table-column>
        </a-table>
      </div>
    </div>
  </div>
  <div v-else class="slo-screen-empty">
    <a-alert
      type="info"
      message="请先选择项目"
      description="请在上方项目菜单中选择一个项目，然后查看SLO大屏数据。"
      show-icon
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import axios from 'axios'
import { useProjectStore } from '../stores/projects'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import customParseFormat from 'dayjs/plugin/customParseFormat'

dayjs.extend(customParseFormat)

const projectStore = useProjectStore()

// 数据状态
const dashboardData = ref(null)
const trendData = ref([])
const events = ref([])
const loading = ref(false)
const eventsLoading = ref(false)
const lastUpdated = ref('')
const globalStatus = ref('green')

// 图表相关
const trendChartRef = ref(null)
let trendChart = null

// 控制参数
const trendMonths = ref(12)
const eventDateRange = ref([
  dayjs().subtract(7, 'day'),
  dayjs()
])
const eventsPagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total) => `共 ${total} 条`,
})

// 计算属性
const projectName = computed(() => {
  if (dashboardData.value?.project?.ms_name) {
    return dashboardData.value.project.ms_name
  }
  return '未知'
})

const monthlyData = computed(() => {
  return dashboardData.value?.monthly || {
    period_value: '',
    target: null,
    achievement_rate: 1.0,
    error_budget_consumption: 0.0,
    remaining_budget: 1.0,
    remaining_time: { days: 0, hours: 0, minutes: 0 },
  }
})

const yearlyData = computed(() => {
  return dashboardData.value?.yearly || {
    period_value: '',
    target: null,
    achievement_rate: 1.0,
    error_budget_consumption: 0.0,
    remaining_budget: 1.0,
    remaining_time: { days: 0, hours: 0, minutes: 0 },
  }
})

const statusText = computed(() => {
  const statusMap = {
    green: '健康',
    yellow: '有风险',
    red: '不健康',
  }
  return statusMap[globalStatus.value] || '未知'
})

// 格式化函数
function formatTarget(target) {
  if (target === null || target === undefined) return '-'
  return (target * 100).toFixed(4) + '%'
}

function formatPercent(value) {
  if (value === null || value === undefined) return '-'
  return (value * 100).toFixed(2) + '%'
}

function formatDateTime(datetimeStr) {
  if (!datetimeStr) return '-'
  return dayjs(datetimeStr).format('YYYY-MM-DD HH:mm:ss')
}

function formatRemainingTime(remaining) {
  if (!remaining) return '-'
  const parts = []
  if (remaining.days > 0) parts.push(`${remaining.days}天`)
  if (remaining.hours > 0) parts.push(`${remaining.hours}小时`)
  if (remaining.minutes > 0) parts.push(`${remaining.minutes}分钟`)
  return parts.length > 0 ? parts.join(' ') : '0分钟'
}

function getRateClass(rate, target) {
  if (target === null || target === undefined) return ''
  if (rate >= target) return 'rate-ok'
  return 'rate-error'
}

function getBudgetColor(consumption) {
  if (consumption >= 1.0) return '#ff4d4f'
  if (consumption >= 0.8) return '#faad14'
  if (consumption >= 0.5) return '#fa8c16'
  return '#52c41a'
}

// 加载数据
let refreshTimer = null

async function loadDashboard() {
  if (!projectStore.selectedProjectId) {
    return
  }

  loading.value = true
  try {
    const project = projectStore.projects.find(p => p.id === projectStore.selectedProjectId)
    if (!project) {
      loading.value = false
      return
    }

    const { data } = await axios.get('/slo/screen/dashboard', {
      params: {
        project_ms_id: project.ms_id,
      },
    })

    dashboardData.value = data
    globalStatus.value = data.global_status || 'green'
    lastUpdated.value = formatDateTime(data.last_updated)

    // 清除旧的定时器
    if (refreshTimer) {
      clearTimeout(refreshTimer)
    }
    // 自动刷新
    refreshTimer = setTimeout(loadDashboard, 60000) // 每60秒刷新一次
  } catch (error) {
    console.error('Failed to load dashboard:', error)
  } finally {
    loading.value = false
  }
}

async function loadTrend() {
  if (!projectStore.selectedProjectId) {
    return
  }

  try {
    const project = projectStore.projects.find(p => p.id === projectStore.selectedProjectId)
    if (!project) return

    const { data } = await axios.get('/slo/screen/trend', {
      params: {
        project_ms_id: project.ms_id,
        period_type: 'monthly',
        months: trendMonths.value,
      },
    })

    trendData.value = data.trends || []
    await nextTick()
    renderTrendChart()
  } catch (error) {
    console.error('Failed to load trend:', error)
  }
}

async function loadEvents() {
  if (!projectStore.selectedProjectId) {
    return
  }

  eventsLoading.value = true
  try {
    const project = projectStore.projects.find(p => p.id === projectStore.selectedProjectId)
    if (!project) {
      eventsLoading.value = false
      return
    }

    const params = {
      project_ms_id: project.ms_id,
      current: eventsPagination.value.current,
      pageSize: eventsPagination.value.pageSize,
    }

    if (eventDateRange.value && eventDateRange.value.length === 2) {
      params.start_time = eventDateRange.value[0].format('YYYY-MM-DD HH:mm:ss')
      params.end_time = eventDateRange.value[1].format('YYYY-MM-DD HH:mm:ss')
    }

    const { data } = await axios.get('/slo/screen/events', { params })

    events.value = data.list || []
    eventsPagination.value.total = data.total || 0
    eventsPagination.value.current = data.current || 1
  } catch (error) {
    console.error('Failed to load events:', error)
  } finally {
    eventsLoading.value = false
  }
}

// 渲染趋势图
function renderTrendChart() {
  if (!trendChartRef.value || trendData.value.length === 0) {
    return
  }

  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value)
  }

  const periods = trendData.value.map(t => t.period)
  const achievementRates = trendData.value.map(t => (t.achievement_rate * 100).toFixed(2))
  const target = trendData.value[0]?.target
  const targetLine = target ? [target * 100] : []

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        let result = `${params[0].name}<br/>`
        params.forEach(param => {
          result += `${param.seriesName}: ${param.value}%<br/>`
        })
        return result
      },
    },
    legend: {
      data: ['SLO达成率', 'SLO目标'],
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: periods,
    },
    yAxis: {
      type: 'value',
      name: 'SLO达成率（%）',
      min: 95,
      max: 100,
    },
    series: [
      {
        name: 'SLO达成率',
        type: 'line',
        smooth: true,
        data: achievementRates,
        itemStyle: {
          color: '#1890ff',
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
              { offset: 1, color: 'rgba(24, 144, 255, 0.1)' },
            ],
          },
        },
      },
      {
        name: 'SLO目标',
        type: 'line',
        data: periods.map(() => target ? (target * 100).toFixed(2) : null),
        lineStyle: {
          type: 'dashed',
          color: '#ff4d4f',
        },
        itemStyle: {
          color: '#ff4d4f',
        },
      },
    ],
  }

  trendChart.setOption(option)
}

// 监听项目变化
watch(() => projectStore.selectedProjectId, (newVal) => {
  if (newVal) {
    loadDashboard()
    loadTrend()
    loadEvents()
  }
})

// 生命周期
onMounted(async () => {
  if (projectStore.selectedProjectId) {
    await loadDashboard()
    await nextTick()
    await loadTrend()
    await loadEvents()
  }

  // 窗口 resize 时重新渲染图表
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearTimeout(refreshTimer)
  }
  window.removeEventListener('resize', handleResize)
  if (trendChart) {
    trendChart.dispose()
    trendChart = null
  }
})

function handleResize() {
  if (trendChart) {
    trendChart.resize()
  }
}
</script>

<style scoped>
.slo-screen {
  min-height: calc(100vh - 100px);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  margin: -16px;
}

.screen-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.95);
  padding: 20px 30px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.header-left {
  flex: 1;
}

.screen-title {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: bold;
  color: #1a1a1a;
}

.update-time {
  font-size: 14px;
  color: #666;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  border-radius: 8px;
  background: #f5f5f5;
}

.status-light {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
}

.status-green .status-light {
  background: #52c41a;
  box-shadow: 0 0 15px rgba(82, 196, 26, 0.6);
}

.status-yellow .status-light {
  background: #faad14;
  box-shadow: 0 0 15px rgba(250, 173, 20, 0.6);
}

.status-red .status-light {
  background: #ff4d4f;
  box-shadow: 0 0 15px rgba(255, 77, 79, 0.6);
}

.status-text {
  font-size: 16px;
  font-weight: bold;
  color: #1a1a1a;
}

.screen-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 20px;
}

.content-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.status-card {
  grid-column: 1;
  grid-row: 1;
}

.trend-card {
  grid-column: 2;
  grid-row: 1;
}

.events-card {
  grid-column: 1 / -1;
  grid-row: 2;
}

.card-title {
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: bold;
  color: #1a1a1a;
  border-bottom: 2px solid #e8e8e8;
  padding-bottom: 8px;
}

.status-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.slo-item {
  padding-bottom: 16px;
  border-bottom: 1px solid #e8e8e8;
}

.slo-label {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 8px;
  color: #1a1a1a;
}

.slo-targets {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.target-item {
  display: flex;
  gap: 8px;
}

.target-label {
  color: #666;
}

.target-value {
  font-weight: bold;
  color: #1890ff;
}

.slo-period {
  padding: 16px;
  background: #f9f9f9;
  border-radius: 4px;
}

.slo-period h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #1a1a1a;
}

.achievement-rate {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.rate-label {
  color: #666;
}

.rate-value {
  font-size: 20px;
  font-weight: bold;
}

.rate-ok {
  color: #52c41a;
}

.rate-error {
  color: #ff4d4f;
}

.error-budget {
  margin-top: 16px;
}

.budget-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  color: #666;
}

.budget-value {
  font-weight: bold;
  color: #1a1a1a;
}

.budget-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #999;
}

.trend-controls {
  margin-bottom: 16px;
}

.trend-chart {
  width: 100%;
  height: 300px;
}

.events-controls {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;
}

.slo-screen-empty {
  padding: 40px;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}
</style>
