<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue:   { type: [String, Number], default: '' },
  id:           { type: String, required: true },
  label:        { type: String, default: '' },
  type:         { type: String, default: 'text' },
  placeholder:  { type: String, default: '' },
  autocomplete: { type: String, default: 'off' },
  maxlength:    { type: [String, Number], default: undefined },
  inputmode:    { type: String, default: undefined },
  error:        { type: String, default: '' },
  required:     { type: Boolean, default: false },
  revealable:   { type: Boolean, default: false },
  disabled:     { type: Boolean, default: false },
})

defineEmits(['update:modelValue'])

const revealed  = ref(false)
const inputType = computed(() => (props.revealable ? (revealed.value ? 'text' : 'password') : props.type))
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="id" class="text-xs font-medium text-slate-600">
      {{ label }} <span v-if="required" class="text-red-500">*</span>
    </label>

    <div class="relative">
      <span v-if="$slots.icon" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
        <slot name="icon" />
      </span>

      <input
        :id="id"
        :type="inputType"
        :value="modelValue"
        :placeholder="placeholder"
        :autocomplete="autocomplete"
        :maxlength="maxlength"
        :inputmode="inputmode"
        :disabled="disabled"
        :aria-invalid="!!error"
        :aria-describedby="error ? `${id}-error` : undefined"
        @input="$emit('update:modelValue', $event.target.value)"
        :class="[
          'w-full h-12 rounded-xl border bg-white text-sm text-slate-800 placeholder-slate-400',
          'transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-offset-0',
          $slots.icon ? 'pl-11' : 'pl-4',
          revealable ? 'pr-11' : 'pr-4',
          error
            ? 'border-red-300 focus:border-red-400 focus:ring-red-400/30'
            : 'border-slate-200 hover:border-slate-300 focus:border-blue-500 focus:ring-blue-500/30',
          disabled && 'bg-slate-50 text-slate-400 cursor-not-allowed',
        ]"
      />

      <button
        v-if="revealable"
        type="button"
        tabindex="-1"
        class="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
        :aria-label="revealed ? 'Hide password' : 'Show password'"
        @click="revealed = !revealed"
      >
        <svg v-if="!revealed" class="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
        </svg>
        <svg v-else class="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
          <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>
        </svg>
      </button>
    </div>

    <p v-if="error" :id="`${id}-error`" class="flex items-center gap-1 text-xs text-red-500">
      <svg class="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="13"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      {{ error }}
    </p>
  </div>
</template>
