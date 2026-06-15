<script setup>
/**
 * BaseCard — standard white rounded card with shadow.
 * Use the default slot for content, and the optional `header` slot for a card title row.
 */
defineProps({
  padding: { type: String, default: 'p-5' },
})
</script>

<template>
  <div :class="['bg-white rounded-xl border border-gray-100 shadow-sm', padding]">
    <div v-if="$slots.header" class="mb-4">
      <slot name="header" />
    </div>
    <slot />
  </div>
</template>
