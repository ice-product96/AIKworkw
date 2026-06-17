<script setup lang="ts">
import { computed } from 'vue'
import { NText } from 'naive-ui'
import { useAuthStore } from '../../stores/auth'

export interface ChatMessage {
  id: string
  sender_type: string
  sender_id: string
  text: string
  created_at: string
}

const props = defineProps<{
  message: ChatMessage
}>()

const auth = useAuthStore()

const isMine = computed(() => {
  const role = auth.user?.role
  const st = props.message.sender_type
  if (role === 'client' && st === 'client' && props.message.sender_id === auth.user?.id) return true
  if (role === 'developer' && st === 'developer' && props.message.sender_id === auth.user?.id) return true
  if (role === 'admin' && st === 'admin') return true
  return false
})

const senderLabel = computed(() => {
  const labels: Record<string, string> = {
    client: 'Клиент',
    developer: 'Разработчик',
    agent: 'AI-агент',
    admin: 'Админ',
    system: 'Система',
  }
  return labels[props.message.sender_type] || props.message.sender_type
})

const bubbleClass = computed(() => {
  if (isMine.value) return 'mine'
  if (props.message.sender_type === 'agent') return 'agent'
  if (props.message.sender_type === 'system') return 'system'
  return 'other'
})

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="bubble-row" :class="{ mine: isMine }">
    <div class="bubble" :class="bubbleClass">
      <NText v-if="!isMine" class="sender" depth="3">{{ senderLabel }}</NText>
      <div class="text">{{ message.text }}</div>
      <NText class="time" depth="3">{{ formatTime(message.created_at) }}</NText>
    </div>
  </div>
</template>

<style scoped>
.bubble-row {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 8px;
  animation: msg-in 0.28s ease-out;
}
.bubble-row.mine {
  justify-content: flex-end;
}
.bubble {
  max-width: 72%;
  padding: 10px 14px;
  border-radius: 16px;
  border-bottom-left-radius: 4px;
  background: #fff;
  border: 1px solid #e8e8e8;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}
.bubble.mine {
  background: linear-gradient(135deg, #4caf50, #43a047);
  color: #fff;
  border: none;
  border-bottom-left-radius: 16px;
  border-bottom-right-radius: 4px;
}
.bubble.agent {
  background: #e3f2fd;
  border-color: #bbdefb;
}
.bubble.system {
  background: #fff8e1;
  border-color: #ffe082;
  max-width: 90%;
  text-align: center;
  margin: 0 auto;
}
.bubble.mine .sender,
.bubble.mine .time {
  color: rgba(255, 255, 255, 0.85) !important;
}
.sender {
  display: block;
  font-size: 11px;
  font-weight: 600;
  margin-bottom: 4px;
}
.text {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.45;
  font-size: 14px;
}
.time {
  display: block;
  font-size: 10px;
  margin-top: 6px;
  text-align: right;
}
@keyframes msg-in {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>
