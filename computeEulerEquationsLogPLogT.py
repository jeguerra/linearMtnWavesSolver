#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 22 13:11:11 2019

@author: -
"""
import numpy as np
import scipy.sparse as sps
from numba import jit

def computePrepareFields(PHYS, REFS, SOLT, INIT, udex, wdex, pdex, tdex, botdex, topdex):
       # Get some physical quantities
       P0 = PHYS[1]
       Rd = PHYS[3]
       kap = PHYS[4]
       
       TQ = SOLT + INIT
       # Make the total quatities
       U = TQ[udex]
       LP = TQ[pdex]
       LT = TQ[tdex]
       
       # Compute the sensible temperature scaling to PGF
       RdT = Rd * P0**(-kap) * np.exp(LT + kap * LP)
       
       fields = np.reshape(SOLT, (len(udex), 4), order='F')
       
       return fields, U, RdT

#%% The linear equation operator
def computeEulerEquationsLogPLogT(DIMS, PHYS, REFS, REFG):
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
       DUDZ = REFG[0]
       DLPDZ = REFG[1]
       DLPTDZ = REFG[2]
       DDXM = REFS[10]
       DDZM = REFS[11]
              
       #%% Compute the various blocks needed
       tempDiagonal = np.reshape(UZ, (OPS,), order='F')
       UM = sps.spdiags(tempDiagonal, 0, OPS, OPS)
       tempDiagonal = np.reshape(DUDZ, (OPS,), order='F')
       DUDZM = sps.spdiags(tempDiagonal, 0, OPS, OPS)
       tempDiagonal = np.reshape(DLPDZ, (OPS,), order='F')
       DLPDZM = sps.spdiags(tempDiagonal, 0, OPS, OPS)
       tempDiagonal = np.reshape(DLPTDZ, (OPS,), order='F')
       DLPTDZM = sps.spdiags(tempDiagonal, 0, OPS, OPS)
       tempDiagonal = np.reshape(PORZ, (OPS,), order='F')
       PORZM = sps.spdiags(tempDiagonal, 0, OPS, OPS)
       unit = sps.identity(OPS)
       
       #%% Compute the terms in the equations
       U0DDX = UM.dot(DDXM)
       
       # Horizontal momentum
       LD11 = U0DDX
       LD12 = DUDZM
       LD13 = PORZM.dot(DDXM)
       
       # Vertical momentum
       LD22 = U0DDX
       LD23 = PORZM.dot(DDZM) + gc * (1.0 / gam - 1.0) * unit
       LD24 = -gc * unit
       
       # Log-P equation
       LD31 = gam * DDXM
       LD32 = gam * DDZM + DLPDZM
       LD33 = U0DDX
       
       # Log-Theta equation
       LD42 = DLPTDZM
       LD44 = U0DDX
       
       DOPS = [LD11, LD12, LD13, LD22, LD23, LD24, LD31, LD32, LD33, LD42, LD44]
       
       return DOPS

# Function evaluation of the non linear equations (dynamic components)
@jit(nopython=True)
def computeEulerEquationsLogPLogT_NL(PHYS, REFS, REFG, fields, U, RdT, botdex, topdex):
       # Get physical constants
       gc = PHYS[0]
       gam = PHYS[6]
       
       # Get the derivative operators
       dHdX = REFS[6]
       DDXM = REFS[10]
       DDZM = REFS[11]
       DZDX = REFS[15]
       
       # Compute terrain following terms
       wxz = fields[:,1]
       WXZ = wxz - U * DZDX
              
       # Apply boundary condition exactly
       fields[botdex,1] = U[botdex] * dHdX
       fields[topdex,1] *= 0.0
       fields[topdex,3] *= 0.0
       WXZ[botdex] *= 0.0
       
       # Compute advective (multiplicative) operators
       U = sps.diags(U, offsets=0, format='csr')
       wxz = sps.diags(wxz, offsets=0, format='csr')
       WXZ = sps.diags(WXZ, offsets=0, format='csr')
       
       # Get the static horizontal and vertical derivatives
       DQDZ = REFG[3]
       wDQDZ = wxz.dot(DQDZ)
       
       # Compute derivative of perturbations
       DqDx = DDXM.dot(fields)
       DqDz = DDZM.dot(fields)
       # Compute advection
       UDqDx = U.dot(DqDx)
       WDqDz = WXZ.dot(DqDz)
       
       # Compute pressure gradient forces
       PGFX = RdT * (DqDx[:,2] - DZDX * DqDz[:,2])
       PGFZ = RdT * (DqDz[:,2] + DQDZ[:,1]) + gc
       
       def DqDt():
              # Horizontal momentum equation
              DuDt = -(UDqDx[:,0] + WDqDz[:,0] + wDQDZ[:,0] + PGFX)
              # Vertical momentum equation
              DwDt = -(UDqDx[:,1] + WDqDz[:,1] + PGFZ)
              # Pressure (mass) equation
              LD33 = gam * (DqDx[:,0] - DZDX * DqDz[:,0] + DqDz[:,1])
              DpDt = -(UDqDx[:,2] + WDqDz[:,2] + wDQDZ[:,1] + LD33)
              # Potential Temperature equation
              DtDt = -(UDqDx[:,3] + WDqDz[:,3] + wDQDZ[:,2])
              
              DwDt[topdex] *= 0.0
              DwDt[botdex] *= 0.0
              DtDt[topdex] *= 0.0
       
              return (DuDt, DwDt, DpDt, DtDt)
                     
       return np.concatenate(DqDt())

def computeRayleighTendency(REFG, fields, udex, wdex, pdex, tdex, botdex, topdex):
       
       # Get the static vertical gradients
       ROPS = REFG[4]
       
       # Compute the tendencies
       DuDt = - ROPS[0].dot(fields[:,0])
       DwDt = - ROPS[1].dot(fields[:,1])
       DpDt = - ROPS[2].dot(fields[:,2])
       DtDt = - ROPS[3].dot(fields[:,3])
       
       # Null tendencies at essential vertical boundaries
       DuDt[topdex] *= 0.0
       DuDt[botdex] *= 0.0
       DwDt[topdex] *= 0.0
       DwDt[botdex] *= 0.0
       DpDt[topdex] *= 0.0
       DpDt[botdex] *= 0.0
       DtDt[topdex] *= 0.0
       DtDt[botdex] *= 0.0
       
       # Concatenate
       DqDt = np.concatenate((DuDt, DwDt, DpDt, DtDt))
       
       return DqDt

def computeDynSGSTendency(RESCF, REFS, fields, udex, wdex, pdex, tdex, botdex, topdex):
       
       # Get the derivative operators
       #DDXM = REFS[10]
       #DDZM = REFS[11]
       DDXM2 = REFS[12]
       DDZM2 = REFS[13]
       
       # Get the anisotropic coefficients
       RESCFX = RESCF[0]
       RESCFZ = RESCF[1]
       
       # Compute derivative of perturbations
       DDx = DDXM2.dot(fields)
       DDz = DDZM2.dot(fields)
       '''
       DuDx = DDx[:,0]
       DwDx = DDx[:,1]
       DlpDx = DDx[:,2]
       DltDx = DDx[:,3]
       DuDz = DDz[:,0]
       DwDz = DDz[:,1]
       DlpDz = DDz[:,2]
       DltDz = DDz[:,3]
       '''
       # Compute the tendencies (divergence of diffusive flux... discontinuous)
       '''
       DuDt = DDXM.dot(RESCFX[udex] * DuDx) + DDZM.dot(RESCFZ[udex] * DuDz)
       DwDt = DDXM.dot(RESCFX[wdex] * DwDx) + DDZM.dot(RESCFZ[wdex] * DwDz)
       DpDt = DDXM.dot(RESCFX[pdex] * DlpDx) + DDZM.dot(RESCFZ[pdex] * DlpDz)
       DtDt = DDXM.dot(RESCFX[tdex] * DltDx) + DDZM.dot(RESCFZ[tdex] * DltDz)
       '''
       # Compute tendencies (2nd derivative term only)
       #'''
       #DuDt = RESCFX[udex] * DDx[:,0] + RESCFZ[udex] * DDz[:,0]
       DuDt = 0.0 * RESCFX[udex]
       DwDt = RESCFX[wdex] * DDx[:,1] + RESCFZ[wdex] * DDz[:,1]
       DpDt = RESCFX[pdex] * DDx[:,2] + RESCFZ[pdex] * DDz[:,2]
       DpDt = 0.0 * RESCFX[pdex]
       DtDt = RESCFX[tdex] * DDx[:,3] + RESCFZ[tdex] * DDz[:,3]
       #'''
       # Null tendencies along vertical boundaries
       DuDt[topdex] *= 0.0
       #DwDt[topdex] *= 0.0
       DpDt[topdex] *= 0.0
       #DtDt[topdex] *= 0.0

       DuDt[botdex] *= 0.0
       #DwDt[botdex] *= 0.0
       DpDt[botdex] *= 0.0
       #DtDt[botdex] *= 0.0

       # Concatenate
       DqDt = np.concatenate((DuDt, DwDt, DpDt, DtDt))
       
       return DqDt
       