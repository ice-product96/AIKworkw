import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/login', component: () => import('../views/LoginView.vue'), meta: { guest: true } },
    { path: '/register', component: () => import('../views/RegisterView.vue'), meta: { guest: true } },
    {
      path: '/dashboard',
      component: () => import('../layouts/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', component: () => import('../views/DashboardView.vue') },
        { path: 'orders', component: () => import('../views/client/OrdersView.vue'), meta: { role: 'client' } },
        { path: 'orders/new', component: () => import('../views/client/CreateOrderView.vue'), meta: { role: 'client' } },
        { path: 'orders/:id', component: () => import('../views/client/OrderDetailView.vue'), meta: { role: 'client' } },
        { path: 'agents', component: () => import('../views/developer/AgentsView.vue'), meta: { role: 'developer' } },
        { path: 'agents/new', component: () => import('../views/developer/CreateAgentView.vue'), meta: { role: 'developer' } },
        { path: 'agents/:id', component: () => import('../views/developer/AgentDetailView.vue'), meta: { role: 'developer' } },
        { path: 'admin/users', component: () => import('../views/admin/UsersView.vue'), meta: { role: 'admin' } },
        { path: 'admin/agents', component: () => import('../views/admin/AgentsView.vue'), meta: { role: 'admin' } },
        { path: 'admin/orders', component: () => import('../views/admin/OrdersView.vue'), meta: { role: 'admin' } },
        { path: 'admin/violations', component: () => import('../views/admin/ViolationsView.vue'), meta: { role: 'admin' } },
        { path: 'admin/webhooks', component: () => import('../views/admin/WebhooksView.vue'), meta: { role: 'admin' } },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.user) {
    const token = localStorage.getItem('access_token')
    if (token) {
      try {
        await auth.fetchMe()
      } catch {
        return '/login'
      }
    } else {
      return '/login'
    }
  }
  if (to.meta.guest && auth.user) {
    return '/dashboard'
  }
  if (to.meta.role && auth.user && auth.user.role !== to.meta.role) {
    return '/dashboard'
  }
})

export default router
