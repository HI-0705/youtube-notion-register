<template>
  <div class="analyze-container">
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner"></div>
      <p>分析中...</p>
    </div>

    <div v-if="!isLoading && analysisResult" class="analyze-content">
      <h1>分析結果</h1>
      <p>分析結果です。必要に応じて内容を修正してください。</p>

      <div class="form-group">
        <label for="title">タイトル案</label>
        <input id="title" type="text" v-model="analysisResult.suggested_titles" />
      </div>

      <div class="form-group">
        <label for="summary">要約</label>
        <textarea id="summary" v-model="analysisResult.summary"></textarea>
      </div>

      <div class="form-group">
        <label for="categories">カテゴリ</label>
        <div class="categories-chips">
          <span v-for="cat in analysisResult.categories" :key="cat" class="chip">{{ cat }}</span>
        </div>
      </div>

      <div class="form-group">
        <label for="emotions">感情</label>
        <div class="emotions-chips">
          <span class="chip">{{ analysisResult.emotions }}</span>
        </div>
      </div>

      <button @click="goToRegister">登録内容を修正して進む</button>
    </div>

    <div v-if="error" class="error-message">
      <h2>エラーが発生しました</h2>
      <p>{{ error }}</p>
      <button @click="goHome">ホームに戻る</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMainStore } from '../store'
import { api } from '../services/api'

interface AnalysisResult {
  summary: string
  suggested_titles: string
  categories: string[]
  emotions: string
}

const mainStore = useMainStore()
const router = useRouter()

const isLoading = ref(true)
const error = ref<string | null>(null)
const analysisResult = ref<AnalysisResult | null>(null)

// 分析
onMounted(async () => {
  const sessionId = mainStore.sessionId
  if (!sessionId) {
    error.value = 'セッションIDが見つかりません。'
    isLoading.value = false
    return
  }

  try {
    console.log(`分析を開始します。セッションID: ${sessionId}`)
    const response = await api.analyzeTranscript({ session_id: sessionId })

    if (response.status === 'success' && response.data) {
      analysisResult.value = response.data
      console.log('分析結果:', response.data)
    } else {
      throw new Error(response.message || '分析に失敗しました。')
    }
  } catch (err: any) {
    console.error('分析エラー:', err)
    error.value = err.response?.data?.detail || err.message || '分析中にエラーが発生しました。'
  } finally {
    isLoading.value = false
  }
})

// ユーザーの修正を保存
const goToRegister = () => {
  if (analysisResult.value) {
    mainStore.setAnalysisResult(analysisResult.value)
    router.push('/register')
  }
}

const goHome = () => {
  router.push('/')
}
</script>

<style scoped>
.analyze-container {
  padding: 2rem;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.spinner {
  border: 8px solid #f3f3f3;
  border-top: 8px solid #3498db;
  border-radius: 50%;
  width: 60px;
  height: 60px;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.analyze-content {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  width: 100%;
  text-align: left;
}

label {
  margin-bottom: 0.5rem;
  font-weight: bold;
  font-size: 1.1rem;
}

input,
textarea {
  padding: 0.75rem;
  font-size: 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  width: 100%;
  box-sizing: border-box;
}

textarea {
  height: 250px;
  resize: vertical;
  line-height: 1.6;
}

.categories-chips,
.emotions-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.chip {
  background-color: #e0e0e0;
  padding: 0.5rem 1rem;
  border-radius: 16px;
  font-size: 0.9rem;
}

button {
  padding: 0.8rem 2rem;
  font-size: 1.1rem;
  cursor: pointer;
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  transition: background-color 0.2s ease;
  align-self: center;
}

button:hover {
  background-color: #218838;
}

.error-message {
  text-align: center;
  color: red;
}
</style>
