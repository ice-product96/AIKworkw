<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  NCard, NButton, NSpace, NSelect, NAlert, NStatistic, NGrid, NGi, NTag,
} from 'naive-ui'
import api from '../../api/client'

const route = useRoute()
const agentId = route.params.id as string
const agent = ref<Record<string, unknown> | null>(null)
const services = ref<Record<string, unknown>[]>([])
const stats = ref<Record<string, unknown> | null>(null)
const apiKey = ref('')
const showKey = ref(false)
const serviceType = ref('landing_page')

const serviceOptions = [
  { label: 'Лендинг', value: 'landing_page' },
  { label: 'SEO аудит', value: 'seo_audit' },
  { label: 'Python скрипт', value: 'python_script' },
  { label: 'Telegram бот', value: 'telegram_bot' },
  { label: 'Копирайтинг', value: 'copywriting' },
]

async function load() {
  const [a, s, st] = await Promise.all([
    api.get(`/developer/agents/${agentId}`),
    api.get(`/developer/agents/${agentId}/services`),
    api.get(`/developer/agents/${agentId}/stats`),
  ])
  agent.value = a.data
  services.value = s.data
  stats.value = st.data
}

async function generateKey() {
  const { data } = await api.post(`/developer/agents/${agentId}/api-key`)
  apiKey.value = data.api_key
  showKey.value = true
}

async function rotateKey() {
  const { data } = await api.post(`/developer/agents/${agentId}/rotate-api-key`)
  apiKey.value = data.api_key
  showKey.value = true
}

async function addService() {
  await api.post(`/developer/agents/${agentId}/services`, { service_type: serviceType.value })
  await load()
}

async function testAgent() {
  await api.post(`/developer/agents/${agentId}/test`)
  alert('Тестовая задача отправлена агенту')
}

onMounted(load)
</script>

<template>
  <NSpace v-if="agent" vertical :size="16">
    <NCard :title="agent.name as string">
      <p>{{ agent.description }}</p>
      <p>Webhook: {{ agent.webhook_url || '—' }}</p>
      <NTag>{{ agent.status }}</NTag>
    </NCard>

    <NGrid v-if="stats" :cols="4" :x-gap="12">
      <NGi><NStatistic label="Заказов" :value="stats.total_orders as number" /></NGi>
      <NGi><NStatistic label="Завершено" :value="stats.completed_orders as number" /></NGi>
      <NGi><NStatistic label="Доход" :value="`${stats.total_revenue} ₽`" /></NGi>
      <NGi><NStatistic label="Рейтинг" :value="stats.average_rating as number" /></NGi>
    </NGrid>

    <NCard title="API Key">
      <NSpace>
        <NButton @click="generateKey">Сгенерировать ключ</NButton>
        <NButton @click="rotateKey">Ротировать</NButton>
      </NSpace>
      <NAlert v-if="showKey" type="warning" style="margin-top: 12px">
        Сохраните ключ — он больше не будет показан: <code>{{ apiKey }}</code>
      </NAlert>
    </NCard>

    <NCard title="Услуги">
      <NSpace>
        <NSelect v-model:value="serviceType" :options="serviceOptions" style="width: 200px" />
        <NButton @click="addService">Добавить услугу</NButton>
      </NSpace>
      <ul>
        <li v-for="s in services" :key="s.id as string">{{ s.service_type }} ({{ s.is_active ? 'активна' : 'выкл' }})</li>
      </ul>
    </NCard>

    <NButton @click="testAgent">Тестовый заказ</NButton>
  </NSpace>
</template>
