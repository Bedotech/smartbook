import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { openDB, DBSchema, IDBPDatabase } from 'idb'
import type { LeaderFormValues } from '../schemas/leaderSchema'
import type { MemberFormValues } from '../schemas/memberSchema'

interface OfflineDB extends DBSchema {
  leaderDrafts: {
    key: string // token
    value: {
      token: string
      data: LeaderFormValues
      updatedAt: number
    }
  }
  memberDrafts: {
    key: string // `${token}-${index}`
    value: {
      token: string
      data: MemberFormValues[]
      updatedAt: number
    }
  }
}

interface OfflineStore {
  // Leader draft
  leaderDraft: Record<string, LeaderFormValues>
  saveLeaderDraft: (token: string, data: LeaderFormValues) => void
  getLeaderDraft: (token: string) => LeaderFormValues | null
  clearLeaderDraft: (token: string) => void

  // Member drafts
  memberDrafts: Record<string, MemberFormValues[]>
  saveMemberDraft: (token: string, data: MemberFormValues) => void
  clearMemberDrafts: (token: string) => void

  // IndexedDB persistence
  initDB: () => Promise<void>
  syncToIndexedDB: () => Promise<void>
}

let db: IDBPDatabase<OfflineDB> | null = null

export const useOfflineStore = create<OfflineStore>()(
  persist(
    (set, get) => ({
      leaderDraft: {},
      memberDrafts: {},

      saveLeaderDraft: (token, data) => {
        set((state) => ({
          leaderDraft: { ...state.leaderDraft, [token]: data },
        }))
        get().syncToIndexedDB()
      },

      getLeaderDraft: (token) => {
        return get().leaderDraft[token] || null
      },

      clearLeaderDraft: (token) => {
        set((state) => {
          const { [token]: _, ...rest } = state.leaderDraft
          return { leaderDraft: rest }
        })
        get().syncToIndexedDB()
      },

      saveMemberDraft: (token, data) => {
        set((state) => {
          const existing = state.memberDrafts[token] || []
          return {
            memberDrafts: {
              ...state.memberDrafts,
              [token]: [...existing, data],
            },
          }
        })
        get().syncToIndexedDB()
      },

      clearMemberDrafts: (token) => {
        set((state) => {
          const { [token]: _, ...rest } = state.memberDrafts
          return { memberDrafts: rest }
        })
        get().syncToIndexedDB()
      },

      initDB: async () => {
        db = await openDB<OfflineDB>('smartbook-guest', 1, {
          upgrade(database) {
            database.createObjectStore('leaderDrafts', { keyPath: 'token' })
            database.createObjectStore('memberDrafts', { keyPath: 'token' })
          },
        })
      },

      syncToIndexedDB: async () => {
        if (!db) return
        const state = get()

        try {
          // Sync leader drafts
          const tx1 = db.transaction('leaderDrafts', 'readwrite')
          await Promise.all(
            Object.entries(state.leaderDraft).map(([token, data]) =>
              tx1.store.put({ token, data, updatedAt: Date.now() })
            )
          )

          // Sync member drafts
          const tx2 = db.transaction('memberDrafts', 'readwrite')
          await Promise.all(
            Object.entries(state.memberDrafts).map(([token, data]) =>
              tx2.store.put({ token, data, updatedAt: Date.now() })
            )
          )
        } catch (error) {
          console.error('Failed to sync to IndexedDB:', error)
        }
      },
    }),
    {
      name: 'smartbook-offline-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
)
