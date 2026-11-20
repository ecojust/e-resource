# 建业里总弄沿街门楼

建业里位于上海市徐汇区建国西路。《上海地名志》记1930年建，列456弄、440弄、496弄，范围约1.7公顷。后期资料将三者分别对应中弄、东弄和西弄。市房管局第二批优秀历史建筑2D017以成组保护范围列建国西路468弄、488弄、424–498号双号。当代酒店公布的联系地址为480号。对于450弄与总弄门洞的对应关系，现有资料仍不足。[上海地名志](https://web.archive.org/web/20201201083354/http://www.shtong.gov.cn/Newsite/node2/node2245/node70862/node70869/node70913/node70917/userobject1ai73690.html) · [房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [酒店地址](https://capellahotels.com/en/capella-shanghai)

2012年的现场报道提到，东弄与中弄经历拆除重建，西弄另作利用。2014年1月，Livelikerw从建国西路拍下重建后的中弄。门额五字「建業里總衖」由右向左排列，门洞内有临时封挡。2020年2月22日同一街段的实景可见，额字已改从左向右排列，下面增设CAPELLA小铜牌，入口处露出门洞的退进。模型采用2020年照片所见的这一状态。[2012年同期报道](https://finance.sina.com.cn/leadership/mroll/20120222/185211432164.shtml) · [2014年原摄照片](https://commons.wikimedia.org/wiki/File:Main_Gateway_of_JianyeLi.JPG) · [原图与街景取景点](reference-review.json)

从街面对照三个门楼，中间总弄门楼有两樘木窗，每樘有三扇窗叶，每叶分两列三排玻璃。另两处灰石门楼宽度较小，只有单组窄窗和三字门额。三个已知相机位置对中楼门额与门柱交会，入口净宽估计为5.52米、两柱外缘约6.79米。中心交点按临街方向投影到冻结的119号建筑南墙。参考影像坐标与地图边线存在约4.11米法向偏差，公布的尺寸和位置均为近似值。模型包含两侧柱脚、门洞退进、木窗、回纹和阶梯式女儿墙，其余连续沿街商铺、两侧门楼和后排住宅保留原有城市几何。[地块与配准](footprint-review.json) · [尺寸依据](elevation-study.json) · [独立模型](../../../jianye-li-main-gate.html) · [城市地图](../../../index.html#landmark=xuhui-jianye-li-main-lane-gate&mode=overview) · [模型下载](../../../assets/models/candidates/xuhui-jianye-li-main-lane-gate/manifest.json)

本工程的网格与材质采用MIT许可证。2014年照片由Livelikerw以CC BY-SA 3.0发布，其他参考影像的权利归各提供方。匾字使用重命名的SIL OFL字体子集近似，模型文件不包含街景或照片纹理。[项目许可证](../../../../../LICENSE) · [字体许可与来源](source/fonts/provenance.json)

在项目的 `projects/shanghai` 目录执行以下命令。需要Python、NumPy、Shapely、mapbox-earcut、FontTools、Node、gltfpack、Blender、ImageMagick 7及Open Image Denoise。

```sh
python source/precise/xuhui-jianye-li-main-lane-gate/source/build_model.py \
  --out assets/models/candidates/xuhui-jianye-li-main-lane-gate \
  --audit data/audit/jianye-li-main-gate-v1
```
