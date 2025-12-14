<template>
  <div id="app">
    <header>
    </header>
    <main>
      <router-view />
    </main>
    <GlobalNotification />
  </div>
</template>

<script setup lang="ts">
import GlobalNotification from './components/GlobalNotification.vue';
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
