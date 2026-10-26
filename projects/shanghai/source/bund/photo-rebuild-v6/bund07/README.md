# v3：两扇正面大拱窗格框的小更正

本版只基于已渲染的3325262c候选替换左右两扇首层大拱窗格框：4列×4行，顶行约36%、下三行各约21.33%。照片的三条粗横框与细密百叶线分开核对；百叶不冒充新增实体格框。高度分配是照片比例估计。

新控制点见`arch-grid-controls.json`；执行`python check_arch_grid_revision.py --baseline-dir /path/to/shape-refined/bund07`核验实际GLB：除两块目标frame-grid，其他构件POSITION/NORMAL/UV三角数据、照片和材质必须字节不变。上一次形态修正版的三项纠正已由实际正交及校准透视预览核对；v3已由root与独立review实际查看最终校准透视图，限定增量外观通过；网页验收仍待完成。

下文是承接的前一阶段说明，属于完整源码链；其后屋顶、门、材质、字牌参数本次不再调整。

# 07 照片形态复核修正版（独立 staging）

本版基于玻璃嵌框候选 `77a72f…`，保留该候选历史，不修改生产目录或共享 common。

- 后屋顶改为左右各两处矩形灯窗加弧形石帽、中央独立三角；删除无据的第五个同款拱窗。2016近正面提供拓扑，2025确认可见上部；被前女儿墙遮挡的下部仍有年代/存续不确定性。
- 原后退10.5m无法解释2025低相机的可见部分；本版按固定相机、中央顶点及蓝沿控制点选择约3m退距、22.25m上沿、22.5m三角尖。这是条件估计，必须结合新透视预览检验，不能称测绘。
- 首层中央独立铁门；四侧方口3列×5行，上2行偏暗、下3行偏浅。底部遮挡处比例为估计。
- 金属顶采用更细曲面与接缝，保持原名义冠高。深色、缝距仍为照片估计。
- 中文、泰文、英文为实体字；Garuda分层轮廓更完整，细雕与卷带小字仍未复原。

最终原生校准透视证据见 `visual-acceptance.json` 和 `previews/bund07-photo-perspective.png`，其中明确保留非扫描精度、材质/雕饰简化及browserpending范围。新增几何证据见 `visual-refinement-controls.json`，相机入口为 `photo_camera.py`；旧玻璃阶段说明 `GLASS_FIT.md` 是历史范围，不能将其“全部非玻璃不变”套用到当前形态改动。当前保留18片上层照片玻璃的实际位置/法线/UV/索引及原JPEG不变，另以 `check_visual_refinement.py` 对指定历史输入逐项验证。

# 外滩 7 号：逐栋照片几何重建

本包针对大北电报公司大楼（现盘谷银行），身份为 OSM way 178408810 版本 7；不是延安东路 34 号的另一幢电报大楼，也不含邻楼 6 号或 9 号。原五边轮廓及地理锚点冻结在 `geometry-input.json`，临江原边 3 长约 29.33 m，OSM 数据不等同测绘尺寸。

模型有四层主体、正面 3+5+3 轴、三层中央实体分隔双窗、两端宽扁拱底窗、中央独立铁门及四个侧方矩形开口、圆柱及壁柱、交替三角/弧形山花、独立窗框和真实墙洞。两端屋顶采用封闭切角圆矩形低金属顶，正面弧山花有真实椭圆孔，屋顶鼓座侧窗也开孔。南侧与北侧分别按照 2025 与 2012 的可见构件处理；南侧采用两端三窗组与中间三窗、后方平檐，不镜像北侧曲顶。

六扇无遮挡的中央三、四层窗包含 18 块独立照片玻璃，来源为 Suicasmo 的 2025 CC0 原图。原 JPEG 字节直接嵌入 GLB，没有改色、裁切存储或生成替代图。各玻璃内部安全区域单独配准，窗框、墙面、铁栏、灯杆和人物没有贴到模型上。照片采样会略裁去窗片边缘；不能据此推断完整室内布局。其他窗户保留几何材质。原图控制见 `photo-glass-controls.json`；`photo-glass-inspection.png` 是采样检查图，不是纹理。

