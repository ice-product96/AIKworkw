<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard, NInput, NSelect, NButton, NSpace, NTag, NText, NPagination, NEmpty, NSpin,
} from 'naive-ui'
import api from '../../api/client'
import { SERVICE_OPTIONS, STATUS_OPTIONS, serviceLabel, statusLabel } from '../../constants/orders'

interface FeedOrder {
  id: string
  title: string
  description: string
  service_type: string
  status: string
  budget_min: number | null
  budget_max: number | null
  is_mine: boolean
  message_count: number
  last_message_preview: string | null
  created_at: string
}

const router = useRouter()
const items = ref<FeedOrder[]>([])
const total = ref(0)
const loading = ref(false)
const q = ref('')
const status = ref<string | null>(null)
const serviceType = ref<string | null>(null)
const sort = ref('created_at_desc')
const page = ref(1)
const pageSize = 10

const sortOptions = [
  { label: 'Сначала новые', value: 'created_at_desc' },
  { label: 'Сначала старые', value: 'created_at_asc' },
  { label: 'Недавно обновлённые', value: 'updated_at_desc' },
]

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/feed/orders', {
      params: {
        q: q.value || undefined,
        status: status.value || undefined,
        service_type: serviceType.value || undefined,
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

watch(page, load)

onMounted(load)
</script>

<template>
  <NSpace vertical :size="16">
    <div>
      <h2 style="margin: 0">Лента заказов</h2>
      <NText depth="3">Все опубликованные заказы на платформе</NText>
    </div>

    <NCard size="small">
      <NSpace wrap>
        <NInput v-model:value="q" placeholder="Поиск..." clearable style="width: 220px" @keyup.enter="resetAndLoad" />
        <NSelect
          v-model:value="status"
          :options="STATUS_OPTIONS"
          clearable
          placeholder="Статус"
          style="width: 180px"
        />
        <NSelect
          v-model:value="serviceType"
          :options="SERVICE_OPTIONS"
          clearable
          placeholder="Услуга"
          style="width: 180px"
        />
        <NSelect v-model:value="sort" :options="sortOptions" style="width: 200px" />
        <NButton type="primary" @click="resetAndLoad">Применить</NButton>
      </NSpace>
    </NCard>

    <NSpin :show="loading">
      <NEmpty v-if="!items.length && !loading" description="Заказов не найдено" />
      <NSpace v-else vertical :size="12">
        <NCard v-for="order in items" :key="order.id" hoverable @click="router.push(`/feed/orders/${order.id}`)">
          <NSpace justify="space-between" align="start">
            <NSpace vertical :size="4">
              <NSpace align="center">
                <NText strong>{{ order.title }}</NText>
                <NTag v-if="order.is_mine" type="success" size="small">Мой</NTag>
              </NSpace>
              <NText depth="3">{{ serviceLabel(order.service_type) }} · {{ statusLabel(order.status) }}</NText>
              <NText v-if="order.budget_min || order.budget_max" depth="3">
                Бюджет: {{ order.budget_min ?? '?' }} – {{ order.budget_max ?? '?' }} ₽
              </NText>
              <NText v-if="order.last_message_preview" depth="3" italic>
                💬 {{ order.last_message_preview }}
              </NText>
            </NSpace>
            <NSpace vertical align="end">
              <NTag size="small">{{ order.message_count }} сообщ.</NTag>
              <NButton size="small" @click.stop="router.push(`/chat/${order.id}`)">Чат</NButton>
            </NSpace>
          </NSpace>
        </NCard>
      </NSpace>
    </NSpin>

    <NPagination
      v-if="total > pageSize"
      v-model:page="page"
      :page-size="pageSize"
      :item-count="total"
      style="justify-content: center"
    />
  </NSpace>
</template>
