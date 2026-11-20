# 美琪大戏院模型检查

模型以 2017 年 9 月的街角日景、夜景为主要依据。可辨认的圆顶、五扇竖向玻璃窗、三组入口、弧形灯箱和屋顶招牌以独立几何制作，长屋面、东端后台体量与背墙按屋顶影像估计。窗格、铅条和文字保留可编辑构件。[照片与年代](../../../source/precise/jingan-majestic-theatre/reference-review.json) · [模型与复建说明](../../../source/precise/jingan-majestic-theatre/README.md)

## 原生工程与渲染

原始和网页模型均有 29,644 面，远景模型有 13,580 面。重新打开 .blend 后，188 个可编辑网格的有向三角面与原始 GLB 逐材质一致。两份压缩资产独立解码后均与各自的导出输入逐面相符。另对每件 GLB 执行 30 条射线，检查五条玻璃带、六个墙柱、三组后退门、灯箱、屋面和街角外的空地，共 90 项。[原生与解码检查](geometry-native.json) · [射线结果](surface-checks.json)

初版整栋预览中，观众厅屋面的西端露出暗缝，西侧肩墙遮住一扇玻璃的斜视线。终版封闭屋顶端面、调整肩墙位置。近景渲染发现五字的字面随弧长被拉宽，随后将单字宽度与弧上字距分别设置，保留照片所见的五组独立红字。[初版预览](preflight/first-preview.png) · [初版招牌](preflight/first-sign.png) · [终版预览](jingan-majestic-theatre-preview.png) · [终版街角近景](native-street-corner.png) · [终版斜俯视](native-roof.png)

整体渲染从重开的最终原生文件使用 Cycles 48 采样生成。街角与屋顶两张补充渲染亦重开该文件，使用 Cycles 32 采样，三张图均用 Open Image Denoise CPU 后处理。三处招牌均为字体网格，笔画采用 Noto Sans CJK SC Bold 的改名子集。[补充机位](render-corner.py) · [字体来源和上游散列](../../../source/precise/jingan-majestic-theatre/source/fonts/provenance.json)

## 地图源、碰撞与共墙

整栋替换静安宏块 14-13719-6694 的对象 360。相邻对象 1995 与剧院共用东端墙线，粗面数据的离散边界本身有小片交叠。模型遵循相邻墙线向剧院一侧收进，两栋近景网格实际相距 0.229 米，远景网格相距 0.298 米。地面碰撞按实际 GLB 地面至 2 米高的三角面投影生成。剧院所在近景组的另外四栋建筑与替换边界最少相距 9.44 米。[源图与所有者](../../../source/precise/jingan-majestic-theatre/footprint-review.json) · [逐组解码与几何检查](placement-geometry.json) · [登记契约](final-placement-contract.json)

OpenFreeMap 的 z14 合并建筑对象 64634100 覆盖两栋建筑。以共墙邻栋的登记面裁去 OSM 专用边界后，对 2026 年 11 月 15 日版真实瓦片执行布尔差，邻栋保留面积为 618.902 平方米。Overture 逐独立对象标识进行替换。城市网格的近景依所属瓦片过滤，远景依原生 feature ID 过滤。[90 项地标目录的真实源检查](vector-source-checks.json) · [合并源补丁预检](preflight/merged-vector-staged.json) · [瓦片复查脚本](prepare-fallback.py) · [矢量和网格作用域检查](check-vector.mjs)

以下命令从冻结的公开瓦片重建合并矢量输入。投影审计另需下载地图依据中五个已记录 SHA-256 的宏块文件，将其保存为原始相对路径。

```sh
python data/audit/majestic-theatre-v1/prepare-fallback.py --out /tmp/majestic-fallback.json
node data/audit/majestic-theatre-v1/check-vector.mjs /tmp/majestic-fallback.json
python data/audit/majestic-theatre-v1/verify-placement.py --macro /tmp/majestic-macro --work /tmp/majestic-placement
python data/audit/majestic-theatre-v1/check-surfaces.py --out /tmp/majestic-surfaces.json
```

正式地图有 90 处入口。桌面和手机选中美琪大戏院后显示其街角门厅和两条临街外墙，近景与远景及四种下载均已验证。320 像素宽全市视图的 90 个标记都可独立点选，对 90 号的触屏实点也返回剧院；密集视图全页截屏超时另有记录。东侧邻楼内部仍是建筑碰撞，其近景包内五栋建筑均未被裁剪。105 项预发布输入中，104 项与正式字节一致，制作队列仅追加三个已核验的模型提交号。[主图实测](main-map-browser.json) · [正式登记核对](production-inputs.json) · [东邻楼保留范围](vector-source-checks.json)

## 主地图实测

90处正式目录的桌面入口可辨圆弧门厅和两条临街墙。近景可读红色 MAJESTIC 和五条竖向格窗，左下地点卡遮住部分首层入口。高处可见长屋顶与东侧邻楼，390像素竖屏也能从目录返回同一建筑。[桌面](map-desktop.png) · [街角](map-street-corner.png) · [屋顶及东邻楼](map-roof-and-neighbor.png) · [手机](map-mobile.png) · [图像复核](main-map-visual-review.json)

原剧院360所在近景组只裁这一项。东邻1995的近景组实际加载，裁剪三角数为0。剧院本体和邻楼各有建筑碰撞，入口外两处街面都可通过。浏览器实测近、远景切换，鼠标与320×568触屏均命中90个编号并可选中剧院，四个下载文件的长度和 SHA256 与清单一致。窄屏密集灯牌的额外全页截图在合成时超时，触屏返回记录和四个建筑画面均已保留。[运行记录](main-map-browser.json) · [正式文件比对](main-map-bindings.json) · [街面探点](map-probes.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 28 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/3a9062204c4ef87cad6015f79f3cf4f6ee9b8b24/projects/shanghai/index.html#landmark=jingan-majestic-theatre&mode=overview) · [固定版本逐文件核对](publication.json)

首次读取 master 的 28 个链接时，有 13 项仍返回旧版本。[首次 master 核验](publication-master-initial.json)

[上海市房屋管理局首批保护编号及门牌核对](../first-batch-register-2026-11-20/README.md)
