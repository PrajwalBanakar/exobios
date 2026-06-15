import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    // `@` maps to the `src/` directory for clean cross-feature imports
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
})
