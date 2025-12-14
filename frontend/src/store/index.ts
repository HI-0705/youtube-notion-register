import { defineStore } from "pinia";

interface AnalysisResult {
  summary: string;
  suggested_titles: string;
  categories: string[];
  emotions: string;
}

interface Notification {
  message: string;
  type: "success" | "error";
}

let notificationTimer: number | undefined;

export const useMainStore = defineStore("main", {
  state: () => ({
    sessionId: null as string | null,
    analysisResult: null as AnalysisResult | null,
    notification: null as Notification | null,
  }),
  actions: {
    setSessionId(id: string) {
      this.sessionId = id;
    },
    clearSessionId() {
      this.sessionId = null;
    },
    setAnalysisResult(result: AnalysisResult) {
      this.analysisResult = result;
    },
    clearAnalysisResult() {
      this.analysisResult = null;
    },
    showNotification(notification: Notification, duration: number = 5000) {
      if (notificationTimer) {
        clearTimeout(notificationTimer);
      }
      this.notification = notification;
      notificationTimer = window.setTimeout(() => {
        this.notification = null;
      }, duration);
    },
    hideNotification() {
      this.notification = null;
      if (notificationTimer) clearTimeout(notificationTimer);
    },
  },
});
