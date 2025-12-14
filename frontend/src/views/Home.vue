<template>
  <div class="home">
    <h1>YouTube動画URL入力</h1>
    <p>URLを貼り付けてください。</p>

    <div class="input-area">
      <input type="text" v-model="youtubeUrl" placeholder="https://www.youtube.com/watch?v=..." :disabled="isLoading" />
      <button @click="startCollection" :disabled="isLoading">
        <span v-if="isLoading">収集中...</span>
        <span v-else>収集・字幕取得 (Collect)</span>
      </button>
    </div>
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
const router = useRouter()
const mainStore = useMainStore()
const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]{11}(&.*)?$/

const startCollection = async () => {
  isLoading.value = true

  if (!youtubeRegex.test(youtubeUrl.value)) {
    mainStore.showNotification({ message: '有効なURLを入力してください。', type: 'error' });
    isLoading.value = false
    return
  }

  console.log('入力されたURL:', youtubeUrl.value)
  try {
    const response = await api.collectVideoData({
      url: youtubeUrl.value,
      channel_id: channelId.value || undefined,
    })

    if (response.status === 'success' && response.session_id) {
      mainStore.setSessionId(response.session_id)
      mainStore.showNotification({ message: '動画データの収集と字幕取得が完了しました。', type: 'success' });
      router.push('/analyze')
    } else {
      mainStore.showNotification({ message: response.message || '動画データの収集に失敗しました。', type: 'error' });
    }
  } catch (err: any) {
    console.error('動画データ収集エラー:', err)
    const errorMessage = err.response?.data?.detail || '動画データの収集中にエラーが発生しました。';
    mainStore.showNotification({ message: errorMessage, type: 'error' });
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
</style>
