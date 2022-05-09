import rasterio
from rasterio.merge import merge
from rasterio.plot import show
import glob
import os

# Read all tif files' path into a list
dirpath = r"../data/processed/mass_y"
out_fp = r"../data/processed/y-output/predict.tif"
search_criteria = "*.tif"
q = os.path.join(dirpath, search_criteria)
tif_fps = glob.glob(q)

# open them in a for loop
src_files_to_mosaic = []
for fp in tif_fps:
    src = rasterio.open(fp)
    src_files_to_mosaic.append(src)

# do the mosaic
mosaic, out_trans = merge(src_files_to_mosaic,nodata=999)

# copy meta from one chip (src defined in for loop) and update its heigh and width
out_meta = src.meta.copy()
out_meta.update({"driver": "GTiff",
                 "height": mosaic.shape[1],
                 "width": mosaic.shape[2],
                 "transform": out_trans,
                 "crs": "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
                            }
                            )
# write to disk
with rasterio.open(out_fp, "w", **out_meta) as dest:
    dest.write(mosaic)

# close the opened tif files
for src in src_files_to_mosaic:
    src.close()