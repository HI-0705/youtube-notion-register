<template>
  <div class="analyze-container">
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner"></div>
      <p>分析中...</p>
    </div>

    <div v-if="!isLoading" class="analyze-content">
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
          <span v-for="cat in allCategories" :key="cat" class="chip"
            :class="{ 'chip-selected': isCategorySelected(cat) }" @click="toggleCategory(cat)">
            {{ cat }}
          </span>
        </div>
      </div>

      <div class="form-group">
        <label for="emotions">感情</label>
        <select id="emotions" v-model="analysisResult.emotions">
          <option v-for="emotion in allEmotions" :key="emotion" :value="emotion">
            {{ emotion }}
          </option>
        </select>
      </div>

      <button @click="goToRegister">登録内容を修正して進む</button>
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
const analysisResult = ref<AnalysisResult>({
  summary: '',
  suggested_titles: '',
  categories: [],
  emotions: ''
})

const allCategories = [
  "音楽", "動物", "スポーツ", "旅行", "ゲーム", "コメディ",
  "エンターテインメント", "教育", "科学", "映画", "アニメ",
  "クラシック", "ドキュメンタリー", "ドラマ", "ショートムービー", "その他"
]

const allEmotions = [
  "感動", "愉快", "驚愕", "啓発", "考察", "癒着", "その他"
]

// 分析
onMounted(async () => {
  const sessionId = mainStore.sessionId
  if (!sessionId) {
    mainStore.showNotification({ message: 'セッションIDが見つかりません。', type: 'error' });
    isLoading.value = false
    return
  }

  try {
    console.log(`分析を開始します。セッションID: ${sessionId}`)
    const response = await api.analyzeTranscript({ session_id: sessionId })

    if (response.status === 'success' && response.data) {
      analysisResult.value = {
        ...analysisResult.value,
        ...response.data,
        categories: response.data.categories || [],
        emotions: response.data.emotions || allEmotions[0]
      }
      mainStore.showNotification({ message: '分析が完了しました。内容を確認してください。', type: 'success' });
      console.log('分析結果:', analysisResult.value)
    } else {
      mainStore.showNotification({ message: response.message || '分析に失敗しました。', type: 'error' });
    }
  } catch (err: any) {
    console.error('分析エラー:', err)
    const errorMessage = err.response?.data?.detail || err.message || '分析中にエラーが発生しました。';
    mainStore.showNotification({ message: errorMessage, type: 'error' });
  } finally {
    isLoading.value = false
  }
})

// ユーザーの修正を保存
const goToRegister = () => {
  if (analysisResult.value) {
    mainStore.setAnalysisResult(analysisResult.value)
    router.push('/register')
  } else {
    mainStore.showNotification({ message: '分析結果がありません。ホームに戻ります。', type: 'error' });
    router.push('/');
  }
}

const goHome = () => {
  router.push('/')
}

const toggleCategory = (category: string) => {
  if (!analysisResult.value) return;

  const index = analysisResult.value.categories.indexOf(category);
  if (index > -1) {
    analysisResult.value.categories.splice(index, 1);
  } else {
    analysisResult.value.categories.push(category);
  }
};

const isCategorySelected = (category: string): boolean => {
  return analysisResult.value?.categories.includes(category);
};
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
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}


.chip:hover {
  background-color: #d0d0d0;
}

.chip-selected {
  background-color: #007bff;
  color: white;
}

select {
  padding: 0.75rem;
  font-size: 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  width: 100%;
  box-sizing: border-box;
  background-color: white;
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
</style>
