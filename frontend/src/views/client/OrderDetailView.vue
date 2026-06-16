<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  NCard, NButton, NSpace, NTag, NInput, NAlert, NUpload, NList, NListItem, NText, NDivider,
} from 'naive-ui'
import type { UploadFileInfo } from 'naive-ui'
import api from '../../api/client'

const route = useRoute()
const orderId = route.params.id as string
const order = ref<Record<string, unknown> | null>(null)
const estimates = ref<Record<string, unknown>[]>([])
const messages = ref<Record<string, unknown>[]>([])
const newMessage = ref('')
const warning = ref('')
let pollTimer: ReturnType<typeof setInterval> | null = null

async function load() {
  const [o, e, m] = await Promise.all([
    api.get(`/orders/${orderId}`),
    api.get(`/orders/${orderId}/estimates`),
    api.get(`/orders/${orderId}/messages`),
  ])
  order.value = o.data
  estimates.value = e.data
  messages.value = m.data
}

async function selectEstimate(estimateId: string) {
  await api.post(`/orders/${orderId}/estimates/${estimateId}/select`)
  await load()
}

async function pay() {
  await api.post(`/orders/${orderId}/pay`)
  await load()
}

async function accept() {
  await api.post(`/orders/${orderId}/accept`)
  await load()
}

async function revision() {
  await api.post(`/orders/${orderId}/revision`, { message: newMessage.value })
  newMessage.value = ''
  await load()
}

async function dispute() {
  await api.post(`/orders/${orderId}/dispute`, { reason: newMessage.value })
  newMessage.value = ''
  await load()
}

async function sendMessage() {
  const { data } = await api.post(`/orders/${orderId}/messages`, { text: newMessage.value })
  if (data.warning) warning.value = data.warning
  newMessage.value = ''
  await load()
}

async function uploadFile({ file }: { file: UploadFileInfo }) {
  const form = new FormData()
  form.append('file', file.file as File)
  await api.post(`/orders/${orderId}/files`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  await load()
}

onMounted(() => {
  load()
  pollTimer = setInterval(() => {
    api.get(`/orders/${orderId}/messages`).then((r) => { messages.value = r.data })
  }, 5000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <NSpace v-if="order" vertical :size="16">
    <NCard :title="order.title as string">
      <NTag>{{ order.status }}</NTag>
      <p>{{ order.description }}</p>
      <p v-if="order.result_text"><strong>Результат:</strong> {{ order.result_text }}</p>
    </NCard>

    <NCard v-if="estimates.length" title="Оценки агентов">
      <NSpace vertical>
        <div v-for="est in estimates" :key="est.id as string" class="estimate-row">
          <NText>{{ est.price }} ₽ · {{ est.deadline_hours }}ч · {{ est.message }}</NText>
          <NButton
            v-if="est.status === 'submitted' && ['estimated', 'awaiting_estimate'].includes(order.status as string)"
            size="small"
            type="primary"
            @click="selectEstimate(est.id as string)"
          >
            Выбрать
          </NButton>
        </div>
      </NSpace>
    </NCard>

    <NButton v-if="order.status === 'awaiting_payment'" type="primary" @click="pay">Оплатить (заглушка)</NButton>
    <NButton v-if="order.status === 'submitted'" type="success" @click="accept">Принять работу</NButton>

    <NCard title="Чат">
      <NAlert v-if="warning" type="warning" style="margin-bottom: 12px">{{ warning }}</NAlert>
      <NList>
        <NListItem v-for="msg in messages" :key="msg.id as string">
          <NText depth="3">{{ msg.sender_type }}:</NText> {{ msg.text }}
        </NListItem>
      </NList>
      <NDivider />
      <NSpace>
        <NInput v-model:value="newMessage" placeholder="Сообщение..." style="flex: 1" />
        <NButton @click="sendMessage">Отправить</NButton>
        <NButton v-if="order.status === 'submitted'" @click="revision">Доработка</NButton>
        <NButton v-if="['submitted','in_progress'].includes(order.status as string)" type="error" @click="dispute">Спор</NButton>
      </NSpace>
    </NCard>

    <NCard title="Файлы">
      <NUpload :custom-request="uploadFile" :show-file-list="false">
        <NButton>Загрузить файл</NButton>
      </NUpload>
    </NCard>
  </NSpace>
</template>

<style scoped>
.estimate-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}
</style>
