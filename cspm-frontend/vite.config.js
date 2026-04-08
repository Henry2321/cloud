import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'https://9gkjuri9o4.execute-api.ap-southeast-2.amazonaws.com',
        changeOrigin: true
      }
    }
  }
});
