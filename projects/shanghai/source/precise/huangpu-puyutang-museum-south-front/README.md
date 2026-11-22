# 普育堂旧址一号楼南立面与1925年门厅

从普育西路105号院内望向一号楼，红砖南墙分两层，横向石带在中央门厅处收住。两根尖顶石墩夹着三角山花。石花绳下是四列木格窗，窗台下的石板刻有“1925”，入口上方的褐色匾额写着“上海民政博物馆”。模型依据档案照片《立面20140816》的南立面全景和门厅近照制作。两张照片均拍于2014年8月16日。[档案页、图幅及校验值](measurements/southern-photo-sources.json)

城市底图内一号楼的南墙边长为47.631米。将两个照片的窗角、檐线和门框共同配准后，得到前檐高约8.45米、层间石带高约4.41米。模型覆盖两端可见的南屋坡、斜脊、南面窗墙和门厅。屋顶背坡和建筑内部不在照片范围内。西翼树后有三处窗位无法辨认，模型保留墙面。东翼部分底窗下方被车遮挡，按同层相邻窗的高宽估出了窗台。窗框入墙深度、屋檐出挑和花雕凹凸也采用估计值。[南墙轮廓](measurements/footprint-review.json) · [两张照片的相机](measurements/two-south-cameras.json) · [可见门窗](measurements/observed-frontage.json)

年份的四个字、石花绳和果实浮雕均为可分别编辑的几何。馆名七字使用 Noto Serif CJK SC 的可再分发字形，按照每个实物字的边框调整宽、高和落点。匾末的小竖题在原照中可见，字义未能确认，未补写。红砖纹理由程序生成，按0.88米重复，原照片没有嵌入模型。[数字与石雕](measurements/portal-carvings-2014.json) · [馆名逐字量幅](measurements/museum-sign-layout.json) · [字体、参考图和软件许可](SOURCES-LICENSE.md)

## 从源码重建

在项目完整工作树中进入本目录。所需程序包括 Python、NumPy、SciPy、Shapely、Pillow、gltfpack 及 Blender。以下命令可重建两份原网，并读取与 Blender 重开核查相同的原始 UV。

```sh
python source/paint.py
python source/build_model.py --output museum-full.glb
python source/build_model.py --lod --output museum-low.glb
python source/build_blender_source.py --check-raw museum-full.glb
```

[窗墙、瓦坡与门厅](source/south_front.py) · [石雕与年代](source/portal_carvings.py) · [匾额与七字](source/museum_sign.py) · [七个机位](source/cameras.json)
