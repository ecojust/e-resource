# 崇明学宫大成殿：2005年照片参照外观候选

**本轮更新：**[进入独立模型室外漫游](../../../dacheng-hall.html#mode=model-walk)。支持键盘／触屏移动、转向和外围碰撞；场景未配准到城市原址，不包含室内、登楼或上桥，不增加40处城市漫游数量。

[独立预览](../../../dacheng-hall.html) · [资产清单](../../../assets/models/candidates/chongming-dacheng-hall/manifest.json) · [验收记录](../../../data/audit/dacheng-hall-v1/README.md)

依据博物馆旧官网和两张公开许可照片制作重檐歇山屋顶、瓦垄、檐下构件、前廊柱网、五开间分格门窗及月台。门窗分格为实体构件，后方有独立内退暗面，不提供室内。原生文件包含可编辑网格和独立预览舞台。

这是待核验的外观候选，不是已完成的逐栋复原，也没有替换城市源对象或增加40处漫游目录。源地图轮廓覆盖整个博物馆院落，尚不能据此安全替换单栋大成殿。

## 来源与精度

[尺寸与假设](design-input.json)记录文献殿身21.3×17.3米、总高15.3米（含脊饰1.7米）、月台16.2×9.57×1米、八根前柱与五楹。旧官网没有给出尺寸对应的墙线或檐口，本模型把平面尺寸用于基座；檐口外挑和层间高度均是解释值。模型最高约15.25米，简化脊饰不等同于文献15.3米的精确复原。

两张2005年照片来自Joshua Wickerham，采用[CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0/)。[照片登记](public-photo-register.json)保存Commons页面、原作者、许可、来源日期、原图字节和SHA256；2543224版本由Commons用户Croquant旋转。本项目原样分发取得的Commons文件，照片未贴入模型。原始照片归其作者，原创代码和几何采用MIT。

照片只覆盖正面，树木与雕像遮挡下部。背面、侧面、门窗细分、屋面曲线、台阶和栏杆位置均含估计。平台高度有文献依据，七级台阶及踏步尺寸没有测绘依据。人工照片控制点仅用于轮廓比例核对，不是摄影测量解算或地理配准。无明确证据的雕像、匾额文字、精确雕刻、室内、相邻建筑和院落铺装未复原。材料是原创颜色近似，无照片采样PBR，不声称2026年现状。

## 构建

从仓库根目录运行，Python依赖见`source/requirements.txt`，Blender 4.3.2，gltfpack 1.3.0：

```sh
python -m pip install -r projects/shanghai/source/precise/chongming-dacheng-hall/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/chongming-dacheng-hall/source/build_model.py --out /tmp/dacheng
python projects/shanghai/source/precise/chongming-dacheng-hall/source/build_model.py --out /tmp/dacheng --lod
blender --background --python-exit-code 1 --python projects/shanghai/source/precise/chongming-dacheng-hall/source/build_native.py -- --raw /tmp/dacheng/chongming-dacheng-hall-raw.glb --out /tmp/dacheng/chongming-dacheng-hall.blend --previews /tmp/dacheng-previews
python projects/shanghai/source/precise/chongming-dacheng-hall/source/package_assets.py --raw /tmp/dacheng/chongming-dacheng-hall-raw.glb --lod /tmp/dacheng/chongming-dacheng-hall-lod.glb --native /tmp/dacheng/chongming-dacheng-hall.blend --out /tmp/dacheng-assets --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
```

几何辅助方法来自同仓库尊经阁的MIT源码，具体提取方法与哈希见`source/HELPER_PROVENANCE.json`。大成殿的平面、立面、双檐曲线与月台独立编写，不把尊经阁整楼缩放作为大成殿。

原始与远景源GLB可确定性重建。Blender保存可能因内部元数据产生不同文件字节；验证比较的是保存重开后的实际模型几何，而非承诺原生文件字节可复现。网页检查可先在`projects/shanghai`启动HTTP服务，再运行`node data/audit/dacheng-hall-v1/qa-browser.cjs`（需Playwright及`/usr/bin/chromium`）。
