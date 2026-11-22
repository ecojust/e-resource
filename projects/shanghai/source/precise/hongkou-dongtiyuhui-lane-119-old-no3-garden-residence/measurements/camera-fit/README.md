# Reproducing the rear-corner depth

Run `python fit_depth.py` with Python 3, NumPy and SciPy. The script reads the adjacent coordinate file and prints the conditional model depth, camera matrices and bed-joint and window reprojection residuals. With the supplied coordinates the depth rounds to 12.38846 m.

The observations come from two 2015 views of the same house, one from the front side and one from the rear side. The 23 frontal points share a frontage-width assumption of 8.4 m. The six bed courses are paired by their position above and below the same two rear-facing side-window crowns. Each course was traced over both faces of the rear corner. The four shared arch and sill points provide the longitudinal constraint. The photographs have no surveyed baseline. Changing the assumed frontage rescales the depth. Independent fits and the uncertainty used for the model are documented in the adjacent measurement summary.
