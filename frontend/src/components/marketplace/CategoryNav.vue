<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { MARKETPLACE_CATEGORIES } from '../../constants/marketplace'

const router = useRouter()
const route = useRoute()

const basePath = () => (route.path.startsWith('/feed') ? '/feed' : '/projects')

function goCategory(slug: string | null) {
  const base = basePath()
  if (slug) router.push({ path: base, query: { category: slug } })
  else router.push(base)
}

function isActive(slug: string | null) {
  const c = route.query.category as string | undefined
  if (!slug) return !c
  return c === slug
}
</script>

<template>
  <nav class="cat-nav">
    <button type="button" class="cat-item" :class="{ active: isActive(null) }" @click="goCategory(null)">
      Все категории
    </button>
    <button
      v-for="cat in MARKETPLACE_CATEGORIES"
      :key="cat.slug"
      type="button"
      class="cat-item"
      :class="{ active: isActive(cat.slug) }"
      @click="goCategory(cat.slug)"
    >
      <span class="icon">{{ cat.icon }}</span>
      {{ cat.label }}
    </button>
  </nav>
</template>

<style scoped>
.cat-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 24px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  max-width: 1200px;
  margin: 0 auto;
}
.cat-item {
  border: 1px solid #e0e0e0;
  background: #fafafa;
  border-radius: 20px;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.cat-item:hover,
.cat-item.active {
  background: #e8f5e9;
  border-color: #4caf50;
  color: #1b5e20;
}
.icon {
  margin-right: 4px;
}
</style>
