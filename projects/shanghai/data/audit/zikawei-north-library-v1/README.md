# 徐家汇藏书楼北楼

两层原藏书楼面朝南侧庭院，靠漕溪北路的东山墙下开三座拱门。1897年改建后的馆舍有两层藏书空间。地方志另记面积约两千余平方米，现有具名北楼单体的地面投影约390平方米。历史面积的统计边界有待进一步核对，本模型按现存北楼外墙落位。南侧四层原神父楼沿用已有模型。[地方志、景区照片、新闻资料及街景记录](../../../source/precise/xuhui-zikawei-north-library/reference-review.json) · [建筑范围](../../../source/precise/xuhui-zikawei-north-library/README.md)

庭院立面设六道上层拱窗，红瓦双坡顶以山墙圆气孔和深灰台基收边。照片支持现状粉刷与百叶窗，屋脊约12米、瓦片间距、部分窗扇开合及隐蔽面采用比例估算。馆内的书架和藏品尚无本次建模记录。[原生整楼图](xuhui-zikawei-north-library-preview.png) · [漕溪北路三拱近照](eastern-street-arcade.png) · [庭院百叶窗](courtyard-shutters.png)

原始模型与网页近景各105,688个三角面，远景54,672面。重开Blender的63个具名网格，与原始文件按材质比对。三档各作59项独立射线检查，另验内隔墙两端位于外墙内部。三拱与南北通廊保留开口，外墙转角及隔墙端原预览的黑色条带已修正。[三档射线记录](surface-checks.json) · [原生重开和解码记录](geometry-native.json) · [接缝修改前后](preflight/east-corner-review.json)

北楼使用具名单体667，OSM与冻结源轮廓重合度98.23%。原始、近景和远景按实物柱脚、墙体与库房地坪生成325.53平方米的地面障碍。18个地面见证覆盖街边三拱、街墩、实墙和南北贯通路径，廊下铺地高出基面约4.2厘米，可供通行。模型外形与已发布的南侧原神父楼模型实测相隔1.82米，北楼粗模裁剪边界距离南楼原始模型1.71米。原始两座建筑轮廓间距约2.60米。北楼近、远档粗模投影均在专属裁剪面内，同组其余近档三角面距裁剪边界至少26.70米。[北楼轮廓、原神父楼的资产绑定](../../../source/precise/xuhui-zikawei-north-library/footprint-review.json) · [碰撞与相邻建筑](placement-geometry.json) · [落位合同](final-placement-contract.json) · [独立模型页](../../../zikawei-north-library.html)

独立页在桌面和390像素手机点选「庭院南立面」后，各自切换了近、远档。两档均能看出门廊和六道上层窗，四个下载逐一校验文件长度与SHA-256。[桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png) · [浏览器操作与四件下载](viewer.json)

两次场景之间，董家渡天主堂的默认镜头有调整。其余可拟合镜头的建筑在三种窗口尺寸下共有246组计算，取景参数一致。[场景输入及目录差异](camera-input-revision/input-difference.json) · [逐栋镜头核对](camera-input-revision/camera-arguments.json)

最终场景又通过HTTP逐项读取了14个文件，其中包括本次修改涉及的文件和这栋建筑的四种资产。实收13,226,367字节，均与冻结清单或原文件签名一致。[逐文件核对](revised-scene-http.json)

在123处入口的地图上，通过 HTTP 实取带版本号的三份地图登记表，以及按 SHA-256 寻址的普通建筑总表、分区索引和替换表。共核对14个请求，返回字节与冻结清单一致。[逐次请求](metadata-cache-http.json) · [本次调整涉及的文件](runtime-input-changes.json)

## 与122处原城市对照

先在真实122处原城市选中南楼，移至相同近景查看北侧地块。原有四层神父楼和栏杆已在场，北侧667号源仍为多层平顶粗模。前序页面、目录和实际载入瓦片等10项都重新读取并核对哈希。[前序近景](map-before.png) · [122处浏览器实测](control-browser.json)

123处正式场景的325°、54°默认视角，在390×844手机上可以完整看见两层北藏书楼、红瓦双坡屋面和东侧三孔廊。870×660桌面同时显示南北楼，两个灯牌局部遮住北楼中段。手机上灯牌位于楼身上方，长立面的拱窗清楚。此阶段保留双端默认结果与两套目录签名。[手机默认](map-mobile.png) · [桌面默认](map-desktop.png) · [123处首轮状态](main-map-first-views.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/925b7a8fbedcda93d7f6704b18cf6f2a4bb5e292/projects/shanghai/index.html#landmark=xuhui-zikawei-north-library&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 11 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)

123处城市的五个实景均已取得。近景加载完整网格，远景完成简化档切换。图书室、横廊、三孔廊、南楼保留地面及邻楼等21个地面点与预期相符，四种交付及实际源近远瓦片共6项按字节和SHA-256核对。[东门与南楼近景](map-street-facade.png) · [屋顶](map-roof.png) · [远景](map-distant.png) · [包含地面与下载的完整记录](main-map-browser.json)
