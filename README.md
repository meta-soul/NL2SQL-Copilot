<div align="center">
<img src="./docs/logo.png" alt="icon" width="120px"/>
<h1 align="center">NL2SQL APP</h1>

输入查询描述 极速生成 SQL 代码

支持 MySQL / PostgreSQL 等常用数据源

</div>

## 概述

**NL2SQL Copilot** 是一款利用 NL2SQL 生成模型，辅助开发人员提升 SQL 代码编写效率的工具。该工具专注于利用大模型来解决真实工业场景下 SQL 开发的难点、痛点，同时我们通过引入 Chat2DB 进行二次开发，极大的简化了多数据源对接和管理难题。此外还搭载了开源自研的工业场景 NL2SQL 生成模型，具备多领域泛化性、精确捕获查询意图、高速推理生成等特点。NL2SQL Copilot 提供全套服务和模型，实现了工业场景下的开箱即用。

## 快速安装

目前 NL2SQL Copilot 主要有 Client APP 和 NL2SQL 两类服务：

- Client APP 服务，是基于 Chat2DB 二次开发的，含有前端 NL2SQL 交互、数据源和配置管理等功能。该服务已编译为 jar 包，任何需要使用 Copilot 产品的用户均需要单独安装自己的 Client APP。
- NL2SQL 服务，该服务用来提供 NL2SQL 能力，完全基于我们自研 NL2SQL 模型。并非每个用户都需要部署该服务，您可以在 Client APP 中配置 OpenAI API 或者其它人已部署的 NL2SQL 服务。

### Client APP 安装

NL2SQL Copilot 用户都需要单独安装自己的 Client APP 服务，用于数据源、配置的管理，以及 NL2SQL 功能的前端交互。

安装步骤如下：

1. 前往项目 releases 页面下载**最新版本** jar 包

2. 确保机器上已安装 **JDK 18**，运行如下命令来启动服务

    ```
    version=v1.0.2
    nohup java -jar -Dserver.port=18020 chat2db-server-start.${version}.jar > chat2db-server-start.log 2>&1 &
    ```

3. 浏览器打开 <http://127.0.0.1:18020/>，如通过反向代理配置域名则替换为相应的域名来访问服务

4. 点击数据源管理面板，添加自己的数据源（即配置自己的数据库连接串），确保服务部署的机器可连接该数据源

5. 配置 NL2SQL 服务，即配置需要哪种服务来提供 NL2SQL 功能，当前有这些服务可以使用

  - **OpenAI** 以及类似服务商的接口，配置提供 `Api Host` 和 `Api Key` 即可
  - **自研-elementary**服务接口，配置提供 `Api Host=http://<host:port>/nl2sql/elementary/` 和 `Api key=ak_311e0e1b-2e4a-44b6-8213-ae19b6fccb81`
  - **自研-intermediate**服务接口，配置提供 `Api Host=http://<host:port>/nl2sql/intermediate/` 和 `Api key=ak_311e0e1b-2e4a-44b6-8213-ae19b6fccb81`

### NL2SQL 服务部署（可选）

由于 NL2SQL 服务涉及到模型推理服务，因此最好部署在高性能的 CPU/GPU 机器上。

NL2SQL 服务由以下几个服务组成，应该按照先后次序部署：

1. [model-openai-api](model-openai-api/README.md)

自研 NL2SQL 模型的 OpenAI-style 接口封装。

2. [schemalink-service-api](schemalink-service-api/README.md)

在实际业务场景中，由于数据库存在较多数据表，全部作为输入传递给模型，存在推理性能和语义理解方面的挑战，因此往往需要引入 schema linking 机制，作为一个预处理模块，仅将当前查询相关的表和列结构传入给 NL2SQL 生成模型。

3. [nl2sql-openai-api](nl2sql-openai-api/README.md)

为应用提供 NL2SQL 服务，含 OpenAI 以及自研服务。该服务并非实际模型推理服务，而是一个转接服务，包含了 NL2SQL 业务相关的逻辑，是应用服务和模型服务之间的中间桥梁。在该服务中 NL2SQL 服务被定义为一组模型组件构成的流水线处理，完全基于配置来构造一个 NL2SQL 服务实例。

## 更多

- [数元灵科技荣登“千言数据集-语义解析”权威评测榜首，让湖仓智能触手可及](https://zhuanlan.zhihu.com/p/625128670)
