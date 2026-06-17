<script setup lang="ts">
import { RouterView, useRouter } from 'vue-router'
import { NLayout, NLayoutHeader, NLayoutContent, NButton, NSpace, NText } from 'naive-ui'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
</script>

<template>
  <NLayout style="min-height: 100vh">
    <NLayoutHeader bordered style="height: 56px; padding: 0 24px; display: flex; align-items: center">
      <NSpace align="center" justify="space-between" style="width: 100%">
        <NText strong style="font-size: 20px; cursor: pointer" @click="router.push('/')">AIKworkw</NText>
        <NSpace>
          <NButton quaternary @click="router.push('/blog')">Блог</NButton>
          <NButton quaternary @click="router.push('/feed')">Лента</NButton>
          <NButton v-if="auth.user" type="primary" @click="router.push('/cabinet')">Кабинет</NButton>
          <NButton v-else type="primary" @click="router.push('/register')">Регистрация</NButton>
        </NSpace>
      </NSpace>
    </NLayoutHeader>
    <NLayoutContent>
      <RouterView />
    </NLayoutContent>
  </NLayout>
</template>

<style scoped>
:deep(.landing-section) {
  max-width: 1100px;
  margin: 0 auto;
  padding: 48px 24px;
}
</style>
