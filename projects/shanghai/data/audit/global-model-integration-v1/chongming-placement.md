# 崇明学宫的全局场景接入

20件既有模型已按南北主轴、两侧配属和东轴次序摆入全局场景。位置、共同5°朝向及院落间距是地图、卫星图、航拍与文字引导的近似配准；各原模型的尺寸、外观及历史时段限制继续适用。这不是实测平面，也不是整个学宫在某一日期的完整复原。

[位置数据](../../global-models/chongming-placement.json) · [几何／邻源检查](chongming-placement.json) · [参考与观察](chongming-reference.json) · [布局和保留范围](chongming-layout.png)

冻结城市源 `14-13716-6673` 的第192号（`building:128f4cb0-fcdf-4948-8729-d812245dc745`，OSM `w413345693@3`）是整座博物馆园址，原统一拉高15.3米，面积约12,907.15平方米。接入仅清除主轴与东轴既有模型及其院落所在的约7,085.27平方米，保留约5,821.88平方米的西轴、东北两排未建合院及其余源体示意。清除边界也是估计，不代表考古或实测建筑分界。旧块的剩余部分仍是基线体量，不能当作新制作的建筑。

检查覆盖源园址65米内全部67个其他源要素；邻域在同一宏块内，所有其他ID均保留。它们与本次清除区没有正面积交叠，20件模型的保守平面外包之间也没有正面积交叠。原园址南界未覆盖全部前庭，牌坊和部分门位于其外；它们仍按前庭次序进行估计摆放，不据此改写原地图边界。

碑廊的原独立场景使用两条同向、间距7米的长边。本次另存[全局近景](../../../assets/models/global/chongming-stele-corridors/chongming-stele-corridors-web.glb)与[远景](../../../assets/models/global/chongming-stele-corridors/chongming-stele-corridors-lod.glb)：只改变两个场景节点，分别旋转±90°、平移到东西±9米，使它们朝院。18米间距为本次布局估计，未增补南北短段。近景232,696面、远景42,200面保持不变；GLB二进制块、网格、索引、材质、其他JSON逐字节不变。原独立GLB与Blender均保留，Blender仍表示原展示布局；本轮没有另存声称地理配准的原生模型。

泮池为适配零高程底图，采用 **0.85米显示抬升**，使原本-0.8米的水面显示在0.05米处。这不是实测场地标高，也没有开挖地形；原模型文件未改。所有20个新入口仅提供全局俯瞰定位，未验收院内漫游、门洞、台阶、上桥或室内通行。

重建位置数据、派生碑廊与数值检查（需原Git对象、已有inventory.json、Python和shapely）：

```sh
python projects/shanghai/tools/build_chongming_global_placements.py
# 可选：重建原创布局图，另需matplotlib与Noto Sans CJK字体
python projects/shanghai/tools/render_chongming_global_layout.py
```

参考图像只用于观察，不在仓库再分发、嵌入或采样。公开布局图只包含原创模型外包、原地图轮廓及说明；地图来源保留 © OpenStreetMap contributors、ODbL-1.0。卫星图来源及每瓦片响应SHA256、航拍来源与限制均见参考记录。
