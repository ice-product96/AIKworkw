<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute, RouterView } from 'vue-router'
import { NLayout, NLayoutSider, NLayoutContent, NMenu, NButton, NSpace, NText } from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const menuOptions = computed<MenuOption[]>(() => {
  const role = auth.user?.role
  if (role === 'client') {
    return [
      { label: 'Мои заказы', key: '/dashboard/orders' },
      { label: 'Создать заказ', key: '/dashboard/orders/new' },
    ]
  }
  if (role === 'developer') {
    return [
      { label: 'Мои агенты', key: '/dashboard/agents' },
      { label: 'Создать агента', key: '/dashboard/agents/new' },
    ]
  }
  if (role === 'admin') {
    return [
      { label: 'Пользователи', key: '/dashboard/admin/users' },
      { label: 'Агенты', key: '/dashboard/admin/agents' },
      { label: 'Заказы', key: '/dashboard/admin/orders' },
      { label: 'Нарушения', key: '/dashboard/admin/violations' },
      { label: 'Webhooks', key: '/dashboard/admin/webhooks' },
    ]
  }
  return []
})

function handleMenu(key: string) {
  router.push(key)
}

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <NLayout has-sider style="min-height: 100vh">
    <NLayoutSider bordered width="240" content-style="padding: 16px">
      <NSpace vertical :size="16">
        <NText strong style="font-size: 18px">AIKworkw</NText>
        <NText depth="3">{{ auth.user?.email }}</NText>
        <NMenu :value="route.path" :options="menuOptions" @update:value="handleMenu" />
        <NButton quaternary @click="logout">Выйти</NButton>
      </NSpace>
    </NLayoutSider>
    <NLayoutContent content-style="padding: 24px">
      <RouterView />
    </NLayoutContent>
  </NLayout>
</template>
