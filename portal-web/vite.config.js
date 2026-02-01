import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  // Set base path for GitHub Pages deployment
  // For repo at github.com/username/ErgoLab, use '/ErgoLab/'
  // For custom domain or root deployment, use '/'
  base: mode === 'github-pages' ? '/ErgoLab/' : '/',
  define: {
    'import.meta.env.VITE_API_URL': mode === 'github-pages' 
      ? JSON.stringify('https://ergolab-production.up.railway.app')
      : undefined,
  },
  plugins: [react()],
  server: {
    port: 3000,
    host: true, // Listen on all addresses (needed for Docker)
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 3000,
    host: true,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'build',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@headlessui/react', '@heroicons/react'],
        },
      },
    },
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom'],
    esbuildOptions: {
      loader: {
        '.js': 'jsx',
      },
    },
  },
}));
