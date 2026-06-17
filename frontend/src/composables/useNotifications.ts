import { onMounted, onUnmounted, ref } from 'vue'
import api from '../api/client'

const STORAGE_KEY = 'aikworkw_notifications_since'

interface NotificationEvent {
  type: string
  order_id: string
  title: string
  body: string
  created_at: string
}

export function useNotifications() {
  const permission = ref<NotificationPermission>(
    typeof Notification !== 'undefined' ? Notification.permission : 'denied',
  )
  let timer: ReturnType<typeof setInterval> | null = null

  async function requestPermission() {
    if (typeof Notification === 'undefined') return
    if (Notification.permission === 'default') {
      permission.value = await Notification.requestPermission()
    } else {
      permission.value = Notification.permission
    }
  }

  function showBrowserNotification(event: NotificationEvent) {
    if (typeof Notification === 'undefined' || Notification.permission !== 'granted') return
    const title = event.type === 'new_message' ? `Новое сообщение: ${event.title}` : event.title
    const n = new Notification(title, {
      body: event.body,
      tag: `${event.type}-${event.order_id}`,
    })
    n.onclick = () => {
      window.focus()
      window.location.href = `/chat/${event.order_id}`
    }
  }

  async function poll() {
    const since = localStorage.getItem(STORAGE_KEY) || new Date(Date.now() - 60000).toISOString()
    try {
      const { data } = await api.get('/notifications/poll', { params: { since } })
      localStorage.setItem(STORAGE_KEY, data.server_time)
      for (const event of data.events as NotificationEvent[]) {
        showBrowserNotification(event)
      }
    } catch {
      /* ignore poll errors */
    }
  }

  onMounted(() => {
    requestPermission()
    poll()
    timer = setInterval(poll, 30000)
  })

  onUnmounted(() => {
    if (timer) clearInterval(timer)
  })

  return { permission, requestPermission, poll }
}
