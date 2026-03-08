import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'frontend/src'),
    },
  },
  esbuild: {
    loader: 'jsx',
    include: /\.[jt]sx?$/,
  },
  optimizeDeps: {
    esbuild: {
      loader: {
        '.js': 'jsx',
      },
    },
  },
});
