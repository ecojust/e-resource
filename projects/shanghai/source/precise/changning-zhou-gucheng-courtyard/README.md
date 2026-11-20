# 泰安路115弄6号周谷城旧居庭院入口立面

上海市第一批优秀历史建筑保护编号 **1M005** 登记了泰安路115弄1–8号。长宁区规划和自然资源局记载这组住宅由美商德士古洋行于1948年建造，兼有英式与西班牙式住宅。农工党上海市委记载，周谷城于1975–1996年居于其中的6号。项目以署名6号的2014年庭院照片作为建模时相。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200331/fe7b4d6f35774b708a2c5122849065bd.html) · [区规划资源局](https://www.shcn.gov.cn/col7698/20211207/1151855.html) · [农工党上海市委资料及里弄俯拍](https://m.thepaper.cn/newsDetail_forward_10861033)

正面可辨灰白粉刷墙、门前三级台阶、木门上的浅筒瓦雨篷、两侧三联窗、浅色绞绳窗间柱、中央通长细格门窗与外凸铁栏小阳台。2019年报道中的一幅近似视图可见拱门、石栏及不同阁窗，其图下没有门牌。本件据2014年照片重建门窗和雨篷。庭院外接低屋、其余门牌、背面屋体、完整屋顶及室内待另行核实。生成器采用原创几何和材质，尺寸以实照比例估计。[2014年署名照片与作者](https://commons.wikimedia.org/wiki/File:Terrace_Houses_on_Route_Lorioz_No.6.JPG) · [2019年报道](https://www.sohu.com/a/318012443_391447) · [逐项来源与影像散列](reference-review.json)

庭院位置据房号和「周谷城旧居」两个百度地图条目核实。经坐标换算，两点均落在城市底图同一幢建筑内，距其质心约一米。底图为 Overture 汇编的东亚建筑轮廓，原生编号677。建筑群的 OSM 保护范围涵盖多个门牌。城市模型沿677的北偏西长边放置立面，保留后部以及邻体3498、1274。原生22.483米高度来自100米网格估值。该立面按实照中的两层及局部阁层估计，图后保留原生体块。[房号与坐标核对](footprint-review.json) · [地理底图来源](https://doi.org/10.5281/zenodo.8174931) · [可编辑生成代码](source/courtyard_geometry.py)

从上海项目目录生成三份 GLB、可编辑 Blender 文件和几何对照报告。依赖 Python、Blender、gltfpack、ImageMagick 和 OIDN。

    python -B source/precise/changning-zhou-gucheng-courtyard/source/build_model.py --out /tmp/zhou-gucheng/assets --audit /tmp/zhou-gucheng/audit --decoded /tmp/zhou-gucheng/decoded --gltfpack gltfpack --blender blender --oidn oidnDenoise

原创模型采用 MIT 许可。2014年参考照片由 Livelikerw 拍摄，原图为 CC BY-SA 4.0。本项目链接外部照片，底图及其来源和高度出处见地理记录。[文件清单](../../../assets/models/candidates/changning-zhou-gucheng-courtyard/manifest.json) · [单体预览](../../../zhou-gucheng-courtyard.html)
