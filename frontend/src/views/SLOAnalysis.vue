<template>
  <div class="slo-analysis" v-if="projectStore.selectedProjectId">
    <a-card>
      <template #title>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>SLO分析</span>
          <a-button type="primary" @click="exportToPDF" :disabled="!analysisData || !chatContent" :loading="exporting">
            <template #icon><download-outlined /></template>
            导出PDF
          </a-button>
        </div>
      </template>

      <!-- 上半部分：SLO信息展示 -->
      <div class="analysis-info-section">
        <a-spin :spinning="loading">
          <a-alert v-if="!selectedMsId" type="warning" message="请先在项目菜单选择项目" show-icon style="margin-bottom: 16px;" />
          
          <div v-if="analysisData" class="info-grid">
            <!-- SLO配置 -->
            <a-card title="SLO配置" size="small" class="info-card">
              <a-descriptions :column="2" size="small" bordered>
                <template v-if="analysisData.slo_config.monthly">
                  <a-descriptions-item label="月度SLO目标">
                    {{ formatPercent(analysisData.slo_config.monthly.target) }}
                  </a-descriptions-item>
                  <a-descriptions-item label="月度最大中断时间">
                    {{ analysisData.slo_config.monthly.max_downtime_minutes.toFixed(2) }} 分钟
                  </a-descriptions-item>
                </template>
                <template v-if="analysisData.slo_config.yearly">
                  <a-descriptions-item label="年度SLO目标">
                    {{ formatPercent(analysisData.slo_config.yearly.target) }}
                  </a-descriptions-item>
                  <a-descriptions-item label="年度最大中断时间">
                    {{ analysisData.slo_config.yearly.max_downtime_minutes.toFixed(2) }} 分钟
                  </a-descriptions-item>
                </template>
              </a-descriptions>
            </a-card>

            <!-- 当前SLO值 -->
            <a-card title="当前SLO值" size="small" class="info-card">
              <a-descriptions :column="2" size="small" bordered>
                <template v-if="analysisData.slo_current.monthly">
                  <a-descriptions-item label="月度周期">
                    {{ analysisData.slo_current.monthly.period_value }}
                  </a-descriptions-item>
                  <a-descriptions-item label="月度达成率">
                    <span :class="getRateClass(analysisData.slo_current.monthly.achievement_rate, analysisData.slo_config.monthly?.target)">
                      {{ formatPercent(analysisData.slo_current.monthly.achievement_rate) }}
                    </span>
                  </a-descriptions-item>
                </template>
                <template v-if="analysisData.slo_current.yearly">
                  <a-descriptions-item label="年度周期">
                    {{ analysisData.slo_current.yearly.period_value }}
                  </a-descriptions-item>
                  <a-descriptions-item label="年度达成率">
                    <span :class="getRateClass(analysisData.slo_current.yearly.achievement_rate, analysisData.slo_config.yearly?.target)">
                      {{ formatPercent(analysisData.slo_current.yearly.achievement_rate) }}
                    </span>
                  </a-descriptions-item>
                </template>
              </a-descriptions>
            </a-card>

            <!-- 有效拨测数量 -->
            <a-card title="有效拨测数量" size="small" class="info-card">
              <a-statistic 
                title="当年有效拨测数量（is_valid=1）" 
                :value="analysisData.valid_probe_count" 
                :value-style="{ color: analysisData.valid_probe_count > 0 ? '#cf1322' : '#3f8600' }"
              />
            </a-card>
          </div>
        </a-spin>
      </div>

      <!-- 下半部分：聊天界面 -->
      <a-divider />
      <div class="chat-section">
        <div class="chat-container">
          <!-- 聊天框 -->
          <div class="chat-messages" ref="chatMessagesRef">
            <div v-if="!chatContent && !streaming" class="chat-placeholder">
              <a-empty description="点击发送按钮开始分析" :image="false" />
            </div>
            <div v-else class="chat-content">
              <div class="message-item assistant-message">
                <div class="message-content" v-html="formatMarkdown(chatContent)"></div>
                <a-spin v-if="streaming" size="small" style="margin-top: 8px;" />
              </div>
            </div>
          </div>

          <!-- 输入框 -->
          <div class="chat-input-container">
            <a-textarea
              v-model:value="userMessage"
              :rows="3"
              placeholder="输入您的问题，或直接点击发送进行完整分析..."
              :disabled="streaming"
              @keydown.enter.ctrl="sendMessage"
              @keydown.enter.exact.prevent="sendMessage"
            />
            <div class="chat-input-actions">
              <a-button type="primary" @click="sendMessage" :loading="streaming" :disabled="streaming">
                发送
              </a-button>
              <a-button @click="clearChat" :disabled="streaming">清空</a-button>
            </div>
          </div>
        </div>
      </div>
    </a-card>
  </div>
  <a-empty v-else description="请先选择项目" />
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useProjectStore } from '../stores/projects'
import axios from 'axios'
import { message } from 'ant-design-vue'
import { DownloadOutlined } from '@ant-design/icons-vue'
import jsPDF from 'jspdf'
import { marked } from 'marked'
import html2canvas from 'html2canvas'

