<script setup lang="ts">
import { RouterView, useRouter } from 'vue-router'
import { NLayout, NLayoutHeader, NLayoutContent, NButton, NSpace, NText } from 'naive-ui'
import { useAuthStore } from '../stores/auth'
import MarketplaceStatsBar from '../components/marketplace/MarketplaceStatsBar.vue'
import { MARKETPLACE_CATEGORIES } from '../constants/marketplace'

const router = useRouter()
const auth = useAuthStore()
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
          <NButton v-if="auth.user" quaternary @click="router.push('/feed')">Лента</NButton>
          <NButton v-if="auth.user" quaternary @click="router.push('/cabinet')">Кабинет</NButton>
          <NButton v-if="!auth.user" quaternary @click="router.push('/login')">Вход</NButton>
          <NButton type="primary" style="background: #4caf50; border-color: #4caf50" @click="router.push('/register')">
            {{ auth.user ? 'Разместить заказ' : 'Регистрация' }}
          </NButton>
        </NSpace>
      </NSpace>
      <div class="quick-cats">
        <button
          v-for="cat in MARKETPLACE_CATEGORIES"
          :key="cat.slug"
          type="button"
          class="quick-cat"
          @click="router.push({ path: '/projects', query: { category: cat.slug } })"
        >
          {{ cat.icon }} {{ cat.label }}
        </button>
      </div>
    </NLayoutHeader>
    <NLayoutContent>
      <RouterView />
    </NLayoutContent>
  </NLayout>
</template>

<style scoped>
.quick-cats {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
  max-width: 1200px;
}
.quick-cat {
  border: none;
  background: transparent;
  font-size: 13px;
  color: #444;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}
.quick-cat:hover {
  background: #e8f5e9;
  color: #1b5e20;
}
</style>
