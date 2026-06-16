<script setup lang="ts">
import { h, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NDataTable, NTag, NSpace } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import api from '../../api/client'

interface Agent {
  id: string
  name: string
  status: string
  rating: number
}

const agents = ref<Agent[]>([])
const router = useRouter()

const columns: DataTableColumns<Agent> = [
  { title: 'Название', key: 'name' },
  { title: 'Статус', key: 'status', render: (r) => h(NTag, null, () => r.status) },
  { title: 'Рейтинг', key: 'rating' },
  {
    title: '',
    key: 'id',
    render: (r) => h(NButton, { size: 'small', onClick: () => router.push(`/dashboard/agents/${r.id}`) }, () => 'Открыть'),
  },
]

onMounted(async () => {
  const { data } = await api.get('/developer/agents')
  agents.value = data
})
</script>

<template>
  <NSpace vertical>
    <NSpace justify="space-between">
      <h2>Мои агенты</h2>
      <NButton type="primary" @click="router.push('/dashboard/agents/new')">Создать агента</NButton>
    </NSpace>
    <NDataTable :columns="columns" :data="agents" />
  </NSpace>
</template>
