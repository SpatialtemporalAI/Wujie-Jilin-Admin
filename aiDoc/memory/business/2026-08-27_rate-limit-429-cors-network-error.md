# 2026-08-27 限流 429 跨域 Network Error 修复

## 需求背景

部分页面（运行监控、地图编辑器等）存在高频轮询，容易触发 IP 限流（默认 `rate_limit.ip_per_minute=120`）。触发限流后，内网部署下前端只弹「Network Error」，看不到后端的「请求过于频繁」提示。

## 根因

Starlette `add_middleware` 是**后注册先执行**（`user_middleware.insert(0)`）。原 `setup_registry.py` 中 `CORSMiddleware` 注册得早（执行靠内），`RateLimitMiddleware` / `RequestSizeLimitMiddleware` 执行在它之前，短路返回的 429/413 响应不经过 CORS 中间件，缺少 `Access-Control-Allow-Origin` 头。

内网前端跨域直连后端（`.env.prod` 的 `VITE_SERVICE_BASE_URL=http://192.168.5.93:8000`），浏览器拿不到 CORS 头直接拦截响应，axios 报 `ERR_NETWORK` → 前端只能显示 "Network Error"。同源部署不依赖 CORS 头，所以只有跨域场景暴露。

## 变更内容

- `backend/core/registry/setup_registry.py`：`CORSMiddleware` 移到所有中间件之后注册（最外层执行），所有短路响应（429/413/黑名单）都会携带 CORS 头，前端 `onError` 可正常读取响应体 `msg` 展示「请求过于频繁」。
- 副作用：CORS 预检（OPTIONS）在最外层直接短路，不再进入限流等后续中间件（合理）。

## 约束与备注

- 中间件顺序铁律：任何会**短路返回响应**的中间件（RateLimit/RequestSizeLimit/TrustedHost），都必须注册在 `CORSMiddleware` **之前**（即执行时位于 CORS 内层），否则跨域下短路响应会被浏览器拦截。
- `TrustedHostMiddleware` 仍在最内层（注册最早），其 400 响应同样不带 CORS 头，属可接受边缘场景。
- 若内网多人共享出口 IP 仍频繁触限，可通过 DB 配置 `rate_limit.ip_per_minute` / `rate_limit.whitelist_ips` / `rate_limit.path_rules` 调优（`RateLimitConfigProvider` 定时刷新，无需改代码）。

## 记录日期

2026-08-27
