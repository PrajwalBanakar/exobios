<script setup>
import { reactive } from 'vue'

defineProps({
  citations: { type: Array, required: true },
  sourceLabel: { type: String, default: 'Biochemistry' },
})

const expanded = reactive(new Set())

function toggle(id) {
  if (expanded.has(id)) expanded.delete(id)
  else expanded.add(id)
}
</script>

<template>
  <div class="mt-3 border-t border-slate-100 pt-2.5">
    <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Sources ({{ citations.length }})</p>

    <div class="mt-2 flex flex-wrap gap-1.5">
      <button
        v-for="c in citations"
        :key="c.chunkId"
        type="button"
        @click="toggle(c.chunkId)"
        :aria-expanded="expanded.has(c.chunkId)"
        class="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-medium text-slate-600 transition motion-safe:duration-150 hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40"
      >
        {{ sourceLabel }}<template v-if="c.heading"> &middot; {{ c.heading }}</template>
        <template v-if="c.page"> &middot; Page {{ c.page }}</template>
      </button>
    </div>

    <div v-for="c in citations" :key="`${c.chunkId}-excerpt`">
      <p v-if="expanded.has(c.chunkId) && c.excerpt" class="mt-2 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-xs leading-relaxed text-slate-500">
        {{ c.excerpt }}
      </p>
    </div>
  </div>
</template>
