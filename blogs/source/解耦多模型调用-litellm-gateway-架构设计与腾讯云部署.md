---
title: "解耦多模型调用：LiteLLM Gateway 架构设计与腾讯云部署"
category: "AI"
date: 2026-08-22
slug: 解耦多模型调用-litellm-gateway-架构设计与腾讯云部署
---

## 一、背景：为什么搭建LLM Gateway

随着 AI 应用逐渐从单模型调用走向多模型协作，一个很现实的工程问题随之出现：

不同模型厂商拥有不同的 API 地址、模型名称、鉴权方式和 SDK。

例如一个 AI 应用同时需要使用：

```text
OpenAI
DeepSeek
Qwen
```

如果业务代码直接与每个模型厂商耦合，就会逐渐形成：

```text
应用
 ├── OpenAI API
 ├── DeepSeek API
 └── DashScope API
```

随着模型数量增加，会产生下述问题：

**模型切换成本增加**
**API Key 分散在不同应用中**
**Provider 与业务代码耦合**
**调用方式难以统一**
**后续难以进行统一的限流、成本统计和故障切换。**

因此我开始思考：

> **能不能在业务应用与模型 Provider 之间增加一个统一的模型访问层？**

让上层应用不再关心底层究竟调用 OpenAI、DeepSeek 还是 Qwen。

基于这个目标，我设计了：

```text
                         ┌── OpenAI
                         │
Application → LLM Gateway ├── DeepSeek
                         │
                         └── Qwen
```

在对统一模型调用方案进行分析后，我选择使用 **LiteLLM Gateway** 实现这一层。


因此这个项目的目标非常明确：

> **在自己的云服务器上独立搭建一个统一 LLM Gateway，将 OpenAI、DeepSeek、Qwen 等不同模型接入同一个 API，并完成鉴权、模型路由、密钥隔离和公网调用。**


## 二、架构设计

最终设计的整体架构：

```text
Mac / AI Application / Test Program
                 │
                 │ HTTP Request
                 ▼
        Tencent Cloud Server
                 │
                 ▼
              Docker
                 │
                 ▼
          LiteLLM Gateway
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
     OpenAI   DeepSeek   Qwen
                         │
                     DashScope
```

这里我刻意把 **LiteLLM 放在应用和模型 Provider 中间**。

这样上层应用只需要知道：

```text
LiteLLM Base URL
LiteLLM Master Key
Model Alias
```

而不需要知道真正的：

```text
OPENAI_API_KEY
DEEPSEEK_API_KEY
DASHSCOPE_API_KEY
```

这实际上完成了一层非常重要的**模型访问抽象**。


## 三、服务器环境准备

本次部署环境：

```text
Cloud：Tencent Cloud
OS：Ubuntu 24.04 LTS
CPU：2 Core
Memory：2 GB
Disk：40 GB
```

首先更新 Ubuntu 软件索引：

```bash
apt update
```

安装 Docker：

```bash
apt install -y docker.io
```

检查版本：

```bash
docker --version
```

服务器最终安装：

```text
Docker version 29.1.3
```

确认 Docker 服务：

```bash
docker ps
```

环境准备完成。


## 四、设计 LiteLLM 模型路由

整个项目中，我认为比较重要的设计之一，是**没有让客户端直接使用各 Provider 的真实模型名称**。

我在 `config.yaml` 中建立了一层自己的模型别名：

```yaml
model_list:
  - model_name: gpt
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: os.environ/OPENAI_API_KEY

  - model_name: deepseek
    litellm_params:
      model: deepseek/deepseek-v4-flash
      api_key: os.environ/DEEPSEEK_API_KEY

  - model_name: qwen
    litellm_params:
      model: dashscope/qwen3.7-flash-2026-07-15
      api_key: os.environ/DASHSCOPE_API_KEY

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
```

这样客户端只需要请求：

```json
{
  "model": "deepseek"
}
```

LiteLLM 会完成：

