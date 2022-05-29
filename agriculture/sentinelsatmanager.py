from geojson import Point, Feature, FeatureCollection, dump
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from agriculture import db
from agriculture.models import SatelliteImage, Field, MultiSpectraIndex
import shutil
import os

import json
import rasterio
from rasterio.mask import mask
from shapely.geometry import Polygon
import shapely.wkt
from pyproj import Transformer
from pyproj import CRS
import numpy as np

################################################################################
# Convert Field geometry string to GeoJSON
#

def convert_to_geojson(geometry_string):

    points = []
    geometry_string = geometry_string.split(',')

    for lat,lon in zip(geometry_string[::2], geometry_string[1::2]):
        lat = float(lat)
        lon = float(lon)

        points.append(Feature(geometry=Point((lon,lat))))

    feature_collection = FeatureCollection(points)

    return feature_collection


################################################################################
# Search Sentinel-2 scenes (S2MSI2A product) acquired in the last 5 days
# for a given list of fields

def search(fields):

    # This will be encrypted in some way

    # Define a SentinelSat API
    with open('agriculture/config.json', 'r') as f:
        configs = json.load(f)

    scihub_data = configs["scihub_data"]
    api = SentinelAPI(scihub_data["user"],scihub_data["password"])

    for field in fields:

        ########################################################################
        # Convert field geometry string to GeoJSON and GeoJSON to WKT
        # before using the footprint as query filter
        footprint = geojson_to_wkt(convert_to_geojson(field.geometry))

        ########################################################################
        # Retrieve all product with given specifications
        # As default value the maximum cloudcoverpercentage is set to 20%
        products = api.query(footprint,
                             date=('NOW-5DAYS', 'NOW'),
                             producttype='S2MSI2A',
                             platformname='Sentinel-2',
                             cloudcoverpercentage=(0,30))


        for product in products:

            ####################################################################
            # Retrieve product ODATA (metadata)
            product_odata = api.get_product_odata(product)

            ####################################################################
            # Retrieve the list of all the images linked to the current field

            img_linked_to_field = [img.date for img in field.satellite_images]

            ####################################################################
            #
            #
            # Problem : Why conversion to string??
            if( str(product_odata['date']) not in img_linked_to_field):

                if SatelliteImage.query.filter_by(product_name=product_odata['title']).first() == None:

                    new_sat_img = SatelliteImage(product_id=product_odata['id'],
                                                 product_name=product_odata['title'],
                                                 date=product_odata['date'])

                    field.satellite_images.append(new_sat_img)
                    db.session.commit()

                else:

                    img = SatelliteImage.query.filter_by(product_name=product_odata['title']).first()
                    img.fields.append(field)
                    db.session.commit()


################################################################################
# Compute NDVI given the product ID and a Field
#
def compute_ndvi(prod_id, field):

    print("Compute NDVI . . .")
    rasterPath = os.listdir()

    band_4 = rasterio.open([file for file in rasterPath if 'B04_clipped' in file][0])
    band_8 = rasterio.open([file for file in rasterPath if 'B08_clipped' in file][0])


    bandRed = band_4.read(1)
    bandNir = band_8.read(1)

    crop_indeces = np.argwhere(bandRed!=0)

    xl= []
    yl = []
    ndvil = []

    crs_4326 = CRS.from_epsg(4326)
    crs_32632 = CRS.from_epsg(32632)
    transformer = Transformer.from_crs(crs_32632, crs_4326)

    for x,y in crop_indeces:
        bRed = float(bandRed[x,y])
        bNir = float(bandNir[x,y])
        # Conversione pixel <---> coordinate via trasformazione affine
        xx,yy = band_4.xy(x,y)
        xl.append(transformer.transform(float(xx),float(yy))[0])
        yl.append(transformer.transform(float(xx),float(yy))[1])
        ndvi = ( bNir - bRed ) / ( bRed + bNir )
        ndvil.append(ndvi)


    xl = ','.join([str(xx) for xx in xl])
    yl = ','.join([str(yy) for yy in yl])
    ndvil = ','.join([str(zz) for zz in ndvil])

    return xl, yl, ndvil

################################################################################
# Clipping Sentinel-2 image over field footprint
#

def clipping_band(product_id, field, band_number):

    print("Clipping image . . .")
    ############################################################################
    # field geometry is saved as lat/lon pairs using EPSG:4326 as CRS
    # Sentinel-2 images use EPSG:xxxxx
    # For this reason before masking the raster image we must project the field
    # footprint onto the same CRS. The CRS can be dynamically changed from raster
    # image metadata.

    crs_4326 = CRS.from_epsg(4326)
    crs_32632 = CRS.from_epsg(32632)
    transformer = Transformer.from_crs(crs_4326, crs_32632)

    ############################################################################
    # The area of interest is created as a Shapely Polygon (Shapefile) starting
    # from the field geometry string

    area_of_interest = Polygon([(transformer.transform(float(lat),float(lon))) for lat,lon in zip(field.geometry.split(',')[::2],field.geometry.split(',')[1::2])])

    ############################################################################
    # Using RASTERIO for opening the MultiSpectraIndex image as float32

    band   = rasterio.open([file for file in os.listdir() if 'B0'+str(band_number) in file and 'clipped' not in file][0])

    print("[DEBUG] opening",[file for file in os.listdir() if 'B0'+str(band_number) in file and 'clipped' not in file][0],"...")

    kwargs = band.meta

    band_data, _ = mask(band, shapes=[area_of_interest], crop=False, nodata=0)
    band_data = band_data[0]

    kwargs.update(
            driver='GTiff',
            dtype=rasterio.uint16,
            count=1,
            compress='lzw')

    with rasterio.open(product_id+'_B0'+str(band_number)+'_clipped.tif', 'w', **kwargs) as dst:
        dst.write_band(1, band_data.astype(rasterio.uint16))


################################################################################
# Download images via SentinelSat API


def download(images):

    # Define a SentinelSat API
    with open('agriculture/config.json', 'r') as f:
        configs = json.load(f)

    scihub_data = configs["scihub_data"]
    api = SentinelAPI(scihub_data["user"],scihub_data["password"])

    for img in images:
        if img.downloaded == False :

            print("[DEBUG] Downloading", img.product_name)
            api.download(img.product_id)

            # Set image to downloaded
            img.downloaded = False
            db.session.commit()

            # Extracting image
            shutil.unpack_archive(img.product_name+'.zip')

            os.chdir(img.product_name+'.SAFE/GRANULE')
            os.chdir(os.listdir()[0]+'/IMG_DATA/R10m')

            for field in img.fields:

                print(field.name)
                clipping_band(img.product_name,field,2)
                clipping_band(img.product_name,field,3)
                clipping_band(img.product_name,field,4)
                clipping_band(img.product_name,field,8)

                lat, lon, ndvi = compute_ndvi(img.product_name,field)

                # Declaring a new MSI entry object
                msi_index_entry = MultiSpectraIndex(date=img.date,
                                             latitude=lat,
                                             longitude=lon,
                                             ndvi=ndvi)

                field.msi_index.append(msi_index_entry)

                db.session.commit()

            os.chdir("../../../../../")
            # os.system('rm -r '+img.product_name+'.SAFE')
            # os.system('rm '+img.product_name+'.zip')
