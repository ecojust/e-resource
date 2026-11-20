# 独立叠加模型主图验收

吉祥里西弄门、愚谷邨北门和景华新邨12号均保留原有建筑地块。每个目录的 `city-actions.json` 记录要检查的源建筑编号、内部采样点、门前镜头以及地面证据。脚本从相邻两个真实站点分别读取当时的目录、运行模块、原生宏块与涉及的近景文件，核对SHA-256。普通精模替换了近景组文件时，按该版精细建筑清单核对源组与实际交付文件。

下列命令从上海项目根运行。传入两站各自签署的 `*-production.json`。`before`、`after` 每轮使用一个浏览器，串行运行。后态需要前态浏览器完成的收据，脚本核对它是否确为新地图的直接前身。追加检查请使用新的输出目录。`inputs-before` 或 `inputs-after` 只核对真实站点输入。

```bash
node data/audit/jixiangli-west-gate-v1/check-independent-city.cjs \
  data/audit/jixiangli-west-gate-v1/city-actions.json before \
  http://127.0.0.1:22147/ /tmp/shanghai-dense-owner-clipping/scenes/147-production.json /tmp/jixiang148/map-before
node data/audit/jixiangli-west-gate-v1/check-independent-city.cjs \
  data/audit/jixiangli-west-gate-v1/city-actions.json after \
  http://127.0.0.1:22148/ /tmp/shanghai-dense-owner-clipping/scenes/148-production.json /tmp/jixiang148/map-after \
  /tmp/jixiang148/map-before/before.json
```

前态从上一处模型的正常入口进入，在同一机位等待最近的原生近景组就绪后记录原貌。后态在桌面用鼠标、在手机用触摸从街区地图上实际点选目标灯牌；若界面聚合灯牌，继续点选分组内的建筑。截图检查默认双端、近看街面和远景，并记录模型档位、面数、相机、像素文件与实际浏览器接收的模型字节摘要。对每个相邻源建筑还核实其所在近景组、未裁源号及建筑内部地面。最后从建筑目录进入单体页，逐个点击四个下载项并校验文件内容。
