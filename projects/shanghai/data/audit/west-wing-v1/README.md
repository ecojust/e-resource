# 西庑文字尺寸参照候选检查（2026-10-29）

本检查验证候选文件、实际几何和独立预览可使用。七楹、26.74×7.7×8米和1997修复有旧馆文字依据；七等分、门窗和屋顶端部与东庑候选共用假设，未核实两庑真实细部一致，不视为照片细节验收或城市配准。

- [几何](geometry.json)：完整近景72,820三角面、2,515个源构件；简化远景9,428三角面、323个源构件。源构件封闭、法向一致、正体积；导出顶点有限、无退化面，源与导出面数一致。六个窗口单元的射线穿过真实框格间隙，到达后退暗面，中央估计双门关闭。侧踢脚端盖与前后踢脚内面衔接，没有暴露在墙外面的共面端盖。
- 文献长宽解释为基座约26.74×7.7米，全部构件外包约27.69×8.644×8米，另行记录以免将檐外伸混作文献尺寸。单栋尺寸乘积205.898平方米，两栋合计411.796平方米，与文献“两庑共412平方米”取整相符。
- [原生重开](native.json)：Blender 4.3.2导入后的建筑面数等于raw，保存并重开后几何哈希一致。独立预览舞台不计入建筑；报告记录所用raw SHA256与最终Blender SHA256。
- 实际Cycles渲染：[正面](native-front.png)、[斜侧](native-oblique.png)、[背面](native-rear.png)。采用明确的墙角内缘衔接与踢脚首尾接头；渲染中墙角和后墙下角未出现共面黑条。
- [网页检查](browser.json)、[截图](browser.png)：独立西庑身份、SHA256文件加载、近远景切换、四个视角、适配相机距离、按本件实际模型生成的漫游边界，以及室外漫游进入/移动/Esc退出。建筑门关闭，不提供室内参观。

几何报告中的`lod`哈希对应压缩前的简化源GLB。打包保持三角面数并保留独立西庑名称及范围元数据，发布文件的哈希由manifest及网页加载另行核对。

| 资产 | 文件大小 |
|---|---:|
| 原始GLB | 5.553400 MB |
| 网页GLB | 1.822600 MB |
| 远景GLB | 0.212544 MB |
| Blender | 2.562418 MB |

各文件均小于100 MB。最终资产哈希见[资产清单](../../../assets/models/candidates/chongming-west-wing/manifest.json)，来源、时期区别、尺寸端点和造型假设见[来源说明](../../../source/precise/chongming-west-wing/README.md)。历史九楹/前廊未套用到现代七楹候选，未复制照片或加入神龛、牌位、石像。

网页复测：在`projects/shanghai`运行`python -m http.server 8773`，仓库根目录执行`node projects/shanghai/data/audit/west-wing-v1/qa-browser.cjs`，需Playwright和`/usr/bin/chromium`。结果输出到`/tmp/west-wing-browser.*`。

[最终视觉复核](root-visual-review.json)：已查看正面、斜侧、背面和网页截图，长屋体与七个立面分区显示正常；只确认基础候选的显示质量，不确认估计门窗和屋顶型制符合实物。

[最终视觉复核](root-visual-review.json)：已查看斜侧、背面和网页截图，西庑标识、共用假设说明及接缝显示正常；不将候选外形相同视为实物细节一致。

公开预览检查：[固定提交页面](https://rawcdn.githack.com/ecojust/e-resource/3418a4b1c3add94408868e221e4b542b6a1fb21f/projects/shanghai/west-wing.html) 已加载完整模型并通过SHA256及西庑身份校验，无页面或资源请求错误；同版本来源登记的七楹记载和旧馆URL核对通过。首次访问如遇托管提示，请点击 **Open the page**。记录见 [public-browser.json](public-browser.json)，复测：`node projects/shanghai/data/audit/west-wing-v1/qa-public.cjs`。
