# 邬达克旧居：可重建的外观模型来源

本模型由 agent 制作，原创建模代码、几何和三张程序材质图采用 MIT。`common/LICENSE` 保留所复用几何工具的原始版权声明；建筑位置来源 OpenStreetMap / Overture，地图权利另计。唯一随包公开的建筑照片为 Szalai.laci 的 Commons《Hudec House.jpeg》，CC BY-SA4.0，仅作参考图，不嵌入材质。

表现范围为 2017 年刊登及 2018 年拍摄照片所见的修缮后主宅、北侧门廊，以及按历史总平面近似定位的连接体与东北服务体。看不到的服务体墙面刻意省略窗洞。它不是 1930 年逐寸测绘复原，也没有制作室内。

2.30m 门高是明确选定的尺度先验。±0.15m 仅为先前两个压力案例，不是测量误差或统计置信区间。来源 713.9㎡ 五边形仅确定背景对象，不能当作房屋墙线。外观比例和墙面尺寸均有声明的近似范围。

## 在独立目录中重建

需要 Python3、`requirements.txt` 中记录的版本。Blender 使用4.3.2；Meshopt gltfpack 使用1.3.0。精确库及 GEOS 版本见 `ENVIRONMENT.json`。代码不读取参考照片，材质由确定性数值程序生成。

将本源包中的 `source/` 和根级 `LICENSE` 保持相对结构，然后从包根目录执行：

```bash
python -m pip install -r source/requirements.txt
python source/make_materials.py
python source/build_model.py full final-review
python source/build_model.py lod lod-source
blender -b -t 4 --python source/render_final_north.py
python source/package_assets.py --raw final-review/hudec-C-full.glb --lod-source lod-source/hudec-C-lod.glb --native native-final/changning-hudec-residence.blend --out package --gltfpack /path/to/gltfpack
```

输出目录须为新的工作目录；生成器拒绝覆盖已有 GLB。`render_final_north.py` 会制作可编辑原生文件（包含原始全精度网格、打包材质、作者/尺度说明及许可证）并只渲染一张北向审核图。展示地面、相机、灯光位于 `PREVIEW_ONLY_NOT_EXPORTED` 集合，不属于 GLB 模型。

`build_model.py` 及 `hudec_detail.py` 是最终几何入口；`common/photo_architecture.py` 提供有真实洞口和内侧返墙的几何及 GLB 编码。`make_materials.py` 生成512×256的 baseColor / normal / ORM 图集。`ATLAS.json` 声明材质到 UV 单元的映射、9像素内缩、8像素重复边缘、色彩空间及PBR系数。材质是通用示意外观，不是建筑扫描。

全精度模型具有真实分块瓦面、弧形侧屋顶、经裁切的屋谷、曲木撑、凸窗返面、细窗格、烟囱砖缝/凸棱/砖冠、退进的外部门廊和三只实体鸟饰。LOD 从同一输入单独生成，保留轮廓、开口和主要构件，省略瓦片/砖缝微几何并减少曲线分段。Web 仅压缩全精度模型，使用 `-cc -noq -vtf -vnf -km -ke`；不进行几何简化或位置量化。

最终文件及哈希由交付清单指定。原来的西南/西侧审核图绑定 review-v2；最终只新增北侧木格修正的北向图，实际差异为 +36 三角形，边界不变，另有独立差异检查。审核图不充当测绘照片。最终网页、导航及邻楼检查由集成报告单独记录。
