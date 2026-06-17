<script setup lang="ts">
import { h, onMounted, ref } from 'vue'
import {
  NCard, NTabs, NTabPane, NDataTable, NButton, NSpace, NInput, NSelect, NForm, NFormItem,
  useMessage, NModal,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import api from '../../api/client'

interface Post {
  id: string
  slug: string
  title: string
  excerpt: string | null
  content?: string
  status: string
}

const message = useMessage()
const posts = ref<Post[]>([])
const landing = ref<{ title: string; content_json: Record<string, unknown>; meta_title?: string; meta_description?: string } | null>(null)
const editPost = ref<Post | null>(null)
const showModal = ref(false)

const statusOptions = [
  { label: 'Черновик', value: 'draft' },
  { label: 'Опубликован', value: 'published' },
]

const columns: DataTableColumns<Post> = [
  { title: 'Заголовок', key: 'title' },
  { title: 'Slug', key: 'slug' },
  { title: 'Статус', key: 'status' },
  {
    title: '',
    key: 'actions',
    render: (row) =>
      h(NSpace, {}, () => [
        h(NButton, { size: 'small', onClick: () => openEdit(row) }, () => 'Редактировать'),
        h(NButton, { size: 'small', type: 'error', onClick: () => removePost(row.id) }, () => 'Удалить'),
      ]),
  },
]

async function load() {
  const [postsRes, pageRes] = await Promise.all([
    api.get('/admin/content/posts'),
    api.get('/admin/content/pages/home'),
  ])
  posts.value = postsRes.data
  landing.value = pageRes.data
}

async function saveLanding() {
  if (!landing.value) return
  await api.patch('/admin/content/pages/home', {
    title: landing.value.title,
    content_json: landing.value.content_json,
    meta_title: landing.value.meta_title,
    meta_description: landing.value.meta_description,
  })
  message.success('Главная сохранена')
}

async function openEdit(row: Post) {
  const { data } = await api.get(`/admin/content/posts/${row.id}`)
  editPost.value = { ...data }
  showModal.value = true
}

async function savePost() {
  if (!editPost.value) return
  await api.patch(`/admin/content/posts/${editPost.value.id}`, editPost.value)
  showModal.value = false
  message.success('Статья сохранена')
  await load()
}

async function removePost(id: string) {
  await api.delete(`/admin/content/posts/${id}`)
  message.success('Удалено')
  await load()
}

async function createEmpty() {
  const slug = `post-${Date.now()}`
  await api.post('/admin/content/posts', {
    slug,
    title: 'Новая статья',
    content: '# Заголовок\n\nТекст статьи.',
    status: 'draft',
  })
  await load()
}

onMounted(load)
</script>

<template>
  <h2>Контент и блог</h2>
  <NTabs type="line">
    <NTabPane name="blog" tab="Блог">
      <NSpace vertical>
        <NButton type="primary" @click="createEmpty">Новая статья</NButton>
        <NDataTable :columns="columns" :data="posts" />
      </NSpace>
    </NTabPane>
    <NTabPane name="landing" tab="Главная">
      <NCard v-if="landing">
        <NForm label-placement="top">
          <NFormItem label="Title">
            <NInput v-model:value="landing.title" />
          </NFormItem>
          <NFormItem label="Hero title">
            <NInput v-model:value="(landing.content_json as Record<string, string>).hero_title" />
          </NFormItem>
          <NFormItem label="Hero subtitle">
            <NInput v-model:value="(landing.content_json as Record<string, string>).hero_subtitle" type="textarea" />
          </NFormItem>
          <NFormItem label="SEO title">
            <NInput v-model:value="landing.meta_title" />
          </NFormItem>
          <NFormItem label="SEO description">
            <NInput v-model:value="landing.meta_description" type="textarea" />
          </NFormItem>
          <NFormItem label="SEO block">
            <NInput v-model:value="(landing.content_json as Record<string, string>).seo_block" type="textarea" :rows="4" />
          </NFormItem>
          <NButton type="primary" @click="saveLanding">Сохранить</NButton>
        </NForm>
      </NCard>
    </NTabPane>
  </NTabs>

  <NModal v-model:show="showModal" preset="card" title="Редактирование статьи" style="width: 720px">
    <NForm v-if="editPost" label-placement="top">
      <NFormItem label="Заголовок"><NInput v-model:value="editPost.title" /></NFormItem>
      <NFormItem label="Slug"><NInput v-model:value="editPost.slug" /></NFormItem>
      <NFormItem label="Excerpt"><NInput v-model:value="editPost.excerpt" type="textarea" /></NFormItem>
      <NFormItem label="Контент (Markdown)"><NInput v-model:value="editPost.content" type="textarea" :rows="12" /></NFormItem>
      <NFormItem label="Статус"><NSelect v-model:value="editPost.status" :options="statusOptions" /></NFormItem>
      <NButton type="primary" @click="savePost">Сохранить</NButton>
    </NForm>
  </NModal>
</template>
