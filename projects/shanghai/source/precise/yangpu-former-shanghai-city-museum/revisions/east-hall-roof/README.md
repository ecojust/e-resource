# 江湾馆舍东中厅屋面

旧上海市博物馆位于杨浦区长海路174号。现有地图模型的东中厅位于黄瓦门楼东侧、两处内院之间。四期航片都能辨认厅顶的矩形构件，2022、2026 两个发布版本分格较清楚。2022 与 2026 影像上量得长度分别约 10.83、10.83 米，深度约 5.47、5.36 米。以东檐定位时，两期所得的东西方向中心相差约 1.62 米。照片中的窗框式网格简化为三列两排，选用灰绿色板面和浅灰边框。高度、材料、构造方式、使用功能和安装年代均待核。[航片坐标、量取与36片来源](../../../../../data/audit/city-museum-east-hall-roof-v1/roof-observation.json)

《上海文物博物馆志》记载战前江湾馆舍后面大厅两层用于历史部陈列，1937年1月开馆，战后迁至四川北路1844号。《上海市立博物馆要览》存本的馆舍外景题为“本馆现用馆舍外景”，同页另列战前陈列室照片，两者所摄时期有别。资料不足以确认现存东中厅的顶部构件与战前陈列室的对应关系。南北墙开窗和其旁独立连接体的年代仍待实拍或测绘图确认。[地方志](https://web.archive.org/web/20150405112227id_/http://www.shtong.gov.cn/Newsite/node2/node2245/node4467/node20490/node20492/node63796/userobject1ai16055.html) · [档案版本和逐件指纹](../../../../../data/audit/city-museum-east-hall-roof-v1/archive-sources.json)

本次沿用建筑 ID、原有的西立面、南北翼和两处内院。主源 1860 与门楼 1931 的既有配准继续适用。院内两个独立城市源分别为 510、1262。原始、网页近景、远景三种格式均对照上一版实际发行资产，按材质、顶点位置和三角面绕序比较，原有材质参数与三角集合均相同。新增部件共 144 面，位于原地面轮廓以内，最低点高于地面 10.10 米。[四件修订资产](../../../../../assets/models/candidates/yangpu-former-shanghai-city-museum/manifest-east-hall-roof.json) · [原始版本](../../../../../assets/models/candidates/yangpu-former-shanghai-city-museum/manifest.json)

## 重建

从本目录执行下列命令。Python 依赖沿用现有馆舍的 [requirements.txt](../../source/requirements.txt)。资产生成使用 Blender 4.3.2、gltfpack 0.25 和 ImageMagick，渲染去噪使用 Open Image Denoise 的 `oidnDenoise`。Blender 原生文件重开后分别渲染屋面近图和整栋两院视角。

```sh
id=yangpu-former-shanghai-city-museum
python build_roof_revision.py --out build
python build_roof_revision.py --lod --out build
blender -b --threads 2 --python-exit-code 1 --python build_native.py -- \
  --raw "build/$id-raw.glb" --out "build/$id.blend" \
  --previews build/preview --samples 8 --views eastcover,eastcourt --oidn oidnDenoise
python package_revision.py --raw "build/$id-raw.glb" --lod "build/$id-lod.glb" \
  --native "build/$id.blend" --gltfpack /path/to/gltfpack \
  --asset-root "../../../../../assets/models/candidates/$id"
```

可用项目内的 [meshopt 解码器](../../../hongkou-general-post-office/source/decode_meshopt.mjs) 将网页与远景 GLB 解压。分别用 `check_roof.py --decoded 文件 --source 原压缩文件 --out 结果.json` 检查 23 个物理采样点，原始 GLB 直接传给 `--decoded`。用 `check_delta.py --old 旧模型 --revised 新模型 --out 结果.json` 检查全模型；解压输入对应的发行资产通过 `--old-packed` 与 `--new-packed` 传入。几何采用原馆舍模型的 [MIT 许可](../../LICENSE)。

可在本地从四期服务原瓦片复核量取，所有下载先核对 SHA-256。运行 `python review_imagery.py --evidence ../../../../../data/audit/city-museum-east-hall-roof-v1/roof-observation.json --out /tmp/museum-roof-study`，即可生成四个同范围裁图和带人工取样边界的两期参考图。该步骤使用 Pillow。[36 张原瓦片复取收据](../../../../../data/audit/city-museum-east-hall-roof-v1/tile-recheck.json)
