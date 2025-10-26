<template>
  <div class="home">
    <h1>YouTube動画URL入力</h1>
    <p>URLを貼り付けてください。</p>

    <div class="input-area">
      <input type="text" v-model="youtubeUrl" placeholder="https://www.youtube.com/watch?v=..." />
      <button @click="startCollection"> 収集・字幕取得 (Collect)</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';


const youtubeUrl = ref('');
const router = useRouter();
const startCollection = () => {
  console.log('入力されたURL:', youtubeUrl.value);
  router.push('/analyze');
};
</script>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.input-area {
  display: flex;
  gap: 0.5rem;
  width: 500px;
}

input {
  flex-grow: 1;
  padding: 0.5rem;
  font-size: 1rem;
}

button {
  padding: 0.5rem 1rem;
  font-size: 1rem;
  cursor: pointer;
}
</style>
