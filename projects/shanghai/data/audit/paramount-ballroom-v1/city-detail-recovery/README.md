# 精细城市底图目录超时后的恢复

在涌泉坊的真实主图中，初次加载一度只保留旧版底图，手动重新选择精细目录后恢复。裕华新村首次加载时另有一条明确的目录超时记录。两个请求均早于百乐门版本。[涌泉坊原始记录](../../bubbling-well-lane-v1/preflight/detail-retry.json) · [裕华新村原始记录](../../yuhua-residence-03-v1/preflight/revised-first-load.json)

复现时，真实 HTTP 服务声明精细目录共 1,097,700 字节，发送 32 字节后停住。原程序在 25 秒时限后取得 4,005,757 字节的普通目录，此次会话一直停留在普通底图。更改后，普通目录于第 26.230 秒生效，精细目录通过一次后台重试于第 26.378 秒生效。记录包含每次实际传输长度、顺序、散列及应用传给地图接收端的目录。接收端在此项测试中受控，完整 WebGL 场景另行验收。[修正前](http-before.json) · [修正后](http-after.json) · [HTTP 测试程序](http-check.mjs)

回归用例包含请求竞态、场景销毁、无效目录、网络超时及远近模型切换，共 63 项通过。[测试输出](extended-regression.log) · [地图目录测试](../../../../tests/city-detail-map-integration.test.mjs)
