import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig(({ mode }) => {
  // Загружаем .env файлы для конфигурации (если нужно)
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [
      react(),
      VitePWA({
        registerType: 'autoUpdate',
        workbox: {
          globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
          runtimeCaching: [
            {
              // Кэшируем API-запросы в продакшене
              urlPattern: /^https:\/\/ixe-core\.onrender\.com\/.*$/,
              handler: 'NetworkFirst',
              options: {
                cacheName: 'api-cache',
                expiration: {
                  maxEntries: 200,
                  maxAgeSeconds: 86400, // 1 день
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
    server: {
      port: 5173,
      strictPort: true,
      host: true,
      historyApiFallback: true,
      proxy: {
        // Только для локальной разработки
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false,
        },
        '/answer': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path,
        },
      },
    },
    preview: {
      port: 4173,
      strictPort: true,
      host: true,
      historyApiFallback: true,
    },
  }
})