`calibration.json` 列出建筑参数；`calibration-independent.json` 及其控制点文件由独立相机校准产生。层高、柱径、窗宽、退距、穹顶剖面均为有依据的估计，`height_is_measured` 始终为 false。后墙无可靠照片，采用保守无窗墙而不虚构逐栋核验；完整屋顶平面、侧后接顶和被遮挡下层仍有缺口。北侧 2012 曲顶的当前存续及真实后退距离未实测。银行 Garuda 徽记以照片可见羽翼、冠、躯干、屈腿、下垂饰和卷带构成分层简化浮雕，实体字使用许可字体近似，不是银行标志的精确描字；泰文「ธนาคารกรุงเทพ」按原图可读字样及银行官方名称交叉核对；采用 Noto Sans Thai 的 OFL 字形与冻结 HarfBuzz 字位，包含下加元音。不是按照片精描银行字体。旗杆保留，不将某次照片的临时旗面固定为永久状态。

## 重建

要求 Python 3、NumPy、Shapely 2.1 或更新版本，以及 fontTools。`common` 与本目录同级；所用 `BundSignSubset-v6-1.otf` 及许可随共用源包提供。无需 `/workspace` 绝对路径、网络服务或生产目录。

```sh
python build_model.py --output ./output
python check_geometry.py
python check_photo_uv.py --output ./output
python check_visual_refinement.py
python photo_camera.py --check --report output/camera-check.json
python verify_source_package.py --rebuild
```

第一条生成自包含 `bund07.glb` 与构件统计；后续命令中，第二条重建默认 `output` 并检查实际 FLOAT32 构件的边关联、绕序、有限值及正体积；第三条核查最终 GLB 的原图字节、UV、单一照片材质和署名；第四条核查当前正面玻璃嵌框深度，可用显式历史输入核查变更范围；第五条仅验证相机数值变换，不执行 Blender。每件资源必须小于 100,000,000 字节。原生 `.blend` 与预览由主流程用共用 `blender_finish.py` 调度，不由此脚本启动渲染。

几何闭合和 UV 数值检查不能替代照片形态/场景验收。当前原生预览和网页验收由主流程继续完成，结果另存，本文不把几何/UV 数值通过称为视觉验收。旧 77a72f 候选已实际渲染并发现具体形态问题；本版纠正这些问题，新视角验收尚待主流程执行。

## 来源与许可

代码为 MIT。照片逐张许可、作者、日期和原图链接保留于 `research/SOURCES.json` 与原图元数据。2025 Suicasmo 为 CC0，唯一嵌入模型的照片；2012 Ferox Seneca 为 CC BY-SA 3.0、2016 xiquinhosilva 为 CC BY 2.0、2024 Chainwit. 为 CC BY 4.0，作为保留署名的几何参考原图提供；1908 书籍插图为 Commons 标注公有领域。中文/Latin 字体按 SIL OFL 保留 `common/fonts/FONT-LICENSE.txt`；泰文字体许可在 `fonts/OFL-NotoSansThai.txt`，来源、原字体 SHA、子集 SHA 及固定字位见 `thai-sign-layout.json`。正常重建无需网络或 HarfBuzz，HarfBuzz 仅用于产生已冻结的字位。冻结足迹来源为 OpenStreetMap / Overture，按 ODbL-1.0 标注。官方地方志仅引用必要事实和短句，不再分发网页缓存。

来源研究与可观测/推定表见 `research/README.md`、`research/geometry-observations.json`。最终源码清单只包含重建依赖、校准、许可原图和必要证据，不包含原生模型、输出 GLB、网页缓存或下载错误响应。
