import { defineStore } from 'pinia'
import { ref } from 'vue'

/** Persists the user's chosen UI language across sessions. */
export const useLocaleStore = defineStore('locale', () => {
  const locale = ref(localStorage.getItem('exobios_locale') || 'en')

  function setLocale(lang) {
    locale.value = lang
    localStorage.setItem('exobios_locale', lang)
  }

  return { locale, setLocale }
})
