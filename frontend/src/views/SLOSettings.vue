<template>
  <a-card title="SLO 设置">
    <a-space style="margin-bottom: 16px">
      <a-button type="primary" @click="openCreate">新增 SLO</a-button>
    </a-space>

    <!-- SLO配置卡片列表 -->
    <a-row :gutter="16" v-if="configs.length > 0">
      <a-col :span="12" v-for="config in configs" :key="config.id">
        <a-card :title="getPeriodTypeLabel(config.period_type)" style="margin-bottom: 16px">
          <a-descriptions :column="1" bordered>
            <a-descriptions-item label="类型">
              {{ getPeriodTypeLabel(config.period_type) }}
            </a-descriptions-item>
            <a-descriptions-item label="SLO目标">
              {{ formatTarget(config.target) }}
            </a-descriptions-item>
            <a-descriptions-item label="允许中断时间">
              {{ formatDowntime(config.max_downtime_minutes) }}
            </a-descriptions-item>
            <a-descriptions-item label="指标类型">
              {{ config.metric_type === 'probe' ? '拨测' : config.metric_type }}
            </a-descriptions-item>
          </a-descriptions>
          <template #extra>
            <a-space>
              <a-button size="small" @click="openEdit(config)">编辑</a-button>
              <a-button size="small" danger @click="remove(config.id)">删除</a-button>
            </a-space>
          </template>
        </a-card>
      </a-col>
    </a-row>

    <a-empty v-else description="暂无SLO配置，请点击上方按钮新增" />

    <!-- 新增/编辑模态框 -->
    <a-modal
      v-model:open="modalOpen"
      :title="editingId ? '编辑 SLO' : '新增 SLO'"
      @ok="submit"
      @cancel="resetForm"
    >
      <a-form :model="form" layout="vertical">
        <a-form-item label="类型" required>
          <a-select
            v-model:value="form.period_type"
            placeholder="选择年度或月度"
            :options="periodTypeOptions"
            :disabled="!!editingId"
            @change="onPeriodTypeChange"
          />
        </a-form-item>
        <a-form-item label="SLO目标" required>
          <a-input
            v-model:value="form.targetInput"
            placeholder="输入目标等级，如：99.99"
            @input="onTargetInput"
          >
            <template #suffix>%</template>
          </a-input>
          <div style="margin-top: 8px; color: #666; font-size: 12px">
            例如：99.99 表示四个9（99.99%）
          </div>
        </a-form-item>
        <a-form-item label="允许最大中断时间" v-if="calculatedDowntime !== null">
          <a-alert
            :message="`${formatDowntime(calculatedDowntime)}`"
            type="info"
            show-icon
          />
        </a-form-item>
        <a-form-item label="指标类型">
          <a-input v-model:value="form.metric_type" disabled value="probe" />
          <div style="margin-top: 8px; color: #666; font-size: 12px">
            默认指标为拨测
          </div>
        </a-form-item>
      </a-form>
    </a-modal>
  </a-card>
</template>

<script setup>
import { onMounted, ref, reactive, computed } from 'vue'
import axios from 'axios'
import { message } from 'ant-design-vue'

const configs = ref([])
const modalOpen = ref(false)
const editingId = ref(null)
const calculatedDowntime = ref(null)

const form = reactive({
  period_type: null,
  targetInput: '',
  target: null,
  metric_type: 'probe'
})

const periodTypeOptions = [
  { label: '月度', value: 'monthly' },
  { label: '年度', value: 'yearly' }
]

// 格式化SLO目标显示（如：99.99%）
function formatTarget(target) {
  if (target === null || target === undefined) return '-'
  return `${(target * 100).toFixed(2)}%`
}

// 格式化中断时间显示
function formatDowntime(minutes) {
  if (minutes === null || minutes === undefined) return '-'
  if (minutes < 1) {
    return `${(minutes * 60).toFixed(2)} 秒`
  } else if (minutes < 60) {
    return `${minutes.toFixed(2)} 分钟`
  } else {
    const hours = Math.floor(minutes / 60)
    const mins = (minutes % 60).toFixed(2)
    return `${hours} 小时 ${mins} 分钟`
  }
}

// 获取周期类型标签
function getPeriodTypeLabel(periodType) {
  return periodType === 'monthly' ? '月度 SLO' : '年度 SLO'
}

// 当用户输入目标等级时，实时计算允许中断时间
async function onTargetInput() {
  if (!form.period_type || !form.targetInput) {
    calculatedDowntime.value = null
    return
  }

  const targetValue = parseFloat(form.targetInput)
  if (isNaN(targetValue) || targetValue <= 0 || targetValue >= 100) {
    calculatedDowntime.value = null
    return
  }

  // 转换为0-1之间的值
  const target = targetValue / 100
  form.target = target

  try {
    const { data } = await axios.get('/slo/settings/calculate-downtime', {
      params: {
        period_type: form.period_type,
        target: target
      }
    })
    calculatedDowntime.value = data.max_downtime_minutes
  } catch (error) {
    console.error('计算中断时间失败:', error)
    calculatedDowntime.value = null
  }
}

// 当选择周期类型时，重新计算
function onPeriodTypeChange() {
  if (form.targetInput) {
    onTargetInput()
  }
}

// 加载SLO配置列表
async function load() {
  try {
    const { data } = await axios.get('/slo/settings')
    configs.value = data
  } catch (error) {
    console.error('加载SLO配置失败:', error)
    message.error('加载SLO配置失败')
  }
}

// 打开新增表单
function openCreate() {
  editingId.value = null
  resetForm()
  modalOpen.value = true
}

// 打开编辑表单
function openEdit(config) {
  editingId.value = config.id
  form.period_type = config.period_type
  form.target = config.target
  form.targetInput = (config.target * 100).toFixed(2)
  form.metric_type = config.metric_type
  calculatedDowntime.value = config.max_downtime_minutes
  modalOpen.value = true
}

// 重置表单
function resetForm() {
  form.period_type = null
  form.targetInput = ''
  form.target = null
  form.metric_type = 'probe'
  calculatedDowntime.value = null
}

// 提交表单
async function submit() {
  // 验证表单
  if (!form.period_type) {
    message.error('请选择类型（年度或月度）')
    return
  }

  if (!form.targetInput || !form.target) {
    message.error('请输入SLO目标等级')
    return
  }

  const targetValue = parseFloat(form.targetInput)
  if (isNaN(targetValue) || targetValue <= 0 || targetValue >= 100) {
    message.error('SLO目标必须在0-100之间')
    return
  }

  try {
    if (editingId.value) {
      // 更新
      await axios.put(`/slo/settings/${editingId.value}`, {
        target: form.target
      })
      message.success('更新成功')
    } else {
      // 创建
      await axios.post('/slo/settings', {
        period_type: form.period_type,
        target: form.target,
        metric_type: form.metric_type
      })
      message.success('创建成功')
    }
    modalOpen.value = false
    resetForm()
    await load()
  } catch (error) {
    console.error('保存失败:', error)
    const errorMsg = error.response?.data?.detail || '保存失败'
    message.error(errorMsg)
  }
}

// 删除配置
async function remove(id) {
  try {
    await axios.delete(`/slo/settings/${id}`)
    message.success('删除成功')
    await load()
  } catch (error) {
    console.error('删除失败:', error)
    message.error('删除失败')
  }
}

onMounted(load)
</script>

<style scoped>
:deep(.ant-descriptions-item-label) {
  font-weight: 500;
}
</style>
