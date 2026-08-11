# Chalksmith v2 重构计划

> 状态：代码重构完成；GCP 资源开通、数据迁移与生产切流待执行
> 目标版本：v2
> 基准版本：`v1.0`
> 最后更新：2026-08-11

## 0. 实施状态

截至 2026-08-11：

- [x] `v1.0` 已存在于远端，可作为重构回滚基线。
- [x] 2026-08-10 曾在具备 `gcloud` CLI 与 Application Default Credentials 的环境中验证可以访问项目 `gemini-code-shark`；当前审计环境未安装 `gcloud`，本轮未重复验证。
- [x] 已完成 `backend/app/` v2 后端、统一 POST SSE、课程 CRUD、租户隔离、PDF、GCS、Signed URL、Gemini/OpenAI Adapter 和隔离 Renderer 入口。
- [x] 已完成 Identity Platform 前端登录、注册、重置反馈、退出、Google/Microsoft/邮箱密码凭据关联、冲突凭据安全续接和 Bearer Token 直连 API。
- [x] 已删除 Clerk、Next lesson API 代理、Remotion、v1 后端、daemontools 和 `backend/static/` 持久化内容；历史由 `v1.0` 保留。
- [x] 已完成 Cloud SQL/GCS 数据迁移脚本、三个容器镜像、Cloud Build 和最小权限 GCP 部署脚本。
- [x] 已使用 uv/CPython 3.12 锁定依赖；22 项后端测试、前端严格 TypeScript 检查和 Next.js production build 通过。
- [ ] 当前环境无法确认生产 GCP 权限与资源状态；仍需在具备 `gcloud` 的受信环境中完成权限预检、资源开通、真实 Provider smoke test、数据迁移和切流验收。

本地后端安装、入口与测试命令（API 和 renderer 分别在独立终端运行）：

```bash
uv sync --project backend --extra video
uv run --project backend uvicorn backend.app.main:app --reload
uv run --project backend uvicorn backend.app.renderer_main:renderer_app --reload --port 8081
uv run --project backend python -m unittest discover -s backend/tests
```

后端虚拟环境统一由 uv 管理：`backend/pyproject.toml` 是唯一依赖源，`backend/uv.lock` 锁定解析结果，`backend/.python-version` 固定 Python 3.12，环境位于被 Git 忽略的 `backend/.venv/`。Manim 放在 `video` extra 中，本地完整调试环境和 renderer 镜像会安装该 extra，生产 API 镜像不会安装；旧 `requirements.txt` 已删除。

## 1. 重构目标

这次重构的首要目标不是增加功能，而是减少代码层级、运行服务和维护成本，同时为 Google Cloud 部署建立清晰边界。

具体目标：

- 保留 Chalksmith 的核心能力：输入主题或资料，生成交互、幻灯片和视频课程。
- 前端只负责页面、交互、身份令牌和结果展示。
- 后端统一使用 Python，负责业务逻辑、LLM 调用、渲染编排、数据库和文件存储。
- 将当前多个 Next.js API 代理收敛为一个前端 API Client，浏览器直接调用 FastAPI。
- 将 LLM 调用收敛到统一 Provider 接口；默认使用 Google AI Studio Key 调用 Gemini Developer API，也可仅通过配置切换到 OpenAI GPT。
- 将数据库收敛为 Cloud SQL PostgreSQL。
- 将所有生成文件迁移到 Cloud Storage，不依赖容器本地 `static/` 目录。
- 使用 Google Cloud Identity Platform 管理最终用户身份，移除 Clerk Webhook 和用户同步逻辑。
- 初期保持同步流式生成，不立即引入消息队列、微服务或 Kubernetes。
- 对生成代码的执行建立明确安全边界，避免让不可信代码长期运行在拥有数据库权限的 API 容器中。

## 2. 不在本次范围内

- 不增加订阅、配额、Stripe 或复杂计费功能。
- 不引入 GKE、Terraform、多区域数据库、服务网格或事件驱动微服务。
- 不在前端开放任意 Provider、模型或 API Key 配置；首版由部署环境统一选择后端 Provider。
- 不实现自动故障切换、负载均衡或跨 Provider 重试，避免一次请求产生不可预测的行为和费用。
- 不重做营销页面视觉；生成 Prompt 仅补回课程结构、可读性、准确性和安全约束。

## 3. 核心技术决策

| 领域 | v2 决策 | 原因 |
|---|---|---|
| 前端 | Next.js + React + TypeScript + Tailwind CSS | 保留当前技术栈，避免无收益重写 |
| 后端 | Python 3.12 + FastAPI | 当前 LLM、PDF、Manim、SQLModel 生态均以 Python 为主 |
| ORM | SQLModel + psycopg | 延续现有模型，降低迁移成本 |
| 数据库 | Cloud SQL for PostgreSQL | 替代 Neon，统一到 GCP |
| LLM | 统一 Provider 接口；Gemini Developer API 默认、OpenAI Responses API 可选 | 业务层不感知厂商，仅通过配置切换实现 |
| 文件存储 | Cloud Storage | 替代 `backend/static/`，适配无状态容器 |
| 身份认证 | Google Cloud Identity Platform：Google、Microsoft、托管邮箱密码 | 替代 Clerk，以统一 ID Token 支持三种首版登录方式 |
| API | 浏览器直接调用 FastAPI `/v2/*` | 删除重复的 Next.js API 代理层 |
| 生成流 | `fetch()` POST + SSE 响应流 | 同时支持 Bearer Token、JSON/文件上传和进度事件 |
| 部署 | Cloud Run | 前后端分别容器化并自动缩容 |
| 配置 | Pydantic 验证模型 + Secret Manager 注入环境变量 | 复用现有依赖，只有一个配置入口，不自行读取多个 `.env` |
| 日志 | stdout 结构化日志 + Cloud Logging | 不建设单独日志服务 |

### 3.1 后端继续使用 Python

后端建议继续使用 Python，而不是改写成 Node.js：

