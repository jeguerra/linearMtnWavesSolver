#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 22 13:11:11 2019

@author: -
"""
import numpy as np
import scipy.sparse as sps

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

# Function evaluation of the non linear equations
def computeEulerEquationsLogPLogT_NL(PHYS, REFS, REFG, uxz, wxz, pxz, txz, U, RdT, botdex, topdex):
       # Get physical constants
       gc = PHYS[0]
       gam = PHYS[6]
       
       # Get the derivative operators
       DDXM = REFS[13]
       DDZM = REFS[14]
       
       # Get the static vertical gradients
       DUDZ = REFG[0]
       DLPDZ = REFG[1]
       DLPTDZ = REFG[2]
       
       # Compute derivative of perturbations
       DuDx = DDXM.dot(uxz)
       DuDz = DDZM.dot(uxz)
       DwDx = DDXM.dot(wxz)
       DwDz = DDZM.dot(wxz)
       DlpDx = DDXM.dot(pxz)
       DlpDz = DDZM.dot(pxz)
       DltDx = DDXM.dot(txz)
       DltDz = DDZM.dot(txz)
       # Horizontal momentum equation
       LD11 = U * DuDx
       LD12 = wxz * (DuDz + DUDZ)
       LD13 = RdT * DlpDx
       DuDt = -(LD11 + LD12 + LD13)
       # Vertical momentum equation
       LD21 = U * DwDx
       LD22 = wxz * DwDz
       LD23 = RdT * (DlpDz + DLPDZ) + gc
       DwDt = -(LD21 + LD22 + LD23)
       DwDt[topdex] = np.zeros(len(topdex))
       DwDt[botdex] = np.zeros(len(botdex))             
       # Pressure (mass) equation
       LD31 = U * DlpDx
       LD32 = wxz * (DlpDz + DLPDZ)
       LD33 = gam * (DuDx + DwDz)
       DpDt = -(LD31 + LD32 + LD33)     
       # Potential Temperature equation
       LD41 = U * DltDx
       LD42 = wxz * (DltDz + DLPTDZ)
       DtDt = -(LD41 + LD42)
       DtDt[topdex] = np.zeros(len(topdex))
       
       DqDt = np.concatenate((DuDt, DwDt, DpDt, DtDt))
       
       return DqDt

def computeRayleighTendency(REFG, uxz, wxz, pxz, txz, udex, wdex, pdex, tdex, botdex, topdex):
       
       # Get the static vertical gradients
       ROPS = REFG[3]
       
       # Compute the tendencies
       DuDt = - ROPS[0].dot(uxz)
       DwDt = - ROPS[1].dot(wxz)
       DpDt = - ROPS[2].dot(pxz)
       DtDt = - ROPS[3].dot(txz)
       
       # Null tendencies at vertical boundaries
       DwDt[topdex] = np.zeros(len(topdex))
       DwDt[botdex] = np.zeros(len(botdex))
       DtDt[topdex] = np.zeros(len(topdex))
       
       # Concatenate
       DqDt = np.concatenate((DuDt, DwDt, DpDt, DtDt))
       
       return DqDt

def computeDynSGSTendency(RESCF, REFS, uxz, wxz, pxz, txz, udex, wdex, pdex, tdex, botdex, topdex):
       
       # Get the derivative operators
       #DDXM = REFS[13]
       #DDZM = REFS[14]
       DDXM2 = REFS[15]
       DDZM2 = REFS[16]
       
       # Get the anisotropic coefficients
       RESCFX = RESCF[0]
       RESCFZ = RESCF[1]
       
       # Compute the tendencies
       #DuDt = DDXM.dot(RESCFX[udex] * DDXM.dot(uxz)) + DDZM.dot(RESCFZ[udex] * DDZM.dot(uxz))
       #DwDt = DDXM.dot(RESCFX[wdex] * DDXM.dot(wxz)) + DDZM.dot(RESCFZ[wdex] * DDZM.dot(wxz))
       #DpDt = DDXM.dot(RESCFX[pdex] * DDXM.dot(pxz)) + DDZM.dot(RESCFZ[pdex] * DDZM.dot(pxz))
       #DtDt = DDXM.dot(RESCFX[tdex] * DDXM.dot(txz)) + DDZM.dot(RESCFZ[tdex] * DDZM.dot(txz))
       
       # Compute tendencies (2nd derivative term only)
       DuDt = RESCFX[udex] * DDXM2.dot(uxz) + RESCFZ[udex] * DDZM2.dot(uxz)
       DwDt = RESCFX[wdex] * DDXM2.dot(wxz) + RESCFZ[udex] * DDZM2.dot(wxz)
       DpDt = RESCFX[pdex] * DDXM2.dot(pxz) + RESCFZ[udex] * DDZM2.dot(pxz)
       DtDt = RESCFX[tdex] * DDXM2.dot(txz) + RESCFZ[udex] * DDZM2.dot(txz)
       
       # Null tendencies at vertical boundaries
       DuDt[topdex] = np.zeros(len(topdex))
       DuDt[botdex] = np.zeros(len(botdex))
       DwDt[topdex] = np.zeros(len(topdex))
       DwDt[botdex] = np.zeros(len(botdex))
       DpDt[topdex] = np.zeros(len(topdex))
       DpDt[botdex] = np.zeros(len(botdex))
       DtDt[topdex] = np.zeros(len(topdex))
       DtDt[botdex] = np.zeros(len(botdex))
       
       # Concatenate
       DqDt = np.concatenate((DuDt, DwDt, DpDt, DtDt))
       
       return DqDt
       