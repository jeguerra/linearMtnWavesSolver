#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 22 11:21:27 2019

SUPPORTS AN ANALYTICAL PROFILE FOR WIND ONLY...

@author: TempestGuerra
"""

import numpy as np

def computeShearProfileOnGrid(PHYS, JETOPS, P0, PZ, dlnPZdz):
       
       # Get jet profile options
       U0 = JETOPS[0]
       uj = JETOPS[1]
       b = JETOPS[2]
       
       # Compute the normalized pressure coordinate (Ullrich, 2015)
       pcoord = 1.0 / P0 * PZ;
       lpcoord = np.log(pcoord);
       lpcoord2 = np.power(lpcoord, 2.0)
       
       # Compute the decay portion of the jet profile
       jetDecay = np.exp(-(1.0 / b**2.0 * lpcoord2));
       UZ = -uj * np.multiply(lpcoord, jetDecay) + U0;
    
       # Compute the shear
       temp = np.multiply(jetDecay, (1.0 - 2.0 / b**2 * lpcoord2))
       dUdz = -uj * temp * np.reciprocal(pcoord);
       dUdz *= (1.0 / P0);
       dUdz *= P0 * (pcoord * dlnPZdz);
       
       return UZ, dUdz
       
       