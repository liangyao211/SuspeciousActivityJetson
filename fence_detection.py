from config_site import *
import requests
import numpy as np

def mask2rle(img):
    '''
    img: numpy array, 1 - mask, 0 - background
    Returns run length as string formated
    '''
    pixels= img.T.flatten()
    pixels = np.concatenate([[0], pixels, [0]])
    runs = np.where(pixels[1:] != pixels[:-1])[0] + 1
    runs[1::2] -= runs[::2]
    return ' '.join(str(x) for x in runs)
 
def rle2mask(mask_rle, shape=(1600,256)):
    '''
    mask_rle: run-length as string formated (start length)
    shape: (width,height) of array to return 
    Returns numpy array, 1 - mask, 0 - background

    '''
    s = mask_rle.split()
    starts, lengths = [np.asarray(x, dtype=int) for x in (s[0:][::2], s[1:][::2])]
    starts -= 1
    ends = starts + lengths
    img = np.zeros(shape[0]*shape[1], dtype=np.uint8)
    for lo, hi in zip(starts, ends):
        img[lo:hi] = 1
    return img.reshape(shape).T


class aws_segmentor:
    def __init__(self) -> None:
        pass
    
    def predict(self,file_in):
        if isinstance(file_in,str):
            img = {'file': open(file_in, 'rb')}   
        else:
            img=file_in
        resp=requests.post(aws_get_fence, files=img)
        data = resp.json()
        rle=data['message']['rle']
        w,h=data['message']['size']
        mask_fence=rle2mask(rle,(w,h))
        final_out={'name':file_in,'rle':{'counts': rle, 'size':[h,w]}}
        return final_out, mask_fence
    