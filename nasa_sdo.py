from PIL import Image
from utils import download

def getSDOImage(args):
    name = args.colorMode
    supportedArgs = ["0171", "0171pfss", "0304", "0304pfss", "HMIIC"]

    if name == None:
        name = "0304"       #default color mode

    if name not in supportedArgs:
        raise ValueError("Wrong parameter for colorMode: SDO only support '' as colorMode!")

    url = f"https://sdo.gsfc.nasa.gov/assets/img/latest/latest_2048_{name}.jpg"
 
    print(f"Downloading Image ({url})")
    img = download(url)
    img = img.resize((1080,1080))

    return img