import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useLocaleStore = defineStore('locale', () => {
  const locale = ref(localStorage.getItem('exobios_lang') || 'en')

  function setLocale(lang) {
    locale.value = lang
    localStorage.setItem('exobios_lang', lang)
  }

  return { locale, setLocale }
})
