import fs from 'node:fs';
import process from 'node:process';
import { URL, fileURLToPath } from 'node:url';
import { defineConfig, loadEnv } from 'vite';
import { setupVitePlugins } from './build/plugins';
import { createViteProxy, getBuildTime } from './build/config';

/**
 * 本地/测试环境 HTTPS 证书（自签）
 *
 * 浏览器仅在安全上下文（HTTPS 或 localhost）开放麦克风录音，
 * 因此开发与测试环境通过自签证书启用 HTTPS。
 * 证书缺失时自动降级为 HTTP，不影响正常启动。
 */
const certKeyFile = fileURLToPath(new URL('./cert/key.pem', import.meta.url));
const certFile = fileURLToPath(new URL('./cert/cert.pem', import.meta.url));
const httpsOptions =
  fs.existsSync(certKeyFile) && fs.existsSync(certFile)
    ? { key: fs.readFileSync(certKeyFile), cert: fs.readFileSync(certFile) }
    : undefined;

export default defineConfig(configEnv => {
  const viteEnv = loadEnv(configEnv.mode, process.cwd()) as unknown as Env.ImportMeta;

  const buildTime = getBuildTime();

  const enableProxy = configEnv.command === 'serve' && !configEnv.isPreview;

  return {
    base: viteEnv.VITE_BASE_URL,
    resolve: {
      alias: {
        '~': fileURLToPath(new URL('./', import.meta.url)),
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    css: {
      preprocessorOptions: {
        scss: {
          api: 'modern-compiler',
          additionalData: `@use "@/styles/scss/global.scss" as *;`
        }
      }
    },
    plugins: setupVitePlugins(viteEnv, buildTime),
    define: {
      BUILD_TIME: JSON.stringify(buildTime)
    },
    server: {
      host: '0.0.0.0',
      port: 9527,
      open: true,
      https: httpsOptions,
      proxy: createViteProxy(viteEnv, enableProxy)
    },
    preview: {
      host: '0.0.0.0',
      port: 9725,
      https: httpsOptions
    },
    build: {
      reportCompressedSize: false,
      sourcemap: viteEnv.VITE_SOURCE_MAP === 'Y',
      commonjsOptions: {
        ignoreTryCatch: false
      }
    }
  };
});
