#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 22 13:11:11 2019

@author: -
"""

import numpy as np
import scipy.sparse as sps
#import matplotlib.pyplot as plt

#%% The linear equation operator
def computeEulerEquationsLogPLogT(DIMS, PHYS, REFS):
       # Get physical constants
       gc = PHYS[0]
       gam = PHYS[6]
       
       # Get the dimensions
       NX = DIMS[3] + 1
       NZ = DIMS[4]
       OPS = NX * NZ
       
       # Get REFS data
       UZ = REFS[8]
       PORZ = REFS[9]
       DUDZ = REFS[10]
       DLPDZ = REFS[11]
       DLPTDZ = REFS[12]
       DDXM = REFS[13]
       DDZM = REFS[14]
              
       #%% Compute the various blocks needed
       tempDiagonal = np.reshape(UZ, (OPS,), order='F')
       UM = sps.spdiags(tempDiagonal, 0, OPS, OPS)
       tempDiagonal = np.reshape(DUDZ, (OPS,), order='F')
       DUDZM = sps.spdiags(tempDiagonal, 0, OPS, OPS)
       tempDiagonal = np.reshape(DLPDZ, (OPS,), order='F')
       DLPDZM = sps.spdiags(tempDiagonal, 0, OPS, OPS)
       tempDiagonal = np.reshape(DLPTDZ, (OPS,), order='F')
       DLPTDZM = sps.spdiags(tempDiagonal, 0, OPS, OPS)
       U0DX = UM.dot(DDXM)
       tempDiagonal = np.reshape(PORZ, (OPS,), order='F')
       PORZM = sps.spdiags(tempDiagonal, 0, OPS, OPS)
       unit = sps.identity(OPS)
       
       #%% Compute the terms in the equations
       
       # Horizontal momentum
       LD11 = U0DX
       LD12 = DUDZM
       LD13 = PORZM.dot(DDXM)
       
       # Vertical momentum
       LD22 = U0DX
       LD23 = PORZM.dot(DDZM) + gc * (1.0 / gam - 1.0) * unit
       LD24 = -gc * unit
       
       # Log-P equation
       LD31 = gam * DDXM
       LD32 = gam * DDZM + DLPDZM
       LD33 = U0DX
       
       # Log-Theta equation
       LD42 = DLPTDZM
       LD44 = U0DX
       
       DOPS = [LD11, LD12, LD13, LD22, LD23, LD24, LD31, LD32, LD33, LD42, LD44]
       
       return DOPS

# Function evaluation of the non linear equations
def computeEulerEquationsLogPLogT_NL(PHYS, REFS, REFG, SOLT, INIT, sysDex, udex, wdex, pdex, tdex, bdex):
       # Get physical constants
       gc = PHYS[0]
       P0 = PHYS[1]
       Rd = PHYS[3]
       kap = PHYS[4]
       gam = PHYS[6]
       
       # Get the boundary terrain
       DZT = REFS[6]
       
       # Get the derivative operators
       DDXM = REFS[13]
       DDZM = REFS[14]
       
       # Get the static vertical gradients
       DUDZ = REFG[0]
       DLPDZ = REFG[1]
       DLPTDZ = REFG[2]
       ROPS = REFG[3]
       
       # Get the solution components
       uxz = SOLT[udex]
       wxz = SOLT[wdex]
       pxz = SOLT[pdex]
       txz = SOLT[tdex]
       
       # Make the total quatities
       U = np.add(uxz, INIT[udex])
       LP = np.add(pxz, INIT[pdex])
       LT = np.add(txz, INIT[tdex])
       
       # Apply boundary condition
       wxz[bdex] = DZT[0,:] * U[bdex]
        
       # Compute the sensible temperature scaling to PGF
       RdT = Rd * P0**(-kap) * np.exp(LT + kap * LP)
       
       DlpDx = DDXM.dot(pxz)
       DlpDz = DDZM.dot(pxz)
        
       # Horizontal Momentum
       LD11 = U * (DDXM.dot(uxz))
       LD12 = wxz * (DDZM.dot(uxz) + DUDZ)
       LD13 = RdT * DlpDx
       
       # Vertical Momentum
       LD21 = 0.5 * DDZM.dot(np.power(wxz, 2.0))
       LD22 = U * (DDXM.dot(wxz))
       LD23 = RdT * (DlpDz + DLPDZ) + gc
       
       # Pressure (mass) equation
       LD31 = U * DlpDx
       LD32 = wxz * (DlpDz + DLPDZ)
       LD33 = gam * DDXM.dot(uxz)
       LD34 = gam * DDZM.dot(wxz)
       
       # Potential Temperature equation
       LD41 = U * (DDXM.dot(txz))
       LD42 = wxz * (DDZM.dot(txz) + DLPTDZ)
       
       # Compute the combined terms
       DuDt = -(LD11 + LD12 + LD13) - ROPS[0].dot(uxz)
       DwDt = -(LD21 + LD22 + LD23) - ROPS[1].dot(wxz)
       DpDt = -(LD31 + LD32 + LD33 + LD34) - ROPS[2].dot(pxz)
       DtDt = -(LD41 + LD42) - ROPS[3].dot(txz)
       
       # Concatenate
       DqDt = np.concatenate((DuDt, DwDt, DpDt, DtDt))
       
       return DqDt[sysDex]
       