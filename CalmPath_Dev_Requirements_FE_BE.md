# CalmPath 开发需求精简版(前端 / 后端)

> 基于 `CalmPath_App_Development_Requirements.md` 精简,只保留代码实现相关内容,略去背景、人物画像、商业决策、风险清单等。

技术栈:**React Native (Expo) + FastAPI + PostgreSQL/PostGIS**

---

## 一、前端(React Native / Expo)

### 1.1 技术选型

- React Native + TypeScript
- Expo(构建/开发平台)
- Expo Router(导航)
- TanStack Query 或同类库(服务端状态管理)
- Zod 或同类库(客户端响应校验)
- 尽量使用 OpenAPI 生成的客户端类型

### 1.2 页面清单

| 页面 | 作用 | 范围 |
|---|---|---|
| `PreferenceSetupScreen` | 选择低/中/高拥挤敏感度 | 仅原型(除非 US 1.3 转正) |
| `DestinationScreen` | 选择起点/终点 | MVP |
| `RouteResultsScreen` | 路线对比、标签、时长、解释 | MVP |
| `RouteMapScreen` | 查看路线与拥挤路段 | MVP |
| `QuietPlacesScreen` | 选择附近庇护候选点 | Stretch |
| `QuietPlaceDetailScreen` | 查看地点详情与到达路线 | Stretch |

### 1.3 表单与交互(对应 FR-01)

- 起点/终点必须可选或可输入,坐标或受控地点 ID。
- 终点必须校验在配置的 CBD 服务范围内。
- 客户端和后端都要做输入校验。
- 校验失败时显示字段级错误,**不能清空用户已填内容**。
- 提交按钮要有 loading 状态,并阻止重复提交。

### 1.4 路线结果展示(对应 FR-07)

每张路线卡片必须展示:

- 路线名称
- 预计时长
- 距离(有意义时展示)
- `Low Sensory` / `High Sensory` / `Sensory information unavailable` 文字
- 是否为推荐路线
- 简短推荐理由
- 行人数据的更新时间/新鲜度状态

### 1.5 路线地图与详情(对应 FR-08)

- 显示选中路线、起点、终点。
- 拥挤路段必须在地图上可识别。
- 必须同时提供等价的文字信息(**地图不能是唯一信息来源**)。
- 用户可返回路线对比页。

### 1.6 展示规则(硬性约束,直接影响 UI 实现)

- 感官等级**必须用文字表达**,颜色/图标只能作为辅助,不能只靠红绿区分。
- 数据不足时必须显示 `Sensory information unavailable`,不能自行猜测等级。
- 全部路线都拥挤时,需明确说明"推荐路线并非无拥挤"。

### 1.7 无障碍(Accessibility)

- 可交互区域最小 44×44 点。
- 支持动态字号,不裁切关键内容。
- 文字与背景对比度达到 WCAG 2.1 AA。
- 每个图标、路线标签、地图标记、操作都要有无障碍标签(accessible label)。
- 焦点顺序与视觉阅读顺序一致。
- 支持用户的"减少动效"偏好设置。
- 界面避免闪烁、意外位移和不必要的刺激。
- 核心流程需支持键盘导航与屏幕阅读器(在支持的平台上)。

### 1.8 客户端状态管理

- 服务端响应、缓存、重试、新鲜度 → 作为 server state 管理(如 TanStack Query)。
- 已选路线、临时界面值 → 本地 client state。
- **默认不持久化精确的出行历史**。
- 渲染异常需被 Error Boundary 捕获,并提供恢复操作(而非白屏)。

### 1.9 前端需处理的错误/边界状态

| 情况 | 前端行为 | 恢复操作 |
|---|---|---|
| 某条路线无可用数据 | 显示 `Sensory information unavailable`,不展示基于感官的推荐 | 查看其他路线或重试 |
| 所有路线都拥挤 | 说明"所有路线均有拥挤",标出相对更优的一条 | 对比并选择 |
| 终点无效/超出 CBD | 字段级校验错误,保留已填内容 | 修改终点 |
| 开放数据源不可用 | 显示数据新鲜度与"暂不可用"提示 | 使用仍有效的缓存快照或稍后重试 |
| 无可用步行路线 | 说明未找到路线 | 修改起点/终点 |
| 附近无庇护地点 | 显示空状态,不能编造地点 | 扩大搜索范围或返回路线 |

