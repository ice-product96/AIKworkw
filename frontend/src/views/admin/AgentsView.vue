<script setup lang="ts">
import { h, onMounted, ref } from 'vue'
import { NDataTable, NButton } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import api from '../../api/client'

const agents = ref<Record<string, unknown>[]>([])

const columns: DataTableColumns = [
  { title: 'Название', key: 'name' },
  { title: 'Статус', key: 'status' },
  {
    title: '',
    key: 'id',
    render: (row) =>
      h(NButton, { size: 'small', type: 'error', onClick: () => api.patch(`/admin/agents/${row.id}/block`) }, () => 'Блок'),
  },
]

onMounted(async () => {
  const { data } = await api.get('/admin/agents')
  agents.value = data
})
</script>

<template>
  <h2>Агенты</h2>
  <NDataTable :columns="columns" :data="agents" />
</template>
