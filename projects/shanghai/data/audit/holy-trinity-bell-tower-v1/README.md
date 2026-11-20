# 圣三一独立钟塔与连接廊

第49项是圣三一主堂北侧的独立方塔。1908年刊出的照片已有高塔，2006年实景仍是失去尖顶的方形台顶，2015年日景和2026年夜景可辨重建后的长尖与四座角塔。主管机构将现尖塔记为48米。Darwent的105英尺对应旧塔记述。拍摄材料、官方名录1A025、门牌和高度异文见来源登记。[制作说明](../../../source/precise/huangpu-holy-trinity-bell-tower/README.md) · [来源收据](../../../source/precise/huangpu-holy-trinity-bell-tower/reference-review.json)

| 检查 | 结果 |
| --- | --- |
| 四种文件 | 近景50,384个三角面，远景28,880个三角面。Blender重开95个可编辑网格，与原始GLB按材料核对。[资产与哈希](../../../assets/models/candidates/huangpu-holy-trinity-bell-tower/manifest.json) · [原生与解码报告](geometry-native.json) |
| 钟室及尖塔 | 三份GLB各通过42项射线，包括百叶之间的空隙、四角小塔与金属端饰、上台三种深度和高处石环。首稿中方台栏孔的原墙和凸窗位置经过修正。[三档射线](surface-checks.json) · [首轮修正](preflight/tower-stage-review.json) · [原生全景和两张细部](author-visual-review.json) |
| 开敞短廊 | 四跨均可横向穿过，纵向可沿中线到实际塔门。测试发现第二稿的门洞偏离中线，重新校正其方向并导出成品。[门位修订](preflight/door-check.json) · [合并两套成品坐标后的实测](connecting-walk.json) |
| 独立查看器 | 桌面与手机各验证完整、远景两档，四种下载实际落盘并核对字节和SHA-256。[查看器实测](viewer.json) · [四张截图核验](viewer-visual-review.json) |

两个模型以不同经纬点为原点，钟塔与主堂方向一致。地图放置采用塔心在主堂本地坐标约X24.0、Y9.6米的位置。塔体、短廊柱脚、四面铺地及相邻源体按实际占地分别处理。两栋之间短廊与主堂北廊的地面高差约2.3厘米。[主堂核验](../holy-trinity-cathedral-v1/README.md) · [位置与保留原体](placement-geometry.json) · [正式合同](final-placement-contract.json)

```sh
python -B projects/shanghai/source/precise/huangpu-holy-trinity-bell-tower/source/check_surfaces.py --out /tmp/tower-rays.json
python -B projects/shanghai/data/audit/holy-trinity-bell-tower-v1/check-connecting-walk.py --out /tmp/tower-walk.json
```

## 城市位置与首屏视角

冻结城市中的616号源是比塔基更长的普通建筑。主管机构的整院俯视与分期航片可把塔基、短廊和主堂定位在同一院内。新模型只在塔基横向占用616号的一段，近、远原网格各保留约66%，两个切面按原源20.3米的屋顶高度封口。主堂587号此前在同一近景分组使用12个裁剪三角面，加入塔身仅增2面。源楼远离塔基的两端仍不可穿过，短廊留下走廊铺地和2米以下独立柱脚间的通行空间。[位置、原航片与源比对](../../../source/precise/huangpu-holy-trinity-bell-tower/footprint-review.json) · [源网格留存与剪切](placement-geometry.json) · [近远与两层矢量运行](runtime-placement.json)

在470×740的真实地图比较了六个首屏角度，保持原楼两端、相邻主堂与灯牌。最初268°/54°的视角让长体屋面挡住钟室以下；最终取315°/22°，阳面的钟室、塔尖、角饰和接往主堂的短廊屋面均可辨。常驻灯牌仍会遮住塔身右侧局部。77°的侧视有利于看清两栋之间的距离和短廊长度。[六组同源视图](preflight/map-overview-cameras.png) · [相机、原网格和模型哈希](preflight/map-overview-cameras.json)

在实际94处旧地图中用相同短廊相机回拍，原616号为狭长平屋面，旁边已加载137,604面主堂。本组原有12个裁剪三角面均属于587号主堂，旧地图没有钟塔的切面或替换。10项原网页与地图文件均成功回读。[原楼与已建主堂](map-before.png) · [94处浏览器记录](control-browser.json)

正式95处地图的390×844手机和870×660桌面首屏均已实看，两端都显示了50,384面钟塔、137,604面主堂及616号源的两个切面。近处短廊视角已实际加载使用14面裁剪的共同分组。手机常驻灯牌横过钟层中段，塔尖和通向主堂的廊面可见。近景及屋顶实测共同分组共14面，仅含原主堂587和新加入的616号。楼内、廊道、源体两端及四处邻楼等10个地面点全过。600×460城市视图实际载入28,880面远景，四件模型与两份原城市网格的6项HTTP下载核对一致。此次正式95处会话没有页面错误、请求失败或加载告警。[手机默认入口](map-mobile.png) · [桌面默认入口](map-desktop.png) · [短廊近景](map-street-facade.png) · [首次入库时的阶段记录](preflight/main-browser-before-completion.json) · [95处完整浏览器记录](main-browser.json) · [屋顶与主堂](map-roof.png) · [城市远景](map-distant.png) · [六图实看](map-visual-review.json) · [公开95处与实测的14项文件核对](primary-map-inputs.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 32 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/bbe7f20cbec5ba6a0f617c8c5d8ebfac3aa07954/projects/shanghai/index.html#landmark=huangpu-holy-trinity-bell-tower&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 32 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
