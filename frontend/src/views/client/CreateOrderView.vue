<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NForm, NFormItem, NInput, NInputNumber, NSelect, NButton } from 'naive-ui'
import api from '../../api/client'

const router = useRouter()
const title = ref('')
const description = ref('')
const serviceType = ref('landing_page')
const budgetMin = ref<number | null>(10000)
const budgetMax = ref<number | null>(30000)

const serviceOptions = [
  { label: 'Лендинг', value: 'landing_page' },
  { label: 'SEO аудит', value: 'seo_audit' },
  { label: 'Python скрипт', value: 'python_script' },
  { label: 'Telegram бот', value: 'telegram_bot' },
  { label: 'Копирайтинг', value: 'copywriting' },
  { label: 'Баннер', value: 'design_banner' },
  { label: 'Обработка данных', value: 'data_processing' },
  { label: 'Анализ документов', value: 'document_analysis' },
]

async function submit() {
  const { data } = await api.post('/orders', {
    title: title.value,
    description: description.value,
    service_type: serviceType.value,
    budget_min: budgetMin.value,
    budget_max: budgetMax.value,
  })
  await api.post(`/orders/${data.id}/publish`)
  router.push(`/dashboard/orders/${data.id}`)
}
</script>

<template>
  <NCard title="Создать заказ">
    <NForm @submit.prevent="submit">
      <NFormItem label="Название">
        <NInput v-model:value="title" />
      </NFormItem>
      <NFormItem label="Описание">
        <NInput v-model:value="description" type="textarea" :rows="4" />
      </NFormItem>
      <NFormItem label="Тип услуги">
        <NSelect v-model:value="serviceType" :options="serviceOptions" />
      </NFormItem>
      <NFormItem label="Бюджет от">
        <NInputNumber v-model:value="budgetMin" style="width: 100%" />
      </NFormItem>
      <NFormItem label="Бюджет до">
        <NInputNumber v-model:value="budgetMax" style="width: 100%" />
      </NFormItem>
      <NButton type="primary" attr-type="submit">Создать и опубликовать</NButton>
    </NForm>
  </NCard>
</template>
