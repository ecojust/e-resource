# 新乐路圣母大堂

徐汇区新乐路55号，上海市第二批优秀历史建筑2D041。地方志记载圣母大堂于1936年2月落成、1988年维修。市房管局名录中，原使用单位为东正教堂，公布时使用单位为建设银行。2011年正门照片上可辨新乐路55号门牌。[市房管局原表](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [地方志、摄影者及原图记录](reference-review.json)

## 街面与屋顶

新乐路一面的中央双扇门退入半圆门洞，每扇门中部有一对同心圆线脚，门上扇形窗有半圆内环和三条辐射窗梃。门旁的绿色55号牌、门前石级与两侧细长窗均采自正面照。襄阳北路一面的中央拱端下方是两扇窄窗。两个街面依据2011年实照，另用2013年10月和2020年2月在两条街上的全景核对门窗方向。近正面照片上，从门槛到起拱处约为门洞宽的1.49倍，门牌中心比门槛高约一个门洞宽；门扇、圆饰、门匾和最上一级踏步按这些比例校正。树冠、围栏和车辆遮住的部位按相邻开间比例推定。[正门照片的比例读点](entrance-photo-study.json) · [两条街的全景影像记录](street-source-receipts.json)

地方志记中央穹顶高35米，木架覆铜皮，外涂孔雀蓝，四周各有次穹顶。模型保留顶壳底缘收束、肩部鼓起、向尖端收拢的轮廓。鼓座窗洞有实体窗套和退后的玻璃，十字形殿顶在街墙上显露出圆拱形尽端。次顶和鼓座的高度、鼓座背面窗数、铜皮分缝、门窗进深及遮挡处装饰按照片比例估计。[上海市地方志办公室建筑记录](https://web.archive.org/web/20200221114658id_/http://www.shtong.gov.cn/Newsite/node2/node71994/node81772/node81777/node81790/userobject1ai109148.html)

## 定位与分栋

具名街坊轮廓与冻结底图3953对应，中心约为东经121.451018°、北纬31.219350°。轮廓局部长宽约24.35米和27.06米，沿襄阳北路的窗墙位于模型东侧。2018、2022和2024年发布的航片可核对屋顶和邻房相对位置。高顶在斜拍影像中有投影偏移，建筑脚点采用门牌、街面和底图共同定位。[本地坐标与登记轮廓](author-frame.json) · [航片图块及发布日期](roof-source-receipts.json) · [源建筑及邻屋](footprint-review.json)

南侧主教公署在历史合照中有独立楼体。主教公署、教堂内部与背街面待查的开窗另列。皋兰路16号圣尼古拉斯堂有单独登记和建造年代，两堂的容量、朝向和落成年份分别核对。[上海宗教志的两堂专节](https://web.archive.org/web/20190415154034id_/http://www.shtong.gov.cn/newsite/node2/node2245/node75195/node75205/node75325/node75333/userobject1ai92291.html)

## 重建

在上海项目目录运行以下命令。构建器生成原始近景、压缩网页近景、远景和可编辑的 Blender 文件，分别核对解码的有向表面，并从重新打开的场景渲染转角视图。工具需要 Python、Blender、gltfpack、Node.js、ImageMagick 和 Open Image Denoise。

```sh
python source/precise/xuhui-xinle-orthodox-cathedral/source/build_model.py \
  --out assets/models/candidates/xuhui-xinle-orthodox-cathedral \
  --audit data/audit/xinle-orthodox-cathedral-v1
python data/audit/xinle-orthodox-cathedral-v1/check-surfaces.py
```

原创代码与几何按仓库 MIT 许可发布。摄影作品署名与许可逐件列于来源表，图像仅作造型参考。具名轮廓和街区矢量数据由 OpenStreetMap 贡献者提供，适用 ODbL 1.0。[来源及摄影署名](reference-review.json) · [OpenStreetMap 版权](https://www.openstreetmap.org/copyright)
