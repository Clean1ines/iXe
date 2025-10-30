import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        // Добавим стратегию networkFirst для API-запросов, если нужно
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/ixe-core\.onrender\.com\/.*$/,
            handler: 'NetworkFirst', // или 'StaleWhileRevalidate', в зависимости от предпочтений
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 200,
                maxAgeSeconds: 60 * 60 * 24, // 1 день
              },
            },
          },
        ],
      },
      manifest: {
        name: 'Подготовка к ЕГЭ',
        short_name: 'ЕГЭ PWA',
        description: 'Приложение для подготовки к ЕГЭ',
        theme_color: '#ffffff',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
          },
        ],
      },
    }),
  ],
  // Добавим настройку для корректной работы SPA
  server: {
    historyApiFallback: true, // Это ключевая настройка
  },
  preview: {
    historyApiFallback: true, // Применяем и для preview
  },
})
