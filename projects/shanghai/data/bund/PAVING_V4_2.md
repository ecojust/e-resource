# 外滩前景铺装 v4.2

白色空白来自道路边带和步行区之间未建模的地面，露出底图背景；原有顶面没有大面积缺失。此次在外滩18号前、两处标注过街线之间补充188.917㎡连接铺装，最大边界距离约8.486m。

这是沿已有道路边带和步行区外缘生成的施工范围估算，不是新增测绘足迹。两处来源凹口用途不明，分别约133.79㎡、104.65㎡，因此继续保留；三个检查点仅填补第一个。原始16个OSM内环和7个瓦片内环、道路、水体、已有铺装及10栋候选主足迹均被排除。未新增树木或家具，也没有恢复台阶、坡道及平台高差。

参考[滨江照片](../../source/bund/street/references/README.md)，铺装改为中性灰、较宽板块和较弱接缝。1.20×0.60m板块与4mm接缝是比例估算。继续使用原有CC0表面纹理，没有新增照片贴图。

原始街道模型的11组材质几何顶点、法线和索引均保留，新增174个顶点、112个三角面；铺装颜色有意调整。网页模型关闭位置量化和简化，实际解码后全部三角面位置与原始模型一致，法线最大方向差0.0104°。不要将原始几何保留与网页法线逐位一致混为一谈。

[交付与大小](validation/streets-v4.2.json) · [几何核验](validation/connector-geometry-v4.2.json) · [独立审查](validation/connector-review-v4.2.json) · [来源及排除范围](validation/connector-plan-v4.2.json) · [实际解码对照](validation/street-compression-v4.2.json) · [可重建检查](validation/street-rebuild-v4.2.json)

[更新前](../../assets/previews/paving-v4.2/before-street.png) · [公开版实测街景](../../assets/previews/paving-v4.2/public-street.png) · [公开浏览器记录](../../tests/paving-v4.2-public.json)。截图保留未确认的两处开口，不表示这些区域已经复原。
