# 金山卫瓮城城楼 · 可复现外观模型

范围包括墙上楼阁、瓮城围合外墙、主门砖拱、门前低阶及东侧外梯。这里没有整个纪念园、独立纪念墙、群雕、河道、室内或可步行的墙顶与楼梯。

建筑位置、朝向和约35×36.7米的围合上缘来自公开图像人工判读；高度约18.9米、隐蔽连接、瓦列、窗格、台基和内向水平面有估计，不能作为现场测量成果。正面、侧面与简化背面分别建造，保留双重曲面檐、瓦列、砖拱、内退闭门和336个前窗格开口。门额是开源字体字形，不是对原有书法的扫描。

模型采用原创程序灰砖PBR材质，三张512×512 PNG分别为颜色、法线和ORM。每1.28×0.64米重复，砖缝与色彩是通用估计，不是实景扫描；研究照片与卫星影像只作观察参考，没有进入本源码、模型贴图或分发文件。参考来源见[来源登记](source-reference-register.json)和[估计范围](REFERENCE_NOTES.md)。

在本目录的独立副本中生成模型（既有导出文件默认不会被覆盖）：

```sh
python -m pip install -r source/requirements.txt
python source/build_model.py
mkdir -p review
python source/check_actual_glb.py
python source/check_horizontal_surfaces.py
blender --background --factory-startup --threads 2 --python source/render_native.py
```

原始模型生成到`exports/jinshanwei-gatehouse-raw.glb`，远景源模型生成到`exports/jinshanwei-gatehouse-lod-source.glb`。Blender脚本实际导入原始GLB，保存已打包三张贴图的可编辑文件到`review/native/`，并生成正面低眼位、东北斜视、后侧高视三张中性预览。预览地面与灯光置于单独集合，不属于建筑或园区模型。Blender4.3.2、Python3.12与附带依赖版本用于作者验证。

建筑局部米制XYZ先变换为锚点ENU，GLB坐标是East/Up/-North，地理朝向已烘焙，网页heading为0。`source/design-input.json`的研究路径和SHA仅作来源标识，不是外部运行依赖；建模不需要研究照片。

重建原始材质：

```sh
python source/generate_material.py --output material-rebuilt
```

建模与材质代码、几何和原创PNG由agent以MIT许可提供。通用几何辅助代码保留MIT许可及[来源记录](source/HELPER_PROVENANCE.json)。门额字体使用重新命名的Noto Serif CJK子集，附[SIL OFL1.1许可](source/FONT-LICENSE.txt)及[字形来源](source/FONT_PROVENANCE.json)。

浏览器WEB/LOD使用附带的`source/encode_web.py`编码，需要另行安装gltfpack并将可执行文件加入PATH。该工具保留米制浮点位置、法线、UV和来源元数据，不再次简化三角形：

```sh
python source/encode_web.py --raw exports/jinshanwei-gatehouse-raw.glb --lod exports/jinshanwei-gatehouse-lod-source.glb --out web-models --gltfpack gltfpack
```
