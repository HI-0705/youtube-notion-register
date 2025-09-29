import { defineStore } from 'pinia'

// ストア定義
export const useMainStore = defineStore('main', {
  state: () => ({
    sessionId: null as string | null,
  }),
  actions: {
    // set
    setSessionId(id: string) {
      this.sessionId = id
    },
    // clear
    clearSessionId() {
      this.sessionId = null
    },
  },
})
