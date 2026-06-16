<script setup lang="ts">
import { useAuthStore } from '../stores/auth'
import { NCard, NText, NButton } from 'naive-ui'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

const roleLabels: Record<string, string> = {
  client: 'Клиент',
  developer: 'Разработчик',
  admin: 'Администратор',
}

function goToCabinet() {
  const role = auth.user?.role
  if (role === 'client') router.push('/dashboard/orders')
  else if (role === 'developer') router.push('/dashboard/agents')
  else if (role === 'admin') router.push('/dashboard/admin/orders')
}
</script>

<template>
  <NCard title="Личный кабинет">
    <NText>Добро пожаловать, {{ auth.user?.email }}</NText>
    <br />
    <NText depth="3">Роль: {{ roleLabels[auth.user?.role || ''] || auth.user?.role }}</NText>
    <br /><br />
    <NButton type="primary" @click="goToCabinet">Перейти в кабинет</NButton>
  </NCard>
</template>
