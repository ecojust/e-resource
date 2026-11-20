# 逸村2号淮海中路园侧立面

市房管局第二批优秀历史建筑表2D008登记「逸村」，地址为淮海中路1610弄。徐汇区旅游资料记载，这个花园住宅群于1942年建成，华业工程股份有限公司设计，远东公司营造，共八栋二至三层住宅。该资料将蒋经国一家1948年的住址列为逸村2号，另载徐恩曾住7号。本模型取2013至2020年照片上仍可辨认的园侧外观。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [徐汇区原文存档](https://web.archive.org/web/20211220055148id_/http://www.qjtrip.com/xhtrip/XHShowDetail.aspx?Id=4050&fromsType=)

2015年1月26日的照片同时收进路口两栋住宅及「1610弄1–8号」总门牌。沿街往东北的一栋在公共弄口右侧，它的主山墙明显向前伸出。1号与2号的单栋地址点分别落在城市原件2927、2940内。2号对应的OSM建筑w790829238与2940足印的交并比为96.7%。三期街景能核对窗墙、屋顶和花铁门的位置。照片中尚未辨出2号的单户金属牌，模型保留未题字的门柱。[2015年全图](https://commons.wikimedia.org/wiki/File:YiCun_on_Huaihai_Rd..JPG) · [总门牌剪裁](../../../data/audit/yicun-no2-street-front-v1/compound-number-2015.jpg) · [地址点、照片及出处](sources-and-identity.json) · [两栋分界](registered-front.json)

右侧山墙分三层，每层的三扇窗之间有两根螺旋石柱。顶层横窗上方有浅半圆饰和窄通气孔。前缩的左开间有开圆窗的楼梯间、带铁栏的小阳台和瓦沿。院门为成对门柱、灯具和卷草铁饰。照片与四期屋顶影像支持交接的两组红瓦坡面及两处烟囱。门窗高度、花铁纹样曲率、屋坡背面以及园门至窗墙的距离按比例估算。后墙保持简单，室内、公共弄门及其余七栋留待另行调查。[园侧原照剪裁](../../../data/audit/yicun-no2-street-front-v1/garden-front-2015.jpg) · [摄影署名](../../../data/audit/yicun-no2-street-front-v1/photo-credits.md) · [屋顶影像收据](roof-sources.json) · [2015街景三点投影](street-image-calibration.json)

模型原点来自2940号地块，横轴朝真方位53.5°，园侧朝143.5°。地面碰撞取实墙、两扇关闭的铁门和门柱，住宅与门之间保留花园空地。按既有城市近、远网格分别核对裁切范围及邻楼，实查数值见审计。[几何参数](source/parameters.json) · [原件与冻结版本](footprint-review.json) · [核验记录](../../../data/audit/yicun-no2-street-front-v1/README.md) · [旋转查看与下载](../../../yicun-no2-street-front.html)

运行项目通用的建筑模型打包工具需要 NumPy、Shapely、Blender、gltfpack 和 OIDN。几何源码用米为单位生成两档网格，原生文件保留可编辑的构件。下方命令将成品写入所选目录。

```sh
python source/precise/xuhui-yicun-no2-street-front/source/build_villa.py \
  --out /tmp/yicun-assets --audit /tmp/yicun-audit --decoded /tmp/yicun-decoded \
  --blender blender --gltfpack gltfpack --oidn oidnDenoise
```
