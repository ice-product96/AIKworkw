<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { NDataTable } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import api from '../../api/client'

const violations = ref<Record<string, unknown>[]>([])

const columns: DataTableColumns = [
  { title: 'Заказ', key: 'order_id' },
  { title: 'Отправитель', key: 'sender_type' },
  { title: 'Причина', key: 'reason' },
  { title: 'Дата', key: 'created_at' },
]

onMounted(async () => {
  const { data } = await api.get('/admin/violations')
  violations.value = data
})
</script>

<template>
  <h2>Нарушения модерации</h2>
  <NDataTable :columns="columns" :data="violations" />
</template>
