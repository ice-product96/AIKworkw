<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  NCard, NForm, NFormItem, NInput, NButton, NSpace, NAvatar, NUpload, NText, NStatistic, NGrid, NGridItem, useMessage,
} from 'naive-ui'
import type { UploadCustomRequestOptions } from 'naive-ui'
import api from '../api/client'
import { useAuthStore } from '../stores/auth'
import type { UserProfile } from '../types/profile'

const message = useMessage()
const auth = useAuthStore()
const profile = ref<UserProfile | null>(null)
const loading = ref(false)
const saving = ref(false)
const uploadingAvatar = ref(false)
const avatarVersion = ref(0)

const form = ref({
  display_name: '',
  bio: '',
  company: '',
  location: '',
  website: '',
  developer_title: '',
})

const isClient = computed(() => profile.value?.role === 'client')
const isDeveloper = computed(() => profile.value?.role === 'developer')
const avatarSrc = computed(() => {
  if (!profile.value?.avatar_url) return undefined
  const joiner = profile.value.avatar_url.includes('?') ? '&' : '?'
  return `${profile.value.avatar_url}${joiner}t=${avatarVersion.value}`
})

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/profile/me')
    profile.value = data
    form.value = {
      display_name: data.display_name || '',
      bio: data.bio || '',
      company: data.company || '',
      location: data.location || '',
      website: data.website || '',
      developer_title: data.developer_title || '',
    }
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    const { data } = await api.patch('/profile/me', form.value)
    profile.value = data
    await auth.fetchMe()
    message.success('Профиль сохранён')
  } finally {
    saving.value = false
  }
}

async function uploadAvatar({ file, onFinish, onError }: UploadCustomRequestOptions) {
  if (!file.file) {
    onError()
    return
  }
  uploadingAvatar.value = true
  try {
    const fd = new FormData()
    fd.append('file', file.file as File)
    const { data } = await api.post('/profile/avatar', fd)
    profile.value = data
    avatarVersion.value = Date.now()
    await auth.fetchMe()
    message.success('Аватар обновлён')
    onFinish()
  } catch {
    message.error('Не удалось загрузить аватар')
    onError()
  } finally {
    uploadingAvatar.value = false
  }
}

onMounted(load)
</script>

<template>
  <NSpace vertical :size="16">
    <h2 style="margin: 0">Мой профиль</h2>
    <NText depth="3">Публичная информация отображается в объявлениях и на бирже (как на Kwork)</NText>

    <NGrid :cols="2" :x-gap="16" responsive="screen">
      <NGridItem>
        <NCard title="Аватар и статистика">
          <NSpace vertical align="center" :size="16">
            <NAvatar
              round
              :size="96"
              :src="avatarSrc"
              style="background: #4caf50; font-size: 36px"
            >
              {{ (form.display_name || profile?.email || '?').slice(0, 1).toUpperCase() }}
            </NAvatar>
            <NUpload :show-file-list="false" accept="image/*" :custom-request="uploadAvatar">
              <NButton size="small" :loading="uploadingAvatar">Загрузить фото</NButton>
            </NUpload>
            <NSpace v-if="profile">
              <NStatistic label="Уровень" :value="profile.level" />
              <NStatistic v-if="isClient" label="Проектов" :value="profile.projects_posted" />
              <NStatistic v-if="isClient" label="Нанято %" :value="profile.hire_rate_percent" />
              <NStatistic v-if="isDeveloper" label="Агентов" :value="profile.agents_count" />
            </NSpace>
          </NSpace>
        </NCard>
      </NGridItem>

      <NGridItem>
        <NCard title="Редактирование профиля">
          <NForm label-placement="top">
            <NFormItem label="Имя / ник (виден как заказчик)">
              <NInput v-model:value="form.display_name" placeholder="Motion_design" />
            </NFormItem>
            <NFormItem label="О себе">
              <NInput v-model:value="form.bio" type="textarea" :rows="3" placeholder="Кратко о вас..." />
            </NFormItem>
            <NFormItem label="Компания">
              <NInput v-model:value="form.company" />
            </NFormItem>
            <NFormItem label="Город">
              <NInput v-model:value="form.location" />
            </NFormItem>
            <NFormItem v-if="isDeveloper" label="Специализация (исполнитель)">
              <NInput v-model:value="form.developer_title" placeholder="Разработчик AI-агентов" />
            </NFormItem>
            <NFormItem v-if="isDeveloper" label="Сайт / портфолио">
              <NInput v-model:value="form.website" placeholder="https://..." />
            </NFormItem>
            <NButton type="primary" :loading="saving" @click="save">Сохранить</NButton>
          </NForm>
        </NCard>
      </NGridItem>
    </NGrid>
  </NSpace>
</template>
