<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NList, NListItem, NText, NEmpty, NSpin, NTag, NButton, NSpace } from 'naive-ui'
import api from '../../api/client'
import { statusLabel } from '../../constants/orders'

interface ChatOrder {
  order_id: string
  title: string
  status: string
  last_message_preview: string | null
  last_message_at: string | null
  last_sender_type: string | null
}

const router = useRouter()
const orders = ref<ChatOrder[]>([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await api.get('/chat/orders')
    orders.value = data
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <NSpace vertical :size="16">
    <div>
      <h2 style="margin: 0">Чат</h2>
      <NText depth="3">Переписка по заказам</NText>
    </div>
    <NSpin :show="loading">
      <NEmpty v-if="!orders.length && !loading" description="Нет активных чатов" />
      <NList v-else bordered>
        <NListItem
          v-for="item in orders"
          :key="item.order_id"
          style="cursor: pointer"
          @click="router.push(`/chat/${item.order_id}`)"
        >
          <NSpace justify="space-between" align="center" style="width: 100%">
            <NSpace vertical :size="2">
              <NText strong>{{ item.title }}</NText>
              <NText v-if="item.last_message_preview" depth="3">{{ item.last_message_preview }}</NText>
              <NText v-else depth="3">Нет сообщений — начните диалог</NText>
            </NSpace>
            <NSpace vertical align="end">
              <NTag size="small">{{ statusLabel(item.status) }}</NTag>
              <NButton size="tiny" quaternary>Открыть</NButton>
            </NSpace>
          </NSpace>
        </NListItem>
      </NList>
    </NSpin>
  </NSpace>
</template>
