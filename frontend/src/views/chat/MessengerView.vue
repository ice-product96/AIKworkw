<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NInput, NButton, NSpin, NEmpty, NText, NAlert } from 'naive-ui'
import api from '../../api/client'
import { useAuthStore } from '../../stores/auth'
import ChatBubble, { type ChatMessage } from '../../components/chat/ChatBubble.vue'
import { statusLabel, serviceLabel } from '../../constants/orders'
import { timeAgo } from '../../constants/marketplace'

interface ChatOrder {
  order_id: string
  title: string
  status: string
  service_type?: string
  is_mine?: boolean
  message_count?: number
  last_message_preview: string | null
  last_message_at: string | null
  last_sender_type: string | null
}

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const orders = ref<ChatOrder[]>([])
const messages = ref<ChatMessage[]>([])
const activeOrderId = ref<string | null>(null)
const orderTitle = ref('')
const orderStatus = ref('')
const orderService = ref('')
const search = ref('')
const draft = ref('')
const warning = ref('')
const loadingList = ref(false)
const loadingChat = ref(false)
const sending = ref(false)
const messagesEl = ref<HTMLElement | null>(null)

let listPoll: ReturnType<typeof setInterval> | null = null
let msgPoll: ReturnType<typeof setInterval> | null = null

const isDeveloper = computed(() => auth.user?.role === 'developer')
const isClient = computed(() => auth.user?.role === 'client')
const canSend = computed(() => isClient.value || isDeveloper.value || auth.user?.role === 'admin')
const showMobileChat = computed(() => !!activeOrderId.value)

const listHint = computed(() => {
  if (isClient.value) return 'Ваши заказы — переписка только по своим проектам'
  if (isDeveloper.value) return 'Все заказы на бирже — пишите от себя или через AI-агента'
  return 'Чаты по заказам'
})

async function loadOrders() {
  loadingList.value = orders.value.length === 0
  try {
    const { data } = await api.get('/chat/orders', { params: { q: search.value || undefined } })
    orders.value = data
  } finally {
    loadingList.value = false
  }
}

async function scrollToBottom(smooth = true) {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTo({ top: messagesEl.value.scrollHeight, behavior: smooth ? 'smooth' : 'auto' })
  }
}

async function loadMessages(full = false) {
  if (!activeOrderId.value) return
  const params: Record<string, string> = {}
  if (!full && messages.value.length) {
    params.since = messages.value[messages.value.length - 1].created_at
  }
  const { data } = await api.get(`/chat/orders/${activeOrderId.value}/messages`, { params })
  if (full || !params.since) {
    messages.value = data
    await scrollToBottom(false)
  } else if (data.length) {
    messages.value.push(...data)
    await scrollToBottom()
  }
}

async function openChat(orderId: string) {
  if (activeOrderId.value === orderId && messages.value.length) return
  activeOrderId.value = orderId
  router.replace({ path: `/chat/${orderId}` })
  loadingChat.value = true
  messages.value = []
  warning.value = ''
  try {
    const { data: meta } = await api.get(`/chat/orders/${orderId}`)
    orderTitle.value = meta.title
    orderStatus.value = meta.status
    orderService.value = meta.service_type
    await loadMessages(true)
  } finally {
    loadingChat.value = false
  }
  startMsgPoll()
}

function closeMobileChat() {
  activeOrderId.value = null
  router.push('/chat')
  stopMsgPoll()
}

