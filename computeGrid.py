#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 17 14:12:01 2019

@author: TempestGuerra
"""

import numpy as np
from HerfunChebNodesWeights import hefunclb
#from HerfunChebNodesWeights import hefuncm
from HerfunChebNodesWeights import cheblb
#from HerfunChebNodesWeights import chebpolym

def computeGrid(DIMS, HermCheb, FourCheb, ChebCol):
       # Get the domain dimensions
       L1 = DIMS[0]
       L2 = DIMS[1]
       ZH = DIMS[2]
       NX = DIMS[3]
       NZ = DIMS[4]
       
       if ChebCol:
              # Compute the Chebyshev native grids
              xi, wcp = cheblb(NZ) #[-1 +1]
              z = 0.5 * ZH * (1.0 + xi)
       else:
              z = np.linspace(0.0, ZH, num=NZ, endpoint=True)
       
       # Map reference 1D domains to physical 1D domains
       if HermCheb and not FourCheb:
              alpha, whf = hefunclb(NX) #(-inf inf)
              x = 0.5 * abs(L2 - L1) / np.amax(alpha) * alpha
       elif FourCheb and not HermCheb:
              x = np.linspace(L1, L2, num=NX+1, endpoint=True)
       else:
              alpha, whf = hefunclb(NX) #(-inf inf)
              x = 0.5 * abs(L2 - L1) / np.amax(alpha) * alpha
       
       # Return the REFS structure
       REFS = [x, z]
       
       return REFS