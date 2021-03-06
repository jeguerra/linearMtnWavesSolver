#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  2 17:10:18 2019

@author: TempestGuerra
"""

import numpy as np
import scipy.sparse as sps

def computePartialDerivativesXZ(DIMS, REFS, DDX_1D, DDZ_1D):
       # Get the dimensions
       NX = DIMS[3] + 1
       NZ = DIMS[4]
       OPS = NX * NZ
       
       # Get REFS data
       sigma = REFS[7]
       
       # Unwrap the 1D derivative matrices into 2D operators
       
       #%% Vertical derivative and diffusion operators
       DDZ_OP = np.empty((OPS,OPS))
       for cc in range(NX):
              # Advanced slicing used to get submatrix
              ddex = np.array(range(NZ)) + cc * NZ
              # TF adjustment for vertical coordinate transformation
              SIGMA = sps.diags(sigma[:,cc])
              DDZ_OP[np.ix_(ddex,ddex)] = SIGMA.dot(DDZ_1D)
              
       # Make the operators sparse
       DDZM = sps.csr_matrix(DDZ_OP); del(DDZ_OP)
           
       #%% Horizontal Derivative
       DDX_OP = np.empty((OPS,OPS))
       for rr in range(NZ):
              ddex = np.array(range(0,OPS,NZ)) + rr
              # Advanced slicing used to get submatrix
              DDX_OP[np.ix_(ddex,ddex)] = DDX_1D
              
       # Make the operators sparse
       DDXM = sps.csr_matrix(DDX_OP); del(DDX_OP)

       return DDXM, DDZM

def computePartialDerivativesXZ_BC(DIMS, REFS, DDX_1D, DDZ_1D, DDX_BC, DDZ_BC):
       # Get the dimensions
       NX = DIMS[3] + 1
       NZ = DIMS[4]
       OPS = NX * NZ
       
       # Get REFS data
       sigma = REFS[7]
       
       # Unwrap the 1D derivative matrices into 2D operators
       
       #%% Vertical derivative and diffusion operators
       DDZ_OP = np.empty((OPS,OPS))
       for cc in range(NX):
              # Advanced slicing used to get submatrix
              ddex = np.array(range(NZ)) + cc * NZ
              # TF adjustment for vertical coordinate transformation
              SIGMA = sps.diags(sigma[:,cc])
              if cc == 0 or cc == NX-1:
                     DDZ_OP[np.ix_(ddex,ddex)] = SIGMA.dot(DDZ_BC)
              else:
                     DDZ_OP[np.ix_(ddex,ddex)] = SIGMA.dot(DDZ_1D)
              
       # Make the operators sparse
       DDZM = sps.csr_matrix(DDZ_OP); del(DDZ_OP)
           
       #%% Horizontal Derivative
       DDX_OP = np.empty((OPS,OPS))
       for rr in range(NZ):
              ddex = np.array(range(0,OPS,NZ)) + rr
              # Advanced slicing used to get submatrix
              if rr == 0 or cc == NZ-1:
                     DDX_OP[np.ix_(ddex,ddex)] = DDX_BC
              else:
                     DDX_OP[np.ix_(ddex,ddex)] = DDX_1D
              
       # Make the operators sparse
       DDXM = sps.csr_matrix(DDX_OP); del(DDX_OP)

       return DDXM, DDZM