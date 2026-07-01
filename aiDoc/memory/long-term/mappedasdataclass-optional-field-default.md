# MappedAsDataclass 模型的 Optional 字段必须写 default=None

**适用范围**：全项目所有业务 ORM 模型（均继承 `Base` → `DataClassBase(MappedAsDataclass, MappedBase)`，见 `backend/database/models/base.py`）。

## 约束

项目 ORM 用 SQLAlchemy 2.0 原生 dataclass 映射（`MappedAsDataclass`），其 `__init__` 由 dataclass 生成：

- `Mapped[str | None]` **只是类型注解，不提供 dataclass 默认值**。
- Optional 字段若不在 `mapped_column(...)` 里显式写 `default=None`（或 `init=False` / `default_factory=...`），会被 dataclass 当作**必填位置参数**。
- 后果：实例化时不传该字段 → `TypeError: __init__() missing N required positional arguments: '<field>'`，接口直接 500。

## 正确写法

```python
entity_id: Mapped[str | None] = mapped_column(
    String(64), nullable=True, default=None, comment="阿里云人脸库实体ID"
)
```

- 非空必填字段（`Mapped[str]` + `nullable=False`）无需 default，dataclass 必填符合语义。
- 审计字段（`id` / `created_at` / `updated_at` / `deleted_at`）在 `base.py` 的 `LogicMixin` / `DateTimeMixin` 里已是 `init=False`，不进 `__init__`，无需处理。

## 字段顺序

dataclass 要求**无默认字段在前、有默认字段在后**。新增带 `default=None` 的 Optional 字段应放在所有必填字段之后，否则触发 dataclass 字段顺序错误。

## 典型案例

- 2026-07-01：`POST /robot/config/face` 500。`RobotFaceRecognition` 的 `entity_id` / `face_id` 是 Optional 却漏写 `default=None`；而 `RobotConfigService.create_face` 需先 `db.flush()` 拿 `face.id` 作 `entity_id`、注册阿里云后回填这两个字段（创建时不传）→ 报 `missing 2 required positional arguments: 'entity_id' and 'face_id'`。修复：补 `default=None`（见 `backend/database/models/business/robot_face_recognition.py`）。`nullable=True` 未变，**无需数据库迁移**。

## 如何排查

接口 500 且日志含 `TypeError: __init__() missing N required positional arguments: '<field>'` → 检查该模型对应字段是否为 Optional 却漏写 `default=None`。
