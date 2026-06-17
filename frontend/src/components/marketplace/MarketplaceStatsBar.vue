<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import axios from 'axios'

const stats = ref({
  users_online: 0,
  last_order_seconds_ago: null as number | null,
  total_orders: 0,
  active_agents: 0,
})

let timer: ReturnType<typeof setInterval> | undefined

async function load() {
  try {
    const { data } = await axios.get('/api/v1/marketplace/stats')
    stats.value = data
  } catch {
    /* ignore */
  }
}

function lastOrderLabel(sec: number | null) {
  if (sec == null) return '—'
  if (sec < 60) return `${sec} сек. назад`
  return `${Math.floor(sec / 60)} мин. назад`
}

onMounted(() => {
  load()
  timer = setInterval(load, 60000)
})
onUnmounted(() => timer && clearInterval(timer))
</script>

<template>
  <div class="stats-bar">
    <span>Пользователей онлайн: <strong>{{ stats.users_online }}</strong></span>
    <span class="dot">·</span>
    <span>Последний заказ: <strong>{{ lastOrderLabel(stats.last_order_seconds_ago) }}</strong></span>
    <span class="dot">·</span>
    <span>Проектов: <strong>{{ stats.total_orders }}</strong></span>
    <span class="dot">·</span>
    <span>AI-агентов: <strong>{{ stats.active_agents }}</strong></span>
  </div>
</template>

<style scoped>
.stats-bar {
  background: #f0f7f0;
  color: #2d6a2d;
  font-size: 13px;
  padding: 8px 24px;
  text-align: center;
  border-bottom: 1px solid #dce8dc;
}
.dot {
  margin: 0 10px;
  opacity: 0.5;
}
</style>
