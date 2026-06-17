<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { NButton, NSpin } from 'naive-ui'
import { renderMarkdown, setPageMeta } from '../../utils/content'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const html = ref('')
const title = ref('')

onMounted(async () => {
  const slug = route.params.slug as string
  const { data } = await axios.get(`/api/v1/blog/posts/${slug}`)
  title.value = data.title
  html.value = renderMarkdown(data.content)
  setPageMeta(data.meta_title || data.title, data.meta_description || data.excerpt)
  loading.value = false
})
</script>

<template>
  <div class="landing-section">
    <NButton quaternary @click="router.push('/blog')">← К блогу</NButton>
    <NSpin :show="loading">
      <article v-if="!loading" class="article">
        <h1>{{ title }}</h1>
        <div class="content" v-html="html" />
      </article>
    </NSpin>
  </div>
</template>

<style scoped>
.article {
  max-width: 760px;
  margin: 24px auto 80px;
}
.content :deep(h1) { font-size: 1.8rem; }
.content :deep(h2) { font-size: 1.4rem; margin-top: 1.5rem; }
.content :deep(h3) { font-size: 1.15rem; }
.content :deep(p) { line-height: 1.75; margin: 0.75rem 0; }
</style>
