<template>
  <div class="analyze">
    <h1>分析結果の確認・修正</h1>
    <p>要約結果を必要に応じて修正してください。</p>

    <div class="form-group">
      <label for="title">タイトル</label>
      <input id="title" type="text" v-model="title" />
    </div>

    <div class="form-group">
      <label for="summary">要約</label>
      <textarea id="summary" v-model="summary"></textarea>
    </div>

    <button @click="register">2. Notionに登録 (Register)</button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useMainStore } from '../store';

const mainStore = useMainStore();
const router = useRouter();
const title = ref('');
const summary = ref('');

// 現時点ではダミーデータを設定
onMounted(() => {
  console.log('セッションID:', mainStore.sessionId);
  title.value = 'サンプルタイトル';
  summary.value = '動画の要約がセットされ内容を自由に編集できる。';
});

const register = () => {
  console.log('登録する内容:', { title: title.value, summary: summary.value });
  router.push('/register');
};
</script>

<style scoped>
.analyze {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}
.form-group {
  display: flex;
  flex-direction: column;
  width: 600px;
  text-align: left;
}
label {
  margin-bottom: 0.5rem;
  font-weight: bold;
}
input, textarea {
  padding: 0.75rem;
  font-size: 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}
textarea {
  height: 200px;
  resize: vertical;
}
button {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  cursor: pointer;
}
</style>