const projectStore = useProjectStore()
const selectedMsId = ref('')
const loading = ref(false)
const analysisData = ref(null)
const userMessage = ref('')
const chatContent = ref('')
const streaming = ref(false)
const chatMessagesRef = ref(null)
const exporting = ref(false)

// 解析选中的项目ID为ms_id
async function resolveSelectedMsId() {
  const sel = projectStore.selectedProjectId
  if (!sel) return ''
  if (!projectStore.projects?.length) {
    try {
      await projectStore.fetchProjects()
    } catch {
      // ignore
    }
  }
  const projects = projectStore.projects || []
  const direct = projects.find(p => String(p.ms_id) === String(sel))
  if (direct) return String(direct.ms_id)
  const byId = projects.find(p => String(p.id) === String(sel))
  return byId ? String(byId.ms_id) : ''
}

// 加载SLO分析数据
async function loadAnalysisData() {
  if (!selectedMsId.value) return
  loading.value = true
  try {
    const { data } = await axios.get('/slo/analysis/data', {
      params: { project_ms_id: selectedMsId.value }
    })
    analysisData.value = data
  } catch (e) {
    message.error('加载SLO分析数据失败')
    console.error(e)
  } finally {
    loading.value = false
  }
}

// 发送消息
async function sendMessage() {
  if (!selectedMsId.value) {
    message.warning('请先选择项目')
    return
  }
  if (streaming.value) return

  const messageText = userMessage.value.trim()
  if (!messageText && chatContent.value) {
    // 如果没有输入消息但有历史内容，重新分析
    userMessage.value = ''
  }

  streaming.value = true
  chatContent.value = ''

  try {
    const token = localStorage.getItem('token')
    // 使用完整的后端API URL（与axios配置保持一致）
    const apiBaseURL = axios.defaults.baseURL || 'http://127.0.0.1:8000'
    const response = await fetch(`${apiBaseURL}/slo/analysis/chat?project_ms_id=${selectedMsId.value}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        message: messageText || null
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.error) {
              message.error(data.error)
              streaming.value = false
              return
            }
            if (data.content) {
              chatContent.value += data.content
              // 滚动到底部
              await nextTick()
              scrollToBottom()
            }
            if (data.done) {
              streaming.value = false
              return
            }
          } catch (e) {
            // 忽略JSON解析错误
            console.warn('Failed to parse SSE data:', e)
          }
        }
      }
    }
  } catch (e) {
    message.error('发送消息失败: ' + (e.message || '未知错误'))
    console.error(e)
  } finally {
    streaming.value = false
  }
}

// 清空聊天
function clearChat() {
  chatContent.value = ''
  userMessage.value = ''
}

// 滚动到底部
function scrollToBottom() {
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
  }
}

// 格式化百分比
function formatPercent(value) {
  if (value === null || value === undefined) return '-'
  return (value * 100).toFixed(4) + '%'
}

// 获取达成率样式类
function getRateClass(rate, target) {
  if (!target) return ''
  if (rate >= target) return 'rate-ok'
  return 'rate-fail'
}

// 格式化Markdown（使用marked库）
function formatMarkdown(text) {
  if (!text) return ''
  try {
    // 配置marked选项
    marked.setOptions({
      breaks: true, // 支持换行
      gfm: true, // 支持GitHub风格的Markdown
    })
    // 使用marked解析markdown
    return marked.parse(text)
  } catch (e) {
    console.error('Markdown parsing error:', e)
    return text.replace(/\n/g, '<br>')
  }
}

// 导出PDF
async function exportToPDF() {
  if (!analysisData.value || !chatContent.value) {
    message.warning('没有可导出的内容')
    return
  }

  exporting.value = true
  try {
    // 创建一个临时div来渲染内容
    const tempDiv = document.createElement('div')
    tempDiv.style.position = 'absolute'
    tempDiv.style.left = '-9999px'
    tempDiv.style.width = '800px'
    tempDiv.style.padding = '40px'
    tempDiv.style.backgroundColor = '#fff'
    tempDiv.style.fontFamily = 'Arial, "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", sans-serif'
    tempDiv.style.fontSize = '14px'
    tempDiv.style.lineHeight = '1.6'
    tempDiv.style.color = '#000'
    
    // 构建HTML内容
    let htmlContent = `
      <div style="margin-bottom: 24px;">
        <h1 style="font-size: 24px; margin-bottom: 12px; font-weight: bold; border-bottom: 2px solid #333; padding-bottom: 8px;">SLO分析报告</h1>
        <p style="margin: 4px 0;"><strong>项目名称:</strong> ${analysisData.value.project.ms_name}</p>
        <p style="margin: 4px 0;"><strong>项目ID:</strong> ${analysisData.value.project.ms_id}</p>
        <p style="margin: 4px 0;"><strong>生成时间:</strong> ${new Date().toLocaleString('zh-CN')}</p>
      </div>
      
      <div style="margin-bottom: 24px;">
        <h2 style="font-size: 18px; margin-bottom: 12px; font-weight: bold; border-bottom: 1px solid #ddd; padding-bottom: 6px;">SLO配置</h2>
    `
    
    if (analysisData.value.slo_config.monthly) {
      htmlContent += `<p style="margin: 6px 0;">月度SLO目标: ${formatPercent(analysisData.value.slo_config.monthly.target)}</p>`
    }
    if (analysisData.value.slo_config.yearly) {
      htmlContent += `<p style="margin: 6px 0;">年度SLO目标: ${formatPercent(analysisData.value.slo_config.yearly.target)}</p>`
    }
    
    htmlContent += `
      </div>
      
      <div style="margin-bottom: 24px;">
        <h2 style="font-size: 18px; margin-bottom: 12px; font-weight: bold; border-bottom: 1px solid #ddd; padding-bottom: 6px;">当前SLO值</h2>
    `
    
    if (analysisData.value.slo_current.monthly) {
      htmlContent += `<p style="margin: 6px 0;">月度达成率: ${formatPercent(analysisData.value.slo_current.monthly.achievement_rate)}</p>`
    }
    if (analysisData.value.slo_current.yearly) {
      htmlContent += `<p style="margin: 6px 0;">年度达成率: ${formatPercent(analysisData.value.slo_current.yearly.achievement_rate)}</p>`
    }
    
    htmlContent += `
      </div>
      
      <div style="margin-bottom: 24px;">
        <h2 style="font-size: 18px; margin-bottom: 12px; font-weight: bold; border-bottom: 1px solid #ddd; padding-bottom: 6px;">有效拨测数量</h2>
        <p style="margin: 6px 0;">当年有效拨测数量: ${analysisData.value.valid_probe_count}</p>
      </div>
      
      <div style="margin-bottom: 24px;">
        <h2 style="font-size: 18px; margin-bottom: 12px; font-weight: bold; border-bottom: 1px solid #ddd; padding-bottom: 6px;">分析报告</h2>
        <div style="font-size: 14px; line-height: 1.8;">
          ${formatMarkdown(chatContent.value)}
        </div>
      </div>
    `
    
    tempDiv.innerHTML = htmlContent
    document.body.appendChild(tempDiv)
    
    // 等待内容渲染
    await new Promise(resolve => setTimeout(resolve, 100))
    
    // 使用html2canvas将HTML转换为图片
    const canvas = await html2canvas(tempDiv, {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: '#ffffff',
      width: tempDiv.scrollWidth,
      height: tempDiv.scrollHeight
    })
    
    // 清理临时div
    document.body.removeChild(tempDiv)
    
    // 创建PDF
    const imgWidth = canvas.width
    const imgHeight = canvas.height
    const pdfWidth = 210 // A4宽度（mm）
    const pdfHeight = (imgHeight * pdfWidth) / imgWidth
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pageHeight = 297 // A4高度（mm）
    
    // 如果内容超过一页，需要分页
    let heightLeft = pdfHeight
    let position = 0
    
    // 添加第一页
    pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, position, pdfWidth, pdfHeight)
    heightLeft -= pageHeight
    
    // 如果内容超过一页，继续添加页面
    while (heightLeft > 0) {
      position = heightLeft - pdfHeight
      pdf.addPage()
      pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, position, pdfWidth, pdfHeight)
      heightLeft -= pageHeight
    }
    
    // 保存PDF
    const fileName = `SLO分析报告_${analysisData.value.project.ms_name}_${new Date().toISOString().split('T')[0]}.pdf`
    pdf.save(fileName)
    message.success('PDF导出成功')
  } catch (e) {
    message.error('PDF导出失败: ' + (e.message || '未知错误'))
    console.error(e)
  } finally {
    exporting.value = false
  }
}

// 监听项目变化
watch(
  () => projectStore.selectedProjectId,
  async () => {
    selectedMsId.value = await resolveSelectedMsId()
    if (selectedMsId.value) {
      await loadAnalysisData()
    } else {
      analysisData.value = null
      chatContent.value = ''
    }
  },
  { immediate: true }
)

onMounted(async () => {
  selectedMsId.value = await resolveSelectedMsId()
  if (selectedMsId.value) {
    await loadAnalysisData()
  }
})
</script>

<style scoped>
.slo-analysis {
  padding: 16px;
}

.analysis-info-section {
  margin-bottom: 24px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.info-card {
  height: 100%;
}

.rate-ok {
  color: #3f8600;
  font-weight: bold;
}

.rate-fail {
  color: #cf1322;
  font-weight: bold;
}

.chat-section {
  margin-top: 24px;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 600px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background-color: #fafafa;
}

.chat-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.chat-content {
  max-width: 100%;
}

.message-item {
  margin-bottom: 16px;
}

.assistant-message .message-content {
  background-color: #fff;
  padding: 16px;
  border-radius: 4px;
  border: 1px solid #e8e8e8;
  word-wrap: break-word;
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}

.assistant-message .message-content :deep(h1) {
  font-size: 1.5em;
  margin-top: 16px;
  margin-bottom: 12px;
  font-weight: bold;
  border-bottom: 2px solid #e8e8e8;
  padding-bottom: 8px;
}

.assistant-message .message-content :deep(h2) {
  font-size: 1.3em;
  margin-top: 14px;
  margin-bottom: 10px;
  font-weight: bold;
  border-bottom: 1px solid #e8e8e8;
  padding-bottom: 6px;
}

.assistant-message .message-content :deep(h3) {
  font-size: 1.1em;
  margin-top: 12px;
  margin-bottom: 8px;
  font-weight: bold;
}

.assistant-message .message-content :deep(h4) {
  font-size: 1em;
  margin-top: 10px;
  margin-bottom: 6px;
  font-weight: bold;
}

.assistant-message .message-content :deep(p) {
  margin-bottom: 8px;
  line-height: 1.6;
}

.assistant-message .message-content :deep(ul),
.assistant-message .message-content :deep(ol) {
  margin-left: 24px;
  margin-top: 8px;
  margin-bottom: 8px;
  padding-left: 0;
}

.assistant-message .message-content :deep(li) {
  margin-bottom: 6px;
  line-height: 1.6;
}

.assistant-message .message-content :deep(strong) {
  font-weight: bold;
  color: #000;
}

.assistant-message .message-content :deep(em) {
  font-style: italic;
}

.assistant-message .message-content :deep(code) {
  background-color: #f5f5f5;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.assistant-message .message-content :deep(pre) {
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 8px 0;
}

.assistant-message .message-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.assistant-message .message-content :deep(blockquote) {
  border-left: 4px solid #d9d9d9;
  padding-left: 12px;
  margin: 8px 0;
  color: #666;
}

.assistant-message .message-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0;
}

.assistant-message .message-content :deep(table th),
.assistant-message .message-content :deep(table td) {
  border: 1px solid #e8e8e8;
  padding: 8px;
  text-align: left;
}

.assistant-message .message-content :deep(table th) {
  background-color: #fafafa;
  font-weight: bold;
}

.chat-input-container {
  padding: 12px;
  background-color: #fff;
  border-top: 1px solid #d9d9d9;
}

.chat-input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}
</style>
