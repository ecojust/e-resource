# 永嘉路501号住宅

模型覆盖沿永嘉路的北立面、西北圆塔、西端低附间、朝南的花园立面和相应坡屋顶。2014年1月街面照片用于辨认北墙、塔和临街小檐。天平街道档案网页内两张可独立解出的照片提供西端低附间、南面券窗和檐部的证据；档案网页最迟于2014年收录，拍摄日期未知。2009年杨浦区图书馆资料可辨尖塔的金属顶、砖饰及窄窗。[照片来源和档案散列](reference-review.json)

《上海名建筑志》与杨浦区图书馆将永嘉路501号宋子文旧居记为1928年，两种资料对建筑风格分别采用法国和德国城堡式的说法。现行市房管局第二批表的2D024与2D028均印岳阳路145号，原工作表分列501号、145号。模型以501号实照辨认临永嘉路地块340，岳阳路院内的2048号楼另行登记。2023年同一幅园内照片能同时辨认145号双折檐和树后的501号塔顶。[门牌、地块与航片](address-and-roof.json) · [两栋同框的2023年报道](https://www.thepaper.cn/newsDetail_forward_23188382)

临街建筑轴线、约16.83米的原楼长边和约8.41米的前后深度来自地块和航片。窗框、檐托、塔径与高度采用照片比例估算。未证实的东端仍保留城市模型；室内、院地、围墙和邻楼另列。[配准依据](footprint-review.json)

[独立查看器](../../../yongjia-road-501.html) · [三档和原生清单](../../../assets/models/candidates/xuhui-yongjia-road-501-residence/manifest.json)

[未压缩 GLB](../../../assets/models/candidates/xuhui-yongjia-road-501-residence/xuhui-yongjia-road-501-residence-raw.glb) · [近景 GLB](../../../assets/models/candidates/xuhui-yongjia-road-501-residence/xuhui-yongjia-road-501-residence-web.glb) · [远景 GLB](../../../assets/models/candidates/xuhui-yongjia-road-501-residence/xuhui-yongjia-road-501-residence-lod.glb) · [可编辑 Blender](../../../assets/models/candidates/xuhui-yongjia-road-501-residence/xuhui-yongjia-road-501-residence.blend)

## 重建

在仓库提供的 Blender、Meshoptimizer 和 Open Image Denoise 环境中，从项目目录运行以下命令。命令行依赖及输出参数与上海项目的通用建筑打包器一致。

```bash
python source/precise/xuhui-yongjia-road-501-residence/source/build_model.py \
  --out /tmp/yongjia-501-assets --audit /tmp/yongjia-501-audit \
  --decoded /tmp/yongjia-501-decoded
```

建筑几何与材质位于 [villa.py](source/villa.py)，交付参数位于 [build_model.py](source/build_model.py)。原生场景保留各面、塔身、窗洞、檐托、附间和屋顶构件的独立对象。
