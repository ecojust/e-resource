# 名宦祠文字尺寸参照候选检查（2026-10-29）

这份检查确认候选文件及几何可使用，不确认其假设屋顶/开窗与真实建筑一致。名称、三开间、中央开门和文献尺寸有文字依据；单体照片身份尚未核验，未地理配准。

- [几何](geometry.json)：近景25,324三角面、905个源构件；远景3,436三角面、145个源构件。构件封闭、法向一致、正体积；导出顶点有限、无退化面且与源面数一致。几何报告分别记录基座约8.8×6.6米及全部构件约9.55×7.542×6.5米，避免将檐外伸当作文献实测。窗口单元射线穿过框格间隙到达后退暗面，中央关闭门存在。
- [原生重开](native.json)：Blender 4.3.2保存重开几何哈希一致，舞台不计入建筑。
- 实际Cycles渲染：[正面](native-front.png)、[斜侧](native-oblique.png)、[背面](native-rear.png)。初版前后墙与山墙端面共面，角部出现黑条；最终将前后墙收至侧墙内缘，踢脚条改为首尾相接、端盖隐于接头，消除墙角与背面下角的共面条带后重导出和检查。
- [网页检查](browser.json)、[截图](browser.png)：SHA256模型加载、近远景切换、四个相机视角及室外漫游进入、移动和Esc退出。中央门关闭、外部碰撞保留，不提供室内漫游。

资产与哈希见[资产清单](../../../assets/models/candidates/chongming-minghuan-shrine/manifest.json)，每个模型文件均小于100 MB。来源、尺寸端点、屋顶及开窗假设见[来源说明](../../../source/precise/chongming-minghuan-shrine/README.md)。

网页复测：在`projects/shanghai`运行`python -m http.server 8770`，仓库根目录执行`node projects/shanghai/data/audit/minghuan-shrine-v1/qa-browser.cjs`，需Playwright及`/usr/bin/chromium`，输出位于`/tmp/minghuan-shrine-browser.*`。

[最终视觉复核](root-visual-review.json)：已查看最终斜侧、背面和网页截图，确认踢脚条两端黑块已消失；此项仅验收候选显示质量，不证明估计屋顶或门窗符合实物。

公开预览检查：[固定提交页面](https://rawcdn.githack.com/ecojust/e-resource/82f2d21330915b6a1b96c0bbc6b87ea6db48adc0/projects/shanghai/minghuan-shrine.html) 已成功加载25,324三角面的完整模型，查看器SHA256校验通过，无页面或资源请求错误。首次访问如出现托管方提示，点击 **Open the page**。记录见 [public-browser.json](public-browser.json)，复测命令为 `node projects/shanghai/data/audit/minghuan-shrine-v1/qa-public.cjs`。
