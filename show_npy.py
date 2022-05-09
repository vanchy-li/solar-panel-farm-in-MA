import matplotlib.pyplot as plt
import numpy as np
import os


base_dir = 'C:/clark/GEOG387/solar_panel/solar-panel-segmentation/data/models'
# base_dir = 'C:/clark/GEOG387/solar_panel/solar-panel-segmentation/data/processed/empty/org/'
# base_dir = 'C:/clark/GEOG387/project/data/processed/mask'
# print(np.load(os.path.join(base_dir,'segmenter_images.npy')).shape)

# exit()
# print(np.load('C:/clark/GEOG387/solar_panel/solar-panel-segmentation/data_s2band12/models/segmenter_preds.npy').shape)
# exit()
# print(np.load('C:/clark/GEOG387/solar_panel/solar-panel-segmentation/data/processed/solar/org/Fresno_0.npy').transpose(1, 2, 0).shape)
for i in range(10):
    print((i+1))
#img_id = int(input("Enter image id: "))
    img_org = np.load(os.path.join(base_dir,'segmenter_images.npy'))[i].transpose(1,2,0)[:, :, 1:4]/50
    img_pred = np.load(os.path.join(base_dir,'segmenter_preds.npy'))[i]
    img_true = np.load(os.path.join(base_dir,'segmenter_true.npy'))[i]
# print(img_org.shape)
#exit()
# img = np.load('C:/clark/GEOG387/solar_panel/solar-panel-segmentation/data/processed/empty/org/Fresno_8.npy').transpose(1, 2, 0)#os.path.join(base_dir,'Fresno_0.npy')
# plt.imshow(img, cmap='BrBG_r')
#plt.show()
    f, axarr = plt.subplots(1,3) 
    axarr[0].imshow(img_org)
    axarr[1].imshow(img_pred)
    axarr[2].imshow(img_true)

# plt.imshow(img)
# plt.imshow(img_pred)
# plt.tight_layout()
    plt.show()