### 1.10 前端测试要求

- 覆盖 loading / success / empty / 数据不可用 / 重试 五种状态。
- 校验感官文字信息存在(不依赖颜色判断)。
- 推荐及解释内容与 API 响应一致。
- 键盘焦点顺序、屏幕阅读器标签。
- 大字号、减少动效、色盲模拟、弱网行为。
- 重复提交被阻止。
- 工具链:ESLint、Prettier、TypeScript、Jest、React Native Testing Library。

---

## 二、后端(FastAPI)

### 2.1 职责

- 用 Pydantic 校验所有客户端输入。
- 校验配置的服务边界(CBD)。
- 编排:路由服务商、行人数据仓库、分类规则、推荐解释。
- 提供稳定的、带版本号的 REST API。
- 运行/协调定时的开放数据同步任务。
- 提供结构化日志、健康检查、指标、OpenAPI 文档。
- 日志中不暴露内部错误、SQL、凭证、精确用户位置。

### 2.2 API 端点

| 方法与路径 | 作用 | 主要响应 |
|---|---|---|
| `GET /api/v1/health` | 存活/就绪检查 | API、数据库、数据新鲜度状态 |
| `POST /api/v1/routes/compare` | 生成并对比候选路线 | 路线列表、推荐、解释、数据快照 |
| `GET /api/v1/routes/{route_id}` | 获取路线详情 | 路线分段、传感器覆盖、解释 |
| `GET /api/v1/refuges` | 按路线/坐标搜索庇护候选点 | 地点摘要(Stretch) |
| `GET /api/v1/refuges/{place_id}` | 获取庇护地点详情 | 地点、分类、地址、设施、来源(Stretch) |
| `POST /internal/data-sync` | 触发受保护的同步任务 | 仅内部使用,不对外暴露 |

### 2.3 `routes/compare` 返回字段(每条路线至少包含)

```
id, name, duration_minutes, distance_meters, geometry,
sensory_level, crowd_score (数据不可用时为 null),
data_coverage, is_recommended, explanation,
congested_segments, data_updated_at, rule_version
```

### 2.4 错误码表

| HTTP 状态 | 错误码 | 含义 |
|---|---|---|
| 400 | `INVALID_LOCATION` | 坐标无效,或起点终点相同 |
| 422 | `OUTSIDE_SERVICE_AREA` | 终点超出配置的 CBD 边界 |
| 404 | `NO_ROUTE_FOUND` | 没有可用的候选步行路线 |
| 429 | `RATE_LIMITED` | 超出请求限流 |
| 503 | `DATA_SOURCE_UNAVAILABLE` | 没有足够新鲜的开放数据快照 |
| 500 | `INTERNAL_ERROR` | 通用生产错误,不暴露内部实现细节 |

### 2.5 核心业务逻辑(FR-02 ~ FR-06)

**候选路线生成**
- 合法请求至少返回1条路线,目标是2条供对比。
- 路由服务商要用 adapter 隔离,方便替换而不改客户端 API。
- 若正式路由服务商未确定,可用一组受控的演示路线支撑 MVP。
- 同一次对比中的所有路线,必须用同一份数据快照 + 同一分类规则版本。

**行人数据接入**
- 接入 City of Melbourne 行人传感器位置数据。
- 接入最新的分钟级/小时级行人计数。
- 每条导入记录要保留来源、观测时间、同步批次、质量状态。
- 同步任务必须幂等、可安全重试。
- 导入不完整时,不能覆盖上一次成功的有效快照。

**路线-传感器匹配**
- 候选路线拆分为可分析的分段(segment)。
- 配置距离内的有效传感器与该分段关联。
- 记录每条路线使用的传感器数量与数据覆盖率。
- 超过最大配置时效的观测数据不能用于分类。
- 无传感器覆盖的区域**不能默认判定为低感官**。

**感官分类规则(纯规则引擎,非 ML)**

