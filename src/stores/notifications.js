import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useNotificationsStore = defineStore('notifications', () => {
  const items = ref([
    { id: 1, type: 'error',   title: 'High Risk Case',    body: 'Ramesh Kumar — HIGH RISK assessment flagged. Immediate follow-up required.',  time: '10:32 AM', date: '20 May 2025', read: false },
    { id: 2, type: 'warning', title: 'Pending Referrals', body: '3 referrals pending approval in Rampur and Bhelwa areas.',                     time: '10:15 AM', date: '20 May 2025', read: false },
    { id: 3, type: 'success', title: 'Doctor Available',  body: 'Dr. Anjali Sharma is now available for teleconsultation.',                      time: '09:58 AM', date: '20 May 2025', read: true  },
    { id: 4, type: 'info',    title: 'Sync Complete',     body: 'All patient data synced successfully.',                                         time: '09:30 AM', date: '20 May 2025', read: true  },
    { id: 5, type: 'warning', title: 'Dengue Alert',      body: 'District health authorities issued a dengue advisory for Rampur district.',     time: '08:30 AM', date: '20 May 2025', read: false },
    { id: 6, type: 'success', title: 'Referral Done',     body: 'Savitri Devi successfully referred to Rampur Community Health Center.',         time: '4:15 PM',  date: '19 May 2025', read: true  },
    { id: 7, type: 'info',    title: 'System Update',     body: 'Version 2.4.1 deployed. Evidence upload feature is now available.',            time: '3:00 PM',  date: '19 May 2025', read: true  },
  ])

  const unreadCount = computed(() => items.value.filter(n => !n.read).length)

  function markAllRead() {
    items.value.forEach(n => { n.read = true })
  }

  function markRead(id) {
    const n = items.value.find(n => n.id === id)
    if (n) n.read = true
  }

  return { items, unreadCount, markAllRead, markRead }
})
