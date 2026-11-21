# 新华路185弄1号花园住宅

长宁区新华路185弄1号建于1930年。市房管局第二批2M001登记为“住宅”，公布时用途“餐厅”。区文旅局与区融媒体中心的修缮资料记载，1994年公布为上海市优秀历史建筑，2017年4月5日成为长宁区文物保护点。资料将住宅归于邬达克，称其为英国乡村式假三层砖木住宅。原工作索引写“三层砖混”，并记安徽省驻沪办事处招待所。机关、招待所和1号楼在地图上各有不同落点。[市级名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) [区文旅与修复资料](https://m.thepaper.cn/newsDetail_forward_32934633) [原文与图片逐项收据](reference-review.json)

## 恢复开放的南廊

第三次普查照片中的外廊已装窗。2024年保护性修缮后，第四次普查在同一朝向记录了三道重新敞开的浅尖券。本模型以修后外观为准。二层露台的九块交叉花枝镂空栏板分成三组。上方有清水红砖山墙、斩假石窗套和成对阁楼窗，右邻棚式老虎窗。另一张可确定门牌的俯照给出东西主屋脊、向南交叉屋脊、低侧翼、三座烟囱和南庭的关系。区级四普图与英文市府图共享取景，独立俯照和券廊内、外近照另外取样。[俯拍与近照](https://www.thepaper.cn/newsDetail_forward_32420432) [市府外文正面图和门牌题签](https://english.shanghai.gov.cn/en-CityTour/20260303/b8a10d5e27664c69bb294479704a91b9.html)

模型有可通行的前廊、透空花栏、独立砌砖立面和瓦面，两类玻璃窗分别位于露台后与券廊后。门窗样式依据近次修缮后的仿钢格窗。隐蔽侧后墙采用简化轮廓，保留室内及旧附属待考。[独立查看及文件下载](../../../xinhua-lane-185-no1.html) [建模核验](../../../data/audit/xinhua-lane-185-no1-v1/README.md)

## 地块与尺寸

1号楼专属门牌点位于14-13718-6695内的2392，底图轮廓约293.63平方米，与现行OSM环864485598重合97.65%。5号东南入口、7号招待所与机关各自指向其他位置。模型依据可见露台和屋脊，锚点设在南廊正面中央，经纬为121.42394182，31.20359438；露台估宽10.20米。影像透视、树影和屋檐投影存在米级不确定性。屋主、未拍到的室内和隐蔽窗位留待进一步资料。[有来源的地块与屋面](footprint-review.json) [正式地图入口](../../../index.html#landmark=changning-xinhua-lane-185-no1&mode=overview)

## 交付与重建

近景 35,762 个三角面，远景 18,167 个。提供两档压缩GLB、原始GLB和可编辑Blender工程。网格与装饰线脚均为原创，采用项目MIT许可。参考照片版权归原摄影者或刊载方。模型内部无照片贴图。[构建清单](../../../assets/models/candidates/changning-xinhua-lane-185-no1/manifest.json) [项目许可](../../../../../LICENSE)

可从仓库根目录重建。环境需要Python、NumPy、Shapely 2.1、Blender、Node.js、gltfpack、ImageMagick 7及Open Image Denoise。

```sh
python -B projects/shanghai/source/precise/changning-xinhua-lane-185-no1/source/build_model.py \
  --out /tmp/xinhua-assets --audit /tmp/xinhua-audit --decoded /tmp/xinhua-decoded
python -B projects/shanghai/source/precise/changning-xinhua-lane-185-no1/source/check_surfaces.py \
  --manifest /tmp/xinhua-assets/manifest.json --out /tmp/xinhua-audit/surfaces.json
```
