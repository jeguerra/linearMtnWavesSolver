#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 08:05:02 2019

Computes the transient/static solution to the 2D mountain wave problem.
Log P / Log PT equation set with some static condensation to minimize number of terms.

INPUTS: Piecewise linear T(z) profile sounding (corner points), h(x) topography from
analytical function or equally spaced discrete (FFT interpolation)

COMPUTES: Map of T(z) and h(x) from input to computational domain. Linear LHS operator
matrix, boundary forcing vector and RHS residual. Solves steady problem with UMFPACK and
ALSQR Multigrid. Solves transient problem with Ketchenson SSPRK93 low storage method.

@author: Jorge E. Guerra
"""
import sys
import time
import shelve
import numpy as np
import math as mt
import scipy.sparse as sps
import scipy.sparse.linalg as spl
import scipy.linalg as dsl
from matplotlib import cm
import matplotlib.pyplot as plt
# Import from the local library of routines
from computeGrid import computeGrid
from computeAdjust4CBC import computeAdjust4CBC
from computeColumnInterp import computeColumnInterp
from computePartialDerivativesXZ import computePartialDerivativesXZ
from computeTopographyOnGrid import computeTopographyOnGrid
from computeGuellrichDomain2D import computeGuellrichDomain2D
#from computeStretchedDomain2D import computeStretchedDomain2D
from computeTemperatureProfileOnGrid import computeTemperatureProfileOnGrid
from computeThermoMassFields import computeThermoMassFields
from computeShearProfileOnGrid import computeShearProfileOnGrid
from computeRayleighEquations import computeRayleighEquations
from computeInterpolatedFields import computeInterpolatedFields

# Numerical stuff
import computeDerivativeMatrix as derv
import computeEulerEquationsLogPLogT as eqs
from computeTimeIntegration import computeTimeIntegrationLN
from computeTimeIntegration import computeTimeIntegrationNL
from computeIterativeSolveNL import computeIterativeSolveNL

import faulthandler; faulthandler.enable()

def getFromRestart(name, ET, NX, NZ, StaticSolve):
       rdb = shelve.open(restart_file, flag='r')
       
       NX_in = rdb['NX']
       NZ_in = rdb['NZ']
       if NX_in != NX or NZ_in != NZ:
              print('ERROR: RESTART DATA IS INVALID')
              print(NX, NX_in)
              print(NZ, NZ_in)
              sys.exit(2)
       
       SOLT = rdb['SOLT']
       RHS = rdb['RHS']
       IT = rdb['ET']
       if ET <= IT and not StaticSolve:
              print('ERROR: END TIME LEQ INITIAL TIME ON RESTART')
              sys.exit(2)
              
       # Initialize the restart time array
       TI = np.array(np.arange(IT + DT, ET, DT))
       rdb.close()
       
       return SOLT, RHS, NX_in, NZ_in, TI
       
if __name__ == '__main__':
       # Set the solution type (MUTUALLY EXCLUSIVE)
       StaticSolve = True
       LinearSolve = False
       NonLinSolve = False
       
       # Set residual diffusion switch
       ResDiff = False
       
       # Set direct solution method (MUTUALLY EXCLUSIVE)
       SolveFull = False
       SolveSchur = True
       
       # Set restarting
       toRestart = True
       isRestart = False
       restart_file = 'restartDB'
       
       # Set physical constants (dry air)
       gc = 9.80601
       P0 = 1.0E5
       cp = 1004.5
       Rd = 287.06
       Kp = Rd / cp
       cv = cp - Rd
       gam = cp / cv
       PHYS = [gc, P0, cp, Rd, Kp, cv, gam]
       
       # Set grid dimensions and order
       L2 = 1.0E4 * 3.0 * mt.pi
       L1 = -L2
       ZH = 36000.0
       NX = 135 # FIX: THIS HAS TO BE AN ODD NUMBER!
       NZ = 90
       OPS = (NX + 1) * NZ
       numVar = 4
       iU = 0
       iW = 1
       iP = 2
       iT = 3
       varDex = [iU, iW, iP, iT]
       DIMS = [L1, L2, ZH, NX, NZ, OPS]
       # Make the equation index vectors for all DOF
       udex = np.array(range(OPS))
       wdex = np.add(udex, OPS)
       pdex = np.add(wdex, OPS)
       tdex = np.add(pdex, OPS)
       
       # Set the terrain options
       h0 = 25.0
       aC = 5000.0
       lC = 4000.0
       HOPT = [h0, aC, lC]
       
       # Set the Rayleigh options
       depth = 12000.0
       width = 24000.0
       applyTop = True
       applyLateral = True
       mu = [1.0E-2, 1.0E-2, 1.0E-2, 1.0E-2]
       
       #% Transient solve parameters
       DT = 0.05 # Linear transient
       #DT = 0.05 # Nonlinear transient
       HR = 1.0
       ET = HR * 60 * 60 # End time in seconds
       OTI = 200 # Stride for diagnostic output
       ITI = 1000 # Stride for image output
       RTI = 1 # Stride for residual visc update
       
       #% Define the computational and physical grids+
       REFS = computeGrid(DIMS)
       
       #% Compute the raw derivative matrix operators in alpha-xi computational space
       DDX_1D, HF_TRANS = derv.computeHermiteFunctionDerivativeMatrix(DIMS)
       DDZ_1D, CH_TRANS = derv.computeChebyshevDerivativeMatrix(DIMS)
       
       DDX_SP = derv.computeCompactFiniteDiffDerivativeMatrix1(DIMS, REFS[0])
       DDZ_SP = derv.computeCompactFiniteDiffDerivativeMatrix1(DIMS, REFS[1])
       
       # Update the REFS collection
       REFS.append(DDX_1D)
       REFS.append(DDZ_1D)
       
       #% Read in topography profile or compute from analytical function
       AGNESI = 1 # "Witch of Agnesi" profil e
       SCHAR = 2 # Schar mountain profile nominal (Schar, 2001)
       EXPCOS = 3 # Even exponential and squared cosines product
       EXPPOL = 4 # Even exponential and even polynomial product
       INFILE = 5 # Data from a file (equally spaced points)
       HofX, dHdX = computeTopographyOnGrid(REFS, SCHAR, HOPT)
       
       # Make the 2D physical domains from reference grids and topography
       zRay = ZH - depth
       XL, ZTL, DZT, sigma, ZRL = computeGuellrichDomain2D(DIMS, REFS, zRay, HofX, dHdX)
       #XL, ZTL, DZT, sigma = computeStretchedDomain2D(DIMS, REFS, HofX, dHdX)
       # Update the REFS collection
       REFS.append(XL)
       REFS.append(ZTL)
       REFS.append(dHdX)
       REFS.append(sigma)
       
       # Compute DX and DZ grid length scales
       DX = np.mean(np.abs(np.diff(REFS[0])))
       DZ = np.mean(np.abs(np.diff(REFS[1])))
       
       #% Compute the BC index vector
       ubdex, utdex, wbdex, sysDex, vbcDex, wbcDex, tbcDex = \
              computeAdjust4CBC(DIMS, numVar, varDex)
       
       #% Read in sensible or potential temperature soundings (corner points)
       T_in = [300.0, 228.5, 228.5, 244.5]
       Z_in = [0.0, 1.1E4, 2.0E4, 3.6E4]
       SENSIBLE = 1
       POTENTIAL = 2
       # Map the sounding to the computational vertical grid [0 H]
       TofZ, dTdz = computeTemperatureProfileOnGrid(Z_in, T_in, REFS)
       # Compute background fields on the vertical
       dlnPdz, LPZ, PZ, dlnPTdz, LPT, PT, RHO = \
              computeThermoMassFields(PHYS, DIMS, REFS, TofZ, dTdz, SENSIBLE)
              
       # Compute the ratio of pressure to density or (Rd * T(z))
       #POR = PZ * np.reciprocal(RHO)
       POR = Rd * TofZ
       
       # Read in or compute background horizontal wind profile
       MEANJET = 1 # Analytical smooth jet profile
       JETOPS = [10.0, 16.822, 1.386]

       U, dUdz = computeShearProfileOnGrid(REFS, JETOPS, P0, PZ, dlnPdz)
       
       #% Compute the background gradients in physical 2D space
       dUdz = np.expand_dims(dUdz, axis=1)
       DUDZ = np.tile(dUdz, NX+1)
       DUDZ = computeColumnInterp(DIMS, REFS[1], dUdz, 0, ZTL, DUDZ, CH_TRANS, '1DtoTerrainFollowingCheb')
       dlnPdz = np.expand_dims(dlnPdz, axis=1)
       DLPDZ = np.tile(dlnPdz, NX+1)
       DLPDZ = computeColumnInterp(DIMS, REFS[1], dlnPdz, 0, ZTL, DLPDZ, CH_TRANS, '1DtoTerrainFollowingCheb')
       dlnPTdz = np.expand_dims(dlnPTdz, axis=1)
       DLPTDZ = np.tile(dlnPTdz, NX+1)
       DLPTDZ = computeColumnInterp(DIMS, REFS[1], dlnPTdz, 0, ZTL, DLPTDZ, CH_TRANS, '1DtoTerrainFollowingCheb')
       dlnTDz = np.expand_dims(dTdz * np.reciprocal(TofZ), axis=1)
       DLTDZ = np.tile(dlnTDz, NX+1)
       DLTDZ = computeColumnInterp(DIMS, REFS[1], dlnTDz, 0, ZTL, DLTDZ, CH_TRANS, '1DtoTerrainFollowingCheb')
       # Compute the background (initial) fields
       POR = np.expand_dims(POR, axis=1)
       PORZ = np.tile(POR, NX+1)
       PORZ = computeColumnInterp(DIMS, REFS[1], POR, 0, ZTL, PORZ, CH_TRANS, '1DtoTerrainFollowingCheb')
       U = np.expand_dims(U, axis=1)
       UZ = np.tile(U, NX+1)
       UZ = computeColumnInterp(DIMS, REFS[1], U, 0, ZTL, UZ, CH_TRANS, '1DtoTerrainFollowingCheb')
       LPZ = np.expand_dims(LPZ, axis=1)
       LOGP = np.tile(LPZ, NX+1)
       LOGP = computeColumnInterp(DIMS, REFS[1], LPZ, 0, ZTL, LOGP, CH_TRANS, '1DtoTerrainFollowingCheb')
       LPT = np.expand_dims(LPT, axis=1)
       LOGT = np.tile(LPT, NX+1)
       LOGT = computeColumnInterp(DIMS, REFS[1], LPT, 0, ZTL, LOGT, CH_TRANS, '1DtoTerrainFollowingCheb')
       
       # Compute horizontal derivatives of background fields
       '''
       DUDX = np.zeros((NZ,NX+1))
       DLPDX = np.zeros((NZ,NX+1))
       DLTDX = np.zeros((NZ,NX+1))
       for rr in range(NZ):
              # Compute X derivative without constant offsets
              DUDX[rr,:] = DDX_1D.dot(UZ[rr,:] - UZ[rr,0])
              DLPDX[rr,:] = DDX_1D.dot(LOGP[rr,:] - LOGP[rr,0])
              DLTDX[rr,:] = DDX_1D.dot(LOGT[rr,:] - LOGT[rr,0])
              
       DUDX = np.reshape(DUDX, (OPS,), order='F')
       DLPDX = np.reshape(DLPDX, (OPS,), order='F')
       DLPTDX = np.reshape(DLTDX, (OPS,), order='F')
       '''       
       # Get the static vertical gradients and store
       DUDZ = np.reshape(DUDZ, (OPS,1), order='F')
       DLTDZ = np.reshape(DLTDZ, (OPS,1), order='F')
       DLPDZ = np.reshape(DLPDZ, (OPS,1), order='F')
       DLPTDZ = np.reshape(DLPTDZ, (OPS,1), order='F')
       DQDZ = np.hstack((DUDZ, np.zeros((OPS,1)), DLPDZ, DLPTDZ))
       
       # Make a collection for background field derivatives
       REFG = [DUDZ, DLTDZ, DLPDZ, DLPTDZ, DQDZ]
       
       # Update the REFS collection
       REFS.append(np.reshape(UZ, (OPS,1), order='F'))
       REFS.append(np.reshape(PORZ, (OPS,1), order='F'))
       
       # Get some memory back here
       del(PORZ)
       del(DUDZ)
       del(DLTDZ)
       del(DLPDZ)
       del(DLPTDZ)
       
       #%% Get the 2D linear operators in Hermite-Chebyshev space
       DDXM, DDZM = computePartialDerivativesXZ(DIMS, REFS, DDX_1D, DDZ_1D)
       DZDX = sps.diags(np.reshape(DZT, (OPS,), order='F'), offsets=0, format='csr')
       
       #%% Get the 2D linear operators in Compact Finite Diff (for Laplacian)
       DDXM_SP, DDZM_SP = computePartialDerivativesXZ(DIMS, REFS, DDX_SP, DDZ_SP)
       #REFG.append(PPXM_SP)
       #REFG.append(DDZM_SP)
       
       # Update the data storage
       REFS.append(DDXM)
       REFS.append(DDZM)
       # 2nd order derivatives or compact FD sparse 1st derivatives
       #REFS.append(DDXM.dot(DDXM))
       #REFS.append(DDZM.dot(DDZM))
       REFS.append(DDXM_SP)
       REFS.append(DDZM_SP)
       REFS.append(DZT)
       REFS.append(DZDX.diagonal())
       
       del(DDXM)
       del(DDZM)
       #del(DDXM_SP)
       #del(DDZM_SP)
       del(DZDX)
       
       #% Rayleigh opearator
       ROPS = computeRayleighEquations(DIMS, REFS, mu, ZRL, width, applyTop, applyLateral, ubdex, utdex)
       REFG.append(ROPS)
       
       # Initialize transient storage
       SOLT = np.zeros((numVar * OPS, 2))
       INIT = np.zeros((numVar * OPS,))
       RHS = np.zeros((numVar * OPS,))
       
       # Initialize the Background fields
       INIT[udex] = np.reshape(UZ, (OPS,), order='F')
       INIT[wdex] = np.zeros((OPS,))
       INIT[pdex] = np.reshape(LOGP, (OPS,), order='F')
       INIT[tdex] = np.reshape(LOGT, (OPS,), order='F')
       
       if isRestart:
              print('Restarting from previous solution...')
              SOLT, RHS, NX_in, NZ_in, TI = getFromRestart(restart_file, ET, NX, NZ, StaticSolve)
              SOLT[:,0] = SOLT[:,1]
       else:
              # Initialize time array
              TI = np.array(np.arange(DT, ET, DT))
              
       # Initialize fields
       fields, U, RdT = eqs.computePrepareFields(PHYS, REFS, np.array(SOLT[:,0]), INIT, udex, wdex, pdex, tdex, ubdex, utdex)
       # Initialize the RHS and forcing for each field
       RHS = eqs.computeEulerEquationsLogPLogT_NL(PHYS, REFS, REFG, np.array(fields), U, RdT, ubdex, utdex)
       RHS += eqs.computeRayleighTendency(REFG, np.array(fields), ubdex, utdex)
       
       print('Residual 2-norm INITIAL state: ', np.linalg.norm(RHS))
       
       # Set the forcing
       bN = RHS
       
       #% Compute the global LHS operator
       if (StaticSolve or LinearSolve):
              
              # Test evaluation of full Jacobian... must match linearization on first iteration
              #'''
              DOPS_NL = eqs.computeJacobianMatrixLogPLogT(PHYS, REFS, REFG, fields, U, RdT, ubdex, utdex)
              '''
              DOPS = [DOPS_NL[0], DOPS_NL[1], DOPS_NL[2], \
                      DOPS_NL[5], DOPS_NL[6], DOPS_NL[7], \
                      DOPS_NL[8], DOPS_NL[9], DOPS_NL[10], \
                      DOPS_NL[13], DOPS_NL[15]]
              del(DOPS_NL)
              '''
              #DOPS = eqs.computeEulerEquationsLogPLogT(DIMS, PHYS, REFS, REFG)
                     
              print('Compute Jacobian operator blocks: DONE!')
              
              # Convert blocks to 'lil' format for indexing
              DOPS = []
              for dd in range(len(DOPS_NL)):
                     if (DOPS_NL[dd]) is not None: 
                            DOPS.append(DOPS_NL[dd].tolil())
                     else:
                            DOPS.append(DOPS_NL[dd])
              del(DOPS_NL)
              
              # Apply the BC adjustments and indexing block-wise
              A = DOPS[0]              
              B = DOPS[1][:,wbcDex]
              C = DOPS[2]
              D = DOPS[3][:,tbcDex]
              
              E = DOPS[4][wbcDex,:]
              F = DOPS[5][np.ix_(wbcDex,wbcDex)] 
              G = DOPS[6][wbcDex,:]
              H = DOPS[7][np.ix_(wbcDex,tbcDex)]
              
              I = DOPS[8]
              J = DOPS[9][:,wbcDex]
              K = DOPS[10]
              M = DOPS[11]
              
              N = DOPS[12][tbcDex,:]
              O = DOPS[13][np.ix_(tbcDex,wbcDex)]
              P = DOPS[14]
              Q = DOPS[15][np.ix_(tbcDex,tbcDex)]
              
              # The Rayleigh operators are block diagonal
              R1 = ROPS[0]
              R2 = (ROPS[1].tolil())[np.ix_(wbcDex,wbcDex)]
              R3 = ROPS[2]
              R4 = (ROPS[3].tolil())[np.ix_(tbcDex,tbcDex)]
               
              del(DOPS)
              
              # Set up Schur blocks or full operator...
              if (StaticSolve and SolveSchur) and not LinearSolve:
                     # Compute the partitions for Schur Complement solution
                     AS = sps.bmat([[A + R1, B], [E, F + R2]], format='csc')
                     BS = sps.bmat([[C, D], [G, H]], format='csc')
                     CS = sps.bmat([[I, J], [N, O]], format='csc')
                     DS = sps.bmat([[K + R3, M], [P, Q + R4]], format='csc')
                     
                     # Compute the partitions for Schur Complement solution
                     fw = bN[wdex]
                     f1 = np.concatenate((bN[udex], fw[wbcDex]))
                     ft = bN[tdex]
                     f2 = np.concatenate((bN[pdex], ft[tbcDex]))
                     
              if LinearSolve or (StaticSolve and SolveFull):
                     # Compute the global linear operator
                     AN = sps.bmat([[A + R1, B, C, D], \
                              [E, F + R2, G, H], \
                              [I, J, K + R3, M], \
                              [N, O, P, Q + R4]], format='csr')
              
                     # Compute the global linear force vector
                     bN = bN[sysDex]
              
              # Get memory back
              del(A); del(B); del(C)
              del(D); del(E); del(F)
              del(G); del(H); del(J)
              del(K); del(M)
              print('Set up global linear operators: DONE!')
       
       #%% Solve the system - Static or Transient Solution
       start = time.time()
       if StaticSolve:
              print('Starting Linear to Nonlinear Static Solver...')
              
              if SolveFull and not SolveSchur:
                     print('Solving linear system by full operator SuperLU...')
                     # Direct solution over the entire operator (better for testing BC's)
                     #sol = spl.spsolve(AN, bN, permc_spec='MMD_ATA', use_umfpack=False)
                     opts = dict(Equil=True, IterRefine='DOUBLE')
                     factor = spl.splu(AN, permc_spec='MMD_ATA', options=opts)
                     del(AN)
                     sol = factor.solve(bN)
                     del(bN)
                     del(factor)
              if SolveSchur and not SolveFull:
                     print('Solving linear system by Schur Complement...')
                     # Factor DS and compute the Schur Complement of DS
                     #opts = dict(Equil=True, IterRefine='DOUBLE')
                     #factorDS = spl.splu(DS, permc_spec='COLAMD', options=opts)
                     #import scikits.umfpack as um
                     #umfpack = um.UmfpackContext()
                     #umfpack.numeric(DS)
                     factorDS = dsl.lu_factor(DS.toarray())
                     print('Factor D... DONE!')
                     del(DS)
                     #alpha = factorDS.solve(CS.toarray())
                     alpha = dsl.lu_solve(factorDS, CS.toarray())
                     #alpha = umfpack(um.UMFPACK_A, DS, CS, autoTranspose = True)
                     DS_SC = AS.toarray() - (BS.toarray()).dot(alpha)
                     print('Compute Schur Complement of D')
                     del(AS)
                     del(alpha)
                     factorDS_SC = dsl.lu_factor(DS_SC)
                     del(DS_SC)
                     print('Factor D and Schur Complement of D matrix... DONE!')
                     
                     # Compute alpha f2_hat = DS^-1 * f2 and f1_hat
                     #f2_hat = factorDS.solve(f2)
                     f2_hat = dsl.lu_solve(factorDS, f2)
                     #f2_hat = umfpack(um.UMFPACK_A, DS, f2, autoTranspose = True)
                     f1_hat = -BS.dot(f2_hat)
                     # Use dense linear algebra at this point
                     sol1 = dsl.lu_solve(factorDS_SC, f1_hat)
                     print('Solve for u and w... DONE!')
                     f2 = f2 - CS.dot(sol1)
                     #sol2 = factorDS.solve(f2)
                     sol2 = dsl.lu_solve(factorDS, f2)
                     print('Solve for ln(p) and ln(theta)... DONE!')
                     sol = np.concatenate((sol1, sol2))
                     
                     # Update the solution
                     SOLT[sysDex,1] = SOLT[sysDex,0] + sol
                     
                     # Set the boundary condition   
                     SOLT[wbdex,1] = dHdX * (INIT[udex][ubdex] + SOLT[udex,1][ubdex])
                     print('Recover full linear solution vector... DONE!')
                     
                     # Update the forcing vector
                     fields, U, RdT = eqs.computePrepareFields(PHYS, REFS, SOLT[:,1], INIT, udex, wdex, pdex, tdex, ubdex, utdex)
                     RHS = eqs.computeEulerEquationsLogPLogT_NL(PHYS, REFS, REFG, fields, U, RdT, ubdex, utdex)
                     print('Residual 2-norm AFTER linear solve: ', np.linalg.norm(RHS))
                     
                     # Get memory back
                     del(BS); del(CS)
                     del(factorDS)
                     del(factorDS_SC)
                     del(f1_hat); del(f2_hat); del(sol1); del(sol2)
                     
              
              #%% Use the linear solution as the initial guess to the nonlinear solution
              '''
              sol = computeIterativeSolveNL(PHYS, REFS, REFG, DX, DZ, SOLT, INIT, udex, wdex, pdex, tdex, ubdex, utdex, sysDex)
              SOLT[:,1] = sol
              '''
              # Compare the linear and nonlinear solutions
              DSOL = SOLT[:,1] - SOLT[:,0]
              print('Norm of difference nonlinear to linear solution: ', np.linalg.norm(DSOL))
              
              # Initialize the RHS and forcing for each field
              fields, U, RdT = eqs.computePrepareFields(PHYS, REFS, SOLT[:,1], INIT, udex, wdex, pdex, tdex, ubdex, utdex)
              RHS = eqs.computeEulerEquationsLogPLogT_NL(PHYS, REFS, REFG, fields, U, RdT, ubdex, utdex)
              print('Residual 2-norm after NL solve: ', np.linalg.norm(RHS))
       
       #%% Transient solutions       
       elif LinearSolve:
              RHS[sysDex] = bN
              print('Starting Linear Transient Solver...')
       elif NonLinSolve:
              sysDex = np.array(range(0, numVar * OPS))
              print('Starting Nonlinear Transient Solver...')
                                          
       #%% Start the time loop
       if LinearSolve or NonLinSolve:
              error = [np.linalg.norm(RHS)]
              for tt in range(len(TI)):
                     # Compute the SSPRK93 stages at this time step
                     if LinearSolve:
                            # MUST FIX THIS INTERFACE TO EITHER USE THE FULL OPERATOR OR MAKE A MORE EFFICIENT MULTIPLICATION FUNCTION FOR AN
                            sol, rhs = computeTimeIntegrationLN(PHYS, REFS, REFG, bN, AN, DX, DZ, DT, RHS, SOLT, INIT, sysDex, udex, wdex, pdex, tdex, ubdex, utdex, ResDiff)
                     elif NonLinSolve:
                            sol, rhs = computeTimeIntegrationNL(PHYS, REFS, REFG, DX, DZ, DT, RHS, SOLT, INIT, udex, wdex, pdex, tdex, ubdex, utdex, ResDiff)
                     
                     SOLT[sysDex,0] = sol
                     RHS[sysDex] = rhs
                     
                     # Print out diagnostics every OTI steps
                     if tt % OTI == 0:
                            err = np.linalg.norm(RHS)
                            error.append(err)
                            err1 = np.linalg.norm(RHS[udex])
                            err2 = np.linalg.norm(RHS[wdex])
                            err3 = np.linalg.norm(RHS[pdex])
                            err4 = np.linalg.norm(RHS[tdex])
                            print('Time: %d, Residuals: %10.4E, %10.4E, %10.4E, %10.4E, %10.4E' \
                                  % (tt * DT, err1, err2, err3, err4, err))
                     
                     if tt % ITI == 0:
                            fig = plt.figure(figsize=(10.0, 6.0))
                            # Check the tendencies
                            #plt.xlim(-30, 30)
                            #plt.ylim(0, 25)
                            for pp in range(4):
                                   plt.subplot(2,2,pp+1)
                                   if pp == 0:
                                          qdex = udex
                                   elif pp == 1:
                                          qdex = wdex
                                   elif pp == 2:
                                          qdex = pdex
                                   else:
                                          qdex = tdex
                                   dqdt = np.reshape(RHS[qdex], (NZ, NX+1), order='F')
                                   ccheck = plt.contourf(1.0E-3*XL, 1.0E-3*ZTL, dqdt, 101, cmap=cm.seismic)
                                   cbar = plt.colorbar(ccheck, format='%.3e')
                            plt.show()
              
              # Set the boundary condition                      
              SOLT[wbdex,0] = np.multiply(dHdX, np.add(UZ[0,:], SOLT[ubdex,0]))
              
              # Copy state instance 0 to 1
              SOLT[:,1] = SOLT[:,0]
              
       endt = time.time()
       print('Solve the system: DONE!')
       print('Elapsed time: ', endt - start)
       
       #% Make a database for restart
       if toRestart:
              rdb = shelve.open(restart_file, flag='n')
              rdb['SOLT'] = SOLT
              rdb['RHS'] = RHS
              rdb['NX'] = NX
              rdb['NZ'] = NZ
              rdb['ET'] = ET
              rdb.close()
       
       #%% Recover the solution (or check the residual)
       NXI = 2500
       NZI = 200
       if StaticSolve:
              nativeLN, interpLN = computeInterpolatedFields(DIMS, ZTL, SOLT[:,0], NX, NZ, NXI, NZI, udex, wdex, pdex, tdex, CH_TRANS, HF_TRANS)
              nativeNL, interpNL = computeInterpolatedFields(DIMS, ZTL, SOLT[:,1], NX, NZ, NXI, NZI, udex, wdex, pdex, tdex, CH_TRANS, HF_TRANS)
              nativeDF, interpDF = computeInterpolatedFields(DIMS, ZTL, DSOL, NX, NZ, NXI, NZI, udex, wdex, pdex, tdex, CH_TRANS, HF_TRANS)
       else:
              native, interp = computeInterpolatedFields(DIMS, ZTL, SOLT[:,0], NX, NZ, NXI, NZI, udex, wdex, pdex, tdex, CH_TRANS, HF_TRANS)
              uxz = native[0]; wxz = native[1]; pxz = native[2]; txz = native[3]
              uxzint = interp[0]; wxzint = interp[1]; pxzint = interp[2]; txzint = interp[3]
       
       #% Make the new grid XLI, ZTLI
       import HerfunChebNodesWeights as hcnw
       xnew, dummy = hcnw.hefunclb(NX)
       xmax = np.amax(xnew)
       xmin = np.amin(xnew)
       # Make new reference domain grid vectors
       xnew = np.linspace(xmin, xmax, num=NXI, endpoint=True)
       znew = np.linspace(0.0, ZH, num=NZI, endpoint=True)
       
       # Interpolate the terrain profile
       hcf = HF_TRANS.dot(ZTL[0,:])
       dhcf = HF_TRANS.dot(dHdX)
       IHF_TRANS = hcnw.hefuncm(NX, xnew, True)
       hnew = (IHF_TRANS).dot(hcf)
       dhnewdx = (IHF_TRANS).dot(dhcf)
       
       # Scale znew to physical domain and make the new grid
       xnew *= L2 / xmax
       # Compute the new Guellrich domain
       NDIMS = [L1, L2, ZH, NXI-1, NZI]
       NREFS = [xnew, znew]
       XLI, ZTLI, DZTI, sigmaI, ZRLI = computeGuellrichDomain2D(NDIMS, NREFS, zRay, hnew, dhnewdx)
       
       #%% Make some plots for static or transient solutions
       
       if StaticSolve:
              fig = plt.figure(figsize=(12.0, 6.0))
              # 1 X 3 subplot of W for linear, nonlinear, and difference
              plt.subplot(2,2,1)
              ccheck = plt.contourf(1.0E-3 * XLI, 1.0E-3 * ZTLI, interpLN[1], 201, cmap=cm.seismic)#, vmin=0.0, vmax=20.0)
              cbar = fig.colorbar(ccheck)
              plt.xlim(-30.0, 50.0)
              plt.tick_params(axis='x', which='both', bottom=True, top=False, labelbottom=False)
              plt.title('Linear - W (m/s)')
              plt.subplot(2,2,3)
              ccheck = plt.contourf(1.0E-3 * XLI, 1.0E-3 * ZTLI, interpNL[1], 201, cmap=cm.seismic)#, vmin=0.0, vmax=20.0)
              cbar = fig.colorbar(ccheck)
              plt.xlim(-30.0, 50.0)
              plt.title('Nonlinear - W (m/s)')
              plt.subplot(1,2,2)
              ccheck = plt.contourf(1.0E-3 * XLI, 1.0E-3 * ZTLI, interpDF[1], 201, cmap=cm.seismic)
              cbar = fig.colorbar(ccheck)
              #plt.contour(1.0E-3 * XLI, 1.0E-3 * ZTLI, interpDF[1], 51, colors='black', linewidths=1.25)
              plt.xlim(-15.0, 25.0)
              plt.ylim(0.0, 30.0)
              plt.title('Difference - W (m/s)')
              plt.tight_layout()
              plt.show()
              
       elif LinearSolve or NonLinSolve:
              fig = plt.figure()
              # 2 X 2 subplot with all fields at the final time
              for pp in range(4):
                     plt.subplot(2,2,pp+1)
                     ccheck = plt.contourf(XLI, ZTLI, interp[pp], 201, cmap=cm.seismic)#, vmin=0.0, vmax=20.0)
                     cbar = fig.colorbar(ccheck)
              plt.show()

       #%% Check the boundary conditions
       '''
       plt.figure()
       plt.plot(REFS[0],nativeLN[0][0,:])
       plt.plot(REFS[0],nativeNL[0][0,:])
       plt.title('Horizontal Velocity - Terrain Boundary')
       plt.xlim(-15000, 15000)
       plt.figure()
       plt.plot(REFS[0],nativeLN[1][0,:])
       plt.plot(REFS[0],nativeNL[1][0,:])
       plt.title('Vertical Velocity - Terrain Boundary')
       plt.xlim(-15000, 15000)
       '''
       #%% #Spot check the solution on both grids
       '''
       fig = plt.figure()
       ccheck = plt.contourf(XL, ZTL, nativeLN[1], 101, cmap=cm.seismic)
       cbar = fig.colorbar(ccheck)
       #plt.xlim(-25000.0, 25000.0)
       #plt.ylim(0.0, 5000.0)
       #
       fig = plt.figure()
       ccheck = plt.contourf(XLI, ZTLI, interpLN[1], 201, cmap=cm.seismic)#, vmin=0.0, vmax=20.0)
       cbar = fig.colorbar(ccheck)
       #plt.xlim(-20000.0, 20000.0)
       #plt.ylim(0.0, 1000.0)
       #plt.yscale('symlog')
       #
       fig = plt.figure()
       plt.plot(XLI[0,:], (interpLN[1])[0:2,:].T, XL[0,:], (nativeLN[1])[0:2,:].T)
       plt.xlim(-15000.0, 15000.0)
       '''