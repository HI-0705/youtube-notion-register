import { defineStore } from "pinia";

interface AnalysisResult {
  summary: string;
  suggested_titles: string;
  categories: string[];
  emotions: string;
}

export const useMainStore = defineStore("main", {
  state: () => ({
    sessionId: null as string | null,
    analysisResult: null as AnalysisResult | null,
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
  },
});
