<script setup lang="ts">
import { useAuthStore } from '../stores/auth'
import { NCard, NText, NButton, NSpace } from 'naive-ui'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

const roleLabels: Record<string, string> = {
  client: 'Клиент',
  developer: 'Разработчик',
  admin: 'Администратор',
}

function goToSection() {
  const role = auth.user?.role
  if (role === 'client') router.push('/cabinet/orders')
  else if (role === 'developer') router.push('/cabinet/agents')
  else if (role === 'admin') router.push('/cabinet/admin/orders')
}
</script>

<template>
  <NCard title="Личный кабинет">
    <NSpace vertical>
      <NText>Добро пожаловать, {{ auth.user?.email }}</NText>
      <NText depth="3">Роль: {{ roleLabels[auth.user?.role || ''] || auth.user?.role }}</NText>
      <NText depth="3">
        Лента заказов и чат — в верхнем меню. Здесь управление вашими заказами, агентами и настройками.
      </NText>
      <NSpace>
        <NButton type="primary" @click="goToSection">Перейти к разделу</NButton>
        <NButton @click="router.push('/projects')">Биржа проектов</NButton>
      </NSpace>
    </NSpace>
  </NCard>
</template>
