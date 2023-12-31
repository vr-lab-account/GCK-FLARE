# -*- coding: utf-8 -*-
"""
Created on Wed Oct 31 10:24:25 2018

@author: firstname.lastname
"""

import os
import numpy as np
from skimage import io
from skimage.filters import threshold_otsu
import pandas as pd
import imreg_dft as ird
import matplotlib.pyplot as plt


# Creates image split function, which splits images either horizontally or vertically at whatever position you specify
def image_split(im, pos, stack = 'stack', dimen = 'w'):
    if stack == 'stack':
        d,h,w = im.shape
    else:
        h,w = im.shape
        d = 1
    
    if dimen == 'h':
        im_split1 = np.zeros(shape=(d,pos,w), dtype=np.uint16)
        im_split2 = np.zeros(shape=(d,h-pos,w), dtype=np.uint16)
    else:
        im_split1 = np.zeros(shape=(d,h,pos), dtype=np.uint16)
        im_split2 = np.zeros(shape=(d,h,w-pos), dtype=np.uint16)
        
    if dimen == 'h':    
        for count in range (0, d):
            if stack == 'stack':
                im_split1[count] = im[count][:pos, :]
                im_split2[count] = im[count][pos:, :]
            else:
                im_split1 = im[:pos, :]
                im_split2 = im[pos:, :]
    else:
        for count in range (0, d):
            if stack == 'stack':
                im_split1[count] = im[count][:, :pos]
                im_split2[count] = im[count][:, pos:]
            else:
                im_split1 = im[:, :pos]
                im_split2 = im[:, pos:]
    
    return im_split1, im_split2


def PS_align (imP, imS):
    d,h,w = imS.shape
    result = ird.translation(imP[1], imS[1])
    tvec = result["tvec"].round(4)

    imS_regmat = np.zeros(shape=(d,h,w), dtype=np.uint16)
    for count in range(0,d):
        if d>1:
            timg = ird.transform_img(imS[count], tvec=tvec)
        else:
            timg = ird.transform_img(imS, tvec=tvec)
        imS_regmat[count] = timg
    
    return imS_regmat


def isletregion_backsub (im, back_inten=1000, upper_limit = 16383):
    #This function subtracts the background intensity from images and determines the islet region using otsu thresholding
    
    #Gets dimensions of timecourse image
    d1,h1,w1 = im.shape
    
    #Initializes background array
    background = np.zeros((d1,h1,w1))
    #islet_region = np.zeros ((d1,h1,w1))
        
    #Calculates and subtracts out background based on a set intensity threshold provided by the user
    for a in range (0,d1):
        background[a,:,:] = np.mean(im[a][im[a]<back_inten])
    im_minus_back = im - background

    #Defines region of the image corresponding to the islet based on otsu thresholding. The frame before stimulation is used for thresholding.
    # for b in range (0,d1):
    #     im_temp = im_minus_back[b]
    #     im_temp[im_temp > upper_limit] = 0
    #     thresh = threshold_otsu(im_temp)
    #     islet_region[b,:,:] = (im_minus_back[b]>thresh).astype(int)

    im_temp = im_minus_back[2]
    im_temp[im_temp > upper_limit] = 0
    thresh = threshold_otsu(im_temp)
    islet_region_1 = (im_minus_back[2]>thresh).astype(int)
    
    im_temp = im_minus_back[12]
    im_temp[im_temp > upper_limit] = 0
    thresh = threshold_otsu(im_temp)
    islet_region_2 = (im_minus_back[12]>thresh).astype(int)
    
    islet_region = np.multiply(islet_region_1, islet_region_2)
    
    #Returns background subtracted image and binary (0s and 1s) array of islet region
    return im_minus_back, islet_region;


def im_mask_mult (im, islet_region):
    d1,h1,w1 = im.shape
    im_final = np.zeros ((d1,h1,w1))
    #for a in range (0,d1):
    im_final = im * islet_region
    
    return im_final


def anisotropy (P_img, S_img):
    
    d1,h1,w1 = P_img.shape
    
    # Sets g factor
    g = 1.35

    # Checks if all images match each other, if they do not nothing will be calculated
    if len(P_img) == len(S_img):
        numerator = P_img - g*S_img
        denominator = P_img + 2*g*S_img
        R_img = np.divide(numerator, denominator, out=np.zeros_like(numerator).astype(float), where=denominator!=0)
    else:
        R_img = np.zeros((d1,h1,w1))
    
    R_img[R_img > 0.4] = 0
    R_img[R_img < 0.05] = 0
    
    return R_img;


def average_response (im_norm, path = 'C:/Users/fishn/OneDrive/Desktop/', isletid = '1'):
    #This function determines the average response in stimulated and unstimulated regions of the islet.
    
    #Gets dimensions of timecourse image
    d1,h1,w1 = im_norm.shape
    
    #Average responses in stimulated and unstimulated region are calculated excluding zeros
    im_norm[im_norm == 0] = np.nan  
    im_norm_reshape = np.reshape(im_norm, (d1, (h1*w1)))

    
    #Average responses over time are exported to a .csv file
    averageresponse_df = pd.DataFrame({"R": np.nanmean(im_norm_reshape, axis = 1)})
    averageresponse_df.to_csv(path+isletid+'_'+'norm_R.csv')
    
    return
    