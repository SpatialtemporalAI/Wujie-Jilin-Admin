# 商户开放 API 接入文档

> 版本：v1 ｜ 基础路径：`/openapi/v1` ｜ 鉴权方式：HMAC-SHA256 签名

本开放 API 面向第三方商户，通过商户凭证（`api_key` / `api_secret`）驱动机器人完成导航、任务执行与控制、语音播报等能力。

***

## 1. 接入流程

1. **由平台管理员在后台创建商户**（系统管理 → 商户管理 → 新增）。
   - 创建成功后会**一次性**返回 `api_key` 与 `api_secret`，请**立即复制妥善保存**。
   - `api_secret` 仅在创建/重置时展示一次；遗忘后只能在后台「重置密钥」重新生成（旧密钥立即失效）。
2. **为商户绑定可操作的机器人**（商户管理 → 编辑 → 绑定机器人）。开放 API 只能操作已绑定到该商户的机器人。
3. 使用 `api_key` + `api_secret` 按 [第 3 节](#3-鉴权机制) 规则对每个请求签名后调用接口。

***

## 2. 通用约定

| 项目   | 说明                                                   |
| ---- | ---------------------------------------------------- |
| 传输   | HTTPS（生产）/ HTTP（本地），`Content-Type: application/json` |
| 编码   | UTF-8                                                |
| 基础路径 | `/openapi/v1`                                        |
| 时间戳  | **秒级** Unix 时间戳（10 位），与服务端偏差不得超过 ±300 秒              |
| 请求体  | JSON；签名时使用**实际发送的原始字节**                              |

### 2.1 统一响应结构

```json
{
  "code": 200,
  "msg": "Success",
  "data": {
    "success": true,
    "message": "任务已启动",
    "data": { "task_id": 123456, "action": "started" }
  },
  "request_id": "xxxxxxxx",
  "err_code": null
}
```

- `code`：HTTP 状态码（200 成功；401/403/404/409 等为失败）。
- `data.success`：业务是否真正成功（例如播报命令是否成功下发到设备）。
- `data.message`：附加说明。
- `data.data`：附加数据（如任务/记录 ID）。

### 2.2 错误码

| HTTP code | 场景                                                       |
| --------- | -------------------------------------------------------- |
| 401       | 缺少鉴权头 / 时间戳过期 / 无效 API Key / 签名错误 / nonce 重复（重放）/ 凭证解析失败 |
| 403       | 商户已禁用 / 机器人未绑定到当前商户 / 点位不在机器人所在地图                        |
| 404       | 机器人 / 点位 / 任务 / 可操作的任务执行记录不存在                            |
| 409       | 状态冲突（例如暂停一个非运行中的任务）                                      |
| 422       | 参数校验失败：类型不符 / 取值越界 / 枚举非法（如 `task_type` 非 `patrol`·`broadcast`、`volume` 超出 0–100） |

***

## 3. 鉴权机制（HMAC-SHA256）

### 3.1 请求头

每个请求都必须携带以下 4 个头：

| Header        | 说明                   |
| ------------- | -------------------- |
| `X-Api-Key`   | 商户的 `api_key`        |
| `X-Timestamp` | 秒级 Unix 时间戳          |
| `X-Nonce`     | 随机字符串（单次唯一，建议 16+ 位） |
| `X-Signature` | 计算出的签名（见 3.2）        |

### 3.2 签名算法

**第 1 步**：构造待签名串（各项用 `\n` 换行连接，共 5 段）：

```
{HTTP_METHOD}\n{请求路径}\n{时间戳}\n{nonce}\n{请求体的 SHA-256 十六进制摘要}
```

- `HTTP_METHOD`：大写，如 `POST`
- `请求路径`：不含 query string，如 `/openapi/v1/speak`
- `请求体的 SHA-256`：对**实际发送的原始请求体字节**做 SHA-256，取十六进制小写；无 body 时为空串的摘要

**第 2 步**：用 `api_secret` 作为 key，对待签名串做 HMAC-SHA256，取十六进制小写即为 `X-Signature`。

> ⚠️ 关键：用于签名的请求体字节必须与实际 HTTP 发送的字节**完全一致**。请先将 JSON 序列化为字节，再用同一份字节计算摘要并发送，避免框架二次序列化导致空格/顺序不一致。

### 3.3 防重放

- 时间戳偏差超过 ±300 秒 → 拒绝。
- 同一 `nonce` 在有效窗口内只能使用一次，重复使用 → 拒绝（防重放）。

***

## 4. 接口列表

> 所有接口均为 `POST`，请求体均为 JSON。
>
> - **控制类接口**（导航 / 任务 / 语音播报）：必须包含 `robot_sn`（目标机器人序列号，须已绑定到当前商户）。
> - **查询类接口**（场景 / 点位 / 任务列表）：`robot_sn` 为可选过滤条件，详见各接口说明。

### 4.1 单点导航 — `POST /openapi/v1/goto_point`

驱动机器人前往指定点位。

**请求体**

| 字段        | 类型     | 必填 | 说明             |
| --------- | ------ | -- | -------------- |
| robot\_sn | string | 是  | 目标机器人序列号       |
| point\_id | int    | 是  | 目标点位 ID（地图标注点） |

**响应 data**

```json
{ "success": true, "message": "单点导航已下发" }
```

- `success`：导航指令是否成功下发到设备。
- 单点/多点导航为**即时指令**，不再创建任务，因此不返回 `task_id` / `record_id`。

> 约束：点位必须位于该机器人绑定的场景地图上。

### 4.2 多点导航 — `POST /openapi/v1/navigate_route`

驱动机器人按顺序途经多个点位。

**请求体**

| 字段         | 类型     | 必填 | 说明                |
| ---------- | ------ | -- | ----------------- |
| robot\_sn  | string | 是  | 目标机器人序列号          |
| point\_ids | int\[] | 是  | 途经点位 ID 列表（按顺序执行） |

**响应 data**

```json
{ "success": true, "message": "多点导航已下发（3 个点位）" }
```

- 即时指令，不创建任务、不返回 `task_id` / `record_id`。

### 4.3 执行任务 — `POST /openapi/v1/execute_task`

在指定机器人上启动（或恢复已暂停的）已有任务。

**请求体**

| 字段        | 类型     | 必填 | 说明       |
| --------- | ------ | -- | -------- |
| robot\_sn | string | 是  | 目标机器人序列号 |
| task\_id  | int    | 是  | 任务 ID    |

**响应 data**

```json
{ "success": true, "message": "任务已启动", "data": { "task_id": 10, "action": "started" } }
```

> `action` 固定为 `"started"`（启动后只下发 gRPC `run_now`，不再创建执行记录、不再区分新建/恢复、不返回 `record_id`）。

### 4.4 暂停任务 — `POST /openapi/v1/pause_task`

暂停该机器人当前运行中/等待中的任务。

**请求体**：`{ "robot_sn": "WJ-001" }`

**响应 data**：`{ "success": true, "message": "任务已暂停", "data": { "record_id": 456 } }`

### 4.5 恢复任务 — `POST /openapi/v1/resume_task`

恢复该机器人已暂停的任务。

**请求体**：`{ "robot_sn": "WJ-001" }`

**响应 data**：`{ "success": true, "message": "任务已恢复", "data": { "record_id": 456 } }`

### 4.6 停止任务 — `POST /openapi/v1/stop_task`

停止该机器人当前任务（运行中/已暂停/等待中）。

**请求体**：`{ "robot_sn": "WJ-001" }`

**响应 data**：`{ "success": true, "message": "任务已停止", "data": { "record_id": 456 } }`

### 4.7 语音播报 — `POST /openapi/v1/speak`

让机器人播报一段文本。

**请求体**

| 字段          | 类型     | 必填 | 说明         |
| ----------- | ------ | -- | ---------- |
| robot\_sn   | string | 是  | 目标机器人序列号   |
| text        | string | 是  | 播报文本       |
| tts\_params | object | 否  | TTS 参数（见下） |

`tts_params`

| 字段     | 类型     | 说明                     |
| ------ | ------ | ---------------------- |
| voice  | string | 音色，如 `male` / `female` |
| speed  | number | 语速 0.5–2.0             |
| volume | int    | 音量 0–100               |

> 未提供 `tts_params` 时，使用机器人在系统中配置的默认 TTS 参数；仍无则使用系统默认（female / 1.0 / 80）。
>
> `speed` / `volume` 会做范围校验，超出 0.5–2.0 / 0–100 返回 422。

**请求示例**

```json
{
  "robot_sn": "WJ-001",
  "text": "欢迎光临",
  "tts_params": { "voice": "female", "speed": 1.0, "volume": 80 }
}
```

**响应 data**：`{ "success": true, "message": "播报成功" }`（`success` 反映设备是否真正响应）

### 4.8 机器人列表 — `POST /openapi/v1/robots`

获取当前商户已绑定的机器人列表。

**请求体**

```json
{}
```

**响应 data**

```json
{
  "success": true,
  "message": "共 2 个机器人",
  "data": {
    "robots": [
      { "id": 1, "name": "机器人-A", "sn": "WJ-001" },
      { "id": 2, "name": "机器人-B", "sn": "WJ-002" }
    ]
  }
}
```

| 字段   | 类型     | 说明                       |
| ------ | -------- | -------------------------- |
| id     | int      | 机器人 ID                  |
| name   | string   | 机器人名称                 |
| sn     | string   | 机器人序列号（控制类接口的 `robot_sn`） |

### 4.9 场景列表 — `POST /openapi/v1/scenes`

获取当前商户可访问的场景地图列表（即其绑定的机器人所在的场景地图）。

**请求体**

| 字段        | 类型     | 必填 | 说明                                  |
| --------- | ------ | -- | ----------------------------------- |
| robot\_sn | string | 否  | 传入时只返回该机器人绑定的场景；不传则返回商户全部可访问场景（去重） |

**响应 data**

```json
{
  "success": true,
  "message": "共 2 个场景",
  "data": {
    "scenes": [
      { "id": 1, "name": "一楼大厅", "width": 1000, "height": 800, "status": true, "version": 3 }
    ]
  }
}
```

| 字段       | 类型     | 说明                          |
| -------- | ------ | --------------------------- |
| id       | int    | 场景地图 ID（用于 `points` 接口的 `map_id`） |
| name     | string | 场景名称                        |
| width    | int    | 地图宽度（像素）                    |
| height   | int    | 地图高度（像素）                    |
| status   | boolean | 地图状态：`true` 启用 / `false` 停用 |
| version  | int    | 地图版本号                       |

### 4.10 点位列表 — `POST /openapi/v1/points`

获取指定场景下的全部点位（地图标注点），用于 `goto_point` / `navigate_route` 的 `point_id` 取值。

**请求体**

| 字段     | 类型 | 必填 | 说明                                |
| ------ | -- | -- | --------------------------------- |
| map_id | int | 是  | 场景地图 ID（须属于当前商户可访问的场景，否则返回 403） |

**响应 data**

```json
{
  "success": true,
  "message": "共 5 个点位",
  "data": {
    "points": [
      { "id": 12, "name": "前台", "type": "spot", "x": 120.5, "y": 340.0, "angle": 0 }
    ]
  }
}
```

| 字段     | 类型     | 说明                       |
| ------ | ------ | ------------------------ |
| id     | int    | 点位 ID（即导航接口的 `point_id`） |
| name   | string | 点位名称                     |
| type   | string | 标注类型                     |
| x      | number | X 坐标                     |
| y      | number | Y 坐标                     |
| angle  | number | 朝向角度（度）                  |

### 4.11 任务列表 — `POST /openapi/v1/tasks`

获取关联到当前商户机器人的任务列表，可按机器人 / 场景 / 类型 / 状态过滤。返回的 `id` 可用于 `execute_task`。

**请求体**

| 字段         | 类型     | 必填 | 说明                                       |
| ---------- | ------ | -- | ---------------------------------------- |
| robot\_sn  | string | 否  | 仅返回关联该机器人的任务；不传则返回商户全部机器人关联的任务           |
| map\_id    | int    | 否  | 按场景地图过滤                                  |
| task\_type | string | 否  | 任务类型：`patrol`（巡逻）/ `broadcast`（播报）       |
| status     | string | 否  | 执行状态：`idle`（空闲）/ `running`（运行中）/ `paused`（已暂停） |

> `task_type` / `status` 传非枚举值（如 `xxx`）会被拦截并返回 422；传空值或缺省视为不过滤。

**响应 data**

```json
{
  "success": true,
  "message": "共 3 个任务",
  "data": {
    "tasks": [
      {
        "id": 10,
        "name": "日间巡楼",
        "task_type": "patrol",
        "status": "idle",
        "enabled": true,
        "map_id": 1,
        "last_run_at": "2026-07-06T09:30:00+08:00",
        "next_run_at": "2026-07-06T15:00:00+08:00"
      }
    ]
  }
}
```

| 字段           | 类型      | 说明                          |
| ------------ | ------- | --------------------------- |
| id           | int     | 任务 ID（即 `execute_task` 的 `task_id`） |
| name         | string  | 任务名称                        |
| task\_type   | string  | `patrol` / `broadcast`      |
| status       | string  | `idle` / `running` / `paused` |
| enabled      | boolean | 是否启用                        |
| map\_id      | int     | 关联场景地图 ID                   |
| last\_run\_at | string  | 最近一次开始执行时间（ISO 8601，可能为 null） |
| next\_run\_at | string  | 下次计划执行时间（ISO 8601，可能为 null） |

> 仅返回 `enabled` 状态可由商户控制的任务；查询结果只包含已绑定到当前商户机器人的任务，不会泄露其他商户数据。

***

## 5. 完整调用示例

### 5.1 Python

```python
import hashlib, hmac, json, time, secrets
import requests

API_KEY = "mk_xxxxxxxxxxxxxxxx"
API_SECRET = "sk_xxxxxxxxxxxxxxxx"
BASE = "https://your-host"  # 替换为平台地址


def call(path: str, body: dict) -> dict:
    raw = json.dumps(body, separators=(",", ":")).encode("utf-8")  # 与发送字节一致
    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(8)
    body_hash = hashlib.sha256(raw).hexdigest()
    string_to_sign = f"POST\n{path}\n{timestamp}\n{nonce}\n{body_hash}"
    signature = hmac.new(
        API_SECRET.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    resp = requests.post(
        BASE + path,
        data=raw,
        headers={
            "Content-Type": "application/json",
            "X-Api-Key": API_KEY,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
            "X-Signature": signature,
        },
        timeout=10,
    )
    return resp.json()


# 语音播报
print(call("/openapi/v1/speak", {"robot_sn": "WJ-001", "text": "你好"}))

# 单点导航
print(call("/openapi/v1/goto_point", {"robot_sn": "WJ-001", "point_id": 12}))

# 多点导航
print(call("/openapi/v1/navigate_route", {"robot_sn": "WJ-001", "point_ids": [12, 13, 14]}))

# 执行任务
print(call("/openapi/v1/execute_task", {"robot_sn": "WJ-001", "task_id": 10}))

# 暂停 / 恢复 / 停止
print(call("/openapi/v1/pause_task", {"robot_sn": "WJ-001"}))
print(call("/openapi/v1/resume_task", {"robot_sn": "WJ-001"}))
print(call("/openapi/v1/stop_task", {"robot_sn": "WJ-001"}))

# 查询机器人 / 场景 / 点位 / 任务
print(call("/openapi/v1/robots", {}))                         # 商户全部机器人
print(call("/openapi/v1/scenes", {}))                         # 商户全部可访问场景
print(call("/openapi/v1/scenes", {"robot_sn": "WJ-001"}))     # 仅某机器人绑定的场景
print(call("/openapi/v1/points", {"map_id": 1}))             # 该场景下的点位
print(call("/openapi/v1/tasks", {"robot_sn": "WJ-001", "task_type": "patrol"}))  # 过滤任务
```

### 5.2 Node.js

```js
const crypto = require('crypto');
const axios = require('axios');

const API_KEY = 'mk_xxxxxxxxxxxxxxxx';
const API_SECRET = 'sk_xxxxxxxxxxxxxxxx';
const BASE = 'https://your-host';

async function call(path, body) {
  const raw = Buffer.from(JSON.stringify(body)); // 与发送字节一致
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const nonce = crypto.randomBytes(8).toString('hex');
  const bodyHash = crypto.createHash('sha256').update(raw).digest('hex');
  const stringToSign = `POST\n${path}\n${timestamp}\n${nonce}\n${bodyHash}`;
  const signature = crypto
    .createHmac('sha256', API_SECRET)
    .update(stringToSign)
    .digest('hex');

  const resp = await axios.post(BASE + path, raw, {
    headers: {
      'Content-Type': 'application/json',
      'X-Api-Key': API_KEY,
      'X-Timestamp': timestamp,
      'X-Nonce': nonce,
      'X-Signature': signature,
    },
    timeout: 10000,
  });
  return resp.data;
}

call('/openapi/v1/speak', { robot_sn: 'WJ-001', text: '你好' }).then(console.log);
```

***

## 6. 注意事项

- **机器人授权**：每个请求的 `robot_sn` 必须是已绑定到当前商户的机器人，否则返回 403。
- **地图匹配**：`goto_point` / `navigate_route` 的点位必须位于机器人当前绑定的场景地图上，否则返回 403。
- **导航是即时指令**：单点/多点导航直接把目标点位下发给设备，**不再创建任务**，因此不返回 `task_id` / `record_id`，也无法用 `pause_task` / `resume_task` / `stop_task` 控制一次导航。若需要按任务维度暂停/恢复/停止，请改用 `execute_task` 启动已有任务，再对其控制。
- **凭证安全**：`api_secret` 等同于密码，请只在服务端保管，不要暴露在浏览器/小程序前端；建议按需设置 IP 白名单等网络层防护。
- **时间同步**：请确保调用方服务器时间准确（NTP），否则时间戳校验会失败。

***

## 7. 变更记录

| 日期         | 说明                                                                                                                                                                            |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-06-29 | v1 首版：goto\_point / navigate\_route / execute\_task / pause\_task / resume\_task / stop\_task / speak                                                                         |
| 2026-07-03 | 导航改为即时指令：`goto_point` / `navigate_route` 不再创建任务，响应移除 `task_id` / `record_id`，文案改为「单点/多点导航已下发」；`execute_task` 的 `action` 统一为 `"started"`（不再区分 created/resumed，不返回 record\_id）。 |
| 2026-07-06 | 新增查询类接口：`scenes`（场景列表）/ `points`（点位列表）/ `tasks`（任务列表），支持按机器人 / 场景 / 任务类型 / 状态过滤；第 4 节总述拆分为控制类（必须 `robot_sn`）与查询类（`robot_sn` 可选）。 |
| 2026-07-06 | 补充参数类型校验：`tasks.task_type` 限 `patrol`·`broadcast`、`tasks.status` 限 `idle`·`running`·`paused`（非法值 422）；`speak.tts_params.speed` 限 0.5–2.0、`volume` 限 0–100（越界 422）；错误码表新增 422。 |

