<script setup lang="ts">
import { ref } from 'vue'
import { NTag, NText, NButton, NSpace } from 'naive-ui'
import { formatBudget, timeAgo } from '../../constants/marketplace'
import { serviceLabel } from '../../constants/orders'
import BuyerBlock from './BuyerBlock.vue'
import type { ClientPublicInfo } from '../../types/profile'

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
  client?: ClientPublicInfo | null
}

const props = defineProps<{
  project: ProjectCardData
  showChat?: boolean
}>()

const emit = defineEmits<{
  open: [id: string]
  chat: [id: string]
}>()

const expanded = ref(false)

function preview(p: ProjectCardData) {
  const text = p.description_preview || p.description || ''
  if (expanded.value) return text
  return text.length > 180 ? text.slice(0, 180) + '…' : text
}

function budgetLabel() {
  const { budget_min, budget_max } = props.project
  if (budget_max != null) return `до ${Number(budget_max).toLocaleString('ru-RU')} ₽`
  return formatBudget(budget_min, budget_max)
}
</script>

<template>
  <article class="project-card" @click="emit('open', project.id)">
    <div class="card-top">
      <h3 class="title">{{ project.title }}</h3>
      <div class="budget-block">
        <div class="budget-main">Желаемый бюджет: {{ budgetLabel() }}</div>
        <div v-if="project.budget_min && project.budget_max" class="budget-alt">
          Допустимый: {{ formatBudget(project.budget_min, project.budget_max) }}
        </div>
      </div>
    </div>

    <p class="preview">
      {{ preview(project) }}
      <button
        v-if="(project.description_preview || project.description || '').length > 180"
        type="button"
        class="show-more"
        @click.stop="expanded = !expanded"
      >
        {{ expanded ? 'Свернуть' : 'Показать полностью' }}
      </button>
    </p>

    <BuyerBlock v-if="project.client" :client="project.client" />

    <div class="footer">
      <NSpace :size="16">
        <NText depth="3">{{ timeAgo(project.created_at) }}</NText>
        <NText depth="3">
          Предложений: <strong>{{ project.proposals_count ?? 0 }}</strong>
        </NText>
      </NSpace>
      <NSpace @click.stop>
        <NTag size="small">{{ serviceLabel(project.service_type) }}</NTag>
        <NTag v-if="project.is_mine" type="success" size="small">Мой</NTag>
        <NButton v-if="showChat" size="tiny" quaternary @click="emit('chat', project.id)">Чат</NButton>
      </NSpace>
    </div>
  </article>
</template>

<style scoped>
.project-card {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 16px 20px;
  cursor: pointer;
  transition: box-shadow 0.15s, border-color 0.15s;
}
.project-card:hover {
  border-color: #4caf50;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}
.card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 10px;
}
.title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #2e7d32;
  line-height: 1.35;
  flex: 1;
}
.budget-block {
  text-align: right;
  flex-shrink: 0;
}
.budget-main {
  font-weight: 700;
  color: #2e7d32;
  font-size: 14px;
}
.budget-alt {
  font-size: 12px;
  color: #888;
  margin-top: 2px;
}
.preview {
  margin: 0;
  font-size: 14px;
  line-height: 1.55;
  color: #444;
}
.show-more {
  border: none;
  background: none;
  color: #1976d2;
  cursor: pointer;
  padding: 0;
  font-size: 13px;
  margin-left: 4px;
}
.footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f5f5f5;
  font-size: 12px;
}
</style>
