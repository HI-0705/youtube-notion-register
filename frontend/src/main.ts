import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// Vueのインスタンス生成
const app = createApp(App)

// Piniaとルーターの設定
app.use(createPinia())
app.use(router)

app.mount('#app')
