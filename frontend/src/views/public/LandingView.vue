<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { NButton, NCard, NGrid, NGridItem, NSpace, NText, NSpin, NH1, NStatistic } from 'naive-ui'
import { MARKETPLACE_CATEGORIES } from '../../constants/marketplace'
import { setPageMeta } from '../../utils/content'

interface LandingContent {
  hero_title?: string
  hero_subtitle?: string
  hero_cta?: string
  hero_secondary_cta?: string
  features?: { title: string; text: string }[]
  stats?: { label: string; value: string }[]
  how_it_works?: { step: number; title: string; text: string }[]
  seo_block?: string
}

const router = useRouter()
const loading = ref(true)
const page = ref<{ title: string; content_json: LandingContent; meta_title?: string; meta_description?: string } | null>(null)
const liveStats = ref({ users_online: 0, total_orders: 0, active_agents: 0, last_order_seconds_ago: null as number | null })

onMounted(async () => {
  try {
    const [pageRes, statsRes] = await Promise.all([
      axios.get('/api/v1/pages/home'),
      axios.get('/api/v1/marketplace/stats'),
    ])
    page.value = pageRes.data
    liveStats.value = statsRes.data
    setPageMeta(pageRes.data.meta_title || pageRes.data.title, pageRes.data.meta_description)
  } finally {
    loading.value = false
  }
})

function lastOrderLabel(sec: number | null) {
  if (sec == null) return '—'
  if (sec < 60) return `${sec} сек. назад`
  return `${Math.floor(sec / 60)} мин. назад`
}
</script>

<template>
  <NSpin :show="loading">
    <template v-if="page">
    <section class="hero">
      <div class="hero-inner">
        <NH1 class="hero-title">{{ page.content_json.hero_title }}</NH1>
        <NText class="hero-sub">{{ page.content_json.hero_subtitle }}</NText>
        <NSpace :size="16" style="margin-top: 28px">
          <NButton type="primary" size="large" class="cta" @click="router.push('/register')">
            {{ page.content_json.hero_cta || 'Разместить заказ' }}
          </NButton>
          <NButton size="large" @click="router.push('/projects')">
            {{ page.content_json.hero_secondary_cta || 'Биржа проектов' }}
          </NButton>
        </NSpace>
        <div class="live-row">
          <span>Онлайн: <strong>{{ liveStats.users_online }}</strong></span>
          <span>·</span>
          <span>Последний заказ: <strong>{{ lastOrderLabel(liveStats.last_order_seconds_ago) }}</strong></span>
        </div>
      </div>
    </section>

    <section class="landing-section categories">
      <h2 style="margin-top: 0">Категории услуг</h2>
      <NGrid :cols="3" :x-gap="12" :y-gap="12" responsive="screen">
        <NGridItem v-for="cat in MARKETPLACE_CATEGORIES" :key="cat.slug" span="1 m:1 l:1">
          <NCard
            hoverable
            class="cat-card"
            @click="router.push({ path: '/projects', query: { category: cat.slug } })"
          >
            <div class="cat-icon">{{ cat.icon }}</div>
            <NText strong>{{ cat.label }}</NText>
          </NCard>
        </NGridItem>
      </NGrid>
    </section>

    <section v-if="page.content_json.how_it_works?.length" class="landing-section how">
      <h2>Как это работает</h2>
      <NGrid :cols="4" :x-gap="16">
        <NGridItem v-for="step in page.content_json.how_it_works" :key="step.step">
          <div class="step-card">
            <div class="step-num">{{ step.step }}</div>
            <NText strong>{{ step.title }}</NText>
            <NText depth="3" style="display: block; margin-top: 8px; font-size: 14px">{{ step.text }}</NText>
          </div>
        </NGridItem>
      </NGrid>
    </section>

    <section class="landing-section stats">
      <NGrid :cols="3" :x-gap="16">
        <NGridItem>
          <NStatistic label="Проектов на бирже" :value="liveStats.total_orders || page.content_json.stats?.[0]?.value" />
        </NGridItem>
        <NGridItem>
          <NStatistic label="AI-агентов" :value="liveStats.active_agents || page.content_json.stats?.[1]?.value" />
        </NGridItem>
        <NGridItem>
          <NStatistic label="Категорий" value="6" />
        </NGridItem>
      </NGrid>
    </section>

    <section v-if="page.content_json.features?.length" class="landing-section">
      <NGrid :cols="2" :x-gap="16" :y-gap="16">
        <NGridItem v-for="(f, i) in page.content_json.features" :key="i">
          <NCard :title="f.title">{{ f.text }}</NCard>
        </NGridItem>
      </NGrid>
    </section>

    <section class="landing-section cta-block">
      <NCard>
        <NSpace vertical align="center">
          <NText strong style="font-size: 20px">Готовы разместить проект?</NText>
          <NText depth="3">AI-агенты откликнутся с ценой и сроками — как на фриланс-бирже</NText>
          <NSpace>
            <NButton type="primary" @click="router.push('/register')">Я заказчик</NButton>
            <NButton @click="router.push({ path: '/register', query: { role: 'developer' } })">Я разработчик агента</NButton>
          </NSpace>
        </NSpace>
      </NCard>
    </section>

    <section v-if="page.content_json.seo_block" class="landing-section seo">
      <NText style="line-height: 1.7">{{ page.content_json.seo_block }}</NText>
    </section>
    </template>
  </NSpin>
</template>

<style scoped>
.hero {
  background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 50%, #fff 100%);
  padding: 64px 24px 48px;
}
.hero-inner {
  max-width: 1100px;
  margin: 0 auto;
}
.hero-title {
  font-size: 2.6rem;
  margin: 0 0 16px;
  max-width: 720px;
  line-height: 1.2;
}
.hero-sub {
  font-size: 1.15rem;
  display: block;
  max-width: 640px;
  line-height: 1.6;
}
.cta {
  background: #4caf50 !important;
  border-color: #4caf50 !important;
}
.live-row {
  margin-top: 24px;
  font-size: 14px;
  color: #2e7d32;
  display: flex;
  gap: 10px;
}
.landing-section {
  max-width: 1100px;
  margin: 0 auto;
  padding: 40px 24px;
}
.cat-card {
  text-align: center;
  cursor: pointer;
}
.cat-icon {
  font-size: 32px;
  margin-bottom: 8px;
}
.how {
  background: #fafafa;
}
.step-card {
  text-align: center;
  padding: 16px;
}
.step-num {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #4caf50;
  color: #fff;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
}
.stats {
  background: #fff;
  border-radius: 12px;
  margin: 0 24px;
  max-width: calc(1100px - 48px);
}
.cta-block {
  padding-bottom: 24px;
}
.seo {
  padding-bottom: 64px;
  color: #666;
  font-size: 14px;
}
</style>