- Manim、PyMuPDF、SQLModel 和当前生成流程已经是 Python。
- FastAPI 原生支持异步请求、流式响应、依赖注入和 OpenAPI。
- 切换语言会产生大规模无业务收益的重写。
- 移除 Remotion 后，后端不再需要为了视频渲染同时维护 Node.js 运行时。

### 3.2 输出格式收敛

v2 只保留当前用户界面真实开放的三种格式：

| API 值 | 实现 | 输出 |
|---|---|---|
| `interactive` | p5.js | HTML |
| `slides` | Reveal.js | HTML |
| `video` | Manim | MP4 |

删除隐藏的 Remotion 路径、JSON Blueprint、Remotion Player 和相关 Node 渲染依赖。若产品后续决定重新启用 Remotion，应作为独立功能提案，而不是保留半启用代码。

### 3.3 认证迁移策略

v2 首版统一启用以下三种登录方式：

| 登录方式 | Identity Platform 实现 | 首版策略 |
|---|---|---|
| Google | Google Provider | 启用，覆盖个人 Google 与 Google Workspace 账号 |
| Microsoft | Microsoft OAuth Provider | 启用，覆盖个人 Microsoft 与 Microsoft Entra ID 账号；首版不限制单一 Entra Tenant |
| Chalksmith 邮箱密码 | Identity Platform Email/Password | 启用，由 Identity Platform 保存凭据、重置密码和签发 Token |

