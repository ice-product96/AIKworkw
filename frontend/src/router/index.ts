import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('../views/LoginView.vue'), meta: { guest: true } },
    { path: '/register', component: () => import('../views/RegisterView.vue'), meta: { guest: true } },
    {
      path: '/',
      component: () => import('../layouts/MarketingLayout.vue'),
      children: [
        { path: '', component: () => import('../views/public/LandingView.vue') },
        { path: 'blog', component: () => import('../views/public/BlogListView.vue') },
        { path: 'blog/:slug', component: () => import('../views/public/BlogPostView.vue') },
        { path: 'projects', component: () => import('../views/public/ProjectsBoardView.vue'), meta: { projectsBase: '/projects' } },
        { path: 'projects/:id', component: () => import('../views/public/ProjectDetailView.vue') },
      ],
    },
    {
      path: '/',
      component: () => import('../layouts/ShellLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: 'feed', component: () => import('../views/feed/OrderFeedView.vue'), meta: { projectsBase: '/feed' } },
        { path: 'feed/orders/:id', component: () => import('../views/feed/FeedOrderDetailView.vue') },
        { path: 'chat', component: () => import('../views/chat/MessengerView.vue') },
        { path: 'chat/:orderId', component: () => import('../views/chat/MessengerView.vue') },
        {
          path: 'cabinet',
          component: () => import('../layouts/CabinetLayout.vue'),
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
            { path: 'admin/ai', component: () => import('../views/admin/AiStudioView.vue'), meta: { role: 'admin' } },
            { path: 'admin/content', component: () => import('../views/admin/ContentAdminView.vue'), meta: { role: 'admin' } },
          ],
        },
      ],
    },
    { path: '/dashboard', redirect: '/cabinet' },
    { path: '/dashboard/:pathMatch(.*)*', redirect: (to) => `/cabinet/${to.params.pathMatch}` },
    { path: '/admin', redirect: '/cabinet/admin/ai' },
    { path: '/admin/:pathMatch(.*)*', redirect: (to) => `/cabinet/admin/${to.params.pathMatch}` },
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
        return { path: '/login', query: { redirect: to.fullPath } }
      }
    } else {
      return { path: '/login', query: { redirect: to.fullPath } }
    }
  }
  if (to.meta.guest && auth.user) {
    return '/feed'
  }
  if (to.meta.role && auth.user && auth.user.role !== to.meta.role) {
    return '/feed'
  }
})

export default router
