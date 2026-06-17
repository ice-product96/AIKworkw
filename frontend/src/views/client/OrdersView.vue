<script setup lang="ts">
import { h, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NDataTable, NTag, NSpace, NInput, NSelect, NCard } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import api from '../../api/client'
import { SERVICE_OPTIONS, STATUS_OPTIONS, serviceLabel, statusLabel } from '../../constants/orders'

interface Order {
  id: string
  title: string
  service_type: string
  status: string
  created_at: string
}

const orders = ref<Order[]>([])
const router = useRouter()
const q = ref('')
const status = ref<string | null>(null)
const serviceType = ref<string | null>(null)

const columns: DataTableColumns<Order> = [
  { title: 'Название', key: 'title' },
  {
    title: 'Услуга',
    key: 'service_type',
    render: (row) => serviceLabel(row.service_type),
  },
  {
    title: 'Статус',
    key: 'status',
    render: (row) => h(NTag, { type: 'info' }, () => statusLabel(row.status)),
  },
  {
    title: '',
    key: 'actions',
    render: (row) =>
      h(NButton, { size: 'small', onClick: () => router.push(`/cabinet/orders/${row.id}`) }, () => 'Открыть'),
  },
]

async function load() {
  const { data } = await api.get('/orders', {
    params: {
      q: q.value || undefined,
      status: status.value || undefined,
      service_type: serviceType.value || undefined,
    },
  })
  orders.value = data
}

onMounted(load)
</script>

<template>
  <NSpace vertical>
    <NSpace justify="space-between">
      <h2 style="margin: 0">Мои заказы</h2>
      <NButton type="primary" @click="router.push('/cabinet/orders/new')">Создать заказ</NButton>
    </NSpace>
    <NCard size="small">
      <NSpace wrap>
        <NInput v-model:value="q" placeholder="Поиск..." clearable style="width: 200px" @keyup.enter="load" />
        <NSelect
          v-model:value="status"
          :options="STATUS_OPTIONS"
          clearable
          placeholder="Статус"
          style="width: 160px"
        />
        <NSelect
          v-model:value="serviceType"
          :options="SERVICE_OPTIONS"
          clearable
          placeholder="Услуга"
          style="width: 160px"
        />
        <NButton @click="load">Фильтр</NButton>
      </NSpace>
    </NCard>
    <NDataTable :columns="columns" :data="orders" :bordered="false" />
  </NSpace>
</template>