实现参考：[Google 登录](https://cloud.google.com/identity-platform/docs/web/google)、[Microsoft 登录](https://cloud.google.com/identity-platform/docs/web/microsoft) 和 [邮箱密码登录](https://cloud.google.com/identity-platform/docs/sign-in-user-email)。

Chalksmith 保留自有品牌的登录和注册页面，但不自建密码表、密码哈希、Session 或找回密码服务。三种登录方式最后都取得相同格式的 Identity Platform ID Token，FastAPI 只验证该 Token，不为不同登录方式建立三套认证逻辑。

暂不进入首版的能力：

- 自定义账号库与 Custom Token 登录。现有需求可由托管邮箱密码覆盖，避免承担密码安全责任。
- SAML/OIDC 学校或学区 SSO。待出现明确机构客户后，作为 Identity Provider 配置扩展，不修改业务 API。
- Identity Platform Multi-tenancy。待需要按学校隔离用户、Provider 和认证策略时再启用。

账号关联必须遵循以下规则：

- 同一用户可以关联 Google、Microsoft 或邮箱密码凭据，关联后继续使用同一个 Identity Platform `uid`。
- 不得仅因为 email 相同就在后端静默合并账号；用户必须先验证已有登录方式，再显式关联新凭据。
- 前端必须处理 `account-exists-with-different-credential`，引导用户使用原方式登录后完成关联；参考 [Identity Platform account linking](https://cloud.google.com/identity-platform/docs/multi-tenancy-authentication#linking_multi-tenant_user_credentials)。
- 课程所有权只绑定稳定 `uid`，不绑定可能变化的 email 或 Provider 用户 ID。

认证迁移分两步完成：

1. 先定义统一的 `AuthUser` 和后端 Bearer Token 验证接口；过渡期允许 Clerk Adapter。
2. 配置三种首版登录方式并迁移用户与课程所有权；完成后删除 Clerk 包、Webhook、`proxy.ts` Clerk 逻辑和 `User` 同步表。

数据库中的课程所有权只存认证系统提供的稳定 `owner_id`。除非未来需要额外用户资料，否则不再建立本地 `User` 表。

```mermaid
flowchart LR
    Google["Google / Workspace"] --> Identity["Identity Platform"]
    Microsoft["Microsoft / Entra ID"] --> Identity
    Password["Chalksmith 邮箱 + 密码<br/>凭据由 Identity Platform 托管"] --> Identity
    Identity -->|统一 ID Token| Web["Next.js"]
    Web -->|Bearer Token| API["FastAPI"]
    API -->|验证 Token，取得 uid| Lessons["课程与 owner_id"]

    Future["未来：SAML / OIDC / Multi-tenancy"] -.-> Identity
```

### 3.4 Google AI Studio 与 Vertex AI 的区别

Gemini Provider 使用 Google AI Studio 中创建的 Gemini API Key，对应 **Gemini Developer API**，不是 Vertex AI：

| 项目 | Gemini Developer API | Vertex AI Gemini |
|---|---|---|
| 入口 | Google AI Studio / Gemini API | Google Cloud Vertex AI |
| 认证 | `GEMINI_API_KEY` | Service Account + ADC/IAM |
| Python Client | `genai.Client(api_key=...)` | `genai.Client(vertexai=True, project=..., location=...)` |
| 本计划 | 采用 | 暂不采用 |

两者都使用官方 `google-genai` SDK，因此以后迁移 Vertex AI 时，不需要重写 Prompt 和生成编排，只需调整 Gemini Adapter 的 Client 初始化与部署配置。

合规门槛：截至本计划日期，[Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms) 规定 Gemini Developer API 的使用者须年满 18 岁，并限制将 API Client 面向或提供给可能未满 18 岁的用户。Chalksmith 的目标受众包含中小学生，因此在正式发布前必须确认实际使用场景是否满足条款；若不满足，应切换 Vertex AI 或选择经确认适用于该场景的服务。此项属于发布阻断条件，不应仅以技术可用作为上线依据。

### 3.5 可互换的 LLM Provider

`GenerationService` 只依赖一个小型协议，不导入 Gemini 或 OpenAI SDK：

```python
from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMProvider(Protocol):
    async def generate(self, prompt: str) -> LLMResult: ...
```

- `GeminiProvider` 使用 `google-genai` 和 `GEMINI_API_KEY`。
- `OpenAIProvider` 使用官方 `openai` Python SDK、`OPENAI_API_KEY` 和 Responses API。OpenAI 当前模型文档将 Responses API 作为最新模型的调用入口之一：[OpenAI Models](https://developers.openai.com/api/docs/models)。
- 生产配置在应用启动时验证所选 Provider；`create_llm_provider(settings)` 在首次请求时创建并缓存唯一 Provider，不在每次请求中重复分支或创建 SDK Client。
- Prompt 模板、课程格式规则、自动修复流程和结果校验留在业务层；Adapter 只负责 SDK 参数转换、文本提取、Token 用量和错误标准化。
- 模型 ID 只使用 `LLM_MODEL` 配置，不在业务代码硬编码 Gemini Preview 或 GPT 型号。
- 未选中的 Provider 不要求配置对应 Key；选中的 Provider 缺少 Key 或模型时，应用启动应立即失败并给出清晰错误。
- 首版只实现 Gemini 与 OpenAI 两个显式 Adapter，不使用“OpenAI-compatible base URL”包装所有厂商；各家的结构化输出、安全设置、错误和计费语义并不完全一致。

Chalksmith 面向未成年人时还必须逐一核对所选 Provider 的条款与数据处理要求。OpenAI 的官方未成年人 API 指南要求额外的安全措施，并对未满 13 岁或当地数字同意年龄儿童的个人数据提出 Zero Data Retention 要求：[Under 18 API Guidance](https://developers.openai.com/api/docs/guides/safety-checks/under-18-api-guidance)。这属于上线合规检查，不等同于法律意见。

## 4. 目标运行架构

```mermaid
flowchart LR
    User["教师 / 学生浏览器"]

    subgraph GCP["Google Cloud Project"]
        Web["Cloud Run: web<br/>Next.js"]
        API["Cloud Run: api<br/>FastAPI"]
        Renderer["Cloud Run: renderer<br/>Manim / 无数据权限"]
        Identity["Identity Platform<br/>Google / Microsoft / 邮箱密码"]
        SQL["Cloud SQL<br/>PostgreSQL"]
        Storage["Cloud Storage<br/>PDF / HTML / MP4"]
        Secrets["Secret Manager"]
        Logs["Cloud Logging"]
        Registry["Artifact Registry"]
    end

    Provider["Configured LLM Provider"]
    Gemini["Gemini Developer API<br/>Google AI Studio Key"]
    OpenAI["OpenAI Responses API<br/>OpenAI API Key"]

    User -->|HTTPS 页面| Web
    User -->|登录| Identity
    Identity -->|ID Token| User
    User -->|Bearer Token + HTTPS| API
    API -->|统一 LLM 接口| Provider
    Provider -->|LLM_PROVIDER=gemini| Gemini
    Provider -->|LLM_PROVIDER=openai| OpenAI
    API -->|Unix Socket / psycopg| SQL
    API -->|Storage SDK| Storage
    API -->|OIDC + 生成代码| Renderer
    Renderer -->|MP4 响应| API
    Storage -->|短期 Signed URL| User
    Secrets -.->|部署时注入| API
    Web -->|stdout| Logs
    API -->|stdout| Logs
    Renderer -->|stdout/stderr| Logs
    Registry -.->|容器镜像| Web
    Registry -.->|容器镜像| API
    Registry -.->|容器镜像| Renderer
```

### 4.1 为什么浏览器直接调用 FastAPI

v1 链路是“浏览器 → Next.js API Route → FastAPI”，课程相关请求在两层重复实现。当前 v2 已改为“浏览器 → FastAPI”：

- 前端从 Identity Platform 获取 ID Token。
- `frontend/src/lib/api/client.ts` 自动加入 `Authorization: Bearer <token>`。
- FastAPI 验证 Token 并取得 `uid`。
- FastAPI CORS 只允许正式前端域名和本地开发地址。
- FastAPI 返回一致的 JSON 或 SSE 错误格式。

这样可以删除 `frontend/src/app/api/lesson-*`、`api/lessons`、`api/sources/upload` 等代理路由，也不再需要 `X-User-Id` 和 `INTERNAL_BACKEND_SECRET`。

### 4.2 生成请求采用统一 POST 流

所有生成请求都使用一个接口：

```http
POST /v2/generations
Authorization: Bearer <identity-platform-id-token>
Content-Type: multipart/form-data
Accept: text/event-stream
```

无附件和有附件不再走两套实现。前端统一使用 `fetch()` 读取响应流，因为原生 `EventSource` 无法设置 Bearer Token，也不适合上传文件。

```mermaid
sequenceDiagram
    actor User as 用户
    participant Web as Next.js
    participant Auth as Identity Platform
    participant API as FastAPI
    participant AI as Configured LLM Provider
    participant Render as Renderer
    participant DB as Cloud SQL
    participant GCS as Cloud Storage

    User->>Web: 输入主题、格式和可选 PDF
    Web->>Auth: 获取或刷新 ID Token
    Web->>API: POST /v2/generations + Bearer Token
    API->>API: 验证身份、文件和参数
    API->>DB: 创建 generating Lesson
    API-->>Web: SSE started / generating
    API->>AI: 生成摘要与代码
    AI-->>API: 结构化生成结果
    API-->>Web: SSE validating / rendering
    alt interactive / slides
        API->>API: 校验 HTML、注入 CSP、写入临时文件
    else video
        API->>Render: OIDC + Manim 代码
        Render->>Render: AST 校验并在受限进程中执行
        Render-->>API: MP4 响应
    end
    API->>GCS: 上传生成结果
    API->>DB: 更新 ready Lesson 与 object_key
    API-->>Web: SSE complete + lesson_id
    Web->>API: POST /v2/lessons/{id}/access-url
    API-->>Web: 短期 Signed URL
    Web->>GCS: 预览或下载结果
```

## 5. 当前代码结构

目录只按“页面 / API / 业务服务 / 外部集成”拆分。避免建立只有一个文件的过细抽象，也不使用泛型 Repository、事件总线或复杂领域框架。当前物理目录：

```text
.
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   │   ├── generation/page.tsx
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── globals.css
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   ├── auth/
│   │   │   ├── dashboard/
│   │   │   ├── generation/
│   │   │   └── home/
│   │   └── lib/
│   │       ├── api/
│   │       │   ├── client.ts
│   │       │   └── generation-stream.ts
│   │       ├── firebase/client.ts
│   │       ├── hooks/
│   │       │   ├── useApi.ts
│   │       │   └── useGeneration.ts
│   │       └── types/
│   │           └── api.ts
│   ├── package-lock.json
│   ├── package.json
│   └── next.config.ts
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── dependencies.py
│   │   │   ├── generations.py
│   │   │   ├── health.py
│   │   │   ├── lessons.py
│   │   │   └── schemas.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── errors.py
│   │   │   └── logging.py
│   │   ├── db/
│   │   │   ├── models.py
│   │   │   ├── lessons.py
│   │   │   └── session.py
│   │   ├── integrations/
│   │   │   ├── identity.py
│   │   │   ├── storage.py
│   │   │   └── llm/
│   │   │       ├── base.py
│   │   │       ├── factory.py
│   │   │       ├── gemini.py
│   │   │       └── openai.py
│   │   ├── renderers/
│   │   │   ├── base.py
│   │   │   ├── html.py
│   │   │   └── manim.py
│   │   ├── services/
│   │   │   ├── generation.py
│   │   │   ├── prompts.py
│   │   │   └── sources.py
│   │   ├── main.py
│   │   └── renderer_main.py
│   ├── scripts/
│   │   ├── init_db.py
│   │   └── migrate_v1.py
│   ├── tests/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── .python-version
│   └── .env.example
├── infra/
│   ├── docker/
│   │   ├── api.Dockerfile
│   │   ├── renderer.Dockerfile
│   │   └── web.Dockerfile
│   └── gcloud/
│       ├── cloudbuild-backend.yaml
│       ├── cloudbuild-web.yaml
│       ├── deploy.sh
│       └── README.md
├── AGENTS.md
├── README.md
└── REFACTOR.md
```

```mermaid
flowchart TD
    Repo["Chalksmith v2"] --> Frontend["frontend/ Next.js"]
    Repo --> Backend["backend/ FastAPI"]
    Repo --> Infra["infra/ Docker + gcloud"]

    Frontend --> Pages["app/ 页面与路由"]
    Frontend --> Components["components/ 可复用 UI"]
    Frontend --> Client["lib/ API、Firebase、Hooks、Types"]

    Backend --> API["api/ HTTP + SSE"]
    Backend --> Services["services/ 业务编排"]
    Backend --> DB["db/ SQLModel"]
    Backend --> Renderers["renderers/ p5.js、Reveal.js、Manim"]
    Backend --> Integrations["integrations/ 外部服务"]

    Services --> LLMContract["LLMProvider contract"]
    Integrations --> LLMFactory["llm/factory.py"]
    LLMFactory --> GeminiAdapter["Gemini Adapter"]
    LLMFactory --> OpenAIAdapter["OpenAI Adapter"]
    LLMContract -.-> LLMFactory
    Services --> DB
    Services --> Renderers
    Services --> Integrations
```

## 6. 后端功能模块

### 6.1 `api/`

负责 HTTP 边界和简单 CRUD 协调：

- 参数解析和 Pydantic 校验。
- Identity Platform Token 验证依赖。
- 在开始 SSE 前调用 source service 完成有界 PDF 读取和文本提取。
- generation router 将完整生成流程交给 `GenerationService`。
- lessons router 直接协调 `db/lessons.py` 与 Storage integration 完成查询、重命名、Signed URL 和可重试删除，但不承载 LLM、Prompt 或渲染规则。
- 将业务异常映射为统一错误响应。
- 将 service 产生的事件作为 SSE 响应返回。

### 6.2 `services/generation.py`

唯一的课程生成编排器：

1. 创建生成中的课程记录。
2. 编辑请求先校验所属旧课程并加载原代码，避免无效编辑提前上传 source。
3. 上传已验证的可选 source。
4. 构建 Prompt 并调用配置的 `LLMProvider`。
5. 解析摘要和代码。
6. 选择 Renderer，并在视频首次失败时执行一次修复。
7. 在同一个生成总 deadline 内完成 source、模型调用、渲染和 Cloud Storage 上传。
8. 保存数据库记录。
9. 逐阶段产生进度事件。

Router 和 Renderer 都不应重复这套流程。

### 6.3 `renderers/`

通过一个很小的协议统一三种实现：

```python
class Renderer(Protocol):
    async def render(self, code: str, workdir: Path) -> RenderedAsset: ...
```

- `HTMLRenderer`：按 p5.js/Reveal.js 标记校验完整 HTML、注入 CSP 后写入临时文件。
- `RemoteManimRenderer`：API 通过 HTTP 调用隔离 renderer；生产使用 Cloud Run OIDC，本地回环地址不要求 OIDC。
- `LocalManimRenderer`：只由 renderer 服务执行 Manim 进程组，限制超时和输出大小，并将诊断日志限制为尾部内容。
- Renderer 只返回文件，不访问数据库。
- 自动修复属于 `generation.py`，Renderer 只报告结构化错误。

### 6.4 `integrations/`

每类外部系统仅有一个业务入口：

- `llm/base.py`：定义统一请求、响应与错误协议。
- `llm/factory.py`：根据配置创建唯一 Provider 实例。
- `llm/gemini.py`：Gemini Developer API Adapter。
- `llm/openai.py`：OpenAI Responses API Adapter。
- `storage.py`：上传、删除、生成 Signed URL。
- `identity.py`：验证 ID Token，返回 `AuthUser(uid, email)`。

### 6.5 `db/`

- `session.py`：Engine 和请求 Session。
- `models.py`：SQLModel 表。
- `lessons.py`：课程查询和写入。
- 所有查询必须显式包含 `owner_id`，避免跨用户读取。

不再保留独立 `crud/users.py`、Webhook 用户同步和多个含义重叠的 lesson router。

## 7. 最小 API 设计

| Method | Path | 用途 |
|---|---|---|
| `GET` | `/healthz` | Cloud Run 健康检查，不需要用户认证 |
| `POST` | `/v2/generations` | 新建或编辑课程，返回 SSE 流 |
| `GET` | `/v2/lessons` | 当前用户课程列表，支持 `q`、`format` |
| `GET` | `/v2/lessons/{id}` | 当前用户读取单个课程 |
| `PATCH` | `/v2/lessons/{id}` | 修改标题 |
| `DELETE` | `/v2/lessons/{id}` | 删除数据库记录和 GCS 对象 |
| `POST` | `/v2/lessons/{id}/access-url` | 返回短期预览/下载 URL |

不再保留：

- 同一功能的同步 `/lesson` 与流式 `/lesson/generate` 双实现。
- 按 topic、model、format 查找最近课程的接口。
- 单独的 source preview 代理接口。
- Next.js 中镜像 FastAPI CRUD 的 API Routes。

## 8. 最小数据模型

v2 初期只需要一个业务表：

```text
Lesson
├── id: UUID, primary key
├── owner_id: string, indexed
├── topic: string
├── format: interactive | slides | video
├── status: generating | ready | failed | deleting
├── summary: text, nullable
├── source_code: text, nullable
├── object_key: string, nullable
├── error_message: text, nullable
├── created_at: timestamp
└── updated_at: timestamp
```

约束：

- API 永远通过 `(id, owner_id)` 查询课程。
- 数据库保存 GCS `object_key`，不保存会过期的 Signed URL。
- Identity Platform 保存账户；本地数据库不复制 email，除非未来有明确业务需求。
- 编辑课程默认创建新 Lesson 版本，保留旧结果；若产品希望覆盖，需要在实现前明确。

## 9. GCP 服务与外部 LLM API 调用方法

### 9.1 Cloud Run

用途：运行 `web`、`api` 和最小权限 `renderer` 三个容器。

调用方法：

- 用户通过 HTTPS 调用 Cloud Run。
- `web` 允许公开访问。
- `api` 允许公开网络访问，但所有 `/v2/*` 接口必须校验 Identity Platform Token。
- 使用 Request-based billing、`min-instances=0`。
- API 初期将并发设置较低；renderer 并发固定为 1，避免多个 Manim 同时耗尽内存。
- 生成超时设置为高于正常最长渲染时间，但每次生成仍要有应用级超时。

### 9.2 LLM Provider

用途：通过统一接口生成课程摘要和代码。部署时选择一个 Provider，不做自动回退。

#### 9.2.1 Gemini Developer API（Google AI Studio）

用途：生成课程摘要和代码。

调用方法：

```python
from google import genai

client = genai.Client(
    api_key=settings.gemini_api_key,
)
```

- 在 Google AI Studio 创建新的 Gemini API Key；优先使用当前默认创建的 authorization key，不沿用无约束的旧 standard key。
- Key 只存在 Secret Manager，通过 Cloud Run `--set-secrets` 注入为 `GEMINI_API_KEY`。
- Key 不得放入 `NEXT_PUBLIC_*`、浏览器 Bundle、Git 仓库、日志或数据库。
- 模型名称通过通用 `LLM_MODEL` 配置，业务代码中不硬编码 Preview 版本。
- Prompt 按输出格式拆成三个模板，但模型调用入口只有统一 `LLMProvider`。
- API 调用、配额和模型费用归属于该 AI Studio Key 关联的 Google Cloud Project，但它不是 Vertex AI 调用。
- 若未来切换 Vertex AI，只替换 Gemini Adapter 的 Client 初始化和认证方式。

#### 9.2.2 OpenAI API

调用方法：

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=settings.openai_api_key)
response = await client.responses.create(
    model=settings.llm_model,
    input=prompt,
)
text = response.output_text
```

- Key 只存在 Secret Manager，通过 Cloud Run `--set-secrets` 注入为 `OPENAI_API_KEY`。
- Adapter 使用 Responses API，并将返回文本、模型、Token 用量和错误映射为公共类型。
- OpenAI 专用参数只能存在于 Adapter 或 Provider 配置中，不能泄漏到 `GenerationService`。
- 切换 Provider 只修改 `LLM_PROVIDER`、`LLM_MODEL` 和对应 Secret，不修改 Router、Service 或前端代码。

### 9.3 Cloud SQL for PostgreSQL

用途：保存课程元数据、代码和用户所有权。

调用方法：

- Cloud Run 配置 Cloud SQL instance attachment。
- SQLAlchemy/SQLModel 通过 `/cloudsql/<INSTANCE_CONNECTION_NAME>` Unix Socket 连接。
- 数据库密码从 Secret Manager 注入。
- API Service Account 授予 Cloud SQL Client 权限。
- 第一阶段使用单区小实例；达到稳定生产需求后再考虑 HA。

示意连接串：

```text
postgresql+psycopg://USER:PASSWORD@/DATABASE?host=/cloudsql/INSTANCE_CONNECTION_NAME
```

### 9.4 Cloud Storage

用途：保存用户上传资料和生成的 HTML、MP4。

调用方法：

```python
from google.cloud import storage

client = storage.Client()
bucket = client.bucket(settings.gcs_bucket)
blob = bucket.blob(object_key)
blob.upload_from_filename(local_path, content_type=content_type)
```

对象路径统一为：

```text
lessons/{owner_id}/{lesson_id}/lesson.html
lessons/{owner_id}/{lesson_id}/lesson.mp4
sources/{owner_id}/{lesson_id}/{filename}.pdf
```

- 预览和导出返回短期 V4 Signed URL。
- Bucket 禁止公开访问。
- 设置生命周期规则清理失败任务和临时 source。
- HTML 在独立 GCS Origin 打开，并在前端 iframe 上使用 `sandbox`，避免生成脚本取得主站权限。

### 9.5 Identity Platform

用途：统一处理 Google、Microsoft 和托管邮箱密码的注册、登录、密码重置与 ID Token。

调用方法：

- 在 Google Cloud Console 启用 Google Provider、Microsoft Provider 和 Email/Password。
- Microsoft Provider 配置 Microsoft App ID 与 Secret；首版允许个人 Microsoft 与 Entra ID 账号，后续可按机构要求限制 Tenant。
- 前端使用 Firebase Web SDK 的 `GoogleAuthProvider`、`OAuthProvider("microsoft.com")` 和 Email/Password 方法完成登录。
- 登录页面、按钮和表单由 Chalksmith 前端实现；Identity Platform 托管凭据和 Token，不使用自建密码数据库。
- 三种方式登录成功后都取得 Identity Platform ID Token。
- 每次 API 请求在 Authorization Header 中携带 Token。
- 后端使用 Firebase Admin SDK 验证 Token：

```python
from firebase_admin import auth

decoded = auth.verify_id_token(token)
user_id = decoded["uid"]
```

- Cloud Run 使用默认 Service Account 凭据，不提交凭据文件。
- 账号关联必须要求用户先验证已有凭据，不按 email 自动静默合并。
- 首版不配置 SAML、OIDC、Multi-tenancy 或 Custom Token；未来增加这些 Provider 时，FastAPI 验证流程保持不变。
- 删除 Clerk Webhook、本地用户注册接口以及任何本地密码存储职责。

### 9.6 Secret Manager

用途：保存数据库密码与当前所选 LLM Provider 的 API Key。

调用方法：

- 在 `gcloud run deploy` 中通过 `--set-secrets` 注入环境变量。
- 应用只读取环境变量，不在每个请求中调用 Secret Manager API。
- 非敏感配置，例如 region、bucket、model，使用普通 Cloud Run 环境变量。

### 9.7 Artifact Registry 与 Cloud Build

用途：构建和保存三个容器镜像。

调用方法：

- `api.Dockerfile` 构建不含 Manim 的 FastAPI API 运行环境。
- `renderer.Dockerfile` 构建独立 Manim 渲染环境。
- `web.Dockerfile` 构建 Next.js standalone 输出。
- Cloud Build 构建后推送 Artifact Registry。
- Cloud Run 从同一区域 Artifact Registry 部署，避免跨区域传输。

### 9.8 Cloud Logging

用途：收集访问、生成阶段、LLM 和渲染错误。

调用方法：

- 应用输出单行 JSON 到 stdout/stderr。
- 请求日志包含 `request_id`、HTTP 状态和完整流式响应时长；生成日志同时包含适用的 `lesson_id`、`owner_id_hash`、`stage` 和耗时。
- 不记录 PDF 原文、生成代码全文、Token、email 或 API Key。

## 10. 配置与环境变量

后端只通过 `backend/app/core/config.py` 读取配置：

```text
APP_ENV
APP_ROLE                    # api | renderer
FRONTEND_ORIGINS
GCP_PROJECT_ID
IDENTITY_PLATFORM_PROJECT_ID
LLM_PROVIDER                 # gemini | openai
LLM_MODEL                    # Provider 对应的模型 ID
LLM_TIMEOUT_SECONDS
LLM_MAX_OUTPUT_TOKENS
GEMINI_API_KEY             # Secret Manager
OPENAI_API_KEY             # Secret Manager
CLOUD_SQL_INSTANCE
DATABASE_URL                 # 本地 SQLite 或受信环境中的直接连接串
DATABASE_NAME
DATABASE_USER
DATABASE_PASSWORD        # Secret Manager
GCS_BUCKET
GCS_SIGNER_SERVICE_ACCOUNT
SIGNED_URL_TTL_SECONDS
GENERATION_TIMEOUT_SECONDS
MANIM_TIMEOUT_SECONDS
MAX_RENDER_BYTES
MANIM_RENDERER_URL
MAX_SOURCE_FILES
MAX_SOURCE_BYTES
MAX_TOTAL_SOURCE_BYTES
MAX_SOURCE_CHARACTERS
AUTO_CREATE_TABLES
```

`LLM_PROVIDER` 默认设为 `gemini`。部署只需注入被选中 Provider 的 Key；`config.py` 应使用条件校验，不能要求 Gemini 与 OpenAI 两个 Key 同时存在。

前端仅保留可公开配置：

```text
NEXT_PUBLIC_API_URL
NEXT_PUBLIC_FIREBASE_API_KEY
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
NEXT_PUBLIC_FIREBASE_PROJECT_ID
NEXT_PUBLIC_FIREBASE_APP_ID
```

不要在前端使用 `NEXT_PUBLIC_*` 保存后端地址以外的私密信息。Firebase Web 配置用于标识项目，不作为服务器秘密。

## 11. 安全边界

### 11.1 生成的 HTML

- p5.js 和 Reveal.js HTML 必须在与主站不同的 GCS Origin 中运行。
- iframe 使用 sandbox，不能同时启用不必要的 `allow-same-origin` 和 `allow-top-navigation`。
- 上传时设置正确的 `Content-Type`、内联/下载 `Content-Disposition` 与私有缓存策略；HTML 安全策略由文档内 CSP 和 iframe sandbox 共同实施。

### 11.2 生成的 Manim Python

LLM 生成的 Python 属于不可信代码。长期生产环境中不得让它在拥有 Cloud SQL、LLM API Key 和用户数据权限的 API 容器内直接执行。

代码已经采用同一 backend 代码库、两个运行入口的隔离方案：

1. 当前实现：从同一 backend 代码构建独立 renderer image，由 API 使用 OIDC 调用并接收 MP4；API 镜像不安装 Manim，也没有本地回退。
2. 未来替代方案：将视频生成改为受约束的 JSON Scene Schema，由可信 Renderer 渲染，不执行任意 Python。

该安全拆分不需要创建第二套代码库；`renderers/` 仍然共享，但 API 容器不执行生成脚本。正式公开视频生成前仍必须在真实 Cloud Run 环境验证 renderer 为私有服务、API 是唯一 invoker，且 renderer Service Account 无 Cloud SQL、GCS、Secret Manager 或 LLM 凭据权限。

```mermaid
flowchart LR
    API["FastAPI API<br/>DB + LLM Key"] -->|OIDC + 代码| Runner["隔离 Renderer<br/>无 DB / 无 LLM Key / 无 GCS 权限"]
    Runner -->|MP4 响应| API
    API -->|上传结果| Bucket["Cloud Storage"]
    Runner -.->|不得访问| SQL["Cloud SQL"]
    Runner -.->|不得访问| LLM["External LLM Provider"]
```

## 12. 已删除或合并的旧代码

重构已删除：

- `frontend/src/app/api/lesson-generate/`
- `frontend/src/app/api/lesson-record/`
- `frontend/src/app/api/lesson-list/`
- `frontend/src/app/api/lessons/`
- `frontend/src/app/api/lesson-export/`
- `frontend/src/app/api/sources/upload/`
- `frontend/src/app/api/webhooks/clerk/`
- `frontend/src/lib/auth-headers.ts`
- Clerk 相关依赖和 `frontend/src/proxy.ts` 中的 Clerk 保护逻辑
- `backend/routers/users.py`
- `backend/crud/users.py`
- 旧 `llm.py` 中散落的 Provider 分支、未使用模型选项和与 UI 耦合的模型选择逻辑；由明确的 Gemini/OpenAI Adapter 取代
- Remotion Renderer、Player、依赖和 `frontend/src/remotion/`
- `backend/static/` 中的持久化职责
- VPS daemontools 部署脚本

重构已合并：

- 所有课程生成入口 → `/v2/generations`
- `backend/models.py` → `backend/app/db/models.py`
- `backend/database.py` → `backend/app/db/session.py`
- `crud/lessons.py` → `backend/app/db/lessons.py`
- generation 页面状态与请求编排 → `lib/hooks/useGeneration.ts`；页面只保留布局，`GenerationSidebar` 只保留交互面板职责
- 前端所有 API 函数 → `lib/api/client.ts` 和 `generation-stream.ts`

这些旧路径均在替代实现通过测试后删除，历史实现继续由 `v1.0` 分支保留。

## 13. 重构实施阶段

### Phase 0：建立基线（分支已保留；恢复演练待执行）

- 确认 `v1.0` 分支可以构建和运行。
- 为当前关键流程记录手工回归步骤。
- 禁止在重构期间向 v1 同时加入大功能。

验收：能够从 `v1.0` 恢复当前生产版本。

### Phase 1：建立 v2 骨架（完成）

- 创建 `backend/app/` 新目录，不立即移动所有旧代码。
- 增加集中配置、统一错误和 `/healthz`。
- 创建前端 `lib/api/`、`lib/firebase/`、`lib/hooks/`、`components/auth/` 和共享 API 类型。
- 添加最小单元测试框架。

验收：新 FastAPI 入口可以启动，健康检查通过。

### Phase 2：迁移 GCP 数据与存储（代码完成；资源和迁移待执行）

- 创建 Cloud SQL、Cloud Storage、Secret Manager 和 Service Account。
- 将数据库 Engine 切换到 Cloud SQL。
- 将 Renderer 输出改为临时目录 + GCS 上传。
- 数据库改存 `object_key`。
- 完成 Neon 数据迁移脚本和校验。

验收：重启或扩容 Cloud Run 后，已有课程仍能预览和下载。

### Phase 3：收敛生成流程（代码完成；真实 Provider smoke test 待执行）

- 建立 `LLMProvider` 协议、Factory、Gemini Adapter 和 OpenAI Adapter。
- 通过 `LLM_PROVIDER` 与 `LLM_MODEL` 选择实现，并从 Secret Manager 只注入所选 Provider 的 Key。
- 完成统一 `GenerationService`。
- 合并 GET EventSource 与 POST 文件流为统一 POST SSE。
- 统一格式值和错误码。
- 删除同步生成重复实现。

当前验收：Fake Provider 已通过统一生成流程测试，Gemini/OpenAI 共用协议和配置入口。真实 Provider、三种格式及编辑/停止/保存/导出仍需在具备测试 Key 与云资源的环境完成 smoke/E2E 验证。

### Phase 4：认证迁移（代码完成；控制台配置和用户迁移待执行）

- 实现 `AuthUser` Adapter。
- 接入 Identity Platform 的 Google、Microsoft 和 Email/Password Provider。
- 完成 Chalksmith 品牌的登录、注册、密码重置和退出页面。
- 建立 Clerk UID 到 Identity Platform UID 的迁移映射或账号重新登录策略，并迁移课程 `owner_id`。
- 实现凭据关联流程，处理 `account-exists-with-different-credential`，禁止仅按 email 静默合并。
- 前端改为 Bearer Token 直连 API。
- 删除 Next API 代理、Webhook 和内部共享密钥。

当前验收：登录、注册、重置、退出、凭据关联、Token 注入、401 与租户隔离代码已实现并通过本地可替代部分的测试。Google、Microsoft 和邮箱密码的真实登录、账号迁移及正式授权域名仍需在 Identity Platform 环境验证。

### Phase 5：整理前端（代码完成；响应式手工回归待执行）

- 将 generation 页面中的状态逻辑抽到 `useGeneration` 或一个 controller hook。
- 合并重复 sidebar 和 API 类型。
- 保留页面级组件编排，不建立全局状态库。
- 删除 Remotion 和 Clerk 残余依赖。

当前验收：前端严格 TypeScript 检查和 production build 通过；主要页面的移动端与桌面端手工回归仍应在切流前执行。

### Phase 6：Manim 安全隔离（代码和部署资产完成；Cloud Run 验证待执行）

- 已构建独立 Manim renderer image 与最小权限 Cloud Run 部署配置；真实部署尚待执行。
- 限制 CPU、内存、执行时间、输出大小和可用环境变量。
- API 容器不再执行生成 Python。
- 添加恶意代码和超时测试。

当前验收：API 不执行生成 Python，AST/超时/取消/输出限制测试通过；Renderer 在真实 Cloud Run 中无权访问 Cloud SQL、GCS、LLM Key 或 Secret Manager 仍待 IAM smoke test。

### Phase 7：切流与清理（待执行）

- 在测试环境执行完整回归。
- 灰度切换正式域名。
- 观察错误率、延迟和费用。
- 删除旧 Neon、VPS、Vercel 与 Clerk 资源前导出备份。
- 最后删除旧代码路径和已废弃依赖。

验收：连续运行一周无数据丢失或跨用户访问问题，具备回滚方案。

## 14. 测试计划

截至 2026-08-11，当前自动化基线为 22 项后端测试、前端严格 TypeScript 检查和 Next.js production build。已覆盖生产配置约束、共享错误/CORS/Request ID、Manim AST 限制与进程组取消、总 deadline、有界 renderer 诊断、source 数量与总字节限制、SSE 阶段、Fake Provider 完整生成、租户隔离和删除顺序。

下列内容是完整上线测试范围，并非全部已经自动化。仍待补充或在真实云环境执行的重点包括：Gemini/OpenAI Adapter 响应契约、有效/过期 Identity Token、三种真实登录方式、PDF 无文本层与损坏文件、迁移脚本、Cloud SQL/GCS/Signed URL 集成、前端交互自动化以及三种格式的端到端回归。

### 后端单元测试

- Prompt 和格式映射。
- `LLMProvider` 契约、Factory 配置校验与统一错误映射。
- Gemini/OpenAI 响应解析和 Token 用量标准化。
- PDF 无文本层、超限和损坏文件处理。
- Renderer 选择和结构化错误。
- 所有 lesson 查询包含 owner_id。

### 后端集成测试

- Identity Token 有效、过期、缺失。
- Google、Microsoft 和 Email/Password 登录产生的 Token 都映射为同一 `AuthUser` 结构。
- Clerk UID 到 Identity Platform UID 的课程所有权迁移。
- Cloud SQL CRUD。
- GCS 上传、Signed URL 和删除。
- `/v2/generations` SSE 事件顺序。
- 生成取消后子进程终止。
- 使用 Fake Provider 运行完整生成流程；真实 Provider smoke test 仅在显式提供测试 Key 时运行。

### 前端测试

- Google、Microsoft、邮箱注册登录、密码重置、退出、登录状态和 Token 刷新。
- 相同 email 使用不同 Provider 时的已有凭据验证与账号关联流程。
- 无附件与有附件使用同一个生成客户端。
- 流式进度、完成、认证失败、渲染失败和中止。
- Dashboard 搜索、重命名、删除和打开课程。

### 最小端到端回归

1. 分别使用 Google、Microsoft 和邮箱密码登录。
2. 生成 p5.js 课程。
3. 上传 PDF 生成 Reveal.js 课程。
4. 生成 Manim 视频。
5. 编辑已生成课程。
6. 从 Dashboard 重新打开。
7. 下载结果。
8. 删除课程并确认 GCS 对象被删除。

## 15. 可观测性与费用保护

- 为 Cloud Run、Cloud SQL、Cloud Storage 和当前选择的 LLM Provider 设置费用与使用量告警。
- 记录每次生成的模型耗时、渲染耗时、Token 数、文件大小和最终状态。
- Manim 并发初期限制为 1，每个实例最大并发保持较低。
- Cloud Run 默认允许缩容到 0，不设置常驻 Renderer。
- GCS 临时 source 设置短生命周期，课程结果按产品保留策略处理。
- LLM Provider 和渲染必须设置单次请求上限，防止异常 Prompt 造成不可控费用。

## 16. v2 上线完成标准

以下是 v2 正式上线与切流的完成标准，不等同于“代码重构已完成”。涉及真实身份、云资源、迁移和连续运行观察的条目当前仍未验收：

- 生产只运行 GCP 上的 web、api，以及必要的隔离 renderer。
- 课程业务不再经过重复的 Next.js API 代理。
- 不再依赖 Neon、VPS、Vercel、Clerk 或本地持久化静态目录。
- 后端业务层只依赖统一 `LLMProvider`；Gemini 与 OpenAI 可仅通过部署配置互换，Key 只能从 Secret Manager 注入。
- Google、Microsoft 和 Identity Platform 托管邮箱密码均可登录，并向 FastAPI 提供统一 ID Token。
- 应用不保存密码或实现自有 Session；同一用户的多种凭据可以安全关联到稳定 `uid`。
- 数据库中没有不必要的认证用户副本。
- 三种格式生成、编辑、预览、导出和删除全部可用。
- 所有课程操作按 owner_id 隔离。
- 生成文件全部存储在私有 GCS Bucket。
- Manim 不可信代码与数据服务权限隔离。
- 前后端 production build、测试和部署文档均通过验证。
- 可以在一个工作日内从备份和 `v1.0` 分支恢复旧版本。

## 17. 已落实决策与上线阻断项

代码实现采用以下明确决策：

1. 课程迁移要求提供 Clerk uid → Identity Platform uid 的显式 JSON 映射；若 Identity Platform 导入保留了原 uid，必须显式传入 `--preserve-owner-ids`。不会按 email 自动合并。
2. 默认 Provider 为 Gemini，但生产通过 `LLM_PROVIDER`/`LLM_MODEL` 选择 Gemini 或 OpenAI，终端用户不选择模型，也不会自动跨 Provider 回退。
3. Remotion 已删除，只保留 p5.js、Reveal.js 和 Manim。
4. 编辑课程创建新课程版本，旧课程继续保留，避免覆盖后无法恢复。
5. 上传 source 使用 `sources/` 前缀并设置七天 GCS 生命周期；用户删除课程时先将记录标为 `deleting`，再删除 source、输出对象和数据库记录。中途失败可安全重试，不会留下指向缺失输出的 `ready` 记录。
6. 视频只通过受 Cloud Run IAM 保护的独立 renderer 运行；API 生产配置缺少 `MANIM_RENDERER_URL` 时拒绝启动。
7. 部署脚本对课程 Bucket 强制启用 Uniform Bucket-Level Access 与 Public Access Prevention；应用只通过 API Service Account 和短期 Signed URL 访问私有对象。

以下工作不能由代码仓库替代，仍是上线阻断项：

1. 确认所选 Gemini Developer API 或 OpenAI API 条款、数据处理方式和未成年人保护要求适用于实际产品场景。
2. 在 Identity Platform 控制台开通 Google、Microsoft、Email/Password，配置 Microsoft OAuth 凭据和正式授权域名。
3. 在安装 `gcloud` 且具备所需 GCP 权限的受信环境中重新执行权限预检，然后创建资源、运行真实 Provider/GCS/Cloud SQL smoke test、执行 dry run 与正式数据迁移，并完成域名灰度和一周观察。
