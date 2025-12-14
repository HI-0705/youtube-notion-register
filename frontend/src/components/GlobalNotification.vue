<template>
    <transition name="fade">
        <div v-if="notification" :class="['notification', `notification--${notification.type}`]" @click="hide">
            <p>{{ notification.message }}</p>
        </div>
    </transition>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useMainStore } from "../store";

const mainStore = useMainStore();
const notification = computed(() => mainStore.notification);

const hide = () => {
    mainStore.hideNotification();
};
</script>

<style scoped>
.notification {
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    color: white;
    z-index: 2000;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    font-weight: bold;
    cursor: pointer;
}

.notification--success {
    background-color: #28a745;
}

.notification--error {
    background-color: #dc3545;
}

.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
</style>
