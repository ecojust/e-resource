# 宏恩医院历史主楼花园立面

模型包括中央五开间门廊、两端山花和两段各五跨的拱廊窗墙。布局参照 1920 年代的档案影像，中央门廊细部和暖浅色墙面参照 2015 年照片。端部对称关系、标高、进深和遮挡部位为估计。后翼、完整屋顶、与现代院楼的连接另列制作任务。[模型与原始资料](../../../source/precise/jingan-country-hospital/README.md) · [资产清单](../../../assets/models/candidates/jingan-country-hospital/manifest.json)

## 模型与网页

近景 75,388 个三角面，远景 32,128 个。Blender 原生文件重开后有 318 个命名网格。渲染画面可见三组山花、中部两层阳台与五个八角窗，转折檐线、窗楣和投影区分开来。[正立面渲染](jingan-country-hospital-garden-front-preview.png) · [原生与网格核验](geometry-native.json) · [照片比对](author-visual-review.json)

从仓库源码在空目录重新制作，三份 GLB 与发布候选文件逐字节一致。重建的 Blender 容器哈希随保存而变化，重开后仍有 318 个网格。[独立重建核对](rebuild-check.json)

分别向原始 GLB 和实际解压的网页 GLB、远景 GLB 发出 33 条射线，检查指定窗、券洞、柱和山花的实体与留空。独立查看页在桌面和 390 像素窄屏上均能以正面视角容纳两端山花。两档保留了三个门廊的轮廓及底层开口，远景简化了窗格。实际点击四个下载链接后逐件比对 SHA256。[几何探针](surface-checks.json) · [查看页与下载实测](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png)

## 地图接入

当前制作的是约 78 米长的花园立面。历史主楼对应的原始地图体块约 133 米长、21 米深。只裁去花园侧有新模型覆盖的部分，保留两端和后段。地面障碍按实际几何单独计算。原地图粗略屋顶约 24.1 米，立面模型最高约 18.8 米。两者分别记录。[源定位](../../../source/precise/jingan-country-hospital/footprint-review.json) · [裁剪及邻楼](footprint-review.json) · [运行时代码核对](runtime-placement.json)

花园立面只占粗体块的一部分。沿保留体块新增七段中性灰色截面，使用原粗模屋顶标高与材质颜色。截面随目标模型及原地图块的可见状态出现或释放，只用于地图显示。

第一次近景预览可通过原体块的开口看到后方窗格与地面。该轮使用临时目录，灯牌显示临时名称。[修正前的取景与版本](preflight/garden-near-open-cut.json) · [修正前近景](preflight/garden-near-open-cut.png)

正式 Chromium 实测 85 处目录，静安区 2 处。桌面近景和鸟瞰显示保留的原楼与新立面；同机位东侧开口取样可见的地面粉色像素从 83.67% 降至 0。390 像素竖屏直接从目录进入时能容纳两端，选中灯牌会遮住中段的一部分。真实鼠标和触摸在全市缩放能点中该栋，远景模型、近景模型和四项下载的字节均已校验。[最终浏览器记录](main-map-browser.json) · [修正后近景](main-garden-near.png) · [手机主图](main-mobile.png)

## 复核

从仓库根目录运行以下模型专项。浏览器检查使用 Playwright、pngjs、Chromium 和实际上海站点的 HTTP 服务。对稀疏检出的地图资源，可复用上栋的 `qa-server.py`，以 `QA_BASELINE_COMMIT=2b66614baae35f0d032fc4d18e5f4c808d036cc4` 指定地图原始资源的版本。本地应用、目录和模型文件以当前工作区字节提供。

```sh
python -B projects/shanghai/data/audit/country-hospital-v1/check-surfaces.py
MODEL_BASE_URL=http://127.0.0.1:8784/ QA_OUTPUT_DIR=/tmp/country-hospital-viewer node projects/shanghai/data/audit/country-hospital-v1/check-viewer.cjs
MODEL_BASE_URL=http://127.0.0.1:8784/ QA_OUTPUT_DIR=/tmp/country-hospital-city node projects/shanghai/data/audit/country-hospital-v1/check-main-map.cjs
```

六项目录生成检查及本次灯牌、导航、相机和截面专项均通过。全项目 `npm test` 中的旧碰撞测试有六项因夹具未提供 `candidateState` 而失败，在上栋提交和本轮工作区均已复现。[基线对照](test-baseline-comparison.json)


## 公开下载

模型提交 `fe99c185d485d8916b265a0e04fe42b72bde717c` 的 28 个公开文件与 Git 字节一致，包括三份 GLB 和可编辑 Blender 文件。[固定版本主图](https://raw.githack.com/ecojust/e-resource/fe99c185d485d8916b265a0e04fe42b72bde717c/projects/shanghai/index.html#landmark=jingan-country-hospital&mode=overview) · [逐文件哈希](publication.json)

2026-11-20 05:48 UTC 的复查中，master 的 28 项公开字节均与模型提交 `fe99c18` 一致。登记提交 `92fd7a5` 发布后，缓存中两项文档曾仍为旧版，05:53 UTC 复查时该提交的 28 项全部一致。[模型提交的 master 复查](publication-master-fe99c18.json) · [登记提交固定链接实测](publication-92fd7a5.json) · [缓存中的旧文件](publication-master-92fd7a5-initial.json) · [登记提交的 master 复查](publication-master-92fd7a5.json)
