<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NCard, NForm, NFormItem, NInput, NButton, NSelect, NSpace, NAlert } from 'naive-ui'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const email = ref('')
const password = ref('')
const role = ref('client')
const error = ref('')
const loading = ref(false)

onMounted(() => {
  const r = route.query.role as string
  if (r === 'developer' || r === 'client') role.value = r
})

const roleOptions = [
  { label: 'Клиент', value: 'client' },
  { label: 'Разработчик', value: 'developer' },
]

async function submit() {
  loading.value = true
  error.value = ''
  try {
    await auth.register(email.value, password.value, role.value)
    await auth.login(email.value, password.value)
    router.push('/projects')
  } catch {
    error.value = 'Ошибка регистрации'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <NCard title="Регистрация" style="max-width: 400px; width: 100%">
      <NAlert v-if="error" type="error" style="margin-bottom: 16px">{{ error }}</NAlert>
      <NForm @submit.prevent="submit">
        <NFormItem label="Почта">
          <NInput v-model:value="email" />
        </NFormItem>
        <NFormItem label="Пароль">
          <NInput v-model:value="password" type="password" show-password-on="click" />
        </NFormItem>
        <NFormItem label="Роль">
          <NSelect v-model:value="role" :options="roleOptions" />
        </NFormItem>
        <NSpace>
          <NButton type="primary" attr-type="submit" :loading="loading">Зарегистрироваться</NButton>
          <NButton text @click="router.push('/login')">Войти</NButton>
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
