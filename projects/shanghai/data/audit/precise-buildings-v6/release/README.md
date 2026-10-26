# v6 首批三栋网页与视觉核对

本目录只对应外滩05、06、14号修订及相邻新增铺装。三栋的模型加载与交互接入技术检查、有限截图视觉核对均通过；远景背景仍能看到参数推定的普通建筑，不代表全市已逐栋照片复原。

[浏览器原报告](browser.json)按原字节保留，SHA256 `36516029be6abd0bc60adea752bfa488fff96c3ddc1ec092c9e0b358c7bfd306`。它于2026-10-26 07:15:18–07:37:29 UTC运行，单浏览器、1040×760、DPR1，共15组状态／截图记录；其中6个实际近／远景GLB的SHA、字节、照片与压缩状态通过。三栋分别经历近景、斜视、约600m远景及返回近景，另检查精模归属释放、重新进入和城市清单reset。源对象精确替换、14栋邻楼守恒、旧parent释放均有记录；一次重新进入只激活14号，随后reset才重新激活三栋，不将两者混称。

[独立人工视觉记录](visual-review.json)由主审实际查看10张截图后形成，涵盖三栋各自的完整近景、玻璃斜视、远景和一张reset截图。本目录随附这10张原PNG并核对其SHA；其余5组保留在浏览器技术状态记录内，没有声称人工查看全部15张，也未随包附其PNG。浏览器原报告自身的 `visual_review: pending` 是技术采集时状态，后续人工结论以独立视觉记录为准，未改写原报告。详细对应见[范围清单](review-scope.json)。

| 建筑 | 完整近景 | 玻璃斜视 | 远景 |
|---|---|---|---|
| 05 | [截图](bund05-walk-full.png) | [截图](bund05-windows-oblique.png) | [截图](bund05-distant-lod.png) |
| 06 | [截图](bund06-walk-full.png) | [截图](bund06-windows-oblique.png) | [截图](bund06-distant-lod.png) |
| 14 | [截图](bund14-walk-full.png) | [截图](bund14-windows-oblique.png) | [截图](bund14-distant-lod.png) |

[城市清单reset后截图](after-city-manifest-reset.png)。主审确认所查看窗片可读、框槽关系改善、檐口阴影羽化显著减轻、未见明显双重主立面，远近切换和reset后模型仍在。细微栅格阴影锯齿仍存在；这不是将所有雕刻、侧后面、地坪高程和遮挡细节都视为测绘准确。

实际照片玻璃为 `MeshBasicMaterial`，保留 `toneMapped=true`，无重复场景受光、投影或额外HDR；近景原图与05/14的EXIF补偿有检查。远景照片数为零，返回近景恢复。实际阴影贴图4096²、半范围48m，在此设备上通过；该运行记录为8GB设备配置，不作为低内存1024路径的浏览器覆盖。

报告记录0个page／shader／asset／console／request／外部HTTP错误、0次WebGL context loss；同时保留20条warning（15条样式number/null、4条ReadPixels stall、1条宏块取消后保留建筑）和1条预期near请求取消，未声称warning归零。没有注入网络故障、启用强制OSM fallback或评估真实用户硬件帧率，也不能仅凭画面支持关系宣称已验收实测高程或步行ground sampler。

**本次采集早于随后单独自动测试的网络deadline与可选shield filter补丁。** 它证明采集版本的三栋接入状态；补丁后的实际解压v6启动包现已完成[05号与清单重置冒烟](launcher/README.md)。该项只有2组采集／2张主审截图，没有重跑三栋完整远近循环，不改写上述早期三栋报告。

逐栋早期封装／原生记录中保留的browser pending是生成时状态，后续本目录按相同模型SHA补充网页结果。尺寸、照片许可、推定范围见[REALISM_V6](../../../bund/REALISM_V6.md)；后续工作遵循[逐栋标准](../DETAIL_STANDARD.md)。
