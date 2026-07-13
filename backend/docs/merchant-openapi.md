# 商户开放 API 对接文档

> 版本：v1 ｜ 前缀：`/openapi/v1` ｜ 鉴权：HMAC-SHA256 签名

本文档面向第三方商户接入方。通过开放 API，商户可在自己绑定的机器人上执行**导航、任务控制、语音播报**，并查询自己可用的**场景、任务、点位**。

---

## 1. 概述

- **Base URL**：`{API_BASE}`（由平台分配，例如 `https://your-domain.com`，下文以 `{API_BASE}` 代指）
- **接口前缀**：所有开放接口均位于 `{API_BASE}/openapi/v1` 下，即完整路径以 `/openapi/v1` 开头
- **请求方法**：全部为 `POST`，请求体使用 `application/json`
- **鉴权方式**：每个请求需携带 4 个签名请求头（见 [第 2 节](#2-鉴权机制)）
- **数据范围**：商户只能操作/查询**已绑定到本商户**的机器人及其关联的场景、任务、点位

> 列表类接口（场景/点位/任务）同样采用 POST + body，**不使用 GET 查询参数**，以保证查询条件纳入签名校验。

---

## 2. 鉴权机制

### 2.1 凭证

接入前，平台会为商户分配一对凭证：

| 凭证 | 说明 | 示例 |
|---|---|---|
| `api_key` | 商户标识，明文传输，用于路由定位商户 | `mk_xxxx...` |
| `api_secret` | 签名密钥，**仅在服务端验签时使用，绝不在网络中传输** | `sk_xxxx...` |

> `api_secret` 只在创建/重置时由平台展示一次，请妥善保管。泄露后请联系平台重置。

### 2.2 请求头

每个请求必须携带以下 4 个请求头：

| 请求头 | 说明 |
|---|---|
| `X-Api-Key` | 商户 `api_key` |
| `X-Timestamp` | 当前时间的 **秒级 Unix 时间戳**（须与服务端时钟偏差 ≤ ±300 秒） |
| `X-Nonce` | 随机字符串，**每次请求唯一**，用于防重放（同一 nonce 在 300 秒内不可重复使用） |
| `X-Signature` | 按下方规则计算的 HMAC-SHA256 签名（十六进制小写） |

### 2.3 签名算法

**待签名串**（按顺序，用 `\n` 换行拼接）：

```
{METHOD}\n{PATH}\n{TIMESTAMP}\n{NONCE}\n{BODY_SHA256_HEX}
```

| 字段 | 取值 |
|---|---|
| `METHOD` | HTTP 方法，**大写**（即固定为 `POST`） |
| `PATH` | 请求路径，**不含 query string**，如 `/openapi/v1/scenes` |
| `TIMESTAMP` | 与 `X-Timestamp` 一致 |
| `NONCE` | 与 `X-Nonce` 一致 |
| `BODY_SHA256_HEX` | **请求体原始字节**的 SHA-256 十六进制摘要；无 body 时为空串 `""` 的摘要 |

**签名**：

```
signature = lowercase( HMAC-SHA256( api_secret, 待签名串 ).hex )
```

### 2.4 关键注意事项

1. **body 必须与签名一致**：请先将请求体序列化为 JSON 字节串（如 `b'{"robot_sn":"R001"}'`），对**这串字节**计算摘要，并发送**完全相同**的字节。切勿“签名用 A，发送用 B”。
2. **空请求体也应是 `{}`**：即便接口无必填参数（如 `/scenes` 不传 `robot_sn`），请求体也应发送 `{}` 并对 `b"{}"` 计算摘要，不要发送空 body。
3. **时钟同步**：请保证调用方服务器时钟准确（建议开启 NTP）。与服务端偏差超过 300 秒将返回“请求时间戳已过期”。
4. **nonce 唯一**：建议使用 UUID 或“时间戳+随机串”。重复的 nonce 在窗口期内会被拒绝。
5. **`api_secret` 绝不出现在请求中**，仅本地用于计算签名。

### 2.5 签名示例（Python）

```python
import hashlib, hmac, json, time, uuid, requests

API_BASE = "https://your-domain.com"
API_KEY = "mk_xxxxxxxxxxxxxxxx"
API_SECRET = "sk_xxxxxxxxxxxxxxxx"

def call(path: str, payload: dict | None = None) -> dict:
    # 1. 序列化 body（保证发送字节 == 签名字节）
    body_bytes = json.dumps(payload or {}, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    # 2. 构造签名材料
    timestamp = str(int(time.time()))
    nonce = uuid.uuid4().hex
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    string_to_sign = f"POST\n{path}\n{timestamp}\n{nonce}\n{body_hash}"

    # 3. 计算签名
    signature = hmac.new(
        API_SECRET.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    # 4. 发送请求
    headers = {
        "X-Api-Key": API_KEY,
        "X-Timestamp": timestamp,
        "X-Nonce": nonce,
        "X-Signature": signature,
        "Content-Type": "application/json",
    }
    resp = requests.post(f"{API_BASE}{path}", headers=headers, data=body_bytes, timeout=10)
    return resp.json()

# 示例：获取场景列表
print(call("/openapi/v1/scenes"))

# 示例：单点导航
print(call("/openapi/v1/goto_point", {"robot_sn": "R001", "point_id": 123}))
```

### 2.6 签名示例（Shell / curl）

```bash
API_BASE="https://your-domain.com"
API_KEY="mk_xxxxxxxxxxxxxxxx"
API_SECRET="sk_xxxxxxxxxxxxxxxx"
PATH_="/openapi/v1/scenes"

BODY='{}'
TS=$(date +%s)
NONCE=$(uuidgen | tr -d '-')
BODY_HASH=$(printf '%s' "$BODY" | sha256sum | awk '{print $1}')
STRING_TO_SIGN=$(printf 'POST\n%s\n%s\n%s\n%s' "$PATH_" "$TS" "$NONCE" "$BODY_HASH")
SIGN=$(printf '%s' "$STRING_TO_SIGN" | openssl dgst -sha256 -hmac "$API_SECRET" | awk '{print $2}')

curl -X POST "$API_BASE$PATH_" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: $API_KEY" \
  -H "X-Timestamp: $TS" \
  -H "X-Nonce: $NONCE" \
  -H "X-Signature: $SIGN" \
  --data "$BODY"
```

---

## 3. 通用响应结构

所有接口返回统一 JSON 结构：

```jsonc
{
  "code": 200,            // 业务状态码：200 成功
  "msg": "成功",          // 状态描述
  "data": {               // 业务数据（OpenApiResult）
    "success": true,
    "message": "共 3 个场景",
    "data": { ... }       // 各接口的具体数据，见下
  },
  "request_id": "xxx",    // 请求追踪 ID（排障时提供）
  "err_code": null        // 业务错误码，成功时为 null
}
```

> 判断成功请用 `code == 200` 且 `data.success == true`。

### 3.1 错误响应

失败时 HTTP 状态码与 `code` 一致，`msg` 描述原因。常见如下：

| HTTP / `code` | 触发场景（典型） | `msg` 示例 |
|---|---|---|
| `401` | 缺少鉴权头 / 时间戳过期 / api_key 无效 / **签名校验失败** / nonce 重复 | `签名校验失败`、`请求时间戳已过期`、`重复的请求（nonce 已使用）` |
| `403` | 机器人未绑定到当前商户；场景未绑定到当前商户的机器人；商户已被禁用 | `该机器人未绑定到当前商户`、`该场景未绑定到当前商户的机器人` |
| `404` | 机器人 / 点位 / 任务执行记录不存在 | `机器人 R001 不存在`、`点位 123 不存在` |
| `422` | 请求参数校验失败（缺字段、类型错误） | `字段 required` |
| `500` | 服务端内部错误 | `服务器内部错误` |

排障时请把响应中的 `request_id` 一并提供给平台。

---

## 4. 接口列表

### 4.1 资源查询

#### `POST /openapi/v1/robots` — 获取商户关联机器人列表

返回当前商户**已绑定的机器人**列表（含 `id`、`name`、`sn`）。

**请求体**

```json
{}
```

**响应 `data.data`**

```json
{
  "robots": [
    { "id": 1, "name": "机器人-A", "sn": "R001" },
    { "id": 2, "name": "机器人-B", "sn": "R002" }
  ]
}
```

| 字段 | 说明 |
|---|---|
| `id` | 机器人 ID |
| `name` | 机器人名称 |
| `sn` | 机器人序列号（后续控制类接口的 `robot_sn`） |

---

#### `POST /openapi/v1/scenes` — 获取场景列表

返回当前商户**可访问的场景地图**（即其机器人所绑定的地图，去重）。

**请求体**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `robot_sn` | string | 否 | 传入时仅返回该机器人绑定的场景 |

```json
{}
```

**响应 `data.data`**

```json
{
  "scenes": [
    { "id": 1, "name": "一层大厅", "width": 1000, "height": 800, "status": true, "version": 3 },
    { "id": 2, "name": "二层办公区", "width": 1200, "height": 900, "status": true, "version": 1 }
  ]
}
```

| 字段 | 说明 |
|---|---|
| `id` | 场景地图 ID（后续查点位、导航时使用） |
| `name` | 地图名称 |
| `width` / `height` | 地图像素宽高 |
| `status` | 启用状态：`true` 启用 |
| `version` | 地图内容版本号 |

---

#### `POST /openapi/v1/points` — 获取点位列表

返回指定场景下的全部标注点位。

**请求体**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `map_id` | int | 是 | 场景地图 ID（须属于当前商户可访问的场景，否则返回 `403`） |

```json
{ "map_id": 1 }
```

**响应 `data.data`**

```json
{
  "points": [
    { "id": 101, "name": "前台", "type": "charger", "x": 120.5, "y": 88.0, "angle": 0 },
    { "id": 102, "name": "会议室A", "type": "target", "x": 300.0, "y": 210.5, "angle": 90 }
  ]
}
```

| 字段 | 说明 |
|---|---|
| `id` | 点位 ID（`goto_point` / `navigate_route` 的 `point_id(s)` 即取此值） |
| `name` | 点位名称 |
| `type` | 标注类型（字典值） |
| `x` / `y` / `angle` | 坐标与角度（度） |

---

#### `POST /openapi/v1/tasks` — 获取任务列表

返回**关联到当前商户机器人**的任务（即商户可在其机器人上执行的任务）。

**请求体**（所有字段可选，组合过滤）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `robot_sn` | string | 否 | 传入时仅返回关联该机器人的任务 |
| `map_id` | int | 否 | 按场景地图过滤 |
| `task_type` | string | 否 | 任务类型：`patrol` 巡逻 / `broadcast` 播报 |

```json
{ "robot_sn": "R001" }
```

**响应 `data.data`**

```json
{
  "tasks": [
    {
      "id": 5001,
      "name": "早间巡逻",
      "task_type": "patrol",
      "status": "idle",
      "enabled": true,
      "map_id": 1,
      "last_run_at": "2026-06-30 08:00:00",
      "next_run_at": "2026-07-01 08:00:00"
    }
  ]
}
```

| 字段 | 说明 |
|---|---|
| `id` | 任务 ID（`execute_task` 的 `task_id` 即取此值） |
| `name` | 任务名称 |
| `task_type` | `patrol` / `broadcast` |
| `status` | `idle` / `running` / `paused` |
| `enabled` | 是否启用 |
| `map_id` | 关联场景地图（可能为 `null`） |
| `last_run_at` / `next_run_at` | 最近/下次执行时间（`yyyy-MM-dd HH:mm:ss`，上海时区，可能为 `null`） |

---

### 4.2 导航

#### `POST /openapi/v1/goto_point` — 单点导航

```json
{ "robot_sn": "R001", "point_id": 101 }
```

前往指定点位。成功时响应 `data.message` 为 `"单点导航已下发"`，`data.success` 为 `true`。

> 点位须位于机器人当前绑定的场景地图内，否则返回 `403`。

---

#### `POST /openapi/v1/navigate_route` — 多点导航

```json
{ "robot_sn": "R001", "point_ids": [101, 102, 103] }
```

按数组顺序依次途经各点位。成功时响应 `data.message` 为 `"多点导航已下发（N 个点位）"`，`data.success` 为 `true`。

---

### 4.3 任务控制

下列接口均作用于**该机器人当前活跃的执行记录**，请求体相同：

```json
{ "robot_sn": "R001" }
```

| 接口 | 行为 | 可操作的状态 | 响应 `data.data` |
|---|---|---|---|
| `POST /openapi/v1/execute_task` | 在机器人上启动/恢复指定任务（请求体额外含 `task_id`） | — | `{ "task_id": 5001, "action": "started" }` |
| `POST /openapi/v1/pause_task` | 暂停当前任务 | `running` / `pending` | `{ "record_id": 9001 }` |
| `POST /openapi/v1/resume_task` | 恢复已暂停任务 | `paused` | `{ "record_id": 9001 }` |
| `POST /openapi/v1/stop_task` | 停止当前任务 | `running` / `paused` / `pending` | `{ "record_id": 9001 }` |

`execute_task` 请求体：

```json
{ "robot_sn": "R001", "task_id": 5001 }
```

> 若机器人当前没有可操作的执行记录，返回 `404`。

---

### 4.4 语音

#### `POST /openapi/v1/speak` — 语音播报

```json
{
  "robot_sn": "R001",
  "text": "欢迎光临",
  "tts_params": { "voice": "female", "speed": 1.0, "volume": 80 }
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `robot_sn` | string | 是 | 目标机器人 |
| `text` | string | 是 | 播报文本（不可为空） |
| `tts_params.voice` | string | 否 | 音色，如 `male` / `female` |
| `tts_params.speed` | float | 否 | 语速 0.5–2.0 |
| `tts_params.volume` | int | 否 | 音量 0–100 |

> 参数未传时，依次取机器人的语音配置、系统默认值。响应 `data.success` 表示播报是否成功，`data.message` 为结果信息。

---

## 5. 典型调用流程

```
1. 获取机器人    POST /openapi/v1/robots                        → 拿到 robot_sn
2. 获取场景      POST /openapi/v1/scenes                        → 拿到 map_id
3. 获取点位      POST /openapi/v1/points   {map_id}             → 拿到 point_id 列表
4. 导航          POST /openapi/v1/goto_point {robot_sn, point_id}
   或            POST /openapi/v1/navigate_route {robot_sn, point_ids}
5. (可选) 控制   POST /openapi/v1/pause_task / resume_task / stop_task {robot_sn}
6. (可选) 任务   POST /openapi/v1/tasks {robot_sn} → 拿到 task_id → POST /openapi/v1/execute_task
```

---

## 6. 常见问题

| 现象 | 排查方向 |
|---|---|
| `401 签名校验失败` | ① 待签名串拼接顺序/大小写错误；② body 字节与签名时不一致（重新序列化导致）；③ `path` 误带了 query string；④ `api_secret` 错误或已被重置 |
| `401 请求时间戳已过期` | 调用方时钟偏差 > 300 秒，请同步 NTP |
| `401 重复的请求（nonce 已使用）` | nonce 在 300 秒窗口内重复，请确保每次请求唯一 |
| `403 该机器人未绑定到当前商户` | `robot_sn` 不属于本商户，请联系平台核对绑定关系 |
| `403 该场景未绑定到当前商户的机器人` | `/points` 的 `map_id` 不在商户可访问场景内 |
| `404 点位 X 不存在` | `point_id` 无效，或点位已被删除 |

---

## 7. 变更记录

| 日期 | 内容 |
|---|---|
| 2026-07-13 | `/openapi/v1/tasks` 移除 `status` 执行状态过滤条件；修正导航接口响应说明与时间字段格式说明 |
| 2026-07-01 | 新增场景/点位/任务列表接口（`/scenes`、`/points`、`/tasks`） |