```text
deepseek
   ↓
LiteLLM Model Alias
   ↓
config.yaml
   ↓
deepseek/deepseek-v4-flash
   ↓
DeepSeek Provider
```

同样：

```text
qwen
 ↓
dashscope/qwen3.7-flash-2026-07-15
```

这意味着以后即使底层模型发生变化，例如：

```text
DeepSeek Model A
       ↓
DeepSeek Model B
```

理论上客户端仍然可以继续使用：

```json
"model": "deepseek"
```

只需要修改 Gateway 层的配置。

这样可以进一步降低业务代码和模型 Provider 之间的耦合。


## 五、API Key 与业务调用隔离

另一个我重点考虑的问题是：

> **不应该让真实 Provider API Key 出现在 GitHub 或客户端代码中。**

因此我没有直接把 Key 写进 `config.yaml`：

```yaml
api_key: sk-xxxxx
```

而是使用：

```yaml
api_key: os.environ/DEEPSEEK_API_KEY
```

服务器创建：

```bash
nano .env
```

配置：

```env
OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
DEEPSEEK_API_KEY=<YOUR_DEEPSEEK_API_KEY>
DASHSCOPE_API_KEY=<YOUR_DASHSCOPE_API_KEY>

LITELLM_MASTER_KEY=<YOUR_LITELLM_MASTER_KEY>
```

然后限制文件权限：

```bash
chmod 600 .env
```

这样形成两层 Key：

```text
                LiteLLM Master Key
客户端 ───────────────────────────→ LiteLLM
                                      │
                                      │ Provider API Key
                                      ▼
                                   DeepSeek
```

客户端只需要持有：

```text
LITELLM_MASTER_KEY
```

真正的：

```text
OPENAI_API_KEY
DEEPSEEK_API_KEY
DASHSCOPE_API_KEY
```

只存在于服务器环境中。

这既降低了 Provider Key 暴露风险，也方便后续统一管理模型访问权限。

---

## 六、Docker 部署方案的选择

在设计 Docker 部署方式时，我对比了两种方案。

### 方案 A：构建自己的 LiteLLM 镜像

```text
Official LiteLLM Image
          +
     config.yaml
          ↓
     docker build
          ↓
Custom LiteLLM Image
```

对应 Dockerfile：

```dockerfile
FROM docker.litellm.ai/berriai/litellm-non_root:main-stable

COPY config.yaml /app/config.yaml

CMD ["--config", "/app/config.yaml", "--port", "4000", "--host", "0.0.0.0"]
```

这种方式的优势是：

> **镜像本身包含配置，更适合标准化交付。**

但是我考虑到这个 Gateway 后续还需要持续增加、删除和切换模型。

如果把配置直接 COPY 到镜像，每次修改 `config.yaml` 都需要：

```text
修改配置
 ↓
docker build
 ↓
生成新镜像
 ↓
重新创建容器
```

因此我最终没有采用这种方式。

### 方案 B：官方镜像 + Volume Mount

我最终选择：

```text
Tencent Cloud
│
├── config.yaml ───────────┐
│                         │ Volume Mount
│                         ▼
│                  LiteLLM Container
│                         ▲
└── .env ──────────────────┘
```

也就是：

> **保持 LiteLLM 官方镜像不变，在运行容器时动态挂载自己的配置。**

这样以后修改模型配置时，不需要重新 Build 整个镜像。

对于当前这种需要持续实验不同模型的 Gateway，我认为这种方式维护成本更低。

## 七、启动 LiteLLM Gateway

最终没有执行 `docker build`，而是直接使用官方镜像：

```bash
docker run -d \
  --name litellm \
  --restart unless-stopped \
  --env-file .env \
  -p 4000:4000 \
  -v /root/litellm-yuli/config.yaml:/app/config.yaml:ro \
  docker.litellm.ai/berriai/litellm-non_root:main-stable \
  --config /app/config.yaml \
  --host 0.0.0.0 \
  --port 4000
```

其中：

```text
--env-file .env
```

