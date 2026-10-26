# 外滩14号：交通银行大楼逐栋重建

本栋以2025年5月1日Commons正面照片为外观基准，用2010俯拍及2007、2010、2012、2014斜视确认塔体进深、侧墙和屋顶折返。完整照片来源、拍摄日期、作者及许可见 [research/README.md](research/README.md) 和 [research/sources.json](research/sources.json)。28个上层窗的137个清晰玻璃分格使用该CC0原图中的独立采样，原JPEG字节直接嵌入；墙面和实体窗框不贴整幅照片。

模型保留冻结OSM非矩形轮廓、西伸长翼和北侧凹口，正面宽23.174494m。只替换 `930b1722-187d-4727-ad8b-303698ad37ee`；北侧现代外滩公共服务中心不属于本栋。

## 本次几何

- 四排规则窗各8轴，两端窄窗、两翼各2窗、中央2窗。低层两侧各3窗，中部是贯穿两层视觉高度的大入口，未机械复制规则层。
- 48个正面窗洞均有真实孔洞、退距、框、竖梃、上横亮和窗台。墙体为连续开孔多边形，竖向沟槽有实体深度，宽墙肢与窄凸脊分别建模。
- 黑色石材入口含多级内退线脚、门扇、玻璃、门把手、七根金色纵向格栅及节点、水平门楣。金色“上海市总工会”已用SIL OFL许可字形做实体挤出，14门牌也有可读矢量笔画；是近似可读字体，不冒称照片书法描字。
- 中央2层塔不是立面薄片：含侧窗、实体进深、后墙、平顶、向西退阶的中脊、前部两组分节圆弧饰件。两端细长屋顶翼片、折回墙及小帽也有厚度。
- 白水泥/涂饰墙、深色窗框、黑大理石入口分开赋材质；后墙没有套用整片石块纹理。未把旧上海银行广告、2012公交站或临时2025横幅混进建筑。

后翼檐高、部分侧后窗数、精确槽深和所有绝对高程仍是照片/地图比例推定。文献支持6层主体+2层塔，但没有取得可信实测米高。独立透视尺度复核与取值状态记录在 [calibration.json](calibration.json)，不沿用旧模型7×3.2m的22.4m估计。

## 可移植构建

保留目录 `photo-rebuild-v6/{common,bund14}`，本脚本从相邻common导入；不依赖主项目绝对路径。

```sh
python bund14/build_model.py --output /path/to/output
```

需要Python、numpy、fontTools及支持约束三角剖分的Shapely（本机2.2.0）。模型输出自包含GLB、逐部件几何/证据检查报告和字牌坐标。构建器强制GLB小于100,000,000字节；逐个部件检查边配对、正有向体积和float32零面积三角形。建筑层叠构件允许接触/相交，没有冒称已进行全建筑布尔并集。

玻璃控制见 [glazing-samples.json](glazing-samples.json)，选择依据和逐窗图见 [glazing-evidence/README.md](glazing-evidence/README.md)。先以独立3×4投影寻找窗口，再逐窗校正范围、逐分格拟合四角，向内留边排除黑框。遮挡或边界不可靠的4整窗和17个分格保留原材质。`prepare_glazing_samples.py` 可用Pillow/SciPy再生成采样控制；它不修改原JPEG。`validate_model.py --output /path/to/output` 检查嵌入原图SHA、每个纹理顶点与其独立映射、UV范围和真实玻璃深度。

Blender工程、最终材质与EXIF解码检查和预览由统一完成步骤处理。`output/`是构建产物，不应在源码包中重复分发；最终原/优化GLB及blend使用主项目canonical资产路径。

源码与独立生成几何沿用项目MIT约定；地图轮廓来自OpenStreetMap，按ODbL-1.0保留来源。照片各自保留CC0、CC BY或CC BY-SA许可，详情见研究清单。研究中的文章全文HTML、搜索缓存和失败页面不随模型源码发布。

## 玻璃嵌框修订

本轮只把同种窗构造的玻璃前移到现有窗框前脸后20mm，玻璃厚度仍20mm；这是明确的构造估计，不是实测退距。墙洞、窗框前后面和形状、照片、UV、锚点及三角形总数保持。细节和源SHA见[修订依据](glazing-depth-revision.json)，逐材质及玻璃实体差异见[几何比较](glazing-depth-difference.json)。旧源码快照与原生预览另存 [glazing-depth-history](glazing-depth-history/README.md)，附完整输入 SHA 校验和独立恢复命令，仅适用于旧模型。新候选已通过构建、闭合、原图与UV检查；原生预览已由root明确核对，浏览器复验仍单独进行。修订已同步到项目源码与模型；最终浏览器复验仍待完成。

## 修订资产与原生检查

原始、网页、Blender及无照片远景变体已独立打包。原始与原生副本保留原字节，网页经实际解码核对三角位置、法线与UV；原JPEG保留。当前文件大小如下（字节），每件均小于100,000,000。

| 文件 | 字节 | 下载 |
|---|---:|---|
| 原始GLB | 9,844,376 | [下载](../../../../assets/models/bund/bund14.glb) |
| 网页GLB | 6,725,708 | [下载](../../../../assets/models/bund/web/bund14.glb) |
| Blender工程 | 15,048,712 | [下载](../../../../assets/native/bund/bund14.blend) |
| 远景GLB（无照片） | 1,443,684 | [下载](../../../../assets/models/bund/lod-v4/bund14.glb) |

root已实际查看本修订的原生预览；照片和窗框的核对范围见[记录](native-preview-review.json)。浏览器同视角及场景复验另行完成，不以原生预览替代。完整封装、LOD与来源版权检查见[打包摘要](packaging-summary.json)。

[本修订原生预览](../../../../assets/previews/bund/bund14-v6.png)；[公开玻璃差异审计](../../../../data/audit/precise-buildings-v6/bund14/glass-depth-difference.json)。
