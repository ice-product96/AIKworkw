<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute, RouterView } from 'vue-router'
import { NLayout, NLayoutHeader, NLayoutContent, NMenu, NButton, NSpace, NText } from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import { useAuthStore } from '../stores/auth'
import { useNotifications } from '../composables/useNotifications'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
useNotifications()

const navOptions: MenuOption[] = [
  { label: 'Лента заказов', key: '/feed' },
  { label: 'Чат', key: '/chat' },
  { label: 'Личный кабинет', key: '/cabinet' },
]

const activeNav = computed(() => {
  const p = route.path
  if (p.startsWith('/feed')) return '/feed'
  if (p.startsWith('/chat')) return '/chat'
  if (p.startsWith('/cabinet')) return '/cabinet'
  return p
})

function handleNav(key: string) {
  router.push(key)
}

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <NLayout style="min-height: 100vh">
    <NLayoutHeader bordered style="height: 56px; padding: 0 24px; display: flex; align-items: center">
      <NSpace align="center" justify="space-between" style="width: 100%">
        <NSpace align="center" :size="24">
          <NText strong style="font-size: 18px; cursor: pointer" @click="router.push('/')">AIKworkw</NText>
          <NMenu mode="horizontal" :value="activeNav" :options="navOptions" @update:value="handleNav" />
        </NSpace>
        <NSpace align="center">
          <NText depth="3">{{ auth.user?.email }}</NText>
          <NButton quaternary size="small" @click="logout">Выйти</NButton>
        </NSpace>
      </NSpace>
    </NLayoutHeader>
    <NLayoutContent content-style="padding: 24px; max-width: 1200px; margin: 0 auto">
      <RouterView />
    </NLayoutContent>
  </NLayout>
</template>
