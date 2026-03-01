from PIL import Image
import os

def generate_icons(source_png, version="v1"):
    img = Image.open(source_png)
    
    # 1. Windows (.ico) - Contains multiple sizes in one file
    windows_sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
    img.save('..\installer\windows\orvion' + '.ico', format='ICO', sizes=windows_sizes)
    print("Generated orvion_" + version + ".ico")

    # 2. Linux (.png) - Just a high-res square PNG
    img_512 = img.resize((512, 512), Image.LANCZOS)
    img_512.save('..\installer\linux\orvion' + '.png')
    print("Generated orvion_" + version + ".png")

    # 3. macOS (.icns) 
    # Note: On Windows/Linux, it's hard to make a true .icns. 
    # For now, save a 1024x1024 PNG; your GitHub Action script 
    # already has the logic to convert this to .icns using 'iconutil'.
    img_1024 = img.resize((1024, 1024), Image.LANCZOS)
    img_1024.save('..\installer\macos\orvion' + '.png')
    print("Generated orvion_" + version + ".png")

generate_icons(r'.\version\orvion_v1.png')