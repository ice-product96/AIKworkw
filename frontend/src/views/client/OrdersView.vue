<script setup lang="ts">
import { h, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NDataTable, NTag, NSpace } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import api from '../../api/client'

interface Order {
  id: string
  title: string
  service_type: string
  status: string
  created_at: string
}

const orders = ref<Order[]>([])
const router = useRouter()

const columns: DataTableColumns<Order> = [
  { title: 'Название', key: 'title' },
  { title: 'Услуга', key: 'service_type' },
  {
    title: 'Статус',
    key: 'status',
    render: (row) => h(NTag, { type: 'info' }, () => row.status),
  },
  {
    title: '',
    key: 'actions',
    render: (row) =>
      h(NButton, { size: 'small', onClick: () => router.push(`/dashboard/orders/${row.id}`) }, () => 'Открыть'),
  },
]
onMounted(async () => {
  const { data } = await api.get('/orders')
  orders.value = data
})
</script>

<template>
  <NSpace vertical>
    <NSpace justify="space-between">
      <h2>Мои заказы</h2>
      <NButton type="primary" @click="router.push('/dashboard/orders/new')">Создать заказ</NButton>
    </NSpace>
    <NDataTable :columns="columns" :data="orders" :bordered="false" />
  </NSpace>
</template>
