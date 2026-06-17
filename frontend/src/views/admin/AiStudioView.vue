<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  NCard, NForm, NFormItem, NInput, NButton, NSpace, NAlert, NInputNumber, NSlider,
  useMessage, NSpin, NText,
} from 'naive-ui'
import api from '../../api/client'

const message = useMessage()
const loading = ref(false)
const testing = ref(false)
const generating = ref(false)

const settings = ref({
  base_url: 'https://api.deepseek.com',
  model: 'deepseek-chat',
  api_key_masked: '',
  configured: false,
})
const apiKey = ref('')
const activity = ref({
  num_clients: 3,
  num_developers: 2,
  num_agents: 5,
  num_orders: 8,
  complete_ratio: 0.4,
})
const landingTopic = ref('маркетплейс AI-агентов для бизнеса')
const blogTopic = ref('')
const blogTopics = ref('Как выбрать AI-агента для бизнеса\nSEO с помощью AI-агентов\nАвтоматизация заказов через маркетплейс')
const lastResult = ref<Record<string, unknown> | null>(null)

async function loadSettings() {
  loading.value = true
  try {
    const { data } = await api.get('/admin/ai/settings')
    settings.value = data
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  await api.patch('/admin/ai/settings', {
    api_key: apiKey.value || undefined,
    base_url: settings.value.base_url,
    model: settings.value.model,
  })
  apiKey.value = ''
  message.success('Настройки сохранены')
  await loadSettings()
}

async function testConnection() {
  testing.value = true
  try {
    const { data } = await api.post('/admin/ai/test')
    message.success(`DeepSeek ответил: ${data.reply}`)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || 'Ошибка подключения')
  } finally {
    testing.value = false
  }
}

async function generateActivity() {
  generating.value = true
  try {
    const { data } = await api.post('/admin/ai/generate-activity', activity.value)
    lastResult.value = data
    message.success('Демо-активность сгенерирована')
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    message.error(err.response?.data?.detail || 'Ошибка генерации')
  } finally {
    generating.value = false
  }
}

async function generateLanding() {
  generating.value = true
  try {
    const { data } = await api.post('/admin/ai/generate-landing', { topic: landingTopic.value })
    message.success(`Главная обновлена: ${data.title}`)
  } finally {
    generating.value = false
  }
}

async function generateBlog() {
  if (!blogTopic.value) return
  generating.value = true
  try {
    await api.post('/admin/ai/generate-blog', { topic: blogTopic.value, publish: true })
    message.success('Статья создана')
    blogTopic.value = ''
  } finally {
    generating.value = false
  }
}

async function generateBlogBatch() {
  const topics = blogTopics.value.split('\n').map((t) => t.trim()).filter(Boolean)
  if (!topics.length) return
  generating.value = true
  try {
    const { data } = await api.post('/admin/ai/generate-blog-batch', { topics, publish: true })
    message.success(`Создано статей: ${data.length}`)
  } finally {
    generating.value = false
  }
}

onMounted(loadSettings)
</script>

<template>
  <NSpin :show="loading">
    <NSpace vertical :size="16">
      <div>
        <h2 style="margin: 0">AI-студия (DeepSeek)</h2>
        <NText depth="3">Внутренний агент: генерация пользователей, заказов, ответов, контента</NText>
      </div>

      <NCard title="Подключение DeepSeek">
        <NForm label-placement="top">
          <NFormItem label="API Key">
            <NInput
              v-model:value="apiKey"
              type="password"
              :placeholder="settings.api_key_masked || 'sk-...'"
              show-password-on="click"
            />
          </NFormItem>
          <NFormItem label="Base URL">
            <NInput v-model:value="settings.base_url" />
          </NFormItem>
          <NFormItem label="Model">
            <NInput v-model:value="settings.model" />
          </NFormItem>
          <NSpace>
            <NButton type="primary" @click="saveSettings">Сохранить</NButton>
            <NButton :loading="testing" @click="testConnection">Проверить</NButton>
          </NSpace>
        </NForm>
        <NAlert v-if="!settings.configured" type="warning" style="margin-top: 12px">
          Без API-ключа используются шаблонные данные. Для качественной генерации укажите DeepSeek API Key.
        </NAlert>
      </NCard>

      <NCard title="Генерация активности площадки">
        <NSpace vertical>
          <NSpace wrap>
            <NFormItem label="Клиенты" label-placement="top">
              <NInputNumber v-model:value="activity.num_clients" :min="1" :max="20" />
            </NFormItem>
            <NFormItem label="Разработчики" label-placement="top">
              <NInputNumber v-model:value="activity.num_developers" :min="1" :max="10" />
            </NFormItem>
            <NFormItem label="Агенты" label-placement="top">
              <NInputNumber v-model:value="activity.num_agents" :min="1" :max="30" />
            </NFormItem>
            <NFormItem label="Заказы" label-placement="top">
              <NInputNumber v-model:value="activity.num_orders" :min="1" :max="30" />
            </NFormItem>
          </NSpace>
          <NFormItem label="Доля завершённых заказов">
            <NSlider v-model:value="activity.complete_ratio" :min="0" :max="1" :step="0.1" />
          </NFormItem>
          <NButton type="primary" :loading="generating" @click="generateActivity">
            Сгенерировать пользователей, агентов, заказы и ответы
          </NButton>
          <NAlert v-if="lastResult" type="success">
            Создано: {{ lastResult.users_created }} пользователей, {{ lastResult.agents_created }} агентов,
            {{ lastResult.orders_created }} заказов, {{ lastResult.messages_created }} сообщений.
            Пароль демо-пользователей: {{ lastResult.demo_password }}
          </NAlert>
        </NSpace>
      </NCard>

      <NCard title="SEO: главная страница">
        <NSpace vertical>
          <NInput v-model:value="landingTopic" placeholder="Тема для генерации" />
          <NButton :loading="generating" @click="generateLanding">Сгенерировать контент главной</NButton>
        </NSpace>
      </NCard>

      <NCard title="SEO: блог">
        <NSpace vertical>
          <NInput v-model:value="blogTopic" placeholder="Тема одной статьи" />
          <NButton :loading="generating" @click="generateBlog">Сгенерировать статью</NButton>
          <NInput v-model:value="blogTopics" type="textarea" :rows="4" placeholder="Темы по одной на строку" />
          <NButton :loading="generating" @click="generateBlogBatch">Сгенерировать пакет статей</NButton>
        </NSpace>
      </NCard>
    </NSpace>
  </NSpin>
</template>
