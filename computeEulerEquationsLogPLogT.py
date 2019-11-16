#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 22 13:11:11 2019

@author: -
"""
import numpy as np
import scipy.sparse as sps
from numba import jit

def computeInitialFields(PHYS, REFS, SOLT, INIT, udex, wdex, pdex, tdex, botdex, topdex):
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
       
       # The initial condition is an atmosphere in hydrostatic rest
       DZDX = REFS[15]
       # This sets the free slip condition on all coordinate surfaces
       # in the column. Ensures proper initialization of perturbation
       # fields. 
       fields[:,1] = U * DZDX

       return fields, U, RdT

def computePrepareFields(PHYS, REFS, SOLT, INIT, udex, wdex, pdex, tdex, botdex, topdex):
       # Get some physical quantities
       P0 = PHYS[1]
       Rd = PHYS[3]
       kap = PHYS[4]
       
       dHdX = REFS[6]
       
       TQ = SOLT + INIT
       # Make the total quatities
       U = TQ[udex]
       LP = TQ[pdex]
       LT = TQ[tdex]
       
       # Compute the sensible temperature scaling to PGF
       RdT = Rd * P0**(-kap) * np.exp(LT + kap * LP)
       
       fields = np.reshape(SOLT, (len(udex), 4), order='F')
       fields[botdex,1] = U[botdex] * dHdX
       fields[topdex,1] *= 0.0
       fields[topdex,3] *= 0.0

       return fields, U, RdT

#%% Evaluate the Jacobian matrix
def computeJacobianMatrixLogPLogT(PHYS, REFS, REFG, fields, U, RdT, botdex, topdex, DQ):
       # Get physical constants
       gc = PHYS[0]
       Rd = PHYS[3]
       gam = PHYS[6]
       
       # Get the derivative operators
       DDXM = REFS[10]
       DDZM = REFS[11]
       DZDX = REFS[15]
       
       # Compute terrain following terms
       wxz = fields[:,1]
       WXZ = wxz - U * DZDX
       # Apply boundary condition exactly
       WXZ[botdex] *= 0.0
       
       # Compute (total) derivatives of perturbations
       DqDx = DDXM.dot(fields)
       DqDz = DDZM.dot(fields)
       
       # Compute (partial) x derivatives of perturbations
       DZDXM = sps.diags(DZDX, offsets=0, format='csr')
       PqPx = DqDx - DZDXM.dot(DqDz)
       
       # Compute vertical gradient diagonal operators
       DuDzM = sps.diags(DqDz[:,0], offsets=0, format='csr')
       DwDzM = sps.diags(DqDz[:,1], offsets=0, format='csr')
       DlpDzM = sps.diags(DqDz[:,2], offsets=0, format='csr')
       DltDzM = sps.diags(DqDz[:,3], offsets=0, format='csr')
       
       # Compute horizontal gradient diagonal operators
       PuPxM = sps.diags(PqPx[:,0], offsets=0, format='csr')
       PwPxM = sps.diags(PqPx[:,1], offsets=0, format='csr')
       PlpPxM = sps.diags(PqPx[:,2], offsets=0, format='csr')
       PltPxM = sps.diags(PqPx[:,3], offsets=0, format='csr')
       
       # Compute hydrostatic state diagonal operators
       DLTDZ = REFG[1]
       DLTDZM = sps.diags(DLTDZ[:,0], offsets=0, format='csr')
       DQDZ = REFG[4]
       DUDZM = sps.diags(DQDZ[:,0], offsets=0, format='csr')
       DLPDZM = sps.diags(DQDZ[:,2], offsets=0, format='csr')
       DLPTDZM = sps.diags(DQDZ[:,3], offsets=0, format='csr')
       
       # Compute advective (multiplicative) diagonal operators
       UM = sps.diags(U, offsets=0, format='csr')
       WXZM = sps.diags(WXZ, offsets=0, format='csr')
       RdTM = sps.diags(RdT, offsets=0, format='csr')
       
       # Compute diagonal blocks related to sensible temperature
       RdT_bar = REFS[9]
       T_prime = (1.0 / Rd) * (RdT - RdT_bar[:,0])
       RdT_barM = sps.diags(RdT_bar[:,0], offsets=0, format='csr')
       PtPx = DDXM.dot(T_prime) - DZDX * DDZM.dot(T_prime)
       DtDz = DDZM.dot(T_prime)
       PtPxM = sps.diags(PtPx, offsets=0, format='csr')
       DtDzM = sps.diags(DtDz, offsets=0, format='csr')
       
       # Compute partial in X terrain following block
       PPXM = DDXM - DZDXM.dot(DDZM)
       
       # Compute common horizontal transport block
       UPXM = UM.dot(DDXM) + WXZM.dot(DDZM)
       
       unit = sps.identity(len(U))
       
       # Compute the blocks of the Jacobian operator
       LD11 = UPXM + PuPxM
       LD12 = DuDzM + DUDZM
       LD13 = RdTM.dot(PPXM) + (Rd * PtPxM)
       LD14 = RdTM.dot(PlpPxM) # vanish initial
       
       LD21 = PwPxM # vanish initial
       LD22 = UPXM + DwDzM
       LD23 = RdTM.dot(DDZM) + RdT_barM.dot(DLTDZM) + Rd * DtDzM
       LD24 = RdTM.dot(DlpDzM) - gc * unit
       
       LD31 = gam * PPXM + PlpPxM
       LD32 = gam * DDZM + DlpDzM + DLPDZM
       LD33 = UPXM
       LD34 = None
       
       LD41 = PltPxM # vanish initial
       LD42 = DltDzM + DLPTDZM
       LD43 = None
       LD44 = UPXM 

       DOPS = [LD11, LD12, LD13, LD14, \
               LD21, LD22, LD23, LD24, \
               LD31, LD32, LD33, LD34, \
               LD41, LD42, LD43, LD44]
       
       return DOPS
    
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
       DLTDZ = REFG[1]
       DLPDZ = REFG[2]
       DLPTDZ = REFG[3]
       # Full spectral transform derivative matrices
       DDXM = REFS[10]
       DDZM = REFS[11]
       # Sparse 4th order compact FD derivative matrices
       #DDXM = REFS[12]
       #DDZM = REFS[13]
       DZDX = REFS[15]
              
       #%% Compute the various blocks needed
       UM = sps.spdiags(UZ[:,0], 0, OPS, OPS)
       PORZM = sps.spdiags(PORZ[:,0], 0, OPS, OPS)
       
       DUDZM = sps.spdiags(DUDZ[:,0], 0, OPS, OPS)
       DLTDZM = sps.spdiags(DLTDZ[:,0], 0, OPS, OPS)
       DLPDZM = sps.spdiags(DLPDZ[:,0], 0, OPS, OPS)
       DLPTDZM = sps.spdiags(DLPTDZ[:,0], 0, OPS, OPS)
       unit = sps.identity(OPS)
       
       DZDXM = sps.spdiags(DZDX, 0, OPS, OPS)
       
       #%% Compute the terms in the equations
       U0DDX = UM.dot(DDXM)
       PPX = DDXM - DZDXM.dot(DDZM)
       #U0PPX = UM.dot(PPX)
       
       # Horizontal momentum
       LD11 = U0DDX
       LD12 = DUDZM
       LD13 = PORZM.dot(PPX)
       
       # Vertical momentum
       LD22 = U0DDX
       LD23 = PORZM.dot(DDZM + DLTDZM)
       # Equivalent form from direct linearization
       #LD23 = PORZM.dot(DDZM) + gc * (1.0 / gam - 1.0) * unit
       LD24 = -gc * unit
       
       # Log-P equation
       LD31 = gam * PPX
       LD32 = gam * DDZM + DLPDZM
       LD33 = U0DDX
       
       # Log-Theta equation
       LD42 = DLPTDZM
       LD44 = U0DDX
       
       DOPS = [LD11, LD12, LD13, LD22, LD23, LD24, LD31, LD32, LD33, LD42, LD44]
       
       return DOPS

# Function evaluation of the non linear equations (dynamic components)
#@jit(nopython=True)
def computeEulerEquationsLogPLogT_NL(PHYS, REFS, REFG, fields, U, RdT, botdex, topdex):
       # Get physical constants
       gc = PHYS[0]
       gam = PHYS[6]
       
       # Get the derivative operators
       DDXM = REFS[10]
       DDZM = REFS[11]
       DZDX = REFS[15]
       
       # Compute terrain following terms
       wxz = fields[:,1]
       WXZ = wxz - U * DZDX
              
       # Apply boundary condition exactly
       WXZ[botdex] *= 0.0
       
       # Compute advective (multiplicative) operators
       U = sps.diags(U, offsets=0, format='csr')
       wxz = sps.diags(wxz, offsets=0, format='csr')
       WXZ = sps.diags(WXZ, offsets=0, format='csr')
       
       # Get the static horizontal and vertical derivatives
       DQDZ = REFG[4]
       wDQDZ = wxz.dot(DQDZ)
       
       # Compute derivative of perturbations
       DqDx = DDXM.dot(fields)
       DqDz = DDZM.dot(fields)
       # Compute advection
       UDqDx = U.dot(DqDx)
       WDqDz = WXZ.dot(DqDz)
       transport = UDqDx + WDqDz + wDQDZ
       
       # Compute pressure gradient forces
       PGFX = RdT * (DqDx[:,2] - DZDX * DqDz[:,2])
       PGFZ = RdT * (DqDz[:,2] + DQDZ[:,2]) + gc

       def DqDt():
              # Horizontal momentum equation
              DuDt = -(transport[:,0] + PGFX)
              # Vertical momentum equation
              DwDt = -(transport[:,1] + PGFZ)
              # Pressure (mass) equation
              LD33 = gam * (DqDx[:,0] - DZDX * DqDz[:,0] + DqDz[:,1])
              DpDt = -(transport[:,2] + LD33)
              # Potential Temperature equation
              DtDt = -(transport[:,3])
              
              DwDt[topdex] *= 0.0
              DwDt[botdex] *= 0.0
              DtDt[topdex] *= 0.0
       
              return (DuDt, DwDt, DpDt, DtDt)
                     
       return np.concatenate(DqDt())

def computeRayleighTendency(REFG, fields, udex, wdex, pdex, tdex, botdex, topdex):
       
       # Get the static vertical gradients
       ROPS = REFG[5]
       
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
       DDXM = REFS[10]
       DDZM = REFS[11]
       #DDXM = REFS[12]
       #DDZM = REFS[13]
       DZDX = REFS[15]
       
       # Get the anisotropic coefficients
       RESCFX = RESCF[0]
       RESCFZ = RESCF[1]
       
       # Compute derivative of perturbations
       DDz = DDZM.dot(fields)
       DDx = DDXM.dot(fields)
       
       # Compute diffusive fluxes
       DuDx = RESCFX[udex] * (DDx[:,0] - DZDX * DDz[:,0])
       DwDx = RESCFX[wdex] * (DDx[:,1] - DZDX * DDz[:,1])
       DlpDx = RESCFX[pdex] * (DDx[:,2] - DZDX * DDz[:,2])
       DltDx = RESCFX[tdex] * (DDx[:,3] - DZDX * DDz[:,3])
       DuDz = RESCFZ[udex] * DDz[:,0]
       DwDz = RESCFZ[wdex] * DDz[:,1]
       DlpDz = RESCFZ[pdex] * DDz[:,2]
       DltDz = RESCFZ[tdex] * DDz[:,3]
       
       # Compute the tendencies (divergence of diffusive flux... discontinuous)
       #'''
       DuDt = DDXM.dot(DuDx) - DZDX * DDZM.dot(DuDx) + DDZM.dot(DuDz)
       DwDt = DDXM.dot(DwDx) - DZDX * DDZM.dot(DwDx) + DDZM.dot(DwDz)
       DpDt = DDXM.dot(DlpDx) - DZDX * DDZM.dot(DlpDx) + DDZM.dot(DlpDz)
       DtDt = DDXM.dot(DltDx) - DZDX * DDZM.dot(DltDx) + DDZM.dot(DltDz)
       #'''
       # Compute tendencies (2nd derivative term only)
       '''
       DuDt = RESCFX[udex] * DDx[:,0] + RESCFZ[udex] * DDz[:,0]
       DwDt = RESCFX[wdex] * DDx[:,1] + RESCFZ[wdex] * DDz[:,1]
       DpDt = RESCFX[pdex] * DDx[:,2] + RESCFZ[pdex] * DDz[:,2]
       DtDt = RESCFX[tdex] * DDx[:,3] + RESCFZ[tdex] * DDz[:,3]
       '''
       # Null tendencies along vertical boundaries
       DuDt[topdex] *= 0.0
       DwDt[topdex] *= 0.0
       DpDt[topdex] *= 0.0
       DtDt[topdex] *= 0.0

       DuDt[botdex] *= 0.0
       DwDt[botdex] *= 0.0
       DpDt[botdex] *= 0.0
       DtDt[botdex] *= 0.0

       # Concatenate
       DqDt = np.concatenate((DuDt, DwDt, DpDt, DtDt))
       
       return DqDt
       