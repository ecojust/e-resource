# 新恩堂西门廊地图复核

第322期的城市有357个模型，第323期加入新恩堂西门廊后有358个。两版完整目录均可按同目录 comparison 文件的 SHA-256 核对。程序读取相应版本的渲染模块，比较原建筑3149的近远景裁切、两侧券门、66处地面和分高度的遮挡，并保存六个加载状态。checked 文件保存当期实测。

在本目录用支持 Node.js 模块注册钩子的 Node.js 版本运行。默认从相应的本地31322或31323站点读取冻结资源。可用环境变量 SHANGHAI_ORIGIN 指定承载对应版本的其他站点。

```sh
node replay-map.mjs 322 runtime-322.json
node replay-map.mjs 323 runtime-323.json
```
