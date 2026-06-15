import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const SAMPLE_NOTIFICATIONS = [
  { id: 1, type: 'error',   read: false, title: 'High-Risk Alert',       body: 'Patient Priya Sharma shows critical vital signs. Immediate attention required.',          time: '2 min ago'  },
  { id: 2, type: 'warning', read: false, title: 'Medication Reminder',   body: 'Rajesh Kumar is due for his afternoon medication. Please confirm administration.',          time: '15 min ago' },
  { id: 3, type: 'success', read: false, title: 'Referral Confirmed',    body: 'Referral for Anita Devi to Rampur CHC has been confirmed. Transport arranged.',            time: '1 hr ago'   },
  { id: 4, type: 'info',    read: true,  title: 'Teleconsult Scheduled', body: 'Video consultation with Dr. Anjali Sharma is scheduled for today at 3:00 PM.',             time: '2 hr ago'   },
  { id: 5, type: 'success', read: true,  title: 'Sync Complete',         body: 'All patient records have been successfully synchronized with the central server.',          time: '3 hr ago'   },
  { id: 6, type: 'warning', read: true,  title: 'Offline Mode',          body: 'Network connection lost. Working in offline mode. Data will sync when reconnected.',         time: '5 hr ago'   },
  { id: 7, type: 'info',    read: true,  title: 'System Update',         body: 'A new version of Exobios is available. Update to get the latest features and fixes.',       time: 'Yesterday'  },
]

export const useNotificationsStore = defineStore('notifications', () => {
  const items = ref([...SAMPLE_NOTIFICATIONS])

  const unreadCount = computed(() => items.value.filter(n => !n.read).length)

  function markRead(id) {
    const n = items.value.find(n => n.id === id)
    if (n) n.read = true
  }

  function markAllRead() {
    items.value.forEach(n => { n.read = true })
  }

  return { items, unreadCount, markRead, markAllRead }
})
