<template>
  <div class="home">
    <h1>YouTube動画URL入力</h1>
    <p>URLを貼り付けてください。</p>

    <div class="input-area">
      <input type="text" v-model="youtubeUrl" placeholder="https://www.youtube.com/watch?v=..." :disabled="isLoading" />
      <!-- 現状は非表示にしておく -->
      <input v-if="false" type="text" v-model="channelId" placeholder="チャンネルID (例: UC...)" :disabled="isLoading" />
      <button @click="startCollection" :disabled="isLoading">
        <span v-if="isLoading">収集中...</span>
        <span v-else>収集・字幕取得 (Collect)</span>
      </button>
    </div>
    <p v-if="error" class="error-message">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'
import { useMainStore } from '../store'

const youtubeUrl = ref('')
const channelId = ref('')
const isLoading = ref(false)
const error = ref<string | null>(null)
const router = useRouter()
const mainStore = useMainStore()

const startCollection = async () => {
  error.value = null
  isLoading.value = true

  try {
    if (!youtubeUrl.value) {
      error.value = 'YouTube URLは必須です。'
      return
    }
    if (!youtubeUrl.value.startsWith('https://www.youtube.com/watch?v=')) {
      error.value = '動画のURLを入力してください。'
      return
    }

    console.log('入力されたURL:', youtubeUrl.value)

    const response = await api.collectVideoData({
      url: youtubeUrl.value,
      channel_id: channelId.value || undefined,
    })

    if (response.status === 'success' && response.session_id) {
      mainStore.setSessionId(response.session_id)
      router.push('/analyze')
    } else {
      error.value = response.message || '動画データの収集に失敗しました。'
    }
  } catch (err: any) {
    console.error('動画データ収集エラー:', err)
    error.value = err.response?.data?.detail || '動画データの収集中にエラーが発生しました。'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
}

.input-area {
  display: flex;
  gap: 0.8rem;
  width: 100%;
  max-width: 500px;
}

input {
  flex-grow: 1;
  padding: 0.7rem;
  font-size: 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}

button {
  padding: 0.7rem 1.5rem;
  font-size: 1rem;
  cursor: pointer;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

button:hover:not(:disabled) {
  background-color: #0056b3;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.error-message {
  color: red;
  margin-top: 1rem;
  font-weight: bold;
}
</style>
