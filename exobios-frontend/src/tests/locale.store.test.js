import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useLocaleStore } from '@/i18n/locale'
import { useI18n } from '@/i18n'

describe('Locale Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('defaults to English when nothing is persisted', () => {
    const store = useLocaleStore()
    expect(store.locale).toBe('en')
  })

  it('restores a previously persisted locale on store creation', () => {
    localStorage.getItem.mockReturnValueOnce('hi')
    const store = useLocaleStore()
    expect(store.locale).toBe('hi')
  })

  it('setLocale() updates state and persists to localStorage', () => {
    const store = useLocaleStore()
    store.setLocale('kn')
    expect(store.locale).toBe('kn')
    expect(localStorage.setItem).toHaveBeenCalledWith('exobios_locale', 'kn')
  })
})

describe('useI18n composable', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('t() returns the English string by default', () => {
    const { t } = useI18n()
    expect(t('common.cancel')).toBe('Cancel')
  })

  it('t() switches language after setLocale()', () => {
    const { t, setLocale } = useI18n()
    setLocale('hi')
    expect(t('common.cancel')).toBe('रद्द करें')
  })

  it('t() falls back to the key itself for a missing translation', () => {
    const { t } = useI18n()
    expect(t('this.key.does.not.exist')).toBe('this.key.does.not.exist')
  })

  it('locale is reactive to the underlying store', () => {
    const { locale, setLocale } = useI18n()
    expect(locale.value).toBe('en')
    setLocale('kn')
    expect(locale.value).toBe('kn')
  })
})
