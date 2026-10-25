# 外滩三栋历史建筑：照片参照的几何重建

这些模型按公开建筑照片辨识主要体量、窗列、退台和屋顶，并使用当前 OpenStreetMap 平面轮廓定位。它们不是摄影测量、激光扫描或竣工图复原。可辨识的临街构件采用实际网格：窗洞、内侧洞口、凹入玻璃、窗台、石柱、拱券、阳台、檐口和屋顶接缝。未使用照片贴图，也未套用通用窗格着色器。

## 重建与文件

需要 Blender 4.3 或更新版本。每栋包含独立 `.blend`、`.glb`、`metadata.json`、整体与入口近景渲染。脚本按构件分组，便于继续修整。

```sh
blender --background --threads 2 --python build_art_deco.py -- peace_north
blender --background --threads 2 --python build_art_deco.py -- bank_china
blender --background --threads 2 --python build_art_deco.py -- peace_south
```

附加 `--no-render` 可仅生成模型。Blender 没有编译 OpenImageDenoise 时也可重建，因为脚本默认关闭该降噪器。`architecture.py` 是同目录依赖；`footprints.json` 包含地图原始引用、真实平面与屋顶三角形，因此重建不需联网。

中文牌匾在导出前由系统的 `NotoSerifCJK-Bold.ttc` 转为实体网格。重新生成中文字形需安装 Noto CJK 字体（Debian 包 `fonts-noto-cjk`）；现有 GLB 和 Blend 不依赖运行时字体。`front.png`、`detail.png` 和最终 `overview.png` 是实际 GLB 在 Three.js 中的几何检查截图；Blender 重建也能生成 Cycles 渲染。

Blender 使用米制东/北/上坐标；GLB 导出后为 **X 东、Y 上、Z 南**。每栋的 WGS84 anchor 在 metadata 中，不能将网格包围盒中心再次移动到原点。地面位于高度零；相邻普通建筑仅应按 metadata 的精确源 ID 替换，不应半径删除。

## 对照重点与可信范围

**和平饭店北楼 / 沙逊大厦**：临江正面三组九列窄窗、底层三拱、连续竖向窗间板、退台与中央挑台、铜皮金字塔、陶土灯亭。实际地图的三个内庭保持为空洞。77 米屋顶、83 米旗杆顶采用《Peace Hotel》公开建筑说明；各层高度分配和雕花细部按照片推定。背面、内庭窗列与设备围护的证据弱于江面与南京东路立面。

**中国银行大楼（外滩 23 号）**：主入口的深洞口与雕刻柱、中央三道铜色窗间板、两旁普通窗及几何花格、上部两级收分、中式曲面翘檐。主楼尺寸/方向来自真实东塔轮廓；关联部件的错误历史名称未用于识别造型。后接西翼使用独立真实轮廓，按建筑文献“四层”解释；这与当前 OSM 的九层标签冲突，西翼立面明确作为低置信度重建，不能描述为实测状态。

**和平饭店南楼 / 汇中饭店**：六层主楼、红砖柱与浅色填充墙、矩形凹窗、交替弧形/三角山花、深底层拱口、连续挑檐、角部八角灯亭与铜顶。主体约 30 米来自建筑文字，角楼与屋面附属高度按照片比例推定。

石材、砖和铜色为照片参照下的基础 PBR 材质；细小的雕刻纹样采用简化几何，不等同于原雕刻逐毫米复制。室内只包含必要的暗色窗后空间，没有虚构可游览的室内布局。

## 资料与许可

完整作者、原图网页、下载 URL 与许可记录在 `references.json`。主要参考：

- Suicasmo，2025 年沙逊大厦、中国银行和汇中饭店照片，CC0。
- ScareCriterion12，2017 年沙逊大厦正面照片，CC BY-SA 4.0。
- Livelikerw，汇中饭店南京东路立面照片，CC BY-SA 3.0。
- 平面几何：© OpenStreetMap contributors，ODbL 1.0；源对象和精确替换 UUID 保存在各栋 metadata 与 footprints 中。

参考照片没有嵌入 GLB；发布参考照片时仍应保留其各自署名和许可。模型与重建脚本的几何解释、材料和假定应保留本说明。
