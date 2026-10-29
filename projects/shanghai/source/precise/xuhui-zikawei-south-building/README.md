# 徐家汇藏书楼南楼（原神父楼）外观候选

**漫游接入更新：**已开放[原址室外第三人称漫游](../../../index.html#landmark=xuhui-zikawei-south-building&mode=walk)，起点、保守建筑碰撞与近远景切换记录见[接入核验](../../../data/audit/precise-buildings-v22/xuhui-zikawei-south-building/README.md)。下列初次建模记录中的“未接入”描述属于交付时状态；尺寸和未见构造仍为估计，不代表整栋历史复原完成。

以2022年公开外观照片为主，参照较早照片制作南楼主体：五开间三层外廊、六根外柱、凹进的百叶门窗、两层金属栏杆、屋顶白色交叉栏杆、两扇老虎窗、屋瓦与雨水管。模型包含源地图中南楼西侧回翼的估计体量，**不包含相连的北楼**。

这是有源身份的外观候选，尚未接入城市原址漫游，也不计入逐栋复原完成数量。模型尺寸、隐蔽构造和未拍到的后部屋面均为估计，不是测绘或摄影测量成果。

- [打开独立预览](../../../zikawei-library.html)（本地 HTTP 服务）；公开入口见仓库及项目 README。
- [资产清单与 SHA-256](../../../assets/models/candidates/xuhui-zikawei-south-building/manifest.json)：原始 GLB、Meshopt 网页 GLB、远景 LOD、可编辑 Blender 文件。
- [验证记录](../../../data/audit/zikawei-south-building-v1/README.md)。

## 依据与边界

照片许可与原文件哈希见 [public-photo-register.json](public-photo-register.json)。钉钉拍摄的2022年正面／斜侧与现场保护标牌采用 CC BY-SA 4.0；JuneAugust 的2013年照片、Mountain 的较早照片采用 CC BY-SA 3.0。Mountain 署名由原 Commons 文件页面文字核实，照片拍摄日期未确认，不用上传时间替代。照片只作为独立研究参考，未嵌入模型材质。

[设计输入](design-input.json)记录照片观察、估计尺寸、未制作范围及一手文字来源。上海地方志的2009年介绍提到1931年的四层神父楼；2022年现场保护标牌记述南楼始建于1867年。这里保留两条来源的差异，不自行确定重建年代，也不据此推算尺寸。区志中两层藏书楼与书库面积的描述不能直接套用到本南楼。

[源对象输入](geometry-input.json)对应宏块 `14-13718-6696`、局部 ID `1595`、`building:b3792d7b-320e-4107-a9ea-d3cac1c9a323`，来源 `w293862126@8`。独立北楼为局部 ID `667`、`w438816043@2`，本次排除。锚点和朝向从这一南楼源轮廓估计，而非采用百科条目中与此轮廓不一致的坐标。原源要素表 SHA-256 已绑定。

源数据的29.5米高度为估算值，与照片中的三层外廊加阁楼体量不符，未作为设计尺寸。当前估计主体为23.4×24.0米，西侧回翼约13.1×14.0米；主屋脊16.25米，含脊盖的模型最高点约16.405米。所有数值均可在设计输入与生成脚本中复核。L形台基面积约745平方米接近源轮廓面积，但仍有约9.89平方米位于源边界外；这不是墙线或放置位置已验收的证明。

未制作北楼、室内房间和楼梯、庭院围栏、街道、树木及邻楼，也未补画未见后墙的门窗。侧墙近端门窗、灯具、排水管路、后部回翼及屋面交接仍含估计。模型没有创造对应的城市碰撞或行走地面。

## 几何与材质

近景150,176个三角面；LOD 23,140个三角面。门窗在墙体上有真实开口和凹进，近景百叶具有倾斜片体，外廊保持开放。屋面使用相交包络裁切老虎窗，避免整张屋面穿过窗洞；屋面平面交点以0.1毫米网格规范化，避免 FLOAT32 导出产生细小退化面。远景保留建筑体量、真实洞口、外廊、栏杆和主要屋面，简化逐片瓦和百叶。

抹灰墙面使用原创512×512周期性 basecolor、normal、ORM 三图，0.4米重复；颜色、粒径和法线强度为估计。随机种子801867，使用 NumPy PCG64；材质生成器不读取照片像素，ORM 金属通道为0。纹理、几何与生成代码采用 MIT。源轮廓与关系沿用 ODbL-1.0，© OpenStreetMap contributors／Overture Maps Foundation；照片另按各自 CC BY-SA 许可署名。

## 重建

在 `projects/shanghai` 目录执行，Python 依赖见 `source/requirements.txt`；Blender 使用4.3.2，gltfpack 使用项目锁定版本1.3。以下命令不会更改城市地图登记。

```bash
python source/precise/xuhui-zikawei-south-building/source/generate_material.py --output source/precise/xuhui-zikawei-south-building/textures
python source/precise/xuhui-zikawei-south-building/source/build_model.py --out /tmp/zikawei
python source/precise/xuhui-zikawei-south-building/source/build_model.py --out /tmp/zikawei --lod
blender -b -t 4 --python-exit-code 1 --python source/precise/xuhui-zikawei-south-building/source/build_native.py -- --raw /tmp/zikawei/xuhui-zikawei-south-building-raw.glb --out /tmp/zikawei/xuhui-zikawei-south-building.blend --previews /tmp/zikawei/native
python source/precise/xuhui-zikawei-south-building/source/package_assets.py --raw /tmp/zikawei/xuhui-zikawei-south-building-raw.glb --lod /tmp/zikawei/xuhui-zikawei-south-building-lod.glb --native /tmp/zikawei/xuhui-zikawei-south-building.blend --out /tmp/zikawei/assets --gltfpack source/city/detail/tooling/node_modules/.bin/gltfpack
```

屋面与材质生成器改编出处见 `source/HELPER_PROVENANCE.json`。原始／LOD 几何与三张 PBR 图片已验证重复生成字节一致；Blender 文件不宣称跨运行字节一致，但会重新打开并核对实际网格、UV 与打包图片。
