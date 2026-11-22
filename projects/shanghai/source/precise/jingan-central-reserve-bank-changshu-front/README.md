# 中央储备银行常熟路旧址正门与三跨石阳台

上海市静安区常熟路100弄10号。1936年建。上海市第四批优秀历史建筑名录4B021的原名为“中央储备银行”，表载使用单位为“上海歌舞剧院”。2021年《建筑可阅读》以“上海歌剧院”介绍同一处建筑。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [澎湃新闻](https://www.thepaper.cn/newsDetail_forward_12313789)

模型表现花园尽端朝东南的中央三跨。正门两扇木门开启，门套上有竖槽和连续折纹。二、三层中央石栏随阳台折角转回，两侧窗栏较浅。照片中每层的中央正栏有九根石栏柱，两侧各有十一根。两道出挑的石檐沿可见的东侧返面折回。三跨之外的翼楼、后楼、屋顶花园、院门与室内另列后续范围。[照片、逐幅观察与许可](reference-review.json)

现状足印与原城楼号3343相合。中央凸部宽约16.11米，花园正面朝向约161.53°。按正面照片透视推算门洞净宽约2.6米，入口看台与短压顶的整体建模高度为20.45米。地台高、阳台深度、开启角度和石缝宽度均为估值。旧图与现状保留了相近朝向，轮廓已有变化。主图较高的后部仍沿用原城高度。[足印与邻房](footprint-review.json) · [照片量算](measurements/front-rectification.json) · [历史图配准](measurements/historic-plan-registration.json)

## 来源与许可

Antigng 于2018年2月7日拍摄的正面原照采用 CC BY-SA 4.0。窗帘与树影取自该照片内五处小面积采样，各缩成64×64像素，拼入320×64的图集。图集沿用相同许可。原创建模与重建代码采用仓库 MIT 许可。高参88刊载的闭门照片、侧向照片及旧平面图仅供观察。现状足印数据归 OpenStreetMap 贡献者，遵循 ODbL 1.0。[Antigng 原照](https://commons.wikimedia.org/wiki/File:常熟路中央储备银行旧址.jpg) · [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) · [高参88的图文](https://blog.sina.com.cn/s/blog_5d1bdf480101dxr2.html) · [OSM 足印](https://www.openstreetmap.org/way/490278584)

## 重建

在安装了项目所用 Python 依赖、gltfpack、Blender、ImageMagick 和 OIDN 的环境中，从本目录运行下列命令。六个可编辑相机涵盖花园正面、石门套、两处栏杆、上檐和东侧返面。

```sh
python -B source/build_model.py --out ./build/assets --audit ./build/audit
python -B measurements/recheck-photograph.py ./build/changshu-front-measurements.json
```

[返回上海主图](../../../index.html#landmark=jingan-central-reserve-bank-changshu-front&mode=overview)
