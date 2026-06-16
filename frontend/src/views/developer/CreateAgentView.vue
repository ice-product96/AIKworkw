<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NForm, NFormItem, NInput, NButton } from 'naive-ui'
import api from '../../api/client'

const router = useRouter()
const name = ref('')
const description = ref('')
const webhookUrl = ref('')

async function submit() {
  const { data } = await api.post('/developer/agents', {
    name: name.value,
    description: description.value,
    webhook_url: webhookUrl.value || null,
  })
  router.push(`/dashboard/agents/${data.id}`)
}
</script>

<template>
  <NCard title="Создать агента">
    <NForm @submit.prevent="submit">
      <NFormItem label="Название">
        <NInput v-model:value="name" />
      </NFormItem>
      <NFormItem label="Описание">
        <NInput v-model:value="description" type="textarea" />
      </NFormItem>
      <NFormItem label="Webhook URL">
        <NInput v-model:value="webhookUrl" placeholder="https://..." />
      </NFormItem>
      <NButton type="primary" attr-type="submit">Создать</NButton>
    </NForm>
  </NCard>
</template>
