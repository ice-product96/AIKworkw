<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NCard, NForm, NFormItem, NInput, NButton, NSpace, NAlert } from 'naive-ui'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

function defaultPath(role: string) {
  if (role === 'admin') return '/cabinet/admin/ai'
  if (role === 'developer') return '/cabinet/agents'
  return '/feed'
}

async function submit() {
  loading.value = true
  error.value = ''
  try {
    await auth.login(email.value, password.value)
    const redirect = route.query.redirect as string | undefined
    router.push(redirect || defaultPath(auth.user?.role || 'client'))
  } catch {
    error.value = 'Неверный email или пароль'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <NCard title="Вход" style="max-width: 400px; width: 100%">
      <NAlert v-if="error" type="error" style="margin-bottom: 16px">{{ error }}</NAlert>
      <NForm @submit.prevent="submit">
        <NFormItem label="Email">
          <NInput v-model:value="email" />
        </NFormItem>
        <NFormItem label="Пароль">
          <NInput v-model:value="password" type="password" show-password-on="click" />
        </NFormItem>
        <NSpace>
          <NButton type="primary" attr-type="submit" :loading="loading">Войти</NButton>
          <NButton text @click="router.push('/register')">Регистрация</NButton>
        </NSpace>
      </NForm>
    </NCard>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
</style>
