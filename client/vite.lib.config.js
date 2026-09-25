import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/* The components as a package. `vite.config.js` builds the reader itself, an
 * application that mounts on `#root`; this one builds the parts that take what
 * they are given and draw it, so another page can hold them. React stays
 * external: the page that renders these already has one.
 */
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    cssCodeSplit: false,
    lib: {
      entry: 'src/index.js',
      name: 'LawLibraryReader',
      formats: ['es'],
      fileName: () => 'lawlibrary-reader.js',
    },
    rollupOptions: {
      external: ['react', 'react-dom', 'react-dom/client', 'react/jsx-runtime'],
      output: {
        assetFileNames: 'lawlibrary-reader[extname]',
        globals: {
          react: 'React',
          'react-dom': 'ReactDOM',
        },
      },
    },
  },
})
