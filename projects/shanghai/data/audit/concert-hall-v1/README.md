# 上海音乐厅现址外观核验

本批记录 2003 年迁址后黄浦区延安东路 523 号的上海音乐厅。西北主入口、倒角、东北长立面、东南入口和中央双坡屋顶有可辨认的照片或航片参照。西南立面、屋面分段、设备和部分构件尺寸采用估计。建筑内部、搬迁前的地点和构造未纳入本模型。[参考资料](../../../source/precise/huangpu-shanghai-concert-hall/reference-review.json) · [模型制作与重建](../../../source/precise/huangpu-shanghai-concert-hall/README.md)

Blender 4.3.2 重新打开交付的原生文件后识别出 119 个可编辑网格。原始及网页 GLB 各含 42,960 个三角面，远景 GLB 含 23,764 个。几何检查从压缩文件解码索引、材质和顶点，并核对定向三角面。单体页已验证桌面和移动端的两个精度及四种文件下载。[模型清单](../../../assets/models/candidates/huangpu-shanghai-concert-hall/manifest.json) · [原生与几何检查](geometry-native.json) · [双向外观复核](native-visual-review.json) · [单体页检查](viewer.json)

现址底图要素为 `w133465370@12`。城市模型瓦片 `14-13720-6694` 的共享近景组包含音乐厅 2500 与邻楼 199。两枚遮罩三角形仅处理 2500，碰撞轮廓依据交付网格中的地基和入口台阶生成。[原始要素、保留对象与脚下范围](footprint-review.json) · [落位参数](final-placement-contract.json)

88 处版本的真实主地图从黄浦目录打开音乐厅。桌面和 390 × 844 触屏均选中第 88 号地标并显示网页近景；15.5 级远景实际切换为 23,764 个三角面的 GLB。西北、东南和屋顶三处近景均装入包含 2500、199 的原始共享瓦片，三次均仅裁剪 2500。六张截图经逐张检查，桌面主图的信息卡会遮住近景入口的一部分，可从建筑独立页查看无遮挡视图。[浏览器与下载记录](main-map-browser.json) · [六张图片的复核](main-map-visual-review.json) · [桌面地图](main-desktop.png) · [触屏地图](main-mobile.png) · [街区远景](distant.png)

本次运行中，桌面首次读取全域城市细节目录触发了应用的 25 秒超时，并有邻近建筑加载超时的警告。通过原地图加载器重读同一份目录后取得共享近景；浏览器运行完成，保留原告警和重试结果。服务端记录及本地脚本共同绑定了 150 份站内资源及检查输入，并另存 4 份目录生成记录，支持和对应发布修订逐件核对。[加载重试](detail-index-retry.json) · [输入字节记录](main-map-inputs.json)

## 复核主地图

从上海项目目录启动本地网站，确保地图、PMTiles、近远景城市瓦片和建筑资产能够从同一站点成功读取。浏览器脚本需要 Playwright 与 Chromium。下面的输出目录须为空。

```sh
QA_OUTPUT_DIR=/tmp/concert-hall-browser \
MODEL_BASE_URL=http://127.0.0.1:8784/ \
CHROMIUM_PATH=/usr/bin/chromium \
node data/audit/concert-hall-v1/check-main-map.cjs
```

若首次进入桌面地图时确实出现同样的细节目录超时，可用 `QA_CDP_PORT=9376` 启动主脚本。收到应用的超时告警后在另一终端执行 `QA_CDP_ENDPOINT=http://127.0.0.1:9376 QA_RETRY_REPORT=/tmp/concert-hall-browser/detail-index-retry.json node data/audit/concert-hall-v1/retry-detail-index.cjs`。重试脚本会验证浏览器确实记录了该警告。

使用项目内的散列验证服务时，另可从专用服务的 `served.jsonl` 记录重建本次所有站内 HTTP 资源的字节清单。范围请求记录完整源文件的散列。

```sh
python data/audit/concert-hall-v1/check-map-inputs.py capture \
  --server-log "$SERVER_LOG" \
  --browser-report /tmp/concert-hall-browser/main-map-browser.json \
  --inventory /tmp/concert-hall-browser/main-map-inputs.json

python data/audit/concert-hall-v1/check-map-inputs.py verify \
  --browser-report /tmp/concert-hall-browser/main-map-browser.json \
  --inventory /tmp/concert-hall-browser/main-map-inputs.json
```

正式登记后的地图复核了本次浏览器使用的 150 项 HTTP 资源和 4 项目录生成输入，全部与实测版本一致。[正式登记输入核对](main-map-production-inputs.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 26 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/413694b1a740fd216a7ecf3c6d6b3519553cb9ec/projects/shanghai/index.html#landmark=huangpu-shanghai-concert-hall&mode=overview) · [固定版本逐文件核对](publication.json)

同一组 154 项输入也已对照 GitHub 模型提交逐项复核。[提交输入核对](main-map-commit-inputs.json)

首次读取 master 的 26 个链接时，12 项仍返回旧缓存。固定提交的链接已通过全部检查。[master 首次实测](publication-master-initial.json)
