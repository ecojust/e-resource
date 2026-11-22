# 龙门邨尚文路总弄过街楼

尚文路133弄总弄口的拱洞、石门柱、阴刻题匾、红木双扇、窄红砖带和两重灰瓦檐采用实形建模。从街面到弄内保持约3.82米净宽的通道。[逐图依据与年代](../../../source/precise/huangpu-longmen-village-gatehouse/reference-review.json) · [近景、远景和构件检查](preflight/model-review.json) · [出檐比例与修缮做法](roof-review.md)

## 近看构件

原始与网页近景均有35,072个三角面，远景有15,944个。三档各用139条射线从实体或空隙穿过，检查门洞正反方向、拱腹、砖缝、红字凹深、木窗位置、百叶倾角和瓦脊。低檐与高檐的四个端点用2023年正面照片单独校核，修订后投影均方根误差为1.14像素。该照片用于核对相对比例，建筑尺寸仍为估计值。[五向图与尺寸](preflight/model-review.json) · [全部417个首面查询](preflight/exported-surface-checks.json) · [灰石纹理坐标](preflight/exported-uv.json)

## 弄内通行与地图镜头

在离地0.313米及1.711米处切开三个导出网格，得到左右两个门柱截面。沿街、门内和柱脚的51个位置都核对了通行状态。两个相邻图幅内分别解码原始近、远景网格，最近的原城三角面与新模型相隔约0.70米。门楼独立加入城市，两侧邻房保持原有网格。默认视角从尚文路正对弄内，俯角43度；桌面及手机均能同时看见门柱、门券、题匾、双扇、百叶、1935纪年和三段屋脊。[落位与通行检查](verify-placement.py) · [实际地图镜头检查](check-camera.py) · [完整核验数据](preflight/model-review.json)

## 原生工程与正式站点

用 Blender 4.3.2 重新打开交付工程，可分别编辑127个网格。25种材质下的三角面与原始导出逐一匹配，灰石部件的1,320个纹理坐标也已逐点复核。工程预览为760×900像素，实际完成12次Cycles采样。打包器的通用记录沿用了默认的48次，渲染日志保存了本件的真实计数。[渲染设置及日志记录](native-render-settings.json) ·[原生与三档网格](geometry-native.json) · [灰石纹理坐标](native-uv.json) · [成品三档的417次几何检查](visible-surfaces.json)

正式落位清单记录门楼与街面的51个通行点，并分别保留原房353和1608的碰撞。地图两侧图幅中的原房继续使用原城几何，邻近的1726号原房也已从前后两站复核。默认取景在桌面和手机各核对14处构件。[地面坐标与通行状态](map-ground-witnesses.json) · [双端视线](camera-sightlines.json) · [1726号邻房](adjacent-1726-http.json)

最终站点的1,898个文件均已通过HTTP完整读取，合计1,543,756,398字节。站点依赖、模型文件和地图渲染模块均按冻结清单比对。[整站文件收据](31260-all-http.json) · [网页依赖](real-vendor-http.json) · [前后站渲染模块](final-renderer-31260-http.json)

## 独立页的桌面与触屏视图

在1250像素宽的桌面及390像素宽的手机上分别切换近景和远景。四幅正面图均完整显示两重灰瓦檐、红色窗框、横匾与贯通的门洞。实际保存的原始模型、网页近景、远景和Blender工程各自与清单的文件长度及SHA-256相符。[桌面近景](viewer-desktop-full.png) · [桌面远景](viewer-desktop-lod.png) · [手机近景](viewer-mobile-full.png) · [手机远景](viewer-mobile-lod.png) · [四项实际下载](viewer.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/6a81ab0234c1488485e79f240d2621455ed9e96d/projects/shanghai/index.html#landmark=huangpu-longmen-village-gatehouse&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，8 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
