<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NCard, NButton, NSpace, NTag, NInput, NUpload, NText,
} from 'naive-ui'
import type { UploadFileInfo } from 'naive-ui'
import api from '../../api/client'
import { statusLabel } from '../../constants/orders'

const route = useRoute()
const router = useRouter()
const orderId = route.params.id as string
const order = ref<Record<string, unknown> | null>(null)
const estimates = ref<Record<string, unknown>[]>([])
const newMessage = ref('')

async function load() {
  const [o, e] = await Promise.all([
    api.get(`/orders/${orderId}`),
    api.get(`/orders/${orderId}/estimates`),
  ])
  order.value = o.data
  estimates.value = e.data
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

async function uploadFile({ file }: { file: UploadFileInfo }) {
  const form = new FormData()
  form.append('file', file.file as File)
  await api.post(`/orders/${orderId}/files`, form)
  await load()
}

onMounted(load)
</script>

<template>
  <NSpace v-if="order" vertical :size="16">
    <NCard :title="order.title as string">
      <NTag>{{ statusLabel(order.status as string) }}</NTag>
      <p>{{ order.description }}</p>
      <p v-if="order.result_text"><strong>Результат:</strong> {{ order.result_text }}</p>
      <NButton quaternary style="margin-top: 8px" @click="router.push(`/chat/${orderId}`)">
        Открыть чат →
      </NButton>
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

    <NCard v-if="['submitted', 'in_progress'].includes(order.status as string)" title="Действия">
      <NSpace vertical>
        <NInput v-model:value="newMessage" placeholder="Комментарий для доработки или спора..." />
        <NSpace>
          <NButton v-if="order.status === 'submitted'" @click="revision">Запросить доработку</NButton>
          <NButton type="error" @click="dispute">Открыть спор</NButton>
        </NSpace>
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
