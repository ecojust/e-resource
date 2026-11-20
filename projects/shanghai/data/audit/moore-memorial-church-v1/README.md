# 慕尔堂（沐恩堂）

现存西藏中路316号建筑包括两个伸向街面的附楼山墙、退后的礼堂山墙、尖拱花窗与石色门廊，方钟塔在礼堂西南侧。房管局首批表登记为「基督教慕尔堂｜沐恩堂」，编号1A018。[身份、照片和建造年代](../../../source/precise/huangpu-moore-memorial-church/README.md)

## 模型与实测

原始和网页近景均为65,940个三角面，远景42,364个。Blender重新打开后有181个可编辑网格。目检原生渲染可见三个独立的山墙轮廓，两个附楼的双层凸窗、礼堂花窗、两层钟塔长窗和红十字架。塔尖最高点估计42.83米。后部附屋和屋面分界依两期航片简化。[Blender渲染](huangpu-moore-memorial-church-preview.png) · [原生和解码检查](geometry-native.json) · [尺寸依据](elevation-estimates.json)

三档各26条射线核验凹入玻璃、木门、门廊、钟楼上下尖券、十字铁件、附楼屋面及留空的四处地面。近景的百叶与屋面瓦行更密，远景保留主要开口。[三档78条实测](surface-probes.json)

## 地图位置与邻栋

登记原楼为 `14-13720-6694 / 2297`，同一近景组还有1514。按三个成品网格在两米步行高度下的形体生成碰撞。西边前院、南侧两栋之间、东面院角和西藏中路人行空间均在范围外。原建筑近景与远景的实际投影被完整裁剪，最近的邻楼2641距裁剪边界2.66米，另侧1470距3.47米。[地面与两档投影](placement-geometry.json) · [登记契约](final-placement-contract.json)

OpenMapTiles 备用建筑106284410同时覆盖目标和邻楼1470，另一要素513173390覆盖邻楼2641。针对真实图块运行项目矢量裁剪，目标原先占1,704.87平方米，裁后为零。两邻楼各自保留1,594.60和1,986.62平方米。[备用底图核验](vector-source-checks.json)

```bash
cd projects/shanghai
python -B data/audit/moore-memorial-church-v1/check-surfaces.py --out /tmp/moore-surfaces.json
python -B data/audit/moore-memorial-church-v1/verify-placement.py --macro /tmp/macro-14-13720-6694 --work /tmp/moore-placement --out /tmp/moore-audit
python -B data/audit/moore-memorial-church-v1/prepare-vector.py --out /tmp/moore-vector.json
node data/audit/moore-memorial-church-v1/check-vector.mjs /tmp/moore-vector.json /tmp/moore-vectors-checked.json
```

## 真实主地图

108处的前态载入原生近景组2297和1514，均保留。109处从黄浦区目录点选沐恩堂，三处近景和屋顶视角都实际载入同一原生组，仅2297收到模型裁切。11处地面及楼内点、桌面鼠标、390像素触摸、近远景切换和四件下载哈希通过。实读的164项服务器资源与四项目录生成输入逐项一致。[前态](before-browser.json) · [六个真实视角](main-map-browser.json) · [HTTP核验](main-map-input-check.json)

在调整尚贤坊视角之前拍摄的109处版本中，1280×800默认桌面可见礼堂三处山墙、红瓦坡屋和钟楼。选中名称遮住了门廊一角。840×610时邻近名称占用中心位置，390×844则主要是选中名称遮住部分门廊。近景和单体查看器可观察钟楼、窗与门洞。[正常桌面](main-wide.png) · [各张画面的目检](map-visual-review.json) · [三座山墙](three-gables-and-porch.png) · [真实屋顶](sanctuary-roof-and-neighbors.png)

后续尚贤坊起始相机调整后，沐恩堂所在109处版本的219个冻结输入均已从正式预演服务器以HTTP 200逐件读回并校对。[219项完整字节核验](gate300-snapshot-http.json)

同一新版的单体查看器实测了1250×820和390×844。两个尺寸都能完整看清三处山墙与钟楼，完整和远景模型均保留红十字架、尖券塔窗、礼堂中央门廊与两侧凸窗。四个下载文件与模型清单匹配。[单体四视角和下载](viewer.json)

两次场景之间，尚贤坊门楼的默认镜头有调整。其余可拟合镜头的建筑在三种窗口尺寸下共有204组计算，取景参数一致。[场景输入及目录差异](camera-input-revision/input-difference.json) · [逐栋镜头核对](camera-input-revision/camera-arguments.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 35 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/c7cd6eabd440708bd705b920b91e10e5e6e3931b/projects/shanghai/index.html#landmark=huangpu-moore-memorial-church&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 35 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
