#!/usr/bin/python

from PIL import Image
from PIL.ImageOps import invert
from PIL.ImageFilter import FIND_EDGES

import numpy as np
import math, sys, random, time
from io import BytesIO

def rgbToAnsi256(r, g, b):
    if (r == g == b):
        if (r < 8):
            return 16
        if (r > 248):
            return 231
        return int(round((((r - 8) / 247) * 24))) + 232
    ansi = 16 + (36 * int(round(r / 255 * 5))) + (6 * int(round(g / 255 * 5))) + int(round(b / 255 * 5))
    return ansi

def get_average_color(x, y, x_len, y_len, image, skip=1):
    """ Returns a 3-tuple containing the RGB value of the average color of the
    given square bounded area of length = n whose origin (top left corner)
    is (x, y) in the given image"""
    i = image.load()
    r, g, b = 0, 0, 0
    count = 0
    for s in range(x, x+x_len, skip):
        for t in range(y, y+y_len, skip):
            if s<image.size[0] and t< image.size[1]:
                pixlr, pixlg, pixlb = i[s,t]
                r += pixlr ** 2
                g += pixlg ** 2
                b += pixlb ** 2
                count += 1
            else:
                #print("Pos %s, %s out of bounds" % (s, t))
                break
    return (int(math.sqrt(r/count)), int(math.sqrt(g/count)), int(math.sqrt(b/count)))

