import { computed } from 'vue'
import { useLocaleStore } from './locale'
import translations from './translations'

/**
 * Composable for translating UI strings.
 * Returns `t(key)` for lookups, plus reactive `locale` and `setLocale` for language switching.
 * Falls back to English when a key is missing in the active language.
 */
export function useI18n() {
  const localeStore = useLocaleStore()

  function t(key) {
    return translations[localeStore.locale]?.[key] ?? translations['en']?.[key] ?? key
  }

  const locale = computed(() => localeStore.locale)

  function setLocale(lang) {
    localeStore.setLocale(lang)
  }

  return { t, locale, setLocale }
}
