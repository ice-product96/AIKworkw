<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { NCard, NList, NListItem, NSpin, NText, NEmpty } from 'naive-ui'
import { setPageMeta } from '../../utils/content'

interface PostItem {
  slug: string
  title: string
  excerpt: string | null
  published_at: string | null
}

const router = useRouter()
const posts = ref<PostItem[]>([])
const loading = ref(true)

onMounted(async () => {
  setPageMeta('Блог AIKworkw — AI-агенты для бизнеса', 'Статьи о маркетплейсе AI-агентов, автоматизации и SEO.')
  const { data } = await axios.get('/api/v1/blog/posts')
  posts.value = data
  loading.value = false
})
</script>

<template>
  <div class="landing-section">
    <h1 style="margin-top: 0">Блог</h1>
    <NText depth="3">SEO-материалы о AI-агентах и автоматизации бизнес-задач</NText>
    <NSpin :show="loading" style="margin-top: 24px">
      <NEmpty v-if="!posts.length && !loading" description="Пока нет статей" />
      <NList v-else bordered>
        <NListItem
          v-for="post in posts"
          :key="post.slug"
          style="cursor: pointer"
          @click="router.push(`/blog/${post.slug}`)"
        >
          <NCard embedded :bordered="false">
            <h3 style="margin: 0 0 8px">{{ post.title }}</h3>
            <NText v-if="post.excerpt" depth="3">{{ post.excerpt }}</NText>
          </NCard>
        </NListItem>
      </NList>
    </NSpin>
  </div>
</template>
