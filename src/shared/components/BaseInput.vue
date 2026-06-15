<script setup>
/**
 * BaseInput — styled text input with optional label, helper text, and error state.
 *
 * Props:
 *   modelValue – v-model binding
 *   label      – field label displayed above the input
 *   placeholder
 *   type       – native input type (default: 'text')
 *   error      – validation error message; renders the input in red when set
 *   helper     – secondary helper text displayed below the input
 *   required   – adds a red asterisk to the label
 *   disabled
 */
defineProps({
  modelValue:  { type: [String, Number], default: '' },
  label:       { type: String, default: '' },
  placeholder: { type: String, default: '' },
  type:        { type: String, default: 'text' },
  error:       { type: String, default: '' },
  helper:      { type: String, default: '' },
  required:    { type: Boolean, default: false },
  disabled:    { type: Boolean, default: false },
})

defineEmits(['update:modelValue'])
</script>

<template>
  <div class="flex flex-col gap-1">
    <label v-if="label" class="text-xs font-medium text-gray-600">
      {{ label }}
      <span v-if="required" class="text-red-500 ml-0.5">*</span>
    </label>

    <input
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      @input="$emit('update:modelValue', $event.target.value)"
      :class="[
        'w-full border rounded-lg px-3 py-2 text-sm text-gray-800 placeholder-gray-400',
        'focus:outline-none focus:ring-2 transition',
        error
          ? 'border-red-400 focus:ring-red-400'
          : 'border-gray-200 focus:ring-blue-500',
        disabled && 'bg-gray-50 cursor-not-allowed',
      ]"
    />

    <p v-if="error" class="text-xs text-red-500">{{ error }}</p>
    <p v-else-if="helper" class="text-xs text-gray-400">{{ helper }}</p>
  </div>
</template>
