<script setup lang="ts">
import { h, onMounted, ref } from 'vue'
import { NDataTable, NButton } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import api from '../../api/client'

const users = ref<Record<string, unknown>[]>([])

const columns: DataTableColumns = [
  { title: 'Email', key: 'email' },
  { title: 'Роль', key: 'role' },
  {
    title: '',
    key: 'id',
    render: (row) =>
      h(NButton, { size: 'small', onClick: () => api.patch(`/admin/users/${row.id}/block`) }, () => 'Блок'),
  },
]

onMounted(async () => {
  const { data } = await api.get('/admin/users')
  users.value = data
})
</script>

<template>
  <h2>Пользователи</h2>
  <NDataTable :columns="columns" :data="users" />
</template>
