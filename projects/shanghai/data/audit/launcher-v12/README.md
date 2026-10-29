# v12 启动包实际范围

应用提交：`893156002b860400f2c1c0442d83f1c346331d47`。归档75,180,111字节，SHA256 `d08b38eda5f42b0c34ab174c298ecede6db6eeb94e95250a3340b5cbccdf1c4b`；实际归档检查：[通过](archive-check.json)，303件文件CRC、清单字节和SHA及实际解压核对一致，归档严格小于100 MB。

实际导航与目录计数：30项导航、11栋普通精模、9个目录宏块，14项本地模型与16项联网模型。底图、全城资源与远程模型仍需联网，资源固定到上述应用提交。

MAIN、ZIP和实际解压目录的31件运行时文件核对：[通过](runtime-archive-check.json)，三份目录的31件运行时文件逐字节一致。其中只有 `map-scene.js` 是本轮已审修正，其余30件保持原字节。

从实际解压目录加载四行仓库完整模型的结果：[通过](smoke/browser.json)，实际下载网页GLB 9.11 MB，SHA与最终模型一致，共419,884个三角面；源对象和五栋邻楼检查通过；实际截图观察：[root已实际查看1张图](smoke/root-visual-review.json)，完整西墙模型和第三人称角色可见，信息卡没有遮挡角色。这是一次指定建筑完整模型加载，不包含ZIP内的LOD循环、目录生命周期、全部30项导航、全16区或性能验收。

[下载启动包](https://github.com/ecojust/e-resource/raw/refs/heads/master/projects/shanghai/downloads/shanghai-web-launcher.zip) · [建筑来源与限制](../../bund/REALISM_V12.md)。下载入口随master更新，实际包内版本以上述提交为准。
