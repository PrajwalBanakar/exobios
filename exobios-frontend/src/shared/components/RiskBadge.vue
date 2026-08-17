<script setup>
import { computed } from 'vue'
import { useI18n } from '@/i18n'

/**
 * RiskBadge — consistent risk-tier chip used anywhere a patient's risk level is shown.
 * Conveys status via both color and text (never color alone).
 *
 * Props:
 *   risk – 'High' | 'Moderate' | 'Low'
 */
const props = defineProps({
  risk: { type: String, required: true },
})

const { t } = useI18n()

const TIERS = {
  High:     { classes: 'bg-red-50 text-red-700 border-red-100',       dot: 'bg-red-500',   labelKey: 'risk.high'     },
  Moderate: { classes: 'bg-amber-50 text-amber-700 border-amber-100', dot: 'bg-amber-500', labelKey: 'risk.moderate' },
  Low:      { classes: 'bg-green-50 text-green-700 border-green-100', dot: 'bg-green-500', labelKey: 'risk.low'      },
}
const FALLBACK = { classes: 'bg-slate-100 text-slate-600 border-slate-200', dot: 'bg-slate-400', labelKey: '' }

const tier = computed(() => TIERS[props.risk] ?? FALLBACK)
</script>

<template>
  <span :class="['inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold', tier.classes]">
    <span :class="['h-1.5 w-1.5 rounded-full', tier.dot]"/>
    {{ tier.labelKey ? t(tier.labelKey) : risk }}
  </span>
</template>
