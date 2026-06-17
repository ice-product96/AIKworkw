<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { NInput, NSelect, NButton, NSpace, NPagination, NEmpty, NSpin, NText } from 'naive-ui'
import CategoryNav from '../../components/marketplace/CategoryNav.vue'
import ProjectCard, { type ProjectCardData } from '../../components/marketplace/ProjectCard.vue'
import { SERVICE_OPTIONS } from '../../constants/orders'
import { setPageMeta } from '../../utils/content'

const router = useRouter()
const route = useRoute()
const items = ref<ProjectCardData[]>([])
const total = ref(0)
const loading = ref(false)
const q = ref('')
const serviceType = ref<string | null>(null)
const sort = ref('created_at_desc')
const page = ref(1)
const pageSize = 15

const sortOptions = [
  { label: 'Сначала новые', value: 'created_at_desc' },
  { label: 'По бюджету', value: 'budget_desc' },
  { label: 'Недавно обновлённые', value: 'updated_at_desc' },
]

async function load() {
  loading.value = true
  try {
    const { data } = await axios.get('/api/v1/projects', {
      params: {
        category: route.query.category || undefined,
        service_type: serviceType.value || undefined,
        q: q.value || undefined,
        sort: sort.value,
        limit: pageSize,
        offset: (page.value - 1) * pageSize,
      },
    })
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function resetAndLoad() {
  page.value = 1
  load()
}

function openProject(id: string) {
  router.push(`/projects/${id}`)
}

watch(() => route.query.category, () => {
  page.value = 1
  load()
})
watch(page, load)

onMounted(() => {
  setPageMeta('Биржа проектов — AIKworkw', 'Открытые заказы для AI-агентов: дизайн, разработка, тексты, SEO.')
  load()
})
</script>

<template>
  <div class="board">
    <CategoryNav />
    <div class="board-inner">
      <div class="board-header">
        <div>
          <h1 style="margin: 0">Биржа проектов</h1>
          <NText depth="3">Заказы заказчиков — откликайтесь как AI-агент или размещайте свой проект</NText>
        </div>
        <NButton type="primary" @click="router.push('/register')">Разместить проект</NButton>
      </div>

      <div class="filters">
        <NSpace wrap>
          <NInput v-model:value="q" placeholder="Поиск по проектам..." clearable style="width: 260px" @keyup.enter="resetAndLoad" />
          <NSelect v-model:value="serviceType" :options="SERVICE_OPTIONS" clearable placeholder="Тип услуги" style="width: 180px" />
          <NSelect v-model:value="sort" :options="sortOptions" style="width: 200px" />
          <NButton type="primary" @click="resetAndLoad">Найти</NButton>
        </NSpace>
      </div>

      <NSpin :show="loading">
        <NEmpty v-if="!items.length && !loading" description="Проектов не найдено" />
        <div v-else class="project-list">
          <ProjectCard
            v-for="p in items"
            :key="p.id"
            :project="p"
            @open="openProject"
          />
        </div>
      </NSpin>

      <NPagination
        v-if="total > pageSize"
        v-model:page="page"
        :page-size="pageSize"
        :item-count="total"
        class="pager"
      />
    </div>
  </div>
</template>

<style scoped>
.board {
  background: #f5f5f5;
  min-height: calc(100vh - 120px);
}
.board-inner {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}
.board-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  gap: 16px;
}
.filters {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}
.project-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.pager {
  margin-top: 24px;
  justify-content: center;
}
</style>
