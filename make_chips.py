import rasterio
from rasterio.windows import Window
import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Pool
import itertools
import os
import geopandas as gpd
from shapely.geometry import Polygon
from rasterio import features
import random
import shutil
import glob
import warnings

class MakeChips:
 
    def __init__(self, study_area_in):
        
        self.out_folder_bands=''
        self.out_folder_label_yes=''
        self.out_folder_label_no=''
        self.label_polygon_path=''
        self.chip_format = 'tif'
        self.out_folder_bands_yes=''
        self.out_folder_bands_no=''
        self.data_type =''

        global src, height,width, study_area
        # open study area
        study_area = study_area_in
        self.study_area = study_area
        src = rasterio.open(self.study_area)
        # read metadata and transform
        meta_data = src.meta
        self.data_type = meta_data['dtype']
        transform = src.transform
        self.lon_res = transform[0]
        # self.lon_start = self.transform[2]
        self.lat_res = transform[4]
        # self.lat_start = self.transform[5]

        # check if the proposed 224*224 chip exceeds the study area
        self.height = meta_data['height']
        self.width = meta_data['width']
        
        
    
        lon_curser = src.transform[2]
        self.lon_rightend = src.transform[2]+src.meta['width'] * src.transform[0]
        self.lon_list = []
        lat_curser = src.transform[5]
        self.lat_lowerend = src.transform[5]+src.meta['height'] * src.transform[4]
        self.lat_list = []
        while  lon_curser < self.lon_rightend:
            self.lon_list.append(lon_curser)
            lon_curser +=src.transform[0]*224
    
        while  lat_curser > self.lat_lowerend:
            self.lat_list.append(lat_curser)
            lat_curser +=src.transform[4]*224
    
        self.seeds = list(itertools.product(*[self.lon_list, self.lat_list]))
        self.seeds_flag = 'regular'
        
        # print some information for this study area
        print("Study area added: {}".format(os.path.basename(self.study_area)))
        print("CRS: {}".format(meta_data['crs']))
        print("Res.: {}".format([src.transform[0],src.transform[4]]))
        print('data type: {}'.format(self.data_type))
        print("upper-left coordinates: {}".format([src.transform[2],src.transform[5]]))
        print('lower_right coordinates:[{},{}]'.format(self.lon_rightend,self.lat_lowerend)) 
        print("height: {}, width: {}".format(self.height, self.width))
        print("Proposed chip number: {}".format(len(self.seeds)))
    
    def reset_seeds(self):
        self.seeds = list(itertools.product(*[self.lon_list, self.lat_list]))
        self.seeds_flag = 'regular'
        
    def sample_floats(low, high, k=1):
        # cite: https://stackoverflow.com/questions/45394981/how-to-generate-list-of-unique-random-floats-in-python
        """ Return a k-length list of unique random floats
            in the range of low <= x <= high
        """
        result = []
        seen = set()
        random.seed(10)
        for i in range(k):
            x = random.uniform(low, high)
            while x in seen:
                x = random.uniform(low, high)
            seen.add(x)
            result.append(x)
        return result

    def random_seeding(self, n):
        rand_lons = sample_floats(src.transform[2],self.lon_rightend, n)
        rand_lats = sample_floats(src.transform[5],self.lat_lowerend, n)
        self.seeds = list(zip(rand_lons,rand_lats))
        self.seeds_flag = 'random: '+str(n)

    def read_polygons(self, label_polygon_path):
        self.label_polygon_path = label_polygon_path
        self.all_polygons = gpd.read_file(label_polygon_path)
    
    def set_outfolder_bands(self,out_folder):
        self.out_folder_bands = out_folder
    def set_outfolder_bands_yes(self,out_folder):
        self.out_folder_bands_yes = out_folder
    def set_outfolder_bands_no(self,out_folder):
        self.out_folder_bands_no = out_folder
            
    def set_outfolder_label_yes(self,out_folder):
        self.out_folder_label_yes = out_folder
    def set_outfolder_label_no(self,out_folder):
        self.out_folder_label_no = out_folder
            
    def makechip(self, ul_coords):
            # get x,y index offsets from coordinates offsets 
            src = rasterio.open(self.study_area)
            self.offsets = src.index(ul_coords[0],ul_coords[1])[::-1]#give lat/lon not lon/lat
            self.offsets_adjust = list(self.offsets)
            #print('given index (before adj):{}'.format(self.offsets_adjust))
            # if offsets exceeds the study area boundary, 
            #then let the chip's right or lower boundary at the study area
            if self.offsets[0]+224-self.width>0:
                self.offsets_adjust[0] = self.width-224
                self.oversize_lat_flag = 1
            if self.offsets[1]+224-self.height>0:
                self.offsets_adjust[1] = self.height-224
                self.oversize_lon_flag = 1

            # make window for window reading
            self.window=Window(self.offsets_adjust[0],self.offsets_adjust[1], 224,224)

            # make out transform in case to write out in tif
            self.out_transform = src.window_transform(self.window)


            outname = str(ul_coords[0])+'_'+str(ul_coords[1])
            outname = outname.replace('.', 'D').replace('-','')
            outpath = os.path.join(self.out_folder_bands, outname)
            #print('given index (after adj):[{},{}]'.format(self.offsets_adjust[0],self.offsets_adjust[1]))
            #print(src.read(window=self.window).shape)
            if self.chip_format == 'npy':
                np.save(outpath, src.read(window=self.window)) 
            elif self.chip_format == 'tif':
            # prepare out meta
                out_meta = src.meta.copy()
                out_meta.update({"driver": "GTiff",
                     "height": 224,
                     "width": 224,
                     "transform": self.out_transform})
                with rasterio.open(outpath + '.tif', "w", **out_meta) as dest:
                    dest.write(src.read(window=self.window)) 
    def makechips(self,worker=2):
        with Pool(worker) as p:
            p.map(self.makechip, self.seeds)

    def chip_bbox(self, ul_coords):
            ul_lon = ul_coords[0]
            ul_lat = ul_coords[1]
            ur_lon = ul_lon+self.lon_res*224
            lr_lon = ur_lon
            ll_lon = ul_lon
            lon_list = [ul_lon, ur_lon, lr_lon, ll_lon]

            ur_lat = ul_lat
            lr_lat = ul_lat+self.lat_res*224
            ll_lat = lr_lat
            lat_list = [ul_lat, ur_lat, lr_lat, ll_lat]

            polygon_geom = Polygon(zip(lon_list, lat_list))

            crs = {'init': 'epsg:4326'}
            polygon = gpd.GeoDataFrame(index=[0], crs=crs, geometry=[polygon_geom])
            return polygon  
    def make_ul_points(self,out_name):
        crs = {'init': 'epsg:4326'}
        # lon list for each seed, different from lon list for Y axis in __ini__
        seed_lon_list = np.array(self.seeds).transpose(1,0)[0]
        seed_lat_list = np.array(self.seeds).transpose(1,0)[1]
        points_geom = gpd.points_from_xy(seed_lon_list, seed_lat_list)
        out_shape = gpd.GeoDataFrame(crs=crs, geometry=points_geom)
        out_shape.to_file(filename=out_name, driver="GeoJSON")
       
        #polygon_geom = Polygon(self.seeds)
        #out_shape = gpd.GeoDataFrame(index=[0], crs=crs, geometry=[polygon_geom])       
        #out_shape.to_file(filename='/media/sitian/HDD1/solar_panel/newmethod/data/sentinel2_debug/polygon', driver="GeoJSON")
        return 0
        
        
    def make_label(self, ul_coords):
        src = rasterio.open(self.study_area)
        bbox = self.chip_bbox(ul_coords)
        out_transfrom = rasterio.Affine(self.lon_res, 0.0, ul_coords[0],0.0, self.lat_res, ul_coords[1])
        label_chip_vec = gpd.clip(self.all_polygons, bbox)
        
        
        # prepare out meta
        out_meta = src.meta.copy()
        out_meta.update({"driver": "GTiff",
             "height": 224,
             "width": 224,
             "count":1,            
             "transform": out_transfrom})

        outname = str(ul_coords[0])+'_'+str(ul_coords[1])
        outname = outname.replace('.', 'D').replace('-','')
        
        
        if label_chip_vec.empty:
            #print('bbox contains no solar panel!')
            if self.chip_format == 'npy':
                np.save(os.path.join(self.out_folder_label_no, outname),np.zeros((224,224)).astype(self.data_type))
            elif self.chip_format == 'tif':
                with rasterio.open(os.path.join(self.out_folder_label_no, outname), "w", **out_meta) as dest:
                    #print(np.zeros((1,224,224)).shape)
                    dest.write(np.zeros((1,224,224)).astype(self.data_type))
            return 0
        
        label_chip_vec.drop(columns=label_chip_vec.columns.difference(['geometry']), axis=1, inplace=True)
        label_chip_vec['presence']=1
        
        shaply_shapes = ((geom,value) for geom, value in zip(label_chip_vec.geometry, label_chip_vec.presence))
        burned = features.rasterize(shapes=shaply_shapes, fill=0, out=np.zeros((224,224)).astype(self.data_type),transform=out_transfrom)
       
        

        print('found solar panel in: {}'.format(outname))
        if self.chip_format == 'npy':
            np.save(os.path.join(self.out_folder_label_yes, outname),burned.reshape(224,224))
        elif self.chip_format == 'tif':
            with rasterio.open(os.path.join(self.out_folder_label_yes, outname+'.tif'), "w", **out_meta) as dest:
                #print(burned.reshape(1,224,224).shape)
                dest.write(burned.reshape(1,224,224))
                
              
        
    def makelabels(self,worker=5):
        with Pool(worker) as p:
            p.map(self.make_label, self.seeds)   
        # chip_seeds is a list of (lon,lat), each indicates a upperleft coords of a propsed chip       
        #makechip(self,(-74.5061798333447, 42.93497900449253))
        # with Pool(5) as p:
        #     p.map(self.printname, [1,2,3])
        
        

    def populate_folder(self):

        chips_allbands = glob.glob(os.path.join(self.out_folder_bands,'*.'+self.chip_format))
        basename_solar = [os.path.basename(i) for i in glob.glob(os.path.join(self.out_folder_label_yes,'*.'+self.chip_format))]
        basename_empty = [os.path.basename(i) for i in glob.glob(os.path.join(self.out_folder_label_no,'*.'+self.chip_format))]
    

        for i in basename_solar:
            dst = os.path.join(self.out_folder_bands_yes,i)
            src = os.path.join(self.out_folder_bands,i)
            print(dst, src)
            shutil.copyfile(src, dst)

        for i in basename_empty:
            dst = os.path.join(self.out_folder_bands_no,i)
            src = os.path.join(self.out_folder_bands,i)
            shutil.copyfile(src, dst)
    
    # This function will keep the solar and empty chips in the same number
    # by sampling min(solarchips_number, emptychips_number) on larger datasets 
    # (either solar chips or emptychips depending on which set is larger)
    def balance_samples(self,suffix='balanced'):
        basename_solar = [os.path.basename(i) for i in glob.glob(os.path.join(self.out_folder_label_yes,'*.'+self.chip_format))]
        basename_empty = [os.path.basename(i) for i in glob.glob(os.path.join(self.out_folder_label_no,'*.'+self.chip_format))]
        k = min(len(basename_solar),len(basename_empty))
        print('solar chips: {}'.format(len(basename_solar)))
        print('empty chips: {}'.format(len(basename_empty)))
        print('random select {} chips from larger dataset'.format(k))
        
        random.seed(10)
        if len(basename_solar) <= len(basename_empty):
            sampled_basename_empty = random.sample(basename_empty,k)
            # make new folder for balanced label
            out_path_label = self.out_folder_label_no+'_'+suffix
            if not os.path.exists(out_path_label):               
                os.makedirs(out_path_label)
                print('Newly Created: Balance folder (label): {}'.format(out_path_label))
            else: 
                print('Use existing balance folder (label): {}'.format(out_path_label))
                
            for i in sampled_basename_empty:
                dst = os.path.join(out_path_label,i)
                src = os.path.join(self.out_folder_label_no,i)
                shutil.copyfile(src, dst)
                
            # make new folder for balanced bands
            out_path_solar = self.out_folder_bands_no+'_'+suffix
            if not os.path.exists(out_path_solar):               
                os.makedirs(out_path_solar)
                print('Newly Created: Balance folder (bands): {}'.format(out_path_solar))
            else: 
                print('Use existing balance folder (bands): {}'.format(out_path_solar))
                
            for i in sampled_basename_empty:
                dst = os.path.join(out_path_solar,i)
                src = os.path.join(self.out_folder_bands_no,i)
                shutil.copyfile(src, dst)
 
        # solar chips > empty chips        
        else:
            sampled_basename_solar = random.sample(basename_solar,k)
            # make new folder for balanced label
            out_path_label = self.out_folder_label_yes+'_'+suffix
            if not os.path.exists(out_path_label):               
                os.makedirs(out_path_label)
                print('Newly Created: Balance folder (label): {}'.format(out_path_label))
            else: 
                print('Use existing balance folder (label): {}'.format(out_path_label))
                
            for i in sampled_basename_solar:
                dst = os.path.join(out_path_label,i)
                src = os.path.join(self.out_folder_label_yes,i)
                shutil.copyfile(src, dst)
            # make new folder for balanced bands
            out_path_solar = self.out_folder_bands_yes+'_'+suffix
            if not os.path.exists(out_path_solar):               
                os.makedirs(out_path_solar)
                print('Newly Created: Balance folder (bands): {}'.format(out_path_solar))
            else: 
                print('Use existing balance folder (bands): {}'.format(out_path_solar))
                
            for i in sampled_basename_solar:
                dst = os.path.join(out_path_solar,i)
                src = os.path.join(self.out_folder_bands_yes,i)
                shutil.copyfile(src, dst)

    def print_settings(self):
        print('Current polygon label file: {}'.format(self.label_polygon_path))
        print('Current outfolder for bands: {}'.format(self.out_folder_bands))
        print('Current outfolder for bands yes: {}'.format(self.out_folder_bands_yes))
        print('Current outfolder for bands no: {}'.format(self.out_folder_bands_no))
        print('Current outfolder for label yes: {}'.format(self.out_folder_label_yes))
        print('Current outfolder for label no: {}'.format(self.out_folder_label_no))
        print('Current chip output format: {}'.format(self.chip_format))
        print('Current seeding strategy: {}'.format(self.seeds_flag))

    
    
        
