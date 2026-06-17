<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { NButton, NCard, NGrid, NGridItem, NSpace, NText, NSpin, NH1, NStatistic } from 'naive-ui'
import { setPageMeta } from '../../utils/content'

interface LandingContent {
  hero_title?: string
  hero_subtitle?: string
  hero_cta?: string
  features?: { title: string; text: string }[]
  stats?: { label: string; value: string }[]
  seo_block?: string
}

const router = useRouter()
const loading = ref(true)
const page = ref<{ title: string; content_json: LandingContent; meta_title?: string; meta_description?: string } | null>(null)

onMounted(async () => {
  try {
    const { data } = await axios.get('/api/v1/pages/home')
    page.value = data
    setPageMeta(data.meta_title || data.title, data.meta_description)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <NSpin :show="loading">
    <section v-if="page" class="landing-section hero">
      <NH1 style="font-size: 2.5rem; margin: 0 0 16px">{{ page.content_json.hero_title }}</NH1>
      <NText depth="2" style="font-size: 1.15rem; display: block; max-width: 720px; margin-bottom: 24px">
        {{ page.content_json.hero_subtitle }}
      </NText>
      <NSpace>
        <NButton type="primary" size="large" @click="router.push('/register')">
          {{ page.content_json.hero_cta || 'Начать' }}
        </NButton>
        <NButton size="large" @click="router.push('/blog')">Читать блог</NButton>
      </NSpace>
    </section>

    <section v-if="page?.content_json.stats?.length" class="landing-section stats">
      <NGrid :cols="3" :x-gap="16">
        <NGridItem v-for="(s, i) in page.content_json.stats" :key="i">
          <NStatistic :label="s.label" :value="s.value" />
        </NGridItem>
      </NGrid>
    </section>

    <section v-if="page?.content_json.features?.length" class="landing-section">
      <NGrid :cols="3" :x-gap="16" :y-gap="16">
        <NGridItem v-for="(f, i) in page.content_json.features" :key="i">
          <NCard :title="f.title">{{ f.text }}</NCard>
        </NGridItem>
      </NGrid>
    </section>

    <section v-if="page?.content_json.seo_block" class="landing-section seo">
      <NText style="line-height: 1.7; font-size: 1.05rem">{{ page.content_json.seo_block }}</NText>
    </section>
  </NSpin>
</template>

<style scoped>
.hero {
  padding-top: 72px;
  padding-bottom: 48px;
}
.stats {
  background: rgba(0, 0, 0, 0.02);
  border-radius: 12px;
  margin-bottom: 24px;
}
.seo {
  padding-bottom: 80px;
}
</style>
