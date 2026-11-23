# 南京饭店山西南路入口核验

[查看三维模型](../../../nankin-hotel-shanxi-front.html) · [建筑来源及制作范围](../../../source/precise/huangpu-nankin-hotel-shanxi-front/README.md)

现状模型取山西南路西立面中央六个开间。街墙在每道窗洞处实际开口，两层阳台都有前缘折角、可站立的楼板和镂空金属栏杆。门廊凹入街墙，三块雨篷分开悬挑。铜色酒店牌和深绿色邮筒位于入口南侧。四个街景机位记录了入口里程，拍摄日期是 2019 年 5 月 17 日。[入口原图及机位](../../../source/precise/huangpu-nankin-hotel-shanxi-front/entrance-camera-sources.json)

原始 GLB 和压缩近景各有 37,872 个三角面，压缩远景有 17,448 个。分别从三个文件重读三角面，每档检查 142 条射线，覆盖门扇、前沿、肩部、铁栏和台后窗。后退的六层窗带按照片估算。街面视角无法辨认的七层窗位未收录。[三档几何实测](preflight/geometry-rays.json) · [逐材质压缩比对](preflight/decoded-surface-comparison.json)

下列图由交付用的原始几何独立投影，包含真实材质、遮挡和投影阴影。

- [西墙全景](preflight/west-front.jpg)
- [山西南路斜看六开间](preflight/shanxi-road.jpg)
- [三片雨篷、木框入口和门前邮筒](preflight/door-and-mailbox.jpg)
- [铜色酒店牌和深绿色邮筒](preflight/bronze-and-postbox.jpg)
- [四、五层的十二座钝角阳台](preflight/angled-balconies.jpg)
- [镂空铁栏与台后窗](preflight/iron-work.jpg)
- [六层退台](preflight/upper-setback.jpg)

## 城市主图中的南京饭店

本期将山西南路西墙的六个开间接入城市主图，主图目录由 312 处增至 313 处。四层和五层各有六座钝角阳台，每座前缘的尖端和两肩都在三档交付几何上复测过。门廊向内凹进，三块雨篷分别悬挑，入口南侧保留铜牌和邮筒。

桌面鼠标和手机触屏分别从地图标记返回南京饭店。主图留存了十幅城市截图，包括山西南路方向的街面、屋顶、三片门篷以及上层阳台。主图逐点核验了 58 个地面及相邻建筑位置。独立页分别在桌面和手机重开近景和远景，四个下载文件均按实际保存的字节验证。主图库与独立页的十四幅截图可逐张对照核查记录。

[打开城市主图](../../../index.html#landmark=huangpu-nankin-hotel-shanxi-front&mode=overview) · [街面](city-31278/map-street-facade.png) · [入口与三片门篷](city-31278/map-nankin-door-canopies.png) · [四、五层折角阳台](city-31278/map-nankin-angled-balconies.png) · [照片来源、阳台实测与三档射线复算](photo-recheck/README.md) · [逐图观察](city-31278/visual-review.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/d8f65bff3476e16d4bad1660f4fd0df581e71540/projects/shanghai/index.html#landmark=huangpu-nankin-hotel-shanxi-front&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
