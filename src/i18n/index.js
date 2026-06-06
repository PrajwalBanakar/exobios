import { computed } from 'vue'
import { useLocaleStore } from '../stores/locale'
import translations from './translations'

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
