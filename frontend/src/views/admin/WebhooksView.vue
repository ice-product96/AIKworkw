<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { NDataTable } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import api from '../../api/client'

const events = ref<Record<string, unknown>[]>([])

const columns: DataTableColumns = [
  { title: 'Агент', key: 'agent_id' },
  { title: 'Событие', key: 'event_type' },
  { title: 'Статус', key: 'status' },
  { title: 'Попытки', key: 'attempts' },
  { title: 'Ошибка', key: 'last_error' },
]

onMounted(async () => {
  const { data } = await api.get('/admin/webhooks')
  events.value = data
})
</script>

<template>
  <h2>Журнал вебхуков</h2>
  <NDataTable :columns="columns" :data="events" />
</template>
