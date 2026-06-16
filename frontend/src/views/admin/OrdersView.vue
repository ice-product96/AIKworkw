<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { NDataTable } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import api from '../../api/client'

const orders = ref<Record<string, unknown>[]>([])

const columns: DataTableColumns = [
  { title: 'Название', key: 'title' },
  { title: 'Услуга', key: 'service_type' },
  { title: 'Статус', key: 'status' },
]

onMounted(async () => {
  const { data } = await api.get('/admin/orders')
  orders.value = data
})
</script>

<template>
  <h2>Заказы</h2>
  <NDataTable :columns="columns" :data="orders" />
</template>
