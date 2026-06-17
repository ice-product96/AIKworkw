<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { NButton, NCard, NTag, NSpace, NText, NSpin } from 'naive-ui'
import { formatBudget, timeAgo } from '../../constants/marketplace'
import { serviceLabel, statusLabel } from '../../constants/orders'
import { setPageMeta } from '../../utils/content'
import { useAuthStore } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const loading = ref(true)
const project = ref<Record<string, unknown> | null>(null)

onMounted(async () => {
  const id = route.params.id as string
  const { data } = await axios.get(`/api/v1/projects/${id}`)
  project.value = data
  setPageMeta(data.title as string, (data.description as string).slice(0, 160))
  loading.value = false
})

function respond() {
  if (auth.user) {
    router.push(auth.user.role === 'developer' ? '/cabinet/agents' : '/login?redirect=' + encodeURIComponent(route.fullPath))
  } else {
    router.push({ path: '/register', query: { role: 'developer' } })
  }
}
</script>

<template>
  <div class="detail-page">
    <NSpin :show="loading">
      <template v-if="project">
        <NButton quaternary @click="router.push('/projects')">← К бирже проектов</NButton>
        <NCard class="detail-card">
          <NSpace vertical :size="12">
            <h1 style="margin: 0">{{ project.title }}</h1>
            <NSpace>
              <NTag>{{ serviceLabel(project.service_type as string) }}</NTag>
              <NTag type="info">{{ statusLabel(project.status as string) }}</NTag>
              <NTag v-if="(project.proposals_count as number) > 0" type="warning">
                {{ project.proposals_count }} откликов
              </NTag>
            </NSpace>
            <NText strong>{{ formatBudget(project.budget_min as number, project.budget_max as number) }}</NText>
            <NText depth="3">Опубликован {{ timeAgo(project.created_at as string) }}</NText>
            <div class="description">{{ project.description }}</div>
          </NSpace>
        </NCard>
        <NSpace style="margin-top: 16px">
          <NButton v-if="!auth.user" type="primary" @click="router.push('/register')">Войти и откликнуться</NButton>
          <NButton v-else-if="auth.user.role === 'developer'" type="primary" @click="respond">Откликнуться (через агента)</NButton>
          <NButton v-else type="primary" @click="router.push(`/feed/orders/${project.id}`)">Открыть в ленте</NButton>
          <NButton @click="router.push('/projects')">Другие проекты</NButton>
        </NSpace>
      </template>
    </NSpin>
  </div>
</template>

<style scoped>
.detail-page {
  max-width: 760px;
  margin: 0 auto;
  padding: 24px;
}
.detail-card {
  margin-top: 12px;
}
.description {
  white-space: pre-wrap;
  line-height: 1.7;
  font-size: 15px;
}
</style>
