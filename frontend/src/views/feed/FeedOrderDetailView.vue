<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NSpace, NTag } from 'naive-ui'
import api from '../../api/client'
import { useAuthStore } from '../../stores/auth'
import { serviceLabel, statusLabel } from '../../constants/orders'
import { formatBudget } from '../../constants/marketplace'
import BuyerBlock from '../../components/marketplace/BuyerBlock.vue'
import type { ClientPublicInfo } from '../../types/profile'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const orderId = route.params.id as string
const order = ref<Record<string, unknown> | null>(null)
const client = ref<ClientPublicInfo | null>(null)

onMounted(async () => {
  const { data } = await api.get(`/feed/orders/${orderId}`)
  order.value = data
  client.value = data.client as ClientPublicInfo | null
})

const isOwner = () =>
  order.value &&
  auth.user?.role === 'client' &&
  String(order.value.client_id) === String(auth.user.id)
</script>

<template>
  <NSpace v-if="order" vertical :size="16">
    <NButton quaternary @click="router.push('/feed')">← К бирже</NButton>
    <div class="detail-card">
      <div class="detail-top">
        <h1>{{ order.title }}</h1>
        <div class="budget">
          <div class="budget-main">Желаемый бюджет: {{ formatBudget(order.budget_min as number, order.budget_max as number) }}</div>
        </div>
      </div>
      <NSpace style="margin: 12px 0">
        <NTag>{{ serviceLabel(order.service_type as string) }}</NTag>
        <NTag type="info">{{ statusLabel(order.status as string) }}</NTag>
        <NTag type="warning">{{ order.proposals_count }} откликов</NTag>
      </NSpace>
      <p class="description">{{ order.description }}</p>
      <BuyerBlock v-if="client" :client="client" />
    </div>
    <NSpace>
      <NButton type="primary" @click="router.push(`/chat/${orderId}`)">Открыть чат</NButton>
      <NButton v-if="isOwner()" @click="router.push(`/cabinet/orders/${orderId}`)">Управление в кабинете</NButton>
    </NSpace>
  </NSpace>
</template>

<style scoped>
.detail-card {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 20px;
}
.detail-top {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}
h1 {
  margin: 0;
  color: #2e7d32;
  font-size: 22px;
}
.budget-main {
  font-weight: 700;
  color: #2e7d32;
  white-space: nowrap;
}
.description {
  white-space: pre-wrap;
  line-height: 1.65;
  color: #444;
}
</style>
