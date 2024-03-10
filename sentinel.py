import math
import datetime
from utils import download

from PIL import Image
import cv2
import numpy as np

def boundingBox(latitudeInDegrees, longitudeInDegrees, widthInKm, heightInKm):
    widthInM = widthInKm*1000
    heightInM = heightInKm*1000
    southLat = PointLatLng(latitudeInDegrees,longitudeInDegrees,heightInM,180)[0]
    northLat = PointLatLng(latitudeInDegrees,longitudeInDegrees,heightInM,0)[0]
    westLon = PointLatLng(latitudeInDegrees,longitudeInDegrees,widthInM,270)[1]
    eastLon = PointLatLng(latitudeInDegrees,longitudeInDegrees,widthInM,90)[1]
    return f"{southLat},{westLon},{northLat},{eastLon}" 

def PointLatLng(Lat,Lng, distance, bearing):
    rad = bearing * math.pi / 180
    lat1 = Lat * math.pi / 180
    lng1 = Lng * math.pi / 180
    lat = math.asin(math.sin(lat1) * math.cos(distance / 6378137) + math.cos(lat1) * math.sin(distance / 6378137) * math.cos(rad))
    lng = lng1 + math.atan2(math.sin(rad) * math.sin(distance / 6378137) * math.cos(lat1), math.cos(distance / 6378137) - math.sin(lat1) * math.sin(lat))
    return  round(lat * 180 / math.pi,4), round(lng * 180 / math.pi,4)

def calcCoordinateDimensions(args):
    zoomLevel = args.zoomLevel
    maxZoom = 1000        #km for the width
    variableZoom = 850    #the maximum kilometeres we can zoom in from the "maxZoom" 
    #maxZoom - variableZoom determines the min zoom level

    widthInKm = maxZoom-(((zoomLevel/4))*variableZoom)
    if args.width is not None and args.height is not None:
        heightInKm = int(widthInKm/(args.width/args.height))
    else:       #default for args.width and args.heigth is 1920 and 1080
        heightInKm = int(widthInKm/(16/9))

    return widthInKm,heightInKm

def calcImageDimensions(args):
    pixelWidth = 1920
    if args.width is not None and args.height is not None:
        pixelHeight = pixelWidth / (args.width/args.height)
    else:
        pixelHeight = pixelWidth / (16/9)

    return int(3840), int(2160)

def combineURL(args,satellite,time):
    widthInKm,heightInKm = calcCoordinateDimensions(args)
    widthInPx,heightInPx = calcImageDimensions(args)
    if args.latitude == None or args.longitude == None:
        raise ValueError("No coordinates specified! You need to specifiy coordinates by passing the parametera -a and -b.")
    bbox = boundingBox(args.latitude, args.longitude, widthInKm, heightInKm)
    url = f"https://view.eumetsat.int/geoserver/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&FORMAT=image/png&TRANSPARENT=true&LAYERS={satellite}&STYLES=&tiled=true&TIME={time}&WIDTH={args.width}&HEIGHT={args.height}&CRS=EPSG:4326&BBOX={bbox}"
    return url

def white_balance(pilImg):
    img = np.asarray(pilImg)
    result = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    avg_a = np.average(result[:, :, 1])
    avg_b = np.average(result[:, :, 2])
    result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)
    result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)
    result = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)
    return Image.fromarray(result)


def auto_white_balance(pilImg, p=.6):
    im = np.asarray(pilImg)
    # get mean values
    p0, p1 = np.percentile(im, p), np.percentile(im, 100-p)

    for i in range(3):
        ch = im[:,:,i]
        # get channel values
        pc0, pc1 = np.percentile(ch, p), np.percentile(ch, 100-p)
        # stretch channel to same range as mean
        ch = (p1 - p0) * (ch - pc0) / (pc1 - pc0) + p0
        im[:,:,i] = ch
        
    return Image.fromarray(im)

def fetchImage(args):
    dateWithDelay = datetime.datetime.now(datetime.timezone.utc)
    dateWithDelay = dateWithDelay-datetime.timedelta(hours=3)

    from multiprocessing.pool import ThreadPool as Pool

    def download_func(day):
        time = dateWithDelay.strftime("%Y-%m-")+str(dateWithDelay.day-day).zfill(2)+"T00:00:00Z"
        url = combineURL(args,"copernicus:daily_sentinel3ab_olci_l1_rgb_fulres",time)
        print(f"Downloading Image from {time}...\nwith URl:   {url}\n")
        img =  download(url)
        return img

    num_days = 7
    with Pool(num_days) as pool:
        imgs = pool.map(download_func, [i for i in range(1,num_days + 1)])

    bg = Image.new('RGB', (args.width, args.height))

    real_images = list(filter(lambda x : x != None, imgs))
    print("real: ", len(real_images))

    cloud_remove = False
    if cloud_remove:
        def dev(pixel):
            cols = pixel[:4]
            dev = max(cols) - min(cols)
            return dev

        def sm(pixel):
            cols = pixel[:3]
            #dev = max(cols) - min(cols)
            sm = sum(cols)
            if sm == 0:
                return 255*3
            return sm

        for x in range(args.width):
            for y in range(args.height):
                pixels = [img.getpixel((x,y)) for img in real_images]

                pixels.sort(key=sm)
                sum_pixel = pixels[0] # get the lowest sum (least bright)

                pixels.sort(key=dev)
                dev_pixel = pixels[-1] # get the largest dev (darkest single chanel)

                avg_pixel = (
                    int((sum_pixel[0] + dev_pixel[0])/2),
                    int((sum_pixel[1] + dev_pixel[1])/2),
                    int((sum_pixel[2] + dev_pixel[2])/2),
                    255
                )

                bg.putpixel((x,y), avg_pixel)
    else:
        for img in real_images:
            if img.mode == "RGB":
                a_channel = Image.new('L', img.size, 255)   # 'L' 8-bit pixels, black and white
                img.putalpha(a_channel)

            bg.paste(img, (0, 0),img)

    colorGraded = white_balance(bg)
    return colorGraded
    