import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../static',
    emptyOutDir: true,
    rollupOptions: {
      input: 'src/main.jsx',
      output: {
        format: 'es',
        entryFileNames: 'reader.js',
        inlineDynamicImports: true,
      },
    },
  },
})
