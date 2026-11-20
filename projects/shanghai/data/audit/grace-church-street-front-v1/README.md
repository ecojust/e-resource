# 怀恩堂陕西北路入口与东南角砖塔

从陕西北路站在街对面看，东南角的红砖钟塔位于堂面左侧。塔窗下段透光，中部有白色腰板，上段为深色百叶。三字堂名分别在三扇窗下，窗与门的凹进深度可从斜侧观察。12.24米街面宽取自现行轮廓，14.64米塔高按照片估算。[各时期的街面及堂史](../../../source/precise/jingan-grace-church-street-front/README.md) · [独立模型](../../../grace-church-street-front.html)

经 Blender 4.3.2 重新打开及比对，62个可编辑网格和12种材质对应近景58,956个三角面。原始模型与解压后的网页近景逐面吻合，远景保留10,268面。制作中缩小早期门面上的三字堂名，把它们分别放回拱窗下方，并按斜视照片补屋坡瓦棱。另一轮检查纠正最后一个字形意外影响后剖面的错误，在后剖面增加三个独立射线点。最终每档检查31处，覆盖塔的两面、百叶、两扇门、窗框、屋后剖面和十字架。[原生渲染](jingan-grace-church-street-front-preview.png) · [初稿渲染](preflight/first-native.png) · [重新打开与逐面校验](geometry-native.json) · [三档93个射线点](front-checks.json) · [四种文件](../../../assets/models/candidates/jingan-grace-church-street-front/manifest.json)

部分替换位于北京西路与陕西北路口的519。冻结源把这栋楼标成高35.5米，模型只处理陕西北路短段，近源投影约85.83%、远源约85.98%继续显示。西侧原礼堂和南侧宋氏住宅分别保留。近景无逐面编号，按每个三角形重心与各个近景地块的距离识别，属于519的顶点距离其轮廓均在0.11米内。15处地面点覆盖两扇门的凹位、门扇、肩墙、礼堂后部及两栋宋氏住宅。[放置合同](final-placement-contract.json) · [真实近远源与地面检查](placement-geometry.json)

面对陕西北路的原生高楼会遮住站得太低的相机。按桌面及手机各35种取景，用地标和各档原生三角形回射7,755个街面点。采用方位−101°、俯角40°时，两端自模型可见的门窗及塔身样本均能透过街区前景看到。[相机角度对照](camera-preflight.json)

由177处版本生成的178处站点完整复核了以前各候选的目录记录。914件HTTP文件共910,188,168字节，逐一匹配冻结输入及本栋原始城市网格的SHA-256。用同站的裁切模块检查新增两片，所有城市模型合计954片、分布在19个宏区，最大单宏区318片。临街两个门洞和宋氏住宅等15处地面点继续符合登记。[冻结文件下载](frozen-http.json) · [实际地图模块检查](runtime-placement.json)

从178处站点实际打开独立页，桌面和手机均能在画面内看到塔顶十字架、三扇窗、堂名和两扇入口。两端都切换过近景和远景，四种下载文件逐件核实。初次运行完成了桌面和下载检查，手机截屏超时；重开后的四个画面和下载均完成。[桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [桌面远景](viewer-desktop-lod.png) · [手机远景](viewer-mobile-lod.png) · [完整浏览及下载收据](viewer.json) · [初次超时记录](preflight/first-standalone-screenshot-timeout.log)

## 最终主图核验

在177处对照图中，陕西北路街面显示原有高楼。加入怀恩堂后，同一机位能辨出十字架、砖塔纵窗、三角山花和两扇入口。390像素宽手机从目录点入时，建筑完整出现在选择卡上方，堂名字形较小。贴近门厅的低机位被街区前景挡住，双门外观可从街面对照，门凹位及门扇的深度另有射线与碰撞记录。街区远景中，塔窗缩小到难以辨认，浏览器实际加载10,268面的远景模型。[加入前](city-24141/map-before.png) · [街面](city-24141/map-street-facade.png) · [手机入口](city-24141/map-mobile-settled.png) · [低机位遮挡](city-24141/map-street-vestibule.png) · [远景](city-24141/map-distant.png) · [逐图观察](city-24141/visual-review.json)

最终178处站点的919件签名文件共907,363,582字节。浏览器对照前后两个站点，进入主图后核验了15处地面点及两栋邻宅；独立页原有的四张近远景实拍和四种下载也逐一与此版页面、脚本及资产匹配。[两版输入](city-24141/two-served-sites.json) · [最终HTTP校验](city-24141/141-all-http.json) · [主图运行记录](city-24141/main-browser.json) · [独立页下载与最终版本对照](city-24141/individual-downloads-rebound.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/e39804084880a518b0263aa98430f456b3cf8914/projects/shanghai/index.html#landmark=jingan-grace-church-street-front&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