if __name__ == '__main__':
    warnings.filterwarnings('ignore')

    # areas = glob.glob('C:\clark\GEOG387\project\s2\drive-download-20220426T212530Z-002/*.tif')
    # areas = [os.path.basename(i) for i in areas]
    # for i in areas:
    #     print('C:/clark/GEOG387/project/sentinel2_all/' + i)
    
    #     i = MakeChips('C:\clark\GEOG387\project\s2\drive-download-20220426T212530Z-002/' + i)
    #     i.read_polygons('C:/clark/GEOG387/project/solar_3states/solar_clip.shp')
    #     i.set_outfolder_bands('C:/clark/GEOG387/project/data/processed/all_org')
    #     i.set_outfolder_bands_yes('C:/clark/GEOG387/project/data/processed/solar/org')
    #     i.set_outfolder_bands_no('C:/clark/GEOG387/project/data/processed/empty/org')
    #     i.set_outfolder_label_yes('C:/clark/GEOG387/project/data/processed/solar/mask')
    #     i.set_outfolder_label_no('C:/clark/GEOG387/project/data/processed/empty/mask')
    #     i.chip_format='npy'
    #     # print('*'*50)
    #     i.print_settings()

    #     i.makechips(worker=8)
    #     i.makelabels(worker=8)
    #     i.populate_folder()
    
    # i = MakeChips('C:\clark\GEOG387\project\s2\drive-download-20220426T212530Z-002/' + i)
    # i.balance_samples()
    i = MakeChips('C:/clark/GEOG387/project/s2/s2_solarpane_12bands.tif')
    i.chip_format = 'tif'
    i.read_polygons('C:/clark/GEOG387/project/solar_3states/solar_clip_naip.shp')
    i.set_outfolder_bands('../data/processed/all_org')
    i.set_outfolder_bands_yes('../data/processed/solar/org')
    i.set_outfolder_bands_no('../data/processed/empty/org')
    i.set_outfolder_label_yes('../data/processed/solar/mask')
    i.set_outfolder_label_no('../data/processed/empty/mask')
    # i.chip_format='npy'
    # # print('*'*50)
    i.print_settings()
   
    i.makechips(worker=8)
    i.makelabels(worker=8)
    i.populate_folder()
    i.balance_samples()
    # i.populate_folder()