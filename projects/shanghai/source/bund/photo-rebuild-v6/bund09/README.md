# 外滩9号独立重建候选 · roof-continuity-v3

目标：中山东一路9号轮船招商总局大楼，不能与6号中国通商银行、16号招商银行混淆。资料、许可、原文和逐项观察见 [RESEARCH_REPORT.md](RESEARCH_REPORT.md)、[photo-observations.json](photo-observations.json)、[history-sources.json](history-sources.json)。照片最新为2025年5月，部分北侧细节仅有2013年证据。

```sh
python build_model.py --output output
python check_photo_uv.py --output output
python check_roof_revision.py --before /path/to/retained-visible-detail-v2/output/bund09-raw.glb --after output/bund09-raw.glb
```

当前为`roof-continuity-v3`：修复第二版实际预览中南侧短翼与圆角坡面交界的漏瓦。瓦片沿同一连续屋面高度函数裁切，保留完整有效边片，不用平盒填缝。照片观察、有限厚度瓦片、分区和误差范围见 [ROOF_REVISION_V3.md](ROOF_REVISION_V3.md)。第二版raw、原生、渲染和外观复核仍保留在独立相邻`bund09-visible-detail-v2`stage，基准raw哈希为`7e38b487…`，没有覆盖。

仅两种灰瓦材质网格改变；`check_roof_revision.py`要求其他十种材质的全部实际GLB属性和索引逐值不变，包括672块嵌框拱窗玻璃、原JPEG与全部UV、四座放射分缝石券、两座阳台角柱、字牌、砖墙和后部屋顶封口。外廊后墙仍退1.85米，玻璃前脸仍比框前面后退20毫米、厚20毫米。中央阳台九根瓶栏继续标为估计，未凭斜照能见数量强改总数。`check_visible_detail_revision.py`和`check_glass_inset.py`保留作历史核查工具，不用于声称本版所有非玻璃几何与更早版本不变。

需普通Python环境的numpy、Shapely2.1+、Pillow、fontTools。共享代码使用相邻`../common`，本栋不修改公共helper；实际native、压缩与固定相机渲染由根任务统一完成。本目录尚不代表发布或浏览器验收。

`geometry-input.json`冻结OSM19个顶点、edge17、Overture与原城市归属。主体保留地图轮廓；外廊并非实心贴柱墙：外侧只有端墩、柱列与栏杆，后退红砖墙开真实拱孔。二、三层分别为塔司干、科林斯柱式，每层12处圆柱／贴柱位置；后墙五组`2–1–1–1–2`拱窗。北侧三窗轴、南侧短翼窗与源折线转角分别处理。

几何含独立瓶状石栏杆、中央前出门廊和阳台、逐窗框分格、砖券与石拱脚、实际坡屋顶、两个正面山花和北侧三处有年代限制的屋面构件。砖缝、灰瓦盖瓦、檐口卷饰、山花叶饰与柱头为有照片依据的比例近似；不是扫描或逐块测绘。

2025入口金字按实图从右向左读作“輪船招商總局”，模型从左向右排“局總商招船輪”。独立金字实体使用本栋`fonts/Bund09SignSubset.otf`，许可及源字体哈希随包保留；字形可读但不是原书法的描摹，未修改公共字体子集。

照片只映射到南侧短翼两个完整可见窗的20块矩形玻璃。二层有上三排、厚横梁和下四排，三层有三排；逐片源像素四角在 `photo-glass-controls.json`，检查图在 `references/glazing-controls-review-floor*.png`。JPEG原字节嵌入，玻璃以外材料不贴整幅立面。拱顶扇窗、树遮挡区域、外廊后遮挡窗、地面杂物均不强行投影。

高度、廊深、窗宽、屋顶背部和雕饰轮廓是照片比例估计，绝对标高未测绘；`building:levels=5`原值保留但不生成五层。南侧部分底层孔为对应上层及露出片段的推定，完整后立面不开虚构窗阵。具体校准和推定边界由`calibration.json`及独立metric文件说明。

所有原始照片及检查裁图见 `references/manifest.json`。P01为Suicasmo CC0；P02/P03为Legolas1024 CC BY-SA4.0，只作有日期的形制观察，不嵌入模型。官方网页HTML/TXT只作内部研究缓存，不应随公开资产包整目录复制。程序几何MIT，地图保留OSM/Overture ODbL署名。

候选冻结、实际字节数与三角形数见 `MODEL_CANDIDATE.json`、`output/photo-uv-check.json`，生成及打包均要求每个文件低于100,000,000字节。公开源码按`PUBLICATION_SOURCE_FILES.json`复制，避免把完整官方新闻缓存混入。近景原图解码约71.7MB，远景打包使用`--lod-without-photos`保留几何、以说明过的近似玻璃材质替换照片；原始、网页近景与原生工程保留原图。`native-safety/README.md`提供压缩保存、完整有界解压与独立Blender重开核验方案；实际入仓文件需低于100MB，解压后的内存布局另受512MiB安全限额约束。公共helper保持冻结。
