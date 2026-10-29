# 孙中山故居主楼：原址室外漫游接入

[进入第三人称漫游](../../../index.html#landmark=huangpu-sun-yatsen-residence&mode=walk) · [原模型与来源](../../../source/precise/huangpu-sun-yatsen-residence/README.md)

模型位置沿用已识别源对象及照片参照的估计坐标系。`placement.json` 核对实际 Overture UUID、OSM 多面要素的精确组件、9个宏块中的40个周边源建筑，以及起点、前5米、相机和相机臂。目标邻楼不被替换。尺寸及未见立面仍为估计，不宣称实测或完整历史复原。

碰撞为从实际模型底部生成的保守封闭障碍；仅开放虚拟平地上的室外行走，不支持外廊、台阶、登楼或室内。碰撞和底图隐藏依赖当前模型真实可见、资产字节数及 SHA 验证，模型不可用时保留原建筑。

- `baseline-preservation.json`：生产 Three/Meshopt 解码的原分块与分组分块，顶点、法线、材质、绕序及总面数完全一致；故意删除邻楼会被拒绝。
- `partition.json.gz`：逐实例／连续三角面的源归属记录。75项共边歧义通过唯一生成参考消解；容差只用于归属判别，原始数据没有移动或重新量化。
- `installed-assets.json`：原始GLB、近/远景及Blender完整字节契约。近/远景仅补回 GLB 许可元数据，压缩二进制块 SHA 完全一致。所有单文件小于100 MB。
- `walk-local.json`：初次实际起点、键盘移动、松键停止、墙体阻挡和近/远/近切换。
- `walk-final.json`：最终资产路径、普通精模目录及已加载周边近景下的同项复核。测试按实际位置等待，不以按键发送当作移动成功。
- `fallback.json`：人为断开 Overture 后备用底图仍精确替换目标组件；人为阻断模型文件后不激活精模所有权，原建筑碰撞保留。
- `walk-public.json`：合入前固定提交的公开网页复核，随公开验证补入。

几何造型、照片、原生Blender、开口与原创PBR的独立核验保留于此前模型交付审计；本次沿用相同几何。`source-files.json` 绑定本次最终源码、安装资产和运行时文件；历史审计中的文件哈希指向当时版本，不能用其文字替代本轮接入证据。

运行：`node data/audit/precise-buildings-v22/huangpu-sun-yatsen-residence/qa-walk.cjs BASE_URL LABEL`；异常分支：`node data/audit/precise-buildings-v22/huangpu-sun-yatsen-residence/qa-fallback.cjs BASE_URL`。构建与归属工具见 [V22说明](../../../source/city/precise-overrides-v22/README.md)。
