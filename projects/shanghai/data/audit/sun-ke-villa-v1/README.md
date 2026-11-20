# 孙科别墅主楼验收

本模型对应上海市首批优秀历史建筑 **1M003 孙科住宅**。使用单位和地址按原表为「上海生物制品研究所办公楼」「延安西路1262号」；长宁区现状报道以番禺路60号表述园区入口。三处尖拱南廊、楼上四圆拱窗、小阳台和曲面开间在多个时期的照片中能相互核对，北侧车廊与屋顶转折另有照片和航拍。窗框、屋脊、后山墙与隐蔽部位采用估计。院内附楼、门卫室及花园各自保留。[官方登记](../first-batch-register-2026-11-20/register-rows.json) · [研究资料与逐张影像记录](../../../source/precise/changning-sun-ke-villa/reference-review.json)

网页近景和原始 GLB 各含 37,172 个三角面，远景 GLB 含 19,548 个。Blender 4.3.2 重开原生文件后取得 119 组可编辑网格，逐材质比对与原始 GLB 的定向三角面吻合。桌面与触屏页面均切换两种精度，并下载核对近景、远景、原始和 Blender 四件文件。[模型清单](../../../assets/models/candidates/changning-sun-ke-villa/manifest.json) · [原生及解码检查](geometry-native.json) · [网页验收](viewer.json)

南园三尖拱在所有交付精度中可穿过外墙，约两米之后才命中里面的窗或门；北面车廊从外拱口可看到后退的正门。相邻实墙、门柱与二层四个玻璃开间分别有几何对照，三份解码模型合计 30 条射线。先前南坡挡住阁楼窗、阁楼后墙开口的问题已分别用南北视图、改后文件及先前预览核对。[开洞射线](opening-rays.json) · [南园正面](changning-sun-ke-villa-preview.png) · [北车廊和屋面](north-porch.png) · [图像复核](visual-review.json)

城市原始底图将该栋标记为 `w864847877@3`，位于 `14-13718-6695`。只有要素 2445 接受裁剪，共享近景瓦片的另外八栋保留。遮罩约 334.10 平方米；最近的独立源面 1733 距遮罩约 3.36 米，距交付物投影约 3.61 米。碰撞几何来自三份实际模型的地面至两米范围，北车廊中线可通，左右门柱有实体。原粗楼的 20.75 米是栅格估计值，不能推定为主宅测量高度。[源面和固定版本](../../../source/precise/changning-sun-ke-villa/footprint-review.json) · [三档和近远瓦片的核验](footprint-review.json) · [配准合同](final-placement-contract.json)

## 复核命令

从上海项目目录运行。宏瓦片目录应包含资料登记中绑定的 `feature-table.json.gz`、`READY.json`、`far.glb` 和共享近景压缩文件，保持原相对路径。

```sh
python -B data/audit/sun-ke-villa-v1/verify-placement.py \
  --macro "$MACRO_DIRECTORY" --work /tmp/sun-ke-placement --out /tmp/sun-ke-proof
python -B data/audit/sun-ke-villa-v1/check-arches.py \
  --work /tmp/sun-ke-placement --report /tmp/sun-ke-proof/opening-rays.json
blender -b --threads 2 --python-exit-code 1 \
  --python data/audit/sun-ke-villa-v1/render-north.py -- \
  assets/models/candidates/changning-sun-ke-villa/changning-sun-ke-villa.blend \
  /tmp/sun-ke-proof/north-porch.png
```


### 96处主地图

桌面和390×844触屏均从长宁区目录进入孙科别墅，两种默认视角都能看见南园立面、红瓦坡顶和东南圆端。近距加载37,172面，远距切换19,548面；实际近景瓦片的九个建筑编号中，裁剪仅指向2445。六处地面查询符合主楼、拱廊石面、开放车道及独立柱脚的预期。北侧较远反拍的前景屋顶挡住车廊下半部，该帧用于记录真实遮挡。四件文件逐字节核对，六个主图视角的142项资源与四项登记输入已绑定。[桌面](main-desktop.png) · [手机](main-mobile.png) · [花园侧](garden-arcade.png) · [受遮挡的北向反拍](north-carriage-porch.png) · [屋顶](main-roof.png) · [远景](distant.png) · [观察记录](main-map-visual-review.json) · [真实浏览器](main-map-browser.json) · [请求资源](main-map-inputs.json) · [96处快照](production-snapshot.json)
