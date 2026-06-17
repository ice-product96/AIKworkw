<script setup lang="ts">
import type { ClientPublicInfo } from '../../types/profile'

defineProps<{
  client: ClientPublicInfo
  compact?: boolean
}>()
</script>

<template>
  <div class="buyer" :class="{ compact }">
    <div class="avatar-wrap">
      <img v-if="client.avatar_url" :src="client.avatar_url" alt="" class="avatar" />
      <div v-else class="avatar placeholder">{{ client.display_name.slice(0, 1).toUpperCase() }}</div>
      <span class="level">{{ client.level }}</span>
    </div>
    <div class="info">
      <div class="name-row">
        <span class="label">Покупатель:</span>
        <span class="name">{{ client.display_name }}</span>
      </div>
      <div class="stats">
        <span>Размещено проектов: <strong>{{ client.projects_posted }}</strong></span>
        <span>Нанято: <strong>{{ client.hire_rate_percent }}%</strong></span>
      </div>
      <div v-if="client.company && !compact" class="company">{{ client.company }}</div>
    </div>
  </div>
</template>

<style scoped>
.buyer {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px 0;
  border-top: 1px solid #f0f0f0;
  margin-top: 8px;
}
.buyer.compact {
  padding: 8px 0;
}
.avatar-wrap {
  position: relative;
  flex-shrink: 0;
}
.avatar {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  object-fit: cover;
  border: 1px solid #e0e0e0;
}
.avatar.placeholder {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: linear-gradient(135deg, #81c784, #4caf50);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
}
.level {
  position: absolute;
  bottom: -4px;
  right: -4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #ffc107;
  color: #333;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #fff;
}
.info {
  flex: 1;
  min-width: 0;
  font-size: 13px;
}
.name-row {
  margin-bottom: 4px;
}
.label {
  color: #888;
  margin-right: 4px;
}
.name {
  color: #1976d2;
  font-weight: 600;
}
.stats {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: #666;
  font-size: 12px;
}
.company {
  margin-top: 4px;
  color: #999;
  font-size: 12px;
}
</style>