def partition(compress, sqCount, image, rotate=None):
    """ sqCount is the amount of squares in the x-axis (must be at least 2). 
    Compress is the percentage of the image that stays (0<c<1)
    Rotate is the chance (0<r<1) that a square is rotated"""
    empty = []
    sqSize = image.size[0] // sqCount
    i = image.resize((sqSize * sqCount, image.size[1] // sqSize * sqSize))
    a = np.array(i)
    slice_val = 0
    if compress < 1:
        slice_val = sqSize - int(math.sqrt(compress * sqSize **2))
        if slice_val * 2 > sqSize - 1:
            slice_val = sqSize // 2 -1
            #print("Maximum compression met")

    #cut the image up into blocks, then compress the blocks. Add these blocks to empty array
    for y in range(0, i.size[1], sqSize):
        row = []
        for x in range(0, i.size[0], sqSize):
            block = a[y:y+sqSize, x:x+sqSize]
            if len(block) == len(block[0]) == sqSize:
                if compress < 1:
                    block = block[slice_val:-slice_val, slice_val:-slice_val]
                #Image.fromarray(block).show()
                if rotate:
                    random.seed(int(time.time() // 7) + x + y) #7 for 7 second refresh rate
                    if rotate * 100 >= random.randint(1, 100):
                        block = np.rot90(block, random.randint(1, 3))
                row.append(block)
            else:
                print("missing block at (%s, %s)!" % (x, y))
                return a
        empty.append(row)
    
    image_array = []
    for row in empty:
        image_array.append(np.hstack(row))
    image_array = np.vstack(image_array)
    x = Image.fromarray(image_array)
    return x

def removeCols(nCols, image, resize=False):
    '''nCols is how many columns you want to remain in your final image.
    If you specify resize True, it keeps the same size so it stretches the image
    If you keep it default False, your image's width is cut in half'''
    a = np.array(image)
    sqSize = image.size[0] // (nCols * 2 -1)
    empty = []
    for x in range(0, image.size[0], sqSize):
        empty.append(a[0:image.size[1], x:x+sqSize])
    img = Image.fromarray(np.hstack([empty[i] for i in range(len(empty)) if i % 2 == 0]))
    if resize:
        return img.resize(image.size)
    return img

def joinCols(nCols, nTimes, image):
    if nTimes <= 1:
        a = np.array(image)
        sqSize = image.size[0] // (nCols)
        empty = []
        for x in range(0, image.size[0], sqSize):
            empty.append(a[0:image.size[1], x:x+sqSize])
        odds = np.hstack([empty[i] for i in range(1, len(empty), 2)]) #do odds with the full length since a leftover is only even (doesn't matter tho)
        evens = np.hstack([empty[i] for i in range(0, nCols, 2)])#do evens with length of cols since a leftover could occur
        return Image.fromarray(np.hstack([evens, odds]))
    else:
        #image = joinCols(nCols, nTimes - 1, image).rotate(3 * 90, expand=True)
        #image = joinCols(nCols, 1, joinCols(nCols, nTimes-1, image).rotate(3 * 90, expand=True))
        image = joinCols(nCols, nTimes - 1, image)
        if nTimes % 2 == 0:
            image = image.rotate(3 * 90, expand=True)
        image = joinCols(nCols, 1, image)
        return image.rotate(90, expand=True)

def mosaic(sqCount, image, skip=1):
    """ sqCount is the amount of squares in the x-axis (must be at least 2)."""
    sqSize = image.size[0] // sqCount
    pixels = []
    for y in range(0, image.size[1], sqSize):
        row = []
        for x in range(0, image.size[0], sqSize):
            row.append(get_average_color(x, y, sqSize, sqSize, image, skip))
        pixels.append(row)
    x=Image.fromarray(np.array(pixels, dtype=np.uint8))
    return x

def ansi(sqCount, image, text="😎"):
    '''prints out to your console in colored text. sqCount is the amount of squares in the x-axis
    The default text for me is a unicode character that doesn't load, haha, so it just makes the output wide enought
    Change text to anything you'd like, and it'll repeatedly print that in the background'''
    bg = lambda text, color: "\33[48;5;" + str(color) + "m" + text + "\33[0m"
    fg = lambda text, color: "\33[38;5;" + str(color) + "m" + text + "\33[0m"
    if text != "😎":
        text += " "

    a = np.array(mosaic(sqCount, image))
    count = 0
    for row in a:
        for r, g, b in row:
            ansi = rgbToAnsi256(r, g, b)
            iansi = rgbToAnsi256(255-r,255-g,255-b) 
            c = text[count % len(text): count % len(text) + 2]
            for char in c:
                if text == "😎": print(fg(bg("😎", ansi), ansi), end="")
                else: print('\033[1m' + fg(bg(char, ansi), 231), end="")#iansi), end="")
            count += 2
        print("\n", end="")

def rowCol(compress, image):
    '''randomly removes rows and columns of pixels in the image, causes a cool effect
    compress is between 0 and 1, how much of the image should remain'''
    a = np.array(image)
    size = a.size
    aspect = a.shape[1] / a.shape[0]
    if a.shape[1] > a.shape[0]:
        aspect = 1/aspect
    if compress < 1:
        while a.size/size > compress:
            height, width = (a.shape[0], a.shape[1])
            delete_range, row_col = ([height-1, width-1], [0, 1])
            if width > height:
                delete_range, row_col = ([width-1, height-1], [1, 0])
           
            a = np.delete(a, random.randint(0, delete_range[0]), row_col[0]) #delete a row
            for i in range(int(aspect)):
                height, width = (a.shape[0], a.shape[1])
                a = np.delete(a, random.randint(0, delete_range[1]), row_col[1]) #delete a col
            if random.random() < aspect % 1:
                a = np.delete(a, random.randint(0, delete_range[1]), row_col[1]) #delete a col
    return Image.fromarray(a)

def dither(image, threshhold=False):
    '''o4 image dithering or threshold dithering'''
    image = image.convert('L')
    a = np.full((image.size[1], image.size[0]), False, dtype=bool)
    dots = [[64, 128],[192, 0]]

    if threshhold:
        px_list = list(image.getdata())
        sum = 0
        for i in px_list:
            sum += i ** 2
        threshhold = math.sqrt(sum // len(px_list)) #get the average color


    for row in range(a.shape[1]):
        for col in range(a.shape[0]):
            dotrow = 1 if row % 2 else 0
            dotcol = 1 if col % 2 else 0
            px = image.getpixel((row, col))
            a[col, row] = int(px > dots[dotrow][dotcol]) if not threshhold else int(px > threshhold)

    return Image.fromarray(a)

def jpeg(image, r=5, min_compression=10):
    '''Repeated jpeg compression. min_compression is between 0 and 100'''
    r = 100-min_compression if r > 100-min_compression else r
    for i in range(r):
        buffer = BytesIO()
        image.save(buffer, "JPEG", quality=r-i+min_compression-1)
        buffer.seek(0)
        image = Image.open(buffer)
        image.load()
        print("%s compressed at quality %s" % (i, r-i+min_compression-1))
        #print("%s compressed at quality %s" % (i, r-i+int(0.5*r)))
    return image

def meta_jpeg(image, r=5, r_2=5, min_compression=10):
    '''Repeated repeated jpeg compression.'''
    i = image
    for j in range(r):
        i = jpeg(i, r_2, min_compression)
    return i

def edge(image, th=220):
    '''Find edges then makes the edges only black, so a 1 bit image.
    th, or threshold, is between 0 and 255 and is the maximum value of lightness
    in the image before it makes a pixel black.'''
    a = np.full((image.size[1], image.size[0]), False, dtype=bool)
    i = invert(image.filter(FIND_EDGES)).convert('L')
    for row in range(a.shape[1]):
        for col in range(a.shape[0]):
            a[col, row] = 0 if i.getpixel((row, col)) < th else 1
    return Image.fromarray(a)

def main():
    args = sys.argv
    img = Image.open('media/input/%s' % args[1])
    '''images=[rowCol(0.01, img), rowCol(0.05, img),rowCol(0.25, img), partition(0.75, 6, img), partition(0.5, 6, img), mosaic(15, img, 50),
            dither(img), jpeg(img), meta_jpeg(img), mosaic(40, img, 50), removeCols(5, img, True), edge(img)] #specify your filters and settings here'''
    images = [ansi(80, img, "Deep Space Network"), ansi(80, img), ansi(40, img)]
    for count, x in enumerate(images):
        isImage = True
        try:
            q = x.size
        except:
            isImage = False
        
        if '-save' in args and isImage:
            #x.save('media/output/output-%s.png' % count) #save with an output count
            x.save('media/output/output-%s.png' % int(time.time() * 10000)) #save with a timestamp
        if '-show' in args and isImage:
            x.show()
        if isImage:
            print("%.3f%% compression" % ((x.size[0] * x.size[1])/(img.size[0] * img.size[1]) * 100))
        else:
            try:
                print(x)
            except:
                pass


if __name__ == "__main__":
    main()
