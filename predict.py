import torch
#from torch.utils.data import DataLoader
import os
import glob
import numpy as np
from pathlib import Path

from solarnet.models import Segmenter

from matplotlib import pyplot as plt
import rasterio



# Load model and its weights
model = Segmenter()
segmenter_sd = torch.load('C:/clark/GEOG387/solar_panel/solar-panel-segmentation/data/models/segmenter.model')
model.load_base(segmenter_sd)
# model.double() # also make the model parameters to 'double' type

# Load data X

processed_folder = 'C:/clark/GEOG387/project/data/processed/all_org'
tifs = glob.glob(os.path.join(processed_folder,"*"))
print(tifs)

out_folder = 'C:/clark/GEOG387/project/data/processed/mass_y/'

for tif in tifs:
    basename = os.path.basename(tif)
    src = rasterio.open(tif)
    base_name = src
    meta_data = src.meta
    meta_data.update({"driver": "GTiff",
                 "height": 224,
                 "width": 224,
                 "count":1})
    # read meta and array
    dat = src.read().reshape(1,12,224,224)
    src.close()
    x_data = torch.tensor(dat)
    with torch.no_grad():
        y = model(x_data).squeeze(1).cpu().numpy()

    with rasterio.open(os.path.join(out_folder,basename), "w", **meta_data) as dest:
                dest.write(y)


    # write out