| 分类 | 规则 |
|---|---|
| Low Sensory | 数据覆盖率达标 且 拥挤分数低于配置阈值 |
| High Sensory | 数据覆盖率达标 且 拥挤分数≥配置阈值 |
| Unavailable | 数据不足、不够新或无效 |

阈值、最小覆盖率、最大数据时效、当前规则版本号必须作为配置存储,并有自动化测试覆盖。

**推荐逻辑**
- 推荐拥挤分数最低的有效路线。
- 响应中必须解释推荐原因。
- 不能仅因为"更快"就推荐拥挤度更高的路线。
- 全部路线拥挤时,标出相对更优的一条,并明确说明它并非无拥挤。
- 感官数据不可用的路线不能给出基于感官的推荐。

### 2.6 数据库(PostgreSQL + PostGIS)

**核心表**

| 表 | 关键字段 | 用途 |
|---|---|---|
| `data_sources` | `id, name, url, licence, refresh_interval` | 开放数据源注册表 |
| `sync_runs` | `id, source_id, 时间戳, status, row_count, error` | 同步审计 |
| `pedestrian_sensors` | `id, external_id, name, geom, active` | 传感器位置 |
| `pedestrian_observations` | `sensor_id, observed_at, count, interval, quality_flag, sync_run_id` | 行人计数时序数据 |
| `places` | `id, 来源标识, name, category, address, geom, metadata` | 地标/庇护候选点 |
| `route_requests` | `id, origin, destination, snapshot, rule_version` | 可选的短期匿名请求审计 |
| `route_options` | `id, request_id, duration, distance, geom, score, level, coverage, recommended` | 路线对比结果 |
| `route_segments` | `id, route_id, sequence, geom, score, level, sensor_count` | 可解释的分段分析 |
| `classification_rules` | `version, threshold, min_coverage, max_data_age, active` | 版本化规则配置 |

**约束与索引**

- `pedestrian_observations` 上 `(sensor_id, observed_at)` 唯一约束。
- 行人计数不能为负数。
- 空间列使用 SRID 4326(除非有文档说明需要投影坐标系)。
- 空间列需要 GiST 索引。
- 观测表需要 `(sensor_id, observed_at DESC)` 索引。
- 时间统一用 `timestamptz`(UTC 存储),API 返回 ISO 8601。
- API 数据库角色**不能有 schema 迁移权限**。
- 数据库迁移用 Alembic 管理。

**数据保留**

- 精确的路线请求与派生结果建议短期保留(建议 24 小时),或在不需要时关闭。
- 分析统计应使用聚合数据,而非可识别的行程历史。
- 日志中坐标需移除或降低精度。

### 2.7 安全要求

- 校验并限制坐标、文本输入、请求体大小、请求频率。
- 使用 SQLAlchemy 参数化查询。
- CORS 显式配置开发/生产环境的允许来源。
- 部署环境强制 HTTPS。
- 不暴露堆栈信息、SQL、连接字符串、服务商凭证。
- CI 中运行 Bandit、前端 lint、依赖漏洞扫描。
- 存在未解决的高危问题时阻止合并。

### 2.8 后端测试要求

- 分类逻辑:低于/等于/高于阈值三种情况。
- 数据覆盖率:刚好低于/刚好等于最小值。
- 观测时效:刚好在/刚好超出最大时效边界。
- 负数计数、重复观测、非法时间戳、未来时间戳。
- 单条路线不可用、全部不可用、全部拥挤三种场景。
- 验证"更快但更拥挤"的路线不会被误推荐。
- 服务边界校验。
- 限流与生产环境安全错误响应。
- 工具链:Ruff/Flake8、Black、mypy、Pytest、数据库集成测试。

---

## 三、前后端共享的接口契约要点

- 前端使用 OpenAPI 生成的类型消费后端接口,双方需做 OpenAPI contract 校验(CI 中检查)。
- `POST /api/v1/routes/compare` 是核心接口,字段结构见 2.3,前端 `RouteResultsScreen` / `RouteMapScreen` 直接依赖该结构渲染。
- 错误码(2.4)前端需要逐一处理并映射为对应的 UI 状态(见 1.9)。
