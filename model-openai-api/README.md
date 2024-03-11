# 模型推理服务

## 一、简介

NL2SQL 生成模型推理接口，兼容 OpenAI 接口风格（Generation Model's OpenAI-style API）。

## 二、启动

首选需要安装 Python3 依赖的第三方库：

```
pip install -r requirements.txt
```

然后按照如下步骤启动&测试服务：

1）准备配置文件

复制模版配置文件 `conf/config-example.toml` 为 `conf/config.toml`，默认可不更改内容，如需修改参考下面配置文件的具体说明。

2）启动服务

```bash
sh start.sh nl2sql-v2 18021 conf/config.toml
# sh start.sh <model_name> <server_port> <config_file>
```

其中参数 `nl2sql-v2` 是模型名，对应于配置文件中的模型名，可逗号分割传入多个模型名；其中 `18021` 是服务的端口号；

初次启动服务，由于下载模型，需要较久的时间。

3）测试服务

```bash
# sh client.sh <model_name> <server_port>
sh client.sh nl2sql-v2 18021
```

## 三、配置文件

配置文件 `conf/config.toml` 中最重要的部分是模型的加载参数，即 `[models]` 区块的内容：

目前我们提供了轻量化的[自研 NL2SQL 模型-基础版](https://huggingface.co/DMetaSoul/nl2sql-chinese-basic)，此外大家也可以直接加载 LLM 来进行 NL2SQL 推理（注：LLM 虽然在 NL2SQL 任务上具备一定推理能力，但考虑并非针对性优化，生成效果可能较差）。

1）对于 Seq2Seq 架构的 NL2SQL 生成模型，需要增添如下配置项：

```
[models.llm."nl2sql-v2"]
name = "nl2sql-v2"
type = "seq2seq"
#path = "<修改为本地的模型路径或者URL地址或者HuggingFace ID>"
# 如下为基础版模型，若有高级版本模型需求，请联系我们
path = "DMetaSoul/nl2sql-chinese-basic"
tags = ["chat"]
```

2）对于大语言模型（LLM），比如 ChatGLM 模型，则增添如下配置项：

```toml
[models.llm."chatglm-6b"]
name = "chatglm-6b"
type = "chatglm"
path = "THUDM/chatglm-6b"
tags = ["chat", "completion"]
```

服务启动载入 ChatGLM 模型，并进行测试：

```bash
# 启动
sh start.sh chatglm 18021 conf/config.toml

# 测试
sh client.sh chatglm 18021
```

## 四、项目细节

该服务就是常规的纯粹模型推理服务，需要按照 OpenAI 接口风格来准备入参和解析出参，不涉及到任何 NL2SQL 业务逻辑，因此入参中输入给模型的 prompt 完全由调用方给出（当然需要符合模型对应的输入格式），从出参中如何解析得到 SQL 也由调用方实现（同样跟具体的推理模型输出格式有关）。具体可以参考 `client.sh` 脚本，看调用方如何设计入参、以及不同模型的输出格式。

整体架构如下：

```bash
├── conf
│   └── config.toml                 # 服务启动的配置文件，包括加载模型的参数以及授权 token 等
├── api
│   ├── auth.py                     # API token 授权
│   ├── model.py                    # API 请求体
│   ├── response.py                 # API 响应体
│   └── routers
│       ├── basic.py                # OpenAI-style model list API
│       ├── chat.py                 # OpenAI-style chat API
│       ├── completion.py           # OpenAI-style completion API
│       └── embeddings.py           # OpenAI-style embeddins API
├── context.py                      # 全局配置单例对象，包括加载模型、Token列表等
├── app.py                          # FastAPI app 实例，配置 API 路由
├── main.py                         # 服务的启动脚本
├── models
│   ├── chatglm                     # chat 推理模型，基于 ChatGLM 模型
│   ├── embeddings.py               # 文本向量化推理，
│   └── seq2seq                     # chat 推理模型，基于 T5/BART 模型
├── start.sh                        # 服务启动脚本
└── client.sh                       # 服务测试脚本
```
