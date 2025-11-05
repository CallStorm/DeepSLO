import { defineStore } from 'pinia'
import axios from 'axios'

export const useProjectStore = defineStore('projects', {
  state: () => ({
    projects: [],
    selectedProjectId: null
  }),
  actions: {
    async fetchProjects() {
      const { data } = await axios.get('/system/projects')
      this.projects = data
    },
    async syncProjects() {
      await axios.post('/system/projects/sync')
      await this.fetchProjects()
    },
    setSelectedProject(id) {
      this.selectedProjectId = id
    }
  }
})


