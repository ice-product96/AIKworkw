<script setup lang="ts">
import { NTag, NText, NButton, NSpace } from 'naive-ui'
import { formatBudget, timeAgo } from '../../constants/marketplace'
import { serviceLabel, statusLabel } from '../../constants/orders'

export interface ProjectCardData {
  id: string
  title: string
  description_preview?: string
  description?: string
  service_type: string
  budget_min: number | null
  budget_max: number | null
  status: string
  created_at: string
  proposals_count?: number
  is_mine?: boolean
  message_count?: number
}

defineProps<{
  project: ProjectCardData
  showChat?: boolean
}>()

const emit = defineEmits<{
  open: [id: string]
  chat: [id: string]
}>()

function preview(p: ProjectCardData) {
  return p.description_preview || p.description?.slice(0, 220) || ''
}
</script>

<template>
  <article class="project-card" @click="emit('open', project.id)">
    <div class="card-head">
      <h3 class="title">{{ project.title }}</h3>
      <NTag v-if="project.is_mine" type="success" size="small">Мой</NTag>
    </div>
    <p class="preview">{{ preview(project) }}</p>
    <div class="meta">
      <NTag size="small" :bordered="false">{{ serviceLabel(project.service_type) }}</NTag>
      <NTag size="small" type="info">{{ statusLabel(project.status) }}</NTag>
      <NText depth="3" class="budget">{{ formatBudget(project.budget_min, project.budget_max) }}</NText>
    </div>
    <div class="footer">
      <NText depth="3">{{ timeAgo(project.created_at) }}</NText>
      <NSpace class="actions" @click.stop>
        <NTag v-if="(project.proposals_count ?? 0) > 0" type="warning" size="small">
          {{ project.proposals_count }} откл.
        </NTag>
        <NTag v-else size="small">Нет откликов</NTag>
        <NButton v-if="showChat" size="tiny" quaternary @click="emit('chat', project.id)">Чат</NButton>
      </NSpace>
    </div>
  </article>
</template>

<style scoped>
.project-card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px 20px;
  cursor: pointer;
  transition: box-shadow 0.15s, border-color 0.15s;
}
.project-card:hover {
  border-color: #4caf50;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}
.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}
.title {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  line-height: 1.35;
  color: #1a1a1a;
}
.preview {
  margin: 0 0 12px;
  font-size: 14px;
  line-height: 1.55;
  color: #555;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.budget {
  font-weight: 500;
  margin-left: auto;
}
.footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  border-top: 1px solid #f0f0f0;
  padding-top: 10px;
}
.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