负责注入环境变量。

```text
-p 4000:4000
```

建立：

```text
Host :4000
   ↓
Container :4000
```

而：

```text
-v /root/litellm-yuli/config.yaml:/app/config.yaml:ro
```

则建立：

```text
Host config.yaml
        ↓
Volume Mount
        ↓
Container /app/config.yaml
```

`:ro` 表示 Read Only，避免容器修改宿主机配置。

同时：

```text
--restart unless-stopped
```

保证服务器或 Docker 重启后，Gateway 可以自动恢复运行，除非主动停止容器。

---

## 八、验证容器与 Gateway

部署完成之后，我没有立即测试模型，而是按照**从底层到上层逐层验证**的方式进行检查。

首先检查容器：

```bash
docker ps --filter name=litellm
```

确认：

```text
STATUS: Up
PORTS: 0.0.0.0:4000->4000/tcp
```

然后查看服务日志：

```bash
docker logs --tail 50 litellm
```

确认：

```text
Application startup complete.
Uvicorn running on http://0.0.0.0:4000
```

最后进行 Health Check：

```bash
curl -s http://localhost:4000/health/liveliness
```

返回：

```text
"I'm alive!"
```

到这里可以确认：

```text
Docker
  ↓
Container
  ↓
Port Mapping
  ↓
LiteLLM Process
  ↓
HTTP Endpoint

全部正常
```

然后才进入真正的模型调用测试。

---

## 九、验证 DeepSeek 模型路由

加载当前 Shell 环境变量：

```bash
set -a
source .env
set +a
```

然后调用：

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -d '{
    "model": "deepseek",
    "messages": [
      {
        "role": "user",
        "content": "你好，请只回复：DeepSeek测试成功"
      }
    ]
  }'
```

成功返回：

```text
DeepSeek测试成功
```

意味着：

```text
HTTP Request
   ↓
LiteLLM Authentication
   ↓
Model Alias: deepseek
   ↓
Model Routing
   ↓
DEEPSEEK_API_KEY
   ↓
DeepSeek API
   ↓
Response
```

完整链路已经正常。

## 十、实现公网模型调用

服务器内部验证完成后，我继续验证真实客户端访问场景。

在腾讯云防火墙开放 TCP `4000` 端口后，从 Mac 执行：

```bash
curl http://<SERVER_PUBLIC_IP>:4000/health/liveliness
```

成功得到：

```text
"I'm alive!"
```

然后在 Mac 配置：

```bash
export LITELLM_MASTER_KEY='<YOUR_MASTER_KEY>'
```

从公网请求 DeepSeek：

```bash
curl http://<SERVER_PUBLIC_IP>:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -d '{
    "model": "deepseek",
    "messages": [
      {
        "role": "user",
        "content": "你好，请只回复：公网调用成功"
      }
    ]
  }'
```

最终返回：

```text
公网调用成功
```

至此完成：

```text
Mac Client
     ↓
Internet
     ↓
Tencent Cloud Firewall
     ↓
Host :4000
     ↓
Docker Port Mapping
     ↓
LiteLLM Gateway
     ↓
Authentication
     ↓
Model Routing
     ↓
DeepSeek
     ↓
Response
```

完整端到端验证通过。

## 十一、最终成果

最终我独立搭建了一套：

```text
                    ┌── OpenAI
                    │
Client → LiteLLM ───┼── DeepSeek
                    │
                    └── Qwen
```

的统一模型 Gateway。

实现了：

* 多模型 Provider 的统一 API 入口；
* OpenAI-compatible Chat Completions API；
* 自定义模型 Alias 与模型路由；
* Provider API Key 与客户端隔离；
* LiteLLM Master Key 统一鉴权；
* Docker 容器化部署；
* Volume 动态挂载模型配置；
* Docker 自动重启策略；
* DeepSeek、Qwen 实际模型调用验证；
* 应用 → 腾讯云 → LiteLLM → LLM Provider 的公网端到端调用。
