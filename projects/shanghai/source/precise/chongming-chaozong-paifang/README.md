# 崇明学宫东牌坊（题名面待核）：结构参照候选

[独立预览](../../../east-paifang.html) · [资产清单](../../../assets/models/candidates/chongming-chaozong-paifang/manifest.json) · [检查记录](../../../data/audit/east-paifang-v1/README.md)

本件以2021年官方文字中的物理东座为独立身份；官方东座题名组为“德配天地／朝宗”，作为有出处的文献字段保留。沿用资产ID `chongming-chaozong-paifang` 仅为兼容旧队列名称，**不表示已验收“朝宗”近景属于东座某面。两面匾额均留空，不雕刻题字。** 照片近景与物理座别、正反面之间的完整身份链仍未建立，后坡、柱后支承及细部尺寸均包含估计。

## 来源与题名面争议

[旧馆第1节“牌坊”](https://web.archive.org/web/20100102053154id_/http://www.cmbwg.com/page3_1.htm)记载两坊在棂星门前左右，高“三丈”，两层重檐十二角，上层砖木、下承石柱；“柱东西宽1.6米，柱距南北长4.4米”，两坊间距33米。[2021年区政府文章](https://www.shcm.gov.cn/zjcm/006008/20210423/8c183cc2-f5a9-4d52-b152-9d72ec7eb5a7.html)明确物理东、西座及其题名组合。[2023年文章](https://www.sohu.com/a/669412809_121124600)描述高“9米多”，并提供近景拼图。

| 来源与时点 | 原文题名分组 | 适用限制 |
|---|---|---|
| 旧馆1998年记载 | 左：学海、德配天地；右：朝宗、道冠古今 | 未给观察方向或完整正反面对照 |
| 2021年官方文章 | 西：道冠古今、学海；东：德配天地、朝宗 | 有明确物理方位，仍是文字记载 |
| 2023年文章 | 左正反：德配天地、朝宗；右正反：道冠古今、学海 | 左右方向未定义，不能独立确定东西座别 |

只交换观察者左右不能消除这些题名分组差异。来源时段不同，当前证据也不能判定是更题、误记或叙述视角造成。旧馆其他历史题名分别属于各自年代，不拼成同一时点的牌面。

已查看[近景拼图](https://p2.itc.cn/q_70/images01/20230424/2fc5da72435e4177a38d7ab42869f4ef.jpeg)和[正门全景](https://p4.itc.cn/q_70/images01/20230423/6e83f36f3ab04028b133893bfc3e5a96.jpeg)：拼图左幅近面可读“学海”，右幅近面可读“朝宗”；全景左近面为“道冠古今”，右近面为“德配天地”。全景由主门与前庭关系解释左为西、右为东，尚无相机方位测量。

朝宗近景中的棕色P牌、红宣传板及主门背景，反而较支持它与全景左／西座环境相联；学海近景与全景右／东座相联是另一项候选解释。**这只是中等置信的环境关联假说**，图片是否同期、招牌是否变化及同柱构件对应均未完成核实，不能据此改写来源或确定反面题名。详见[视觉身份审查](../../../data/model-todo/chongming-paifang-visual-identity-review.json)、[牌坊资料审查](../../../data/model-todo/chongming-paifang-reference-review.json)和[新增全景审查](../../../data/model-todo/chongming-later-buildings-reference-review.json)。本件继续保留两面空匾。

## 结构与尺寸解释

近景可见两根主要浅石柱、柱脚附块、深红褐木枋、密集分层弯栱、斗块、挑撑及透空雕刻带。屋顶采用**中央高屋顶加左右低挑檐三个独立单元**，每单元四角，合计十二个模型翘角，与文献整体描述相参照；照片没有逐一覆盖全部十二角，不能替换成整圈双檐殿堂屋顶。

本件全部几何沿用[西牌坊候选的设计参数](../chongming-xuehai-paifang/design-input.json)，来源 commit 为 `6673d31dee681d219078b58bc658d77a0aa4e1e5`。石柱、柱脚、通道、空匾、三屋顶、斗栱、原创纹样、配色和隐藏支承均为共用建模假设，不能证明两座实物的尺寸或细部相同；也不为区分两件候选而编造新细节。东座保留独立名称、来源、资产和预览。参数见[设计输入](design-input.json)，所有截面、檐伸、标高、曲率、纹样及隐藏支承均非实测。

| 对象 | 交付参数（共用假设） | 解释或限制 |
|---|---|---|
| 两柱轴距 | 4.4米 | 文献未说明净距、轴距或外包，模型选择轴距 |
| 局部坐标 | X为柱距方向，Y为通道方向 | 分别解释为南北、东西方向；未实测朝向或城市配准 |
| 每柱石轴截面／柱身标高 | 0.68×0.78米；底0.20、顶6.10米 | 柱身几何高5.90米，全部为建模估计 |
| 每柱脚基座 | 0.96×1.60×0.20米 | 1.6米沿局部Y通道方向，解释为柱脚支承深度，不能视为单柱截面实测 |
| 中央屋顶 | 中心X=0；幅5.7×3.10米 | 屋面外伸估计 |
| 中央屋顶标高 | 檐基7.65米，屋面脊线8.65米，角抬1.50米 | 曲率及最高简化角饰9.60米均估计 |
| 左右侧屋顶 | 中心X=±3.0；各幅2.7×2.90米 | 两个独立低屋顶 |
| 侧屋顶标高 | 檐基6.55米，屋面脊线7.30米，角抬1.15米 | 简化角饰约8.15米，均估计 |
| 梁底净高 | 约4.30米 | 建模估计 |
| 总高 | 9.60米 | 对“9米多”的明确建模选择；不把“三丈”硬换为实测10米 |
| 全部构件实际外包 | 9.088909×3.488909×9.600000米 | 从本件最终GLB计算，依次为宽、深、高；含最高角饰，不是现场量测 |
| 通道实际净宽 | 柱身处3.720000米；柱脚处3.440000米 | 本件GLB实际射线计算值；文献4.4米按轴距解释 |

三单元均以简化曲面四坡屋顶构造，四坡端部是建模估计；表中屋面脊线不含另加的脊帽及角饰。雕刻带采用原创简化透空和浮起波纹，表达照片中可见的装饰层次，不复刻精确龙凤、书法或脊兽。风铃是文献所述可悬挂物，现图未可靠确认逐角配置，本件不据此补造。附加脚块、后侧木撑、对称处理的屋面后坡、重复栱件密度、明显上翘曲率及三个单元的隐蔽交接按估计构造处理，不声称榫卯或结构受力已实测复原。

两根石柱之间保持实际开放的通道，不加实体门扇或跨通道地板平台。网页独立漫游沿模型外包外围运行，不声称提供柱间穿行、攀爬或现场通行体验。

## 使用范围与构建

参考照片只用于观察，无照片再分发、嵌入或采样贴图。材料为原创平色和粗糙度近似；拍摄日期未单独确认，不能称2026现状。未包含西牌坊、两坊间33米的现场布置、棂星门、庭墙、花岗石甬道、树木、招牌或实测地面；未作城市配准，不增加正反面铭文或逐栋照片复原验收量。来源URL、响应哈希和限制见[source-register.json](source-register.json)。

仓库根目录执行，依赖见`source/requirements.txt`；Blender 4.3.2、gltfpack 1.3.0：

```sh
python -m pip install -r projects/shanghai/source/precise/chongming-chaozong-paifang/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/chongming-chaozong-paifang/source/build_model.py --out /tmp/east-paifang
python projects/shanghai/source/precise/chongming-chaozong-paifang/source/build_model.py --out /tmp/east-paifang --lod
blender --background --python-exit-code 1 --python projects/shanghai/source/precise/chongming-chaozong-paifang/source/build_native.py -- --raw /tmp/east-paifang/chongming-chaozong-paifang-raw.glb --out /tmp/east-paifang/chongming-chaozong-paifang.blend --previews /tmp/east-paifang-previews
python projects/shanghai/source/precise/chongming-chaozong-paifang/source/package_assets.py --raw /tmp/east-paifang/chongming-chaozong-paifang-raw.glb --lod /tmp/east-paifang/chongming-chaozong-paifang-lod.glb --native /tmp/east-paifang/chongming-chaozong-paifang.blend --out projects/shanghai/assets/models/candidates/chongming-chaozong-paifang --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
python projects/shanghai/source/precise/chongming-chaozong-paifang/source/verify_geometry.py --assets /tmp/east-paifang --out /tmp/east-paifang-geometry.json
```

通用几何辅助、牌坊主体及导出流程的复用范围见`source/HELPER_PROVENANCE.json`。本件所有几何复用西牌坊候选的显式假设，来源及范围见[source-register.json](source-register.json)，不声称对东座实物重新测绘或逐面照片核验。已交付可编辑Blender与近远景GLB，下表使用十进制 MB：

| 文件 | 大小 | 三角面 |
|---|---:|---:|
| chongming-chaozong-paifang-raw.glb | 7.125616 MB | 92848 |
| chongming-chaozong-paifang-web.glb | 2.844624 MB | 92848 |
| chongming-chaozong-paifang-lod.glb | 0.631828 MB | 20996 |
| chongming-chaozong-paifang.blend | 3.312493 MB | 92,848（模型几何） |

全部交付文件小于100 MB。本件两档几何、压缩解码、通道射线、Blender保存重开及网页身份／近远景／视角／外围漫游检查均已独立完成；尺寸与细节仍为共用建模假设，不增加两座实物一致或照片复原验收量。详见[检查记录](../../../data/audit/east-paifang-v1/README.md)。原创代码与几何MIT。
