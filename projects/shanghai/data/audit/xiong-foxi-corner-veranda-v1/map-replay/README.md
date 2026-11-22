# 熊佛西楼转角外廊地图复核

第323期冻结城市有358个模型，第324期加入熊佛西楼后有359个。两个版本均从对应城市服务读取实际的几何、矢量和渲染模块，逐项核对摘要。六个加载状态各检查120个地面点、864个高程采样及原建筑2769与相邻屋的近远裁切。checked 文件记录相应实测读数。

在本目录使用支持 registerHooks 的 Node.js 运行下列命令。SHANGHAI_ORIGIN 可指定提供该版本的站点，默认分别连接本地31323、31324。工程文件按上海项目目录寻找。单独复制本目录时可通过 SHANGHAI_PROJECT_ROOT 指定项目根。

```sh
node replay-map.mjs 323 runtime-323.json
node replay-map.mjs 324 runtime-324.json
```
