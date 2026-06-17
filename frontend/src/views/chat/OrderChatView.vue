<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NCard, NButton, NSpace, NInput, NAlert, NText, NEmpty } from 'naive-ui'
import api from '../../api/client'
import { useAuthStore } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const orderId = route.params.orderId as string
const messages = ref<Record<string, unknown>[]>([])
const newMessage = ref('')
const warning = ref('')
const orderTitle = ref('')
const chatBox = ref<HTMLElement | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

const canSend = () => auth.user?.role === 'client'

async function loadMessages() {
  const params: Record<string, string> = {}
  const { data } = await api.get(`/orders/${orderId}/messages`, { params })
  messages.value = data
  await nextTick()
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
}

async function loadOrder() {
  try {
    const { data } = await api.get(`/projects/${orderId}`)
    orderTitle.value = data.title
  } catch {
    orderTitle.value = `Заказ ${orderId.slice(0, 8)}`
  }
}

async function sendMessage() {
  if (!newMessage.value.trim()) return
  const { data } = await api.post(`/orders/${orderId}/messages`, { text: newMessage.value })
  if (data.warning) warning.value = data.warning
  newMessage.value = ''
  await loadMessages()
}

onMounted(async () => {
  await loadOrder()
  if (canSend()) {
    await loadMessages()
    pollTimer = setInterval(loadMessages, 5000)
  }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <NSpace vertical :size="16">
    <NSpace align="center">
      <NButton quaternary @click="router.push('/chat')">← К списку чатов</NButton>
      <NText strong>{{ orderTitle }}</NText>
    </NSpace>

    <NCard title="Переписка">
      <NAlert v-if="warning" type="warning" style="margin-bottom: 12px">{{ warning }}</NAlert>
      <NAlert v-if="!canSend()" type="info" style="margin-bottom: 12px">
        Отправка сообщений доступна клиенту владельца заказа. Агенты пишут через API.
      </NAlert>

      <div ref="chatBox" class="chat-box">
        <NEmpty v-if="!messages.length && canSend()" description="Нет сообщений" />
        <div v-for="msg in messages" :key="msg.id as string" class="chat-msg">
          <NText depth="3" style="font-size: 12px">{{ msg.sender_type }}</NText>
          <div>{{ msg.text }}</div>
        </div>
      </div>

      <NSpace v-if="canSend()" style="margin-top: 12px">
        <NInput
          v-model:value="newMessage"
          placeholder="Сообщение..."
          style="flex: 1"
          @keyup.enter="sendMessage"
        />
        <NButton type="primary" @click="sendMessage">Отправить</NButton>
      </NSpace>
    </NCard>
  </NSpace>
</template>

<style scoped>
.chat-box {
  max-height: 480px;
  overflow-y: auto;
  padding: 8px;
  background: #fafafa;
  border-radius: 8px;
}
.chat-msg {
  margin-bottom: 12px;
  padding: 8px 12px;
  background: white;
  border-radius: 8px;
}
</style>
