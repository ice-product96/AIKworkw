<script setup lang="ts">
import { RouterView, useRouter } from 'vue-router'
import { NLayout, NLayoutHeader, NLayoutContent, NButton, NSpace, NText } from 'naive-ui'
import { useAuthStore } from '../stores/auth'
import MarketplaceStatsBar from '../components/marketplace/MarketplaceStatsBar.vue'

const router = useRouter()
const auth = useAuthStore()

function placeOrder() {
  if (auth.user?.role === 'client') router.push('/cabinet/orders/new')
  else if (auth.user) router.push('/cabinet')
  else router.push('/register')
}
</script>

<template>
  <NLayout style="min-height: 100vh; background: #f5f5f5">
    <MarketplaceStatsBar />
    <NLayoutHeader bordered style="height: auto; padding: 12px 24px; background: #fff">
      <NSpace align="center" justify="space-between" style="width: 100%; max-width: 1200px; margin: 0 auto">
        <NText strong style="font-size: 22px; cursor: pointer; color: #2e7d32" @click="router.push('/')">
          AIKworkw
        </NText>
        <NSpace align="center" :size="12">
          <NButton quaternary @click="router.push('/projects')">Биржа проектов</NButton>
          <NButton quaternary @click="router.push('/blog')">Блог</NButton>
          <NButton v-if="auth.user" quaternary @click="router.push('/chat')">Чат</NButton>
          <NButton v-if="auth.user" quaternary @click="router.push('/cabinet')">Кабинет</NButton>
          <NButton v-if="!auth.user" quaternary @click="router.push('/login')">Вход</NButton>
          <NButton type="primary" style="background: #4caf50; border-color: #4caf50" @click="placeOrder">
            {{ auth.user ? 'Разместить заказ' : 'Регистрация' }}
          </NButton>
        </NSpace>
      </NSpace>
    </NLayoutHeader>
    <NLayoutContent>
      <RouterView />
    </NLayoutContent>
  </NLayout>
</template>
