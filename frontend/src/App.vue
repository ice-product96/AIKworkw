<script setup lang="ts">
import { RouterView } from 'vue-router'
import { NConfigProvider, NMessageProvider, dateRuRU, ruRU } from 'naive-ui'
</script>

<template>
  <NConfigProvider :locale="ruRU" :date-locale="dateRuRU">
    <NMessageProvider>
      <RouterView />
    </NMessageProvider>
  </NConfigProvider>
</template>
