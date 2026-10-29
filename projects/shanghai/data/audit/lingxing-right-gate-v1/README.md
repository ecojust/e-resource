# 棂星门照片右侧门候选检查（2026-10-29）

本件是1990年代低分辨率历史照片参照的基础外观候选，关闭姿态和门面细分均含估计；不代表完整照片复原、特定修缮阶段或城市配准完成。

- [几何](geometry.json)：近景948三角面、63个源构件，远景684三角面、49个源构件。构件封闭、正体积、法向一致，导出顶点有限、无退化面，源/导出面数一致。实际导出石框射线量测净开口约2.3×3.2米；两根伸高柱存在。关闭中缝与下部板应阻挡射线，上部栅条间隙应畅通，均通过检查。
- [Blender重开](native.json)：模型保存重开几何哈希一致，舞台不计入建筑。
- 最终Cycles预览：[正面](native-front.png)、[斜侧](native-oblique.png)、[背面](native-rear.png)。检查发现初版木框横竖接头共面闪面后，已调整横档、边框和嵌板的前后层次；最终输出已重导出。
- [网页检查](browser.json)、[截图](browser.png)：SHA256校验加载、近远景切换、四个相机按钮及室外漫游进入/行走/Esc退出。闭门与外围碰撞均不提供穿门入院。

模型文件均小于100 MB；大小与哈希见[资产清单](../../../assets/models/candidates/chongming-lingxing-photo-right-gate/manifest.json)。源图不再分发或贴图，出处、图注和年代限制见[来源说明](../../../source/precise/chongming-lingxing-photo-right-gate/README.md)。

复测网页：在`projects/shanghai`运行`python -m http.server 8769`，仓库根目录运行`node projects/shanghai/data/audit/lingxing-right-gate-v1/qa-browser.cjs`。需Playwright和`/usr/bin/chromium`，输出位于`/tmp/lingxing-right-gate-browser.*`。
