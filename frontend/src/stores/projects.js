import { defineStore } from 'pinia'
import axios from 'axios'

const STORAGE_KEY = 'deepSLO_selectedProjectId'

export const useProjectStore = defineStore('projects', {
  state: () => {
    // 从 localStorage 恢复选中的项目ID
    let initialProjectId = null
    try {
      const savedProjectId = localStorage.getItem(STORAGE_KEY)
      if (savedProjectId) {
        const parsedId = parseInt(savedProjectId, 10)
        if (!isNaN(parsedId)) {
          initialProjectId = parsedId
        }
      }
    } catch (error) {
      // 如果读取 localStorage 失败，忽略错误，使用默认值 null
      console.warn('Failed to restore selected project from localStorage:', error)
    }
    
    return {
      projects: [],
      selectedProjectId: initialProjectId
    }
  },
  actions: {
    async fetchProjects() {
      const { data } = await axios.get('/system/projects')
      this.projects = data
      
      // 验证选中的项目是否仍然存在于列表中
      if (this.selectedProjectId) {
        const projectExists = this.projects.some(p => p.id === this.selectedProjectId)
        if (!projectExists) {
          // 如果项目不存在，清除选择
          this.setSelectedProject(null)
        }
      }
    },
    async syncProjects() {
      await axios.post('/system/projects/sync')
      await this.fetchProjects()
    },
    setSelectedProject(id) {
      this.selectedProjectId = id
      // 保存到 localStorage
      if (id === null || id === undefined) {
        localStorage.removeItem(STORAGE_KEY)
      } else {
        localStorage.setItem(STORAGE_KEY, String(id))
      }
    }
  }
})


