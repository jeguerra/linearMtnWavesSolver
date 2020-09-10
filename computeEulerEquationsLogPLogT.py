#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 22 13:11:11 2019

@author: -
"""
import numpy as np
import cupy as cu
import warnings
import scipy.sparse as sps

def computeFieldDerivatives(q, DDX, DDZ):
       DqDx = DDX.dot(q)
       DqDz = DDZ.dot(q)
       
       return DqDx, DqDz
       
def computeFieldDerivatives_GPU(q, DDX, DDZ):
       
       q_gpu = cu.asarray(q)
       DqDx = DDX.dot(q_gpu)
       DqDz = DDZ.dot(q_gpu)
       
       return cu.asnumpy(DqDx), cu.asnumpy(DqDz)

def computeFieldDerivatives2(PqPx, PqPz, DDX, DDZ):

       D2qDx2 = DDX.dot(PqPx)
       D2qDz2 = DDZ.dot(PqPz)
       D2qDxz = DDZ.dot(PqPx)
       
       return D2qDx2, D2qDz2, D2qDxz
       
def computeFieldDerivatives2_GPU(PqPx, PqPz, DDX, DDZ):
       
       PqPx_gpu = cu.asarray(PqPx)
       PqPz_gpu = cu.asarray(PqPz)
       D2qDx2 = DDX.dot(PqPx_gpu)
       D2qDz2 = DDZ.dot(PqPz_gpu)
       D2qDxz = DDZ.dot(PqPx_gpu)
       
       return cu.asnumpy(D2qDx2), cu.asnumpy(D2qDz2), cu.asnumpy(D2qDxz)

def computeAllFieldDerivatives_CPU2GPU(q, DDX_CPU, DDZ_CPU, DDX_GPU, DDZ_GPU, DZDX, DQDZ):
       
       # Compute first derivatives (on CPU)
       DqDx = DDX_CPU.dot(q)
       DqDz = DDZ_CPU.dot(q)
       # Compute first partial in X (on CPU)
       PqPx = DqDx - DZDX * DqDz
       PqPz = DqDz + DQDZ
       
       # Send gradients to GPU
       PqPx_gpu = cu.asarray(PqPx)
       PqPz_gpu = cu.asarray(PqPz)
       # Compute second derivatives (on GPU)
       D2qDx2 = DDX_GPU.dot(PqPx_gpu)
       P2qPz2 = DDZ_GPU.dot(PqPz_gpu)
       D2qDxz = DDZ_GPU.dot(PqPx_gpu)
       
       # 2 transfers to GPU
       # 3 transfers from GPU
       
       return DqDx, DqDz, \
              cu.asnumpy(D2qDx2), cu.asnumpy(P2qPz2), cu.asnumpy(D2qDxz)

def computeAllFieldDerivatives_GPU(q, DDX, DDZ, DZDX, DQDZ):
       # Send state to GPU
       q_gpu = cu.asarray(q)
       DZDX_gpu = cu.asarray(DZDX)
       # Compute first derivatives (on GPU)
       DqDx = DDX.dot(q_gpu)
       PqPz = DDZ.dot(q_gpu)
       # Compute first partial in X (on GPU)
       PqPx = DqDx - DZDX_gpu * (PqPz + DQDZ)
       # Compute second derivatives (on GPU)
       D2qDx2 = DDX.dot(PqPx)
       P2qPz2 = DDZ.dot(PqPz)
       D2qDxz = DDZ.dot(PqPx)
       
       # 2 transfers to GPU
       # 5 transfers from GPU
       
       return cu.asnumpy(DqDx), cu.asnumpy(PqPz), \
              cu.asnumpy(D2qDx2), cu.asnumpy(P2qPz2), cu.asnumpy(D2qDxz)
       
def localDotProduct(arg):
              res = arg[0].dot(arg[1])
              return res

def computePrepareFields(REFS, SOLT, INIT, udex, wdex, pdex, tdex):
       
       TQ = SOLT + INIT
       # Make the total quatities
       U = TQ[udex]
       
       fields = np.reshape(SOLT, (len(udex), 4), order='F')

       return fields, U

#%% Evaluate the Jacobian matrix
def computeJacobianMatrixLogPLogT(PHYS, REFS, REFG, fields, U, botdex, topdex):
       # Get physical constants
       gc = PHYS[0]
       Rd = PHYS[3]
       kap = PHYS[4]
       gam = PHYS[6]
       
       # Get the derivative operators
       DDXM = REFS[10]
       DDZM = REFS[11]
       DZDX = REFS[15].flatten()
       
       GML = REFG[0]
       DLTDZ = REFG[1]
       DQDZ = REFG[2]
       
       # Compute terrain following terms (two way assignment into fields)
       wxz = np.array(fields[:,1])
       UZX = U * DZDX
       WXZ = wxz - UZX

       # Compute (total) derivatives of perturbations
       DqDx = DDXM.dot(fields)
       DqDz = DDZM.dot(fields)
       
       # Compute (partial) x derivatives of perturbations
       DZDXM = sps.diags(DZDX, offsets=0, format='csr')
       PqPx = DqDx - DZDXM.dot(DqDz)
       
       # Compute partial in X terrain following block
       PPXM = DDXM - DZDXM.dot(DDZM)
       
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
       DLTDZM = sps.diags(DLTDZ[:,0], offsets=0, format='csr')
       DUDZM = sps.diags(DQDZ[:,0], offsets=0, format='csr')
       DLPDZM = sps.diags(DQDZ[:,2], offsets=0, format='csr')
       DLPTDZM = sps.diags(DQDZ[:,3], offsets=0, format='csr')
       
       # Compute diagonal blocks related to sensible temperature
       RdT_bar = REFS[9][0]
       T_bar = (1.0 / Rd) * RdT_bar
       
       bf = np.exp(kap * fields[:,2] + fields[:,3])
       T_ratio = bf - 1.0
       RdT = RdT_bar * bf
       
       # Compute T'
       T_prime = T_ratio * T_bar
       
       RdT_barM = sps.diags(RdT_bar, offsets=0, format='csr')
       RdTM = sps.diags(RdT, offsets=0, format='csr')
       bfM = sps.diags(bf, offsets=0, format='csr')
       
       # Compute derivatives of temperature perturbation
       PtPx = PPXM.dot(T_prime)
       DtDz = DDZM.dot(T_prime)
       
       PtPx = DDXM.dot(T_prime) - DZDX * DtDz
       PtPxM = sps.diags(PtPx, offsets=0, format='csr')
       DtDzM = sps.diags(DtDz, offsets=0, format='csr')
       
       # Compute advective (multiplicative) diagonal operators
       UM = sps.diags(U, offsets=0, format='csr')
       WXZM = sps.diags(WXZ, offsets=0, format='csr')
       
       # Compute common horizontal transport block
       UPXM = UM.dot(DDXM) + WXZM.dot(DDZM)
       
       # Compute the blocks of the Jacobian operator
       LD11 = UPXM + PuPxM
       LD12 = DuDzM + DUDZM
       LD13 = RdTM.dot(PPXM) + (Rd * PtPxM)
       LD14 = RdTM.dot(PlpPxM)
       
       LD21 = PwPxM
       LD22 = UPXM + DwDzM
       LD23 = RdTM.dot(DDZM) + RdT_barM.dot(DLTDZM) + Rd * DtDzM
       LD24 = RdTM.dot(DlpDzM) - gc * bfM
       
       LD31 = gam * PPXM + PlpPxM
       LD32 = gam * DDZM + DlpDzM + DLPDZM
       LD33 = UPXM
       LD34 = None
       
       LD41 = PltPxM
       LD42 = DltDzM + DLPTDZM
       LD43 = None
       LD44 = UPXM
       
       DOPS = [LD11, LD12, LD13, LD14, \
               LD21, LD22, LD23, LD24, \
               LD31, LD32, LD33, LD34, \
               LD41, LD42, LD43, LD44]
       
       return DOPS

def computeJacobianVectorProduct(DOPS, REFG, vec, udex, wdex, pdex, tdex):
       # Get the Rayleight operators
       ROPS = REFG[5]
       
       # Compute the variable sections
       uvec = vec[udex]
       wvec = vec[wdex]
       pvec = vec[pdex]
       tvec = vec[tdex]
       
       # Compute the block products
       ures = (DOPS[0] + ROPS[0]).dot(uvec) + DOPS[1].dot(wvec) + DOPS[2].dot(pvec) + DOPS[3].dot(tvec)
       wres = DOPS[4].dot(uvec) + (DOPS[5] + ROPS[1]).dot(wvec) + DOPS[6].dot(pvec) + DOPS[7].dot(tvec)
       pres = DOPS[8].dot(uvec) + DOPS[9].dot(wvec) + (DOPS[10] + ROPS[2]).dot(pvec)
       tres = DOPS[12].dot(uvec) + DOPS[13].dot(wvec) + (DOPS[15] + ROPS[3]).dot(tvec)
       
       qprod = np.concatenate((ures, wres, pres, tres))
       
       return -qprod
    
#%% The linear equation operator
def computeEulerEquationsLogPLogT_Classical(DIMS, PHYS, REFS, REFG):
       # Get physical constants
       gc = PHYS[0]
       gam = PHYS[6]
       
       # Get the dimensions
       NX = DIMS[3] + 1
       NZ = DIMS[4]
       OPS = NX * NZ
       
       # Get REFS data
       UZ = REFS[8]
       PORZ = REFS[9][0]
       # Full spectral transform derivative matrices
       DDXM = REFS[12]
       DDZM = REFS[13]
              
       #%% Compute the various blocks needed
       UM = sps.diags(UZ, offsets=0, format='csr')
       PORZM = sps.diags(PORZ, offsets=0, format='csr')
       
       # Compute hydrostatic state diagonal operators
       DLTDZ = REFG[1]
       DQDZ = REFG[2]
       DLTDZM = sps.diags(DLTDZ[:,0], offsets=0, format='csr')
       DUDZM = sps.diags(DQDZ[:,0], offsets=0, format='csr')
       DLPDZM = sps.diags(DQDZ[:,2], offsets=0, format='csr')
       DLPTDZM = sps.diags(DQDZ[:,3], offsets=0, format='csr')
       unit = sps.identity(OPS)
              
       #%% Compute the terms in the equations
       U0DDX = UM.dot(DDXM)
       
       # Horizontal momentum
       LD11 = U0DDX
       LD12 = DUDZM
       LD13 = PORZM.dot(DDXM)
       LD14 = sps.csr_matrix((OPS,OPS))
       
       # Vertical momentum
       LD21 = sps.csr_matrix((OPS,OPS))
       LD22 = U0DDX
       LD23 = PORZM.dot(DDZM + DLTDZM)
       # Equivalent form from direct linearization
       #LD23 = PORZM.dot(DDZM) + gc * (1.0 / gam - 1.0) * unit
       LD24 = -gc * unit
       
       # Log-P equation
       LD31 = gam * DDXM
       LD32 = gam * DDZM + DLPDZM
       LD33 = U0DDX
       LD34 = None
       
       # Log-Theta equation
       LD41 = sps.csr_matrix((OPS,OPS))
       LD42 = DLPTDZM
       LD43 = None
       LD44 = U0DDX
       
       DOPS = [LD11, LD12, LD13, LD14, \
               LD21, LD22, LD23, LD24, \
               LD31, LD32, LD33, LD34, \
               LD41, LD42, LD43, LD44]
       
       return DOPS

# Function evaluation of the non linear equations (dynamic components)
def computeEulerEquationsLogPLogT_NL(PHYS, REFG, DqDx, DqDz, DZDX, RdT_bar, fields, U, uf, ebcDex):
       # Get physical constants
       gc = PHYS[0]
       kap = PHYS[4]
       gam = PHYS[6]
       
       # Get hydrostatic initial fields
       GML = REFG[0]
       DQDZ = uf * REFG[2]
       
       # Compute advective (multiplicative) operators
       UM = uf * np.expand_dims(U,1)
       wxz = np.expand_dims(fields[:,1],1)
       # Compute normal compnent to terrain surfaces
       velNorm = (wxz - UM * DZDX)
       # Enforce No-Slip condition on transport
       velNorm[ebcDex[1],:] *= 0.0
       velNorm[ebcDex[2],:] *= 0.0
       
       # Compute pressure gradient force scaling (buoyancy)
       with warnings.catch_warnings():
              np.seterr(all='raise')
              try:
                     RdT_hat = np.exp(kap * fields[:,2]) * np.exp(fields[:,3])
                     RdT = RdT_bar * RdT_hat
                     T_ratio = RdT_hat - 1.0
                     #T_ratio = np.exp(kap * fields[:,2] + fields[:,3]) - 1.0
              except FloatingPointError:
                     earg = kap * fields[:,2] + fields[:,3]
                     earg_max = np.amax(earg)
                     earg_min = np.amin(earg)
                     print('In argument to local T ratio: ', earg_min, earg_max)
                     pmax = np.amax(fields[:,2])
                     pmin = np.amin(fields[:,2])
                     print('Min/Max log pressures: ', pmin, pmax)
                     tmax = np.amax(fields[:,3])
                     tmin = np.amin(fields[:,3])
                     print('Min/Max log potential temperature: ', tmin, tmax)
                     # Close out the netcdf file
                            
       # Compute transport and divergence terms
       UPqPx = UM * DqDx
       wDQDz = velNorm * DqDz + wxz * DQDZ
       
       # GML CONFIGURATIONS
       # GML turned off
       #transport = UPqPx + wDQDz
       divergence = DqDx[:,0] + DqDz[:,1] - DZDX[:,0] * DqDz[:,0]
       #pgradx = RdT * (DqDx[:,2] - DZDX[:,0] * DqDz[:,2])
       #pgradz = RdT * DqDz[:,2] - gc * T_ratio
       # GML turned on
       transport = GML.dot(UPqPx + wDQDz)
       #divergence = GMLX.dot(DqDx[:,0]) + GMLZ.dot(DqDz[:,1] - DZDX[:,0] * DqDz[:,0])
       pgradx = GML.dot(RdT * (DqDx[:,2] - DZDX[:,0] * DqDz[:,2]))
       pgradz = GML.dot(RdT * DqDz[:,2] - gc * T_ratio)
       
       DqDt = -transport
       # Horizontal momentum equation
       DqDt[:,0] -= pgradx
       # Vertical momentum equation
       DqDt[:,1] -= pgradz
       # Pressure (mass) equation
       DqDt[:,2] -= gam * divergence
       # Potential Temperature equation (transport only)
                                  
       return DqDt

def computeRayleighTendency(REFG, fields):
       
       # Get the Rayleight operators
       mu = np.expand_dims(REFG[3],0)
       ROP = REFG[4]
       
       DqDt = -mu * ROP.dot(fields)
       
       return DqDt

def computeDiffusiveFluxTendency(RESCF, DqDx, DqDz, DDXM, DDZM, DZDX, ebcDex):
       
       # Get the anisotropic coefficients
       RESCFX = RESCF[0]
       RESCFZ = RESCF[1]
       
       # Compute the partial derivative
       PqPx = DqDx - DZDX * DqDz
       
       # Compute diffusive fluxes
       xflux = RESCFX * PqPx
       zflux = RESCFZ * DqDz
       
       # Scale kinematic fluxes
       xflux[:,0] *= 2.0
       zflux[:,1] *= 2.0
              
       # Compute the Laplacian blocks
       PqPz2 = DDZM.dot(zflux)
       DdqDx = DDZM.dot(xflux) - DZDX * PqPz2
       PqPx2 = DDXM.dot(xflux) - DZDX * DdqDx
       
       # Compute the tendencies (divergence of diffusive flux... discontinuous)
       DqDt = PqPx2 + PqPz2
       
       return DqDt

def computeDiffusionTendency(PHYS, RESCF, D2qDx2, P2qPz2, P2qPxz, DZDX, ebcDex):
       
       # Get the anisotropic coefficients
       RESCFX = RESCF[0]
       RESCFZ = RESCF[1]
       
       # Compute the 2nd partial derivative
       P2qPx2 = D2qDx2 - DZDX * P2qPxz
       
       xflux = RESCFX * P2qPx2 
       zflux = RESCFZ * P2qPz2
       xzflux = RESCFX * P2qPxz[:,0:2]
       zxflux = RESCFZ * P2qPxz[:,0:2]
       
       DqDt = np.zeros(D2qDx2.shape)
       # Diffusion of u-w vector
       DqDt[:,0] = 2.0 * xflux[:,0] + zflux[:,0] + xzflux[:,1]
       DqDt[:,1] = xflux[:,1] + 2.0 * zflux[:,1] + zxflux[:,0]
       # Normal to top and lateral boundaries vanish
       DqDt[ebcDex[3],0] *= 0.0
       DqDt[ebcDex[2],1] *= 0.0
       
       # Normal to top and lateral boundaries vanish
       xflux[ebcDex[3],2:] *= 0.0
       zflux[ebcDex[2],2:] *= 0.0
       # Diffusion of scalars (broken up into anisotropic components)
       DqDt[:,2:] = xflux[:,2:] + zflux[:,2:]
       # No scalar diffusion at boundary
       DqDt[ebcDex[1],2:] *= 0.0

       return DqDt