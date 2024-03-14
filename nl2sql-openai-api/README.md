# NL2SQL pipeline 服务

## 一、简介

此项目（`nl2sql-openai-api`）的核心逻辑，接收类似 OpenAI Chat 请求形式，然后转发给 NL2SQL 模型推理服务（`model-openai-api`），并在转发前和转发后分别完成目标模型相关的预处理和后处理逻辑（如 `schemalink-service-api`）。

可认为该服务是 NL2SQL pipeline 组装服务（或者是用户产品服务和模型推理服务之间的中间人），可以通过配置文件来组装 pipeline，实现预处理+模型服务+后处理的灵活自定义。为了兼容各种工具生态，该服务以类似 OpenAI Chat 接口形式对外提供访问。

## 二、启动

1）拷贝配置文件

```bash
cp conf/config-example.toml conf/config.toml
```

该配置文件已默认开启以下几种 NL2SQL 服务：

- 自研模型（基础版），参见 `[openai.service.elementary]`，最基础版本、足够轻量
- 自研模型（升级版），参见 `[openai.service.intermediate]`，包含了升级版 NL2SQL 模型以及 Schema Linking 功能
- OpenAI Chat，参见 `[openai.service.llm]`，直接转发请求给类似 OpenAI 的接口
- 大模型，参见 `[openai.service.llm]`，利用 LLM 能力解决 NL2SQL 问题

2）启动服务

```bash
sh start.sh 18080 conf/config.toml
```

3）测试服务

启动之后，可以分别通过以下接口，请求不同的 NL2SQL 服务

- `/nl2sql/elementary/` -> 自研模型（基础版）：`sh client.sh 18080 elementary nl2sql-v1`
- `/nl2sql/intermediate/` -> 自研模型（升级版）：`sh client.sh 18080 intermediate nl2sql-v2`
- `/nl2sql/openai/` -> OpenAI 类似服务：`sh client.sh 18080 openai gpt-3.5-turbo <api_key>`
- `/nl2sql/llm-6b/` -> LLM 模型：`sh client.sh 18080 llm-6b nl2sql-6b`
- `/nl2sql/llm-7b/` -> LLM 模型：`sh client.sh 18080 llm-7b nl2sql-7b`

每种 NL2SQL 服务通过灵活配置，具备不同的能力。其中仅自研模型（基础版）接受字符串简写格式作为输入，跟离线自研模型一致；另外的自研模型（升级版）和 OpenAI 服务均接受数据库创建语句格式，跟 Chat2DB 一致（后文详细说明）。

## 三、NL2SQL 服务详解

当前服务提供了类似 OpenAI chat 的请求接口，因此服务的输入和输出完全可以参考 OpenAI 官方接口文档。

目前 NL2SQL 就是一个单轮对话查询服务，因此传入 chat 请求体的内容是一段含有 question 和 schema 信息的文本内容。注意不同 NL2SQL 服务的输入和输出的内容格式不同，接下来进行详细说明。

### 3.1 关于入参

服务的入参即 OpenAI chat 请求体。示例：

```
{
    "model": "nl2sql",
    "messages": [{"role": "user", "content": "Question: 所有章节的名称和描述是什么？ <sep> Tables: sections: section id , course id , section name , section description , other details <sep>"}]
}
```

但注意 chat 请求体中的具体内容 `content`，其实是按照特定格式拼装的 prompt 字符串，主要为了针对 NL2SQL 任务提供查询问题和表结构等信息。目前服务约定的 prompt 格式有以下几种：

**i）字符串简写格式**

如上示例就是简写格式，将数据库的表名、列名、主键和外键等内容表示为一段字符串，同时按照约定格式来拼接查询问题和表信息。这种方式，要求用户自行按照约定格式来准备 prompt 字符串。

**ii）数据库创建语句格式**

这种格式的特色在于，不需要拼接数据库信息，只要给出表创建 SQL 语句即可。每种数据库由于表创建语句语法不同，因此需要单独开发适配，目前 MySQL/PostgreSQL 已支持。

数据库创建语句容易获得，所以这种方式使得用户拼接 prompt 字符串极为简单。示例如下：

```
根据以下 table properties 和 Question, 将自然语言转换成SQL查询. 备注: 无. version: v3
POSTGRESQL SQL database: superhero, with their properties:

CREATE TABLE colour (
   id integer 0 PRI not null  COMMENT 列名：颜色id；注释：颜色id,
   CONSTRAINT colour_pkey PRIMARY KEY (id)
);
COMMENT ON TABLE colour IS '表名：颜色；注释：超级英雄的皮肤/眼睛/头发/等的颜色'

Question: 一共有多少黄色眼睛的超级英雄
```

以上格式也是前端产品服务 Chat2DB 目前使用的 prompt 格式，因此用户如果通过 Chat2DB 进行交互，则由 Chat2DB 在后台自动拼接，用户对 prompt 的格式j就完全无感知了。

### 3.2 关于出参

该服务默认将请求转发给下游的模型 Chat API 服务（自己的或者第三方），然后将模型响应内容按照 OpenAI Chat Stream 方式返回，即流式的生成 SQL 代码。

### 3.3 自定义服务

整个 NL2SQL pipeline 的处理逻辑是支持自定义的，完全通过配置文件实现。

这里 NL2SQL pipeline 服务，起到编排 NL2SQL 整个处理流程的作用，从用户输入解析、提示词构造、模型推理、再到 SQL 返回后处理等，服务大致构成如下：

