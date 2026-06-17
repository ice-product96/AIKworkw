<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NCard, NButton, NSpace, NTag, NText } from 'naive-ui'
import api from '../../api/client'
import { useAuthStore } from '../../stores/auth'
import { serviceLabel, statusLabel } from '../../constants/orders'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const orderId = route.params.id as string
const order = ref<Record<string, unknown> | null>(null)

onMounted(async () => {
  const { data } = await api.get(`/feed/orders/${orderId}`)
  order.value = data
})

const isOwner = () =>
  order.value &&
  auth.user?.role === 'client' &&
  String(order.value.client_id) === String(auth.user.id)
</script>

<template>
  <NSpace v-if="order" vertical :size="16">
    <NButton quaternary @click="router.push('/feed')">← К ленте</NButton>
    <NCard :title="order.title as string">
      <NSpace vertical>
        <NTag>{{ statusLabel(order.status as string) }}</NTag>
        <NText>{{ serviceLabel(order.service_type as string) }}</NText>
        <p>{{ order.description }}</p>
        <NText v-if="order.budget_min || order.budget_max" depth="3">
          Бюджет: {{ order.budget_min }} – {{ order.budget_max }} ₽
        </NText>
      </NSpace>
    </NCard>
    <NSpace>
      <NButton type="primary" @click="router.push(`/chat/${orderId}`)">Открыть чат</NButton>
      <NButton v-if="isOwner()" @click="router.push(`/cabinet/orders/${orderId}`)">Управление в кабинете</NButton>
    </NSpace>
  </NSpace>
</template>
