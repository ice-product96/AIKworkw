<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute, RouterView } from 'vue-router'
import { NLayout, NLayoutSider, NLayoutContent, NMenu, NText } from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const menuOptions = computed<MenuOption[]>(() => {
  const role = auth.user?.role
  if (role === 'client') {
    return [
      { label: 'Обзор', key: '/cabinet' },
      { label: 'Мои заказы', key: '/cabinet/orders' },
      { label: 'Создать заказ', key: '/cabinet/orders/new' },
    ]
  }
  if (role === 'developer') {
    return [
      { label: 'Обзор', key: '/cabinet' },
      { label: 'Мои агенты', key: '/cabinet/agents' },
      { label: 'Создать агента', key: '/cabinet/agents/new' },
    ]
  }
  if (role === 'admin') {
    return [
      { label: 'Обзор', key: '/cabinet' },
      { label: 'Пользователи', key: '/cabinet/admin/users' },
      { label: 'Агенты', key: '/cabinet/admin/agents' },
      { label: 'Заказы', key: '/cabinet/admin/orders' },
      { label: 'Нарушения', key: '/cabinet/admin/violations' },
      { label: 'Webhooks', key: '/cabinet/admin/webhooks' },
    ]
  }
  return [{ label: 'Обзор', key: '/cabinet' }]
})

function handleMenu(key: string) {
  router.push(key)
}
</script>

<template>
  <NLayout has-sider style="min-height: calc(100vh - 120px)">
    <NLayoutSider bordered width="220" content-style="padding: 12px">
      <NText depth="3" style="display: block; margin-bottom: 12px">Личный кабинет</NText>
      <NMenu :value="route.path" :options="menuOptions" @update:value="handleMenu" />
    </NLayoutSider>
    <NLayoutContent content-style="padding: 0 0 0 16px">
      <RouterView />
    </NLayoutContent>
  </NLayout>
</template>
