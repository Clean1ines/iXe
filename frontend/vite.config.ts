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
        // Обратите внимание: runtimeCaching в Workbox применяется к запросам,
        // которые происходят *во время выполнения* в браузере и не влияет на проксирование dev-сервера.
        // Проксирование в dev-сервере настраивается отдельно.
        runtimeCaching: [
          {
            // Этот паттерн теперь соответствует локальному адресу, на который проксируются запросы
            urlPattern: /^http:\/\/127\.0\.0\.1:8001\/.*$/,
            handler: 'NetworkFirst', // или 'StaleWhileRevalidate', в зависимости от предпочтений
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 200,
                maxAgeSeconds: 60 * 60 * 24, // 1 день
              },
            },
          },
          // Также можно оставить кэширование для удаленного адреса на случай,
          // если он где-то используется напрямую или в проде
          {
            urlPattern: /^https:\/\/ixe-core\.onrender\.com\/.*$/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache-remote',
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
    proxy: {
      // Проксируем все запросы к /api/* на FastAPI бэкенд
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        secure: false, // Установите в true, если FastAPI использует HTTPS
      },
      // Проксируем запросы к /answer на FastAPI бэкенд
      '/answer': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        secure: false, // Установите в true, если FastAPI использует HTTPS
        // Убедимся, что путь /answer передается как есть
        rewrite: (path) => path,
      },
      // При необходимости, можно добавить и другие эндпоинты
      // '/quiz': {
      //   target: 'http://127.0.0.1:8001',
      //   changeOrigin: true,
      //   secure: false,
      // },
    },
  },
  preview: {
    historyApiFallback: true, // Проверьте, нужно ли это для preview
  },
})
