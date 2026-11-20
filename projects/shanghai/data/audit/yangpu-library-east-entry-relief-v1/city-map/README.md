# 原有图书馆入口的真实城市地图对照

两次分别从含122处入口的旧版和新版直接打开 `index.html#landmark=yangpu-library&mode=walk`，用生产应用的普通建筑目录和原有 `yangpu-library` 标识显示这座馆。两次均读到 `14-13722-6690`，单个选中模型实际装载，目录无失败，WebGL无错误。进入城市俯瞰后将相机拉远，记录实际模型档位和远景资产。[旧版原始运行](before/ordinary-map.json) · [新版原始运行](after/ordinary-map.json) · [四图检查](comparison.json)

| 同一地图入口 | 实际近景 | 实际远景 | 浏览器实收签名 |
| --- | ---: | ---: | ---: |
| 旧V13 | 365,524面 | 122,688面 | 6项 |
| 东门修订版 | 390,432面 | 139,556面 | 6项 |

新版步行机位的拱券、拱内扇形纹和原V13出现可辨差别，保留的主楼和两翼位置一致。默认图上的建筑灯牌覆盖门扇下半，双扇细节可在独立浏览器的近摄中查看。四份正式下载、宏索引及普通目录另用真实HTTP读取，共43,835,951字节，全部核对SHA-256。[旧版步行](before/east-entry-walk.png) · [新版步行](after/east-entry-walk.png) · [旧版俯瞰](before/city-lod.png) · [新版俯瞰](after/city-lod.png) · [六项独立下载](../download-http.json)

复跑需要Node、Playwright和Chromium。`MODEL_BASE_URL` 指定相应版本的项目根网址，`QA_OUTPUT_DIR` 指向空输出目录。旧版设置 `QA_SNAPSHOT=before/inputs.json` 后执行 `node before/check-map.cjs --control`。新版令 `QA_SNAPSHOT` 指向含 `files` 签名表的东门修订版冻结清单，再执行 `node after/check-map.cjs`。可通过 `CHROMIUM_PATH` 指定系统浏览器。
