<template>
  <div class="register-container">
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner"></div>
      <p>登録しています...</p>
    </div>
    <div v-if="notionUrl" class="result-view">
      <h1>登録完了</h1>
      <p>登録が完了しました。</p>
      <div class="link-area">
        <p>以下のリンクから確認できます。</p>
        <a :href="notionUrl" target="_blank" rel="noopener noreferrer" class="notion-link">{{ notionUrl }}</a>
      </div>
      <button @click="goHome">ホームに戻る</button>
    </div>
    <div v-if="!isLoading && !notionUrl && !error" class="confirmation-view">
      <h1>登録内容の確認</h1>
      <p>以下の内容で登録します。</p>
      <div class="confirmation-content">
        <div class="form-group">
          <label>タイトル</label>
          <p class="value">{{ finalData?.suggested_titles }}</p>
        </div>
        <div class="form-group">
          <label>要約</label>
          <pre class="value summary">{{ finalData?.summary }}</pre>
        </div>
        <div class="form-group">
          <label>カテゴリ</label>
          <div class="categories-chips">
            <span v-for="cat in finalData?.categories" :key="cat" class="chip">{{ cat }}</span>
          </div>
        </div>
        <div class="form-group">
          <label>感情</label>
          <div class="emotions-chips">
            <span class="chip">{{ finalData?.emotions }}</span>
          </div>
        </div>
      </div>
      <div class="button-group">
        <button @click="goBack" class="secondary">戻る</button>
        <button @click="registerToNotion">登録する</button>
      </div>
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

const isLoading = ref(false)
const error = ref<string | null>(null)
const notionUrl = ref<string | null>(null)
const finalData = ref<AnalysisResult | null>(null)

onMounted(() => {
  if (!mainStore.sessionId || !mainStore.analysisResult) {
    error.value = 'セッション情報が見つかりません。'
    return
  }
  finalData.value = mainStore.analysisResult
})

const registerToNotion = async () => {
  if (!mainStore.sessionId || !finalData.value) {
    error.value = '登録データがありません。'
    return
  }

  isLoading.value = true
  error.value = null

  try {
    const response = await api.registerToNotion({
      session_id: mainStore.sessionId,
      modifications: {
        title: finalData.value.suggested_titles,
        summary: finalData.value.summary,
        categories: finalData.value.categories,
        emotions: finalData.value.emotions,
      },
    })

    if (response.status === 'success' && response.data?.notion_url) {
      notionUrl.value = response.data.notion_url
      mainStore.clearSessionId()
      mainStore.setAnalysisResult({ summary: '', suggested_titles: '', categories: [], emotions: '' })
    } else {
      throw new Error(response.message || '登録に失敗しました。')
    }
  } catch (err: any) {
    console.error('登録エラー:', err)
    error.value = err.response?.data?.detail || err.message || '登録中にエラーが発生しました。'
  } finally {
    isLoading.value = false
  }
}

const goBack = () => {
  router.back()
}

const goHome = () => {
  router.push('/')
}
</script>

<style scoped>
.register-container {
  padding: 2rem;
  max-width: 800px;
  margin: 0 auto;
}

.loading-overlay,
.result-view,
.confirmation-view,
.error-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

.spinner {
  border: 8px solid #f3f3f3;
  border-top: 8px solid #3498db;
  border-radius: 50%;
  width: 60px;
  height: 60px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.confirmation-content {
  width: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 2rem;
  background-color: #fafafa;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  text-align: left;
}

label {
  font-weight: bold;
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
  display: block;
}

.value {
  font-size: 1rem;
  background-color: #fff;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.summary {
  white-space: pre-wrap;
  line-height: 1.6;
  max-height: 300px;
  overflow-y: auto;
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

.button-group {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

button {
  padding: 0.8rem 2rem;
  font-size: 1.1rem;
  cursor: pointer;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

button.secondary {
  background-color: #6c757d;
}

button:hover {
  opacity: 0.9;
}

.link-area {
  margin-top: 1rem;
  padding: 1.5rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
  width: 100%;
  text-align: center;
}

.notion-link {
  font-weight: bold;
  color: #007bff;
  word-break: break-all;
}

.error-message {
  color: red;
}
</style>
