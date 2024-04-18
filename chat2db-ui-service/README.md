## 用法

Chat2DB 编译后的 JAR 包 `chat2db-server-start.jar` 保存在该目录下，然后通过如下命令启动服务：

```bash
sh start.sh
```

## Docker 镜像构建

由于 Chat2DB 服务启动时需要下载 Java 依赖包，为了避免启动时下载，这里将其打包在镜像中。需要将本地目录 `~/.chat2db/jdbc-lib` 中的内容，复制到当前目录中，然后再执行镜像构建命令。
