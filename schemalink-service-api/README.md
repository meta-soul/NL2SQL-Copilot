# Schema Linking 服务

## 一、简介

该服务对用户查询问题和数据库表进行打分截断，为下游 NL2SQL 缓解表列混淆问题，同时精准截断数据库表信息后，使得下游 NL2SQL 推理更高效。

## 二、启动

1）拷贝配置文件

```bash
cp conf/config-example.toml conf/config.toml
```

2）启动服务

```bash
sh start.sh 18022 conf/config.toml
```

3）测试服务

```bash
sh client.sh 18022 schema-linking-base
```
