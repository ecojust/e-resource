# 可编辑工程重开复核

Blender 4.3.2 的两个进程分别写入和重开工程。重开后读得325组可编辑网格、14,376个三角面、13种材质和9台展示相机。按材质比对三角面顶点和绕序，均与原始网一致。两张程序绘制的 PNG 均打包进工程。墙灰的2,928个贴图顶角与红砖的624个顶角分别逐一对回原网，UV 最大绝对差为1.20×10⁻⁷和2.24×10⁻⁸。[重开记录](reopened.json) · [两次实际退出](blender-exits.json) · [工程渲染](native-preview.png)

制作脚本从相同的模型源、纹理和相机定义重建上述工程。[生成与独立重开](../../../../source/precise/xuhui-jianguo-629-rounded-garden-residence/source/package_editable.py)
