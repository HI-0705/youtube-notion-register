<template>
  <div class="register">
    <h1>登録完了</h1>
    <p>Notionに登録されました。</p>
    <div class="link-area" v-if="notionUrl">
      <p>以下のリンクから確認できます。</p>
      <a :href="notionUrl" target="_blank" rel="noopener noreferrer">{{ notionUrl }}</a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useMainStore } from '../store';

const mainStore = useMainStore();
const notionUrl = ref('');

// 現時点ではダミーを表示
onMounted(() => {
  notionUrl.value = 'https://www.notion.so/your-page-was-created-successfully';

  // 処理完了後にセッションIDをクリア
  mainStore.clearSessionId();
  console.log('セッションIDをクリア:', mainStore.sessionId);
});
</script>

<style scoped>
.register {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}
.link-area {
  margin-top: 1rem;
  padding: 1.5rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
}
a {
  font-weight: bold;
  color: #007bff;
}
</style>