async function sendMessage() {
  const text = draft.value.trim()
  if (!text || !activeOrderId.value || sending.value) return
  sending.value = true
  try {
    const { data } = await api.post(`/chat/orders/${activeOrderId.value}/messages`, { text })
    if (data.warning) warning.value = data.warning
    draft.value = ''
    messages.value.push(data)
    await scrollToBottom()
    loadOrders()
  } finally {
    sending.value = false
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function startMsgPoll() {
  stopMsgPoll()
  msgPoll = setInterval(() => loadMessages(false), 3000)
}

function stopMsgPoll() {
  if (msgPoll) {
    clearInterval(msgPoll)
    msgPoll = null
  }
}

let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(search, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(loadOrders, 300)
})

watch(
  () => route.params.orderId,
  (id) => {
    if (typeof id === 'string' && id !== activeOrderId.value) openChat(id)
  },
)

onMounted(async () => {
  await loadOrders()
  listPoll = setInterval(loadOrders, 15000)
  const id = route.params.orderId as string | undefined
  if (id) await openChat(id)
  else if (isClient.value && orders.value.length === 1) await openChat(orders.value[0].order_id)
})

onUnmounted(() => {
  if (listPoll) clearInterval(listPoll)
  stopMsgPoll()
})
</script>

<template>
  <div class="messenger">
    <aside class="sidebar" :class="{ hidden: showMobileChat }">
      <div class="sidebar-head">
        <h2 style="margin: 0">Чаты</h2>
        <NText depth="3" style="font-size: 12px">{{ listHint }}</NText>
        <NInput v-model:value="search" placeholder="Поиск заказа..." clearable size="small" style="margin-top: 10px" />
      </div>
      <NSpin :show="loadingList && !orders.length" class="sidebar-list">
        <NEmpty v-if="!orders.length && !loadingList" :description="isClient ? 'Нет заказов' : 'Нет проектов'" />
        <button
          v-for="item in orders"
          :key="item.order_id"
          type="button"
          class="chat-item"
          :class="{ active: activeOrderId === item.order_id }"
          @click="openChat(item.order_id)"
        >
          <div class="chat-item-top">
            <span class="chat-item-title">{{ item.title }}</span>
            <span v-if="item.last_message_at" class="chat-item-time">{{ timeAgo(item.last_message_at) }}</span>
          </div>
          <div class="chat-item-preview">
            {{ item.last_message_preview || 'Начните переписку…' }}
          </div>
          <div class="chat-item-meta">
            <span class="pill">{{ statusLabel(item.status) }}</span>
            <span v-if="item.message_count" class="pill muted">{{ item.message_count }} сообщ.</span>
          </div>
        </button>
      </NSpin>
    </aside>

    <main class="chat-main" :class="{ visible: showMobileChat || activeOrderId }">
      <template v-if="activeOrderId">
        <header class="chat-header">
          <NButton class="back-btn" quaternary size="small" @click="closeMobileChat">←</NButton>
          <div class="chat-header-info">
            <NText strong>{{ orderTitle }}</NText>
            <NText depth="3" style="font-size: 12px">
              {{ serviceLabel(orderService) }} · {{ statusLabel(orderStatus) }}
            </NText>
          </div>
          <NButton quaternary size="small" @click="router.push(`/projects/${activeOrderId}`)">Заказ</NButton>
        </header>

        <NAlert v-if="warning" type="warning" closable style="margin: 8px 12px 0" @close="warning = ''">
          {{ warning }}
        </NAlert>

        <NSpin :show="loadingChat" class="messages-wrap">
          <div ref="messagesEl" class="messages">
            <NEmpty v-if="!messages.length && !loadingChat" description="Напишите первое сообщение" />
            <ChatBubble v-for="msg in messages" :key="msg.id" :message="msg" />
          </div>
        </NSpin>

        <footer v-if="canSend" class="composer">
          <textarea
            v-model="draft"
            class="composer-input"
            placeholder="Сообщение… Enter — отправить, Shift+Enter — новая строка"
            rows="1"
            @keydown="onKeydown"
          />
          <NButton type="primary" class="send-btn" :loading="sending" :disabled="!draft.trim()" @click="sendMessage">
            ➤
          </NButton>
        </footer>
        <div v-else class="composer disabled">Отправка недоступна для вашей роли</div>
      </template>

      <div v-else class="chat-placeholder">
        <div class="placeholder-inner">
          <div class="placeholder-icon">💬</div>
          <NText strong style="font-size: 18px">Выберите чат</NText>
          <NText depth="3">{{ listHint }}</NText>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.messenger {
  display: flex;
  height: calc(100vh - 120px);
  margin: -24px;
  background: #eceff1;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #dde1e4;
}
.sidebar {
  width: 320px;
  min-width: 280px;
  background: #fff;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
}
.sidebar-head {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}
.sidebar-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.chat-item {
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  border-radius: 10px;
  padding: 12px;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s;
  margin-bottom: 4px;
}
.chat-item:hover {
  background: #f5f5f5;
}
.chat-item.active {
  background: #e8f5e9;
  transform: scale(1.01);
}
.chat-item-top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}
.chat-item-title {
  font-weight: 600;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.chat-item-time {
  font-size: 11px;
  color: #999;
  flex-shrink: 0;
}
.chat-item-preview {
  font-size: 13px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 6px;
}
.chat-item-meta {
  display: flex;
  gap: 6px;
}
.pill {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 10px;
  background: #e8f5e9;
  color: #2e7d32;
}
.pill.muted {
  background: #f0f0f0;
  color: #666;
}
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #eceff1;
}
.chat-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
}
.back-btn {
  display: none;
}
.chat-header-info {
  flex: 1;
  min-width: 0;
}
.messages-wrap {
  flex: 1;
  min-height: 0;
}
.messages {
  height: 100%;
  overflow-y: auto;
  padding: 16px;
  scroll-behavior: smooth;
}
.composer {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 12px 16px;
  background: #fff;
  border-top: 1px solid #e0e0e0;
}
.composer.disabled {
  padding: 12px 16px;
  text-align: center;
  color: #999;
  font-size: 13px;
  background: #fafafa;
}
.composer-input {
  flex: 1;
  resize: none;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  padding: 10px 16px;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.4;
  max-height: 120px;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.composer-input:focus {
  border-color: #4caf50;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.15);
}
.send-btn {
  width: 44px;
  height: 44px;
  border-radius: 50% !important;
  background: #4caf50 !important;
  border-color: #4caf50 !important;
  font-size: 18px;
}
.chat-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.placeholder-inner {
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
}
.placeholder-icon {
  font-size: 48px;
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.08); opacity: 1; }
}
@media (max-width: 768px) {
  .messenger {
    margin: -24px -16px;
    height: calc(100vh - 100px);
  }
  .sidebar.hidden {
    display: none;
  }
  .chat-main:not(.visible) {
    display: none;
  }
  .back-btn {
    display: inline-flex;
  }
}
</style>