- 预处理，完成从用户原始请求到模型输入格式之间的转换，当然如果用户请求可直接转发给模型服务则可选
- 模型服务，模型自定义的规范输入到输出过程，调用 OpenAI-style API 模型服务
- 后处理，完成模型输出到用户响应格式之间的转换，当然模型响应也可直接返回给用户，后处理也是可选的

#### 3.3.1 内置 service 类型

在代码实现时，我们将 NL2SQL pipeline 抽象为 service，并且面向不同推理模型而内置了以下几种 service 类型：

- `base` 类型，对应定义代码 `nl2sql/service/base`，主要面向自研基础版本模型
- `seq2seq` 类型，对应定义代码 `nl2sql/service/seq2seq`，主要面向自研升级版本模型
- `openai` 类型，对应定义代码 `nl2sql/service/openai`，主要面向 OpenAI API 模型

以上每种 service 类型之间主要差异在于：

- 数据库的 db、table、column 等字符串化的定义不同
- 用 question 和 db schema 来给模型构造的 prompt 模版不同

从 service 定义的复杂程度来说，`base` < `openai` < `seq2seq`，其中 `base` 仅保留原始表名和列名，并且模型 prompt 也是简单对 question 和 db schema 字符串拼接；其中 `seq2seq` 则略微复杂些。

#### 3.3.2 预设 service 实例

以上是关于 service 类型的介绍。实际使用时，需要自定义 service 实例（就是 NL2SQL pipeline 服务），也即在 service 类型基础之上指定要装配哪些预处理和后处理组件、以及处理流程中的参数设置等。通过配置文件 `conf/config.toml` 中的 `[openai.service]` 部分进行 service 实例定义，

目前配置文件 `conf/config.toml` 已预设了几种 service 实例（NL2SQL pipeline 服务）：

**1）自研模型服务（基础版）**

该 NL2SQL 服务基于 `base` service 类型，请求路径配置为 `/nl2sql/elementary/`。

该服务基于自研 NL2SQL 基础版模型，提供基础的 NL2SQL 生成能力。预处理部分不含 schema linking，并且模型输入和输出内容格式为简单版。

目前 `base` service 类型转发给后续模型的 prompt 支持如下格式：

```
Question: 部门中有多少人年龄大于56岁？ <sep> Tables: department: Department_ID , Name , Creation , Ranking , Budget_in_Billions , Num_Employees ; head: head_ID , name , born_state , age ; management: department_ID , head_ID , temporary_acting <sep>
```

然后模型返回内容支持如下格式：

```
select count ( * ) from head where age > 56
```

**2）自研模型服务（升级版）**

该 NL2SQL 服务基于 `seq2seq` service 类型，请求路径为 `/nl2sql/intermediate/`。

该服务引入自研 NL2SQL 升级版模型+自研 Schema Linking 模型，更适用于大量数据表的工业场景，并且模型输入和输出内容格式为复杂版。

目前 `seq2seq` service 类型转发给后续模型的 prompt 支持如下版本：

v3, 表信息含 original 表名和列名以及主外键，示例如下：

```
Question: 部门中有多少人年龄大于56岁？ <sep> Tables: department: Department_ID , Name , Creation , Ranking , Budget_in_Billions , Num_Employees ; head: head_ID , name , born_state , age ; management: department_ID , head_ID , temporary_acting ; primary keys: department.Department_ID , head.head_ID , management.department_ID ; foreign keys: management.head_ID = head.head_ID , management.department_ID = department.Department_ID <sep>
```

**3）OpenAI ChatGPT 服务**

该 NL2SQL 服务基于 `openai` service 类型，请求路径为 `/nl2sql/openai/`，该服务将请求转发给类似 ChatGPT 风格的 API 进行处理。

目前 `openai` service 类型转发给 OpenAI prompt 支持以下几种版本：

**v1**

```
# postgresql SQL tables, with their properties:
# Table alignment, columns = [ id, alignment ]
# Table attribute, columns = [ id, attribute_name ]
# Table colour, columns = [ id, colour ]
# Table gender, columns = [ id, gender ]
# Table hero_attribute, columns = [ hero_id, attribute_id, attribute_value ]
# Table hero_power, columns = [ hero_id, power_id ]
# Table publisher, columns = [ id, publisher_name ]
# Table race, columns = [ id, race ]
# Create a query for question: 一共有多少超级英雄
```

**v2**

```
根据question和数据库的表信息，生成 SQL

postgresql 表信息如下：

Table alignment, columns = [ id, alignment ]
Table attribute, columns = [ id, attribute_name ]
Table colour, columns = [ id, colour ]
Table gender, columns = [ id, gender ]
Table hero_attribute, columns = [ hero_id, attribute_id, attribute_value ]
Table hero_power, columns = [ hero_id, power_id ]
Table publisher, columns = [ id, publisher_name ]
Table race, columns = [ id, race ]

Question：一共有多少超级英雄

SQL：
```

## 四、更多

**项目结构**

```
├── api                               # API 路由，主要就是 chat 接口，NL2SQL 预处理和后处理会引入到这里
│   ├── model.py
│   └── routers
├── conf                              # NL2SQL 服务配置，包含服务基础配置和 NL2SQL 组装配置
│   └── config.toml
├── app.py                            # FastAPI App
├── context.py                        # 全局单例，载入配置项
├── main.py                           # 启动脚本
├── start.sh                          # 启动脚本
├── client.sh                         # 测试脚本
├── nl2sql                            # NL2SQL pipeline 具体实现
│   ├── models                        # chat 请求和响应对象
│   ├── schema                        # mysql/postgresql 各个数据源的 schema 表示
│   └── service                       # 各个 NL2SQL pipeline 以及预处理和后处理逻辑
├── tests                             # 单元测试
└── utils.py
```
