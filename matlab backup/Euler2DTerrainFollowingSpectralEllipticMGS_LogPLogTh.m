
%% COMPUTES STEADY LNP-LNT 2D MOUNTAIN WAVE PROBLEM IN 4 TEST CONFIGURATIONS:
%% SUPER HIGH RESOLUTION MULTIGRID SOLVER
%% CHOLMOD2 -> GMRES AND ALSQR ITERATIVE SOLVERS ON FINER GRIDS

% 1) 'ShearJetSchar' Discontinous background with strong shear
% 2) 'ShearJetScharCBVF' Uniform background with strong shear
% 3) 'ClassicalSchar' The typical Schar mountain test with uniform
% background and constant wind
% 4) 'AndesMtn' Same as 1) but with real input terrain data

clc
clear
close all
opengl info
addpath(genpath('/home/jeguerra/Documents/MATLAB/'))

%% Create the dimensional XZ grid
NX = 128; % Expansion order matches physical grid
NZ = 84; % Expansion order matches physical grid
OPS = NX * NZ;
numVar = 4;
iW = 1;
iP = 2;
iT = 3;

%% Set the test case and global parameters
TestCase = 'ShearJetSchar'; BC = 0;
%TestCase = 'ShearJetScharCBVF'; BC = 0;
%TestCase = 'ClassicalSchar'; BC = 0;
%TestCase = 'AndesMtn'; BC = 0;

z0 = 0.0;
gam = 1.4;
Rd = 287.06;
cp = 1004.5;
cv = cp - Rd;
ga = 9.80616;
p0 = 1.0E5;
kappa = Rd / cp;
if strcmp(TestCase,'ShearJetSchar') == true
    zH = 36000.0;
    l1 = -1.0E4 * 3.0 * pi;
    l2 = 1.0E4 * 3.0 * pi;
    %l1 = -6.0E4;
    %l2 = 6.0E4;
    L = abs(l2 - l1);
    GAMT = -0.0065;
    HT = 11000.0;
    GAMS = 0.001;
    HML = 9000.0;
    HS = 20000.0;
    T0 = 300.0;
    BVF = 0.0;
    hfactor = 1.0;
    depth = 10000.0;
    width = 15000.0;
    nu1 = hfactor * 1.0E-2; nu2 = hfactor * 1.0E-2;
    nu3 = hfactor * 1.0E-2; nu4 = hfactor * 1.0E-2;
    applyLateralRL = true;
    applyTopRL = true;
    aC = 5000.0;
    lC = 4000.0;
    hC = 10.0;
    mtnh = [int2str(hC) 'm'];
    hfilt = '';
    u0 = 10.0;
    uj = 16.822;
    b = 1.386;
elseif strcmp(TestCase,'ShearJetScharCBVF') == true
    zH = 35000.0;
    l1 = -1.0E4 * 2.0 * pi;
    l2 = 1.0E4 * 2.0 * pi;
    %l1 = -6.0E4;
    %l2 = 6.0E4;
    L = abs(l2 - l1);
    GAMT = 0.0;
    HT = 0.0;
    GAMS = 0.0;
    HML = 0.0;
    HS = 0.0;
    T0 = 300.0;
    BVF = 0.01;
    hfactor = 1.0;
    depth = 10000.0;
    width = 15000.0;
    nu1 = hfactor * 1.0E-2; nu2 = hfactor * 1.0E-2;
    nu3 = hfactor * 1.0E-2; nu4 = hfactor * 1.0E-2;
    applyLateralRL = true;
    applyTopRL = true;
    aC = 5000.0;
    lC = 4000.0;
    hC = 10.0;
    mtnh = [int2str(hC) 'm'];
    hfilt = '';
    u0 = 10.0;
    uj = 16.822;
    b = 1.386;
elseif strcmp(TestCase,'ClassicalSchar') == true
    zH = 35000.0;
    %l1 = -1.0E4 * 2.0 * pi;
    %l2 = 1.0E4 * 2.0 * pi;
    l1 = -6.0E4;
    l2 = 6.0E4;
    L = abs(l2 - l1);
    GAMT = 0.0;
    HT = 0.0;
    GAMS = 0.0;
    HML = 0.0;
    HS = 0.0;
    T0 = 300.0;
    BVF = 0.01;
    depth = 10000.0;
    width = 15000.0;
    hfactor = 1.0;
    nu1 = hfactor * 1.0E-2; nu2 = hfactor * 1.0E-2;
    nu3 = hfactor * 1.0E-2; nu4 = hfactor * 1.0E-2;
    applyLateralRL = true;
    applyTopRL = true;
    aC = 5000.0;
    lC = 4000.0;
    hC = 100.0;
    mtnh = [int2str(hC) 'm'];
    hfilt = '';
    u0 = 10.0;
    uj = 0.0;
    b = 0.0;
elseif strcmp(TestCase,'AndesMtn') == true
    zH = 40000.0;
    l1 = -1.0E5 * 2.0 * pi;
    l2 = 1.0E5 * 2.0 * pi;
    L = abs(l2 - l1);
    GAMT = -0.0065;
    HT = 11000.0;
    GAMS = 0.001;
    HML = 9000.0;
    HS = 20000.0;
    T0 = 300.0;
    BVF = 0.0;
    hfactor = 1.0;
    depth = 15000.0;
    width = 101000.0;
    nu1 = hfactor * 1.0E-2; nu2 = hfactor * 1.0E-2;
    nu3 = hfactor * 1.0E-2; nu4 = hfactor * 1.0E-2;
    applyLateralRL = true;
    applyTopRL = true;
    aC = 5000.0;
    lC = 4000.0;
    hC = 100.0;
    mtnh = [int2str(hC) 'm'];
    hfilt = '100m';
    u0 = 10.0;
    uj = 16.822;
    b = 1.386;
end

%% Set up physical parameters for basic state(taken from Tempest defaults)
BS = struct('gam',gam,'Rd',Rd,'cp',cp,'cv',cv,'GAMT',GAMT,'HT',HT,'GAMS', ...
            GAMS,'HML',HML,'HS',HS,'ga',ga,'p0',p0,'T0',T0,'BVF',BVF);

%% Set up the jet and mountain profile parameters
UJ = struct('u0',u0,'uj',uj,'b',b,'ga',ga);
DS = struct('z0',z0,'zH',zH,'l1',l1,'l2',l2,'L',L,'aC',aC,'lC',lC,'hC',hC,'hfilt',hfilt);

%% Set up the Rayleigh Layer with a coefficient one order of magnitude less than the order of the wave field
RAY = struct('depth',depth,'width',width,'nu1',nu1,'nu2',nu2,'nu3',nu3,'nu4',nu4);

%% Compute coarse and fine matrices and RHS vectors
tic;
%% Compute the initialization and grid
[REFS, ~] = computeGridRefState_LogPLogTh(DS, BS, UJ, RAY, TestCase, NX, NZ, applyTopRL, applyLateralRL);

%% Get the boundary conditions
[SOL,sysDex] = GetAdjust4CBC(REFS, BC, NX, NZ, OPS);

%% Compute the LHS coefficient matrix and force vector for the test case
[LD, ~] = ...
computeCoeffMatrixForce_LogPLogTh(BS, RAY, REFS);

%% Compute coupled multipoint BC by adjusting columns of LD
ubdex = 1:NZ:(OPS - NZ + 1);
wbdex = ubdex + iW*OPS;
dhdx = spdiags((REFS.DZT(1,:))', 0, NX, NX);
% Apply column adjustment for the multipoint coupled BC
LD(:,ubdex) = LD(:,ubdex) + LD(:,wbdex) * dhdx;
% Compute RHS scaling
WBC = REFS.DZT(1,:) .* REFS.ujref(1,:);

%% Solve the system by letting matlab \ do its thing...
%
disp('Solve by direct Cholesky coarse and ALSQR fine.');
tic
spparms('spumoni',2);
A = LD(sysDex,sysDex);
b = -LD(:,wbdex) * WBC'; clear LD FF;
% Solve the symmetric normal equations
AN = A' * A;
bN = A' * b(sysDex); clear A b;
toc; disp('Compute coarse coefficient matrix... DONE!');
%% Solve the coarse residual system by direct method Cholesky decomposition
%solc = AN \ bN; clear AN;
[solc, cholParms] = cholmod2(AN, bN); clear AN;
%disp(cholParms);
SOL(sysDex) = solc; clear solc;
% Set the boundary condition
SOL(wbdex) = REFS.DZT(1,:)' .* (REFS.ujref(1,:)' + SOL(ubdex));

%% Unpack the coarse solution and interpolate up to fine
uxz = reshape(SOL((1:OPS)),NZ,NX);
wxz = reshape(SOL((1:OPS) + iW * OPS),NZ,NX);
pxz = reshape(SOL((1:OPS) + iP * OPS),NZ,NX);
txz = reshape(SOL((1:OPS) + iT * OPS),NZ,NX);
%%
toc; disp('Direct solve on the coarsest mesh and save data... DONE!');
%% Compute a sequence of grids all the way to 100 m resolution
%NXF = [256 384 512 720];
%NZF = [192 256 360 360];
NXF = [256 512];
NZF = [128 256];
OPSF = NXF .* NZF;

%% Generate the fine grids and save the coefficient matrices
REFSC = REFS;
tic;
newMeshes = true;
if newMeshes
    for nn=1:length(NXF)
        [REFS, DOPS] = computeGridRefState_LogPLogTh(DS, BS, UJ, RAY, TestCase, NXF(nn), NZF(nn), applyTopRL, applyLateralRL);
        [SOLF,sysDexF] = GetAdjust4CBC(REFS, BC, NXF(nn), NZF(nn), OPSF(nn));

        % Assemble the LHS operator
        ZSPR = sparse(OPSF(nn),OPSF(nn));
        LD = sparse([DOPS.LD11 DOPS.LD12 DOPS.LD13 ZSPR;      ...
              ZSPR      DOPS.LD22 DOPS.LD23 DOPS.LD24; ...
              DOPS.LD31 DOPS.LD32 DOPS.LD33 ZSPR;      ...
              ZSPR      DOPS.LD42 ZSPR      DOPS.LD44]);
        clear DOPS;
        %% Compute coupled multipoint BC by adjusting columns of LD
        ubdex = 1:NZF(nn):(OPSF(nn) - NZF(nn) + 1);
        wbdex = ubdex + iW*OPSF(nn);
        dhdx = spdiags((REFS.DZT(1,:))', 0, NXF(nn), NXF(nn));
        % Apply column adjustment for the multipoint coupled BC
        LD(:,ubdex) = LD(:,ubdex) + LD(:,wbdex) * dhdx;
        % Compute RHS scaling
        WBC = REFS.DZT(1,:) .* REFS.ujref(1,:);

        spparms('spumoni',2);
        AN = LD(sysDexF, sysDexF);
        b = - LD(:,wbdex) * WBC'; clear LD WBC;
        bN = b(sysDexF); clear b;
        save(['fineANbN' int2str(OPSF(nn))], 'REFS', 'AN', 'bN', 'ubdex', 'wbdex', 'sysDexF', 'SOLF', '-v7.3');
        %save('-binary', ['fineANbN' int2str(OPSF(nn))], 'bN', 'sysDexF', 'SOLF'); clear AN bN;
        clear AN bN;
    end
toc; disp('Save fine meshes... DONE!');
end
toc; disp('Using existing mesh archives...');
%}
%% Solve up from the coarsest grid!
tic;
MITER = [10 10 10 10];
IITER = [10 10 10 10];
LITER = [10 10 10 10];
resVisualCheck = false;
for nn=1:length(NXF)
    
    FP = load(['fineANbN' int2str(OPSF(nn))]);
    [xh,~] = herdif(NXF(nn), 1, 0.5*L, true);
    [zlc, ~] = chebdif(NZF(nn), 1);
    zlc = 0.5 * (zlc + 1.0);
    
    % Get the previous coarser model data
    if nn > 1
        load(['fineANbN' int2str(OPSF(nn-1))], 'REFS');
        REFSC = REFS; 
    end
    
    [duxzint, ~, ~, ~] = HerTransLegInterp(REFSC, DS, RAY, real(uxz), NXF(nn), NZF(nn), xh, zlc);
    [dwxzint, ~, ~, ~] = HerTransLegInterp(REFSC, DS, RAY, real(wxz), NXF(nn), NZF(nn), xh, zlc);
    [dpxzint, ~, ~, ~] = HerTransLegInterp(REFSC, DS, RAY, real(pxz), NXF(nn), NZF(nn), xh, zlc);
    [dtxzint, ~, ~, ~] = HerTransLegInterp(REFSC, DS, RAY, real(txz), NXF(nn), NZF(nn), xh, zlc);

    dsol = [reshape(duxzint, OPSF(nn), 1); ...
            reshape(dwxzint, OPSF(nn), 1); ...
            reshape(dpxzint, OPSF(nn), 1); ...
            reshape(dtxzint, OPSF(nn), 1)];
    %
    % Apply iterative solve up every level of mesh
    % Use GMRES to make the initial solution
    %matMul = @(xVec) computeCoeffMatrixMulLogPLogTh(REFSF(nn), FP.DOPSF, xVec, FP.sysDexF);
    sol = gmres(FP.AN, FP.bN, IITER(nn), 1.0E-6, MITER(nn), [], [], dsol(FP.sysDexF));
    
    % Use ALSQR to get some more convergence... why does this work????
    OPTS.LTOL = 1.0E-12;
    OPTS.K = 64;
    OPTS.MAXITL = 20;
    OPTS.MAXITP = 20;
    [dsol,  ~, rvc3] = alsqrJEG(FP.AN, FP.bN, sol, OPTS);
    FP.SOLF(FP.sysDexF) = dsol;
    % Set the boundary condition
    FP.SOLF(FP.wbdex) = FP.REFS.DZT(1,:)' .* (FP.REFS.ujref(1,:)' + FP.SOLF(FP.ubdex));
    disp(rvc3(end,:));
    
    % Compute the residual and check!
    if nn == length(NXF)
        RV = FP.bN - FP.AN * sol;
        SOLR = zeros(4 * OPSF(nn), 1);
        SOLR(FP.sysDexF) = RV; clear RV;
        if resVisualCheck
            SOLF = SOLR;
        end
    end
    
    % Get the solution fields
    uxz = reshape(FP.SOLF((1:OPSF(nn))), NZF(nn), NXF(nn));
    wxz = reshape(FP.SOLF((1:OPSF(nn)) + iW * OPSF(nn)), NZF(nn), NXF(nn));
    pxz = reshape(FP.SOLF((1:OPSF(nn)) + iP * OPSF(nn)), NZF(nn), NXF(nn));
    txz = reshape(FP.SOLF((1:OPSF(nn)) + iT * OPSF(nn)), NZF(nn), NXF(nn));    
end
toc; disp('Run Multigrid Solution (N grids)... DONE!');

%% Plot the solution in the native grids
%{
% NATIVE GRID PLOTS
figure;
subplot(1,2,1); contourf(FP.REFS.XL,FP.REFS.ZTL,real(FP.REFS.ujref + uxz),31); colorbar;
xlim([l1 l2]);
ylim([0.0 zH]);
title('\textsf{$U^{\prime} ~~ (ms^{-1})$}');
subplot(1,2,2); contourf(FP.REFS.XL,FP.REFS.ZTL,real(wxz),31); colorbar;
xlim([l1 l2]);
ylim([0.0 zH]);
title('\textsf{$W^{\prime} ~~ (ms^{-1})$}');

figure;
subplot(1,2,1); contourf(FP.REFS.XL,FP.REFS.ZTL,real(pxz),31); colorbar;
xlim([l1 l2]);
ylim([0.0 zH]);
title('$(\ln p)^{\prime} ~~ (Pa)$');
subplot(1,2,2); contourf(FP.REFS.XL,FP.REFS.ZTL,real(txz),31); colorbar;
xlim([l1 l2]);
ylim([0.0 zH]);
title('$(\ln \theta)^{\prime} ~~ (K)$');
drawnow
%}

%% Interpolate to a nice regular grid using Hermite and Legendre transforms'
%
NXI = 3001;
NZI = 361;
[uxzint, XINT, ZINT, ZLINT] = HerTransLegInterp(FP.REFS, DS, RAY, real(uxz), NXI, NZI, 0, 0);
[wxzint, ~, ~] = HerTransLegInterp(FP.REFS, DS, RAY, real(wxz), NXI, NZI, 0, 0);
[pxzint, ~, ~] = HerTransLegInterp(FP.REFS, DS, RAY, real(pxz), NXI, NZI, 0, 0);
[txzint, ~, ~] = HerTransLegInterp(FP.REFS, DS, RAY, real(txz), NXI, NZI, 0, 0);

XI = l2 * XINT;
ZI = ZINT;
%}

% Use the NCL hotcold colormap
cmap = load('NCLcolormap254.txt');
cmap = cmap(:,1:3);

% INTERPOLATED GRID PLOTS
% Compute the reference state initialization
%
if strcmp(TestCase,'ShearJetSchar') == true
    [lpref, lrref, dlpref, dlrref] = computeBackgroundPressure(BS, zH, ZINT(:,1), ZINT, RAY);
    [ujref,dujref] = computeJetProfile(UJ, BS.p0, lpref, dlpref);
elseif strcmp(TestCase,'ShearJetScharCBVF') == true
    [lpref, lrref, dlpref, dlrref] = computeBackgroundPressureCBVF(BS, ZINT);
    [ujref,dujref] = computeJetProfile(UJ, BS.p0, lpref, dlpref);
elseif strcmp(TestCase,'ClassicalSchar') == true
    [lpref, lrref, dlpref, dlrref] = computeBackgroundPressureCBVF(BS, ZINT);
    [ujref, ~] = computeJetProfileUniform(UJ, lpref);
elseif strcmp(TestCase,'AndesMtn') == true
    [lpref, lrref, dlpref, dlrref] = computeBackgroundPressure(BS, zH, ZINT(:,1), ZINT, RAY);
    [ujref,dujref] = computeJetProfile(UJ, BS.p0, lpref, dlpref);
end
%}

%%
figure;
colormap(cmap);
contourf(1.0E-3 * XI,1.0E-3 * ZI,uxzint,31); colorbar; grid on; cm = caxis;
%contourf(1.0E-3 * XI,1.0E-3 * ZI,ujref,31); colorbar; grid on; cm = caxis;
hold on; area(1.0E-3 * XI(1,:),1.0E-3 * ZI(1,:),'FaceColor','k'); hold off;
caxis(cm);
%xlim(1.0E-3 * [l1 + width l2 - width]);
%ylim(1.0E-3 * [0.0 zH - depth]);
%xlim([-200 300]);
%ylim([0 15]);
disp(['U MAX: ' num2str(max(max(uxz)))]);
disp(['U MIN: ' num2str(min(min(uxz)))]);
title('\textsf{$U^{\prime} ~~ (ms^{-1})$}');
xlabel('Distance (km)');
ylabel('Elevation (km)');
export_fig(['UREferenceSolution' mtnh '.png']);
%
figure;
colormap(cmap);
contourf(1.0E-3 * XI,1.0E-3 * ZI,wxzint,31); colorbar; grid on; cm = caxis;
hold on; area(1.0E-3 * XI(1,:),1.0E-3 * ZI(1,:),'FaceColor','k'); hold off;
caxis(cm);
%xlim(1.0E-3 * [l1 + width l2 - width]);
%ylim(1.0E-3 * [0.0 zH - depth]);
%xlim([-100 100]);
%ylim([0 15]);
title('\textsf{$W^{\prime} ~~ (ms^{-1})$}');
xlabel('Distance (km)');
ylabel('Elevation (km)');
export_fig(['WREferenceSolution' mtnh '.png']);
%
figure;
colormap(cmap);
subplot(1,2,1); contourf(1.0E-3 * XI,1.0E-3 * ZI,pxzint,31); colorbar; grid on;
xlim(1.0E-3 * [l1 + width l2 - width]);
ylim(1.0E-3 * [0.0 zH - depth]);
title('$(\ln p)^{\prime} ~~ (Pa)$');
subplot(1,2,2); contourf(1.0E-3 * XI,1.0E-3 * ZI,txzint,31); colorbar; grid on;
xlim(1.0E-3 * [l1 + width l2 - width]);
ylim(1.0E-3 * [0.0 zH - depth]);
title('$(\ln \theta)^{\prime} ~~ (K)$');
drawnow
%
%% Compute some of the fields needed for instability checks
lpt = FP.REFS.lthref + txz;
pt = exp(lpt);
lp = FP.REFS.lpref + pxz;
p = exp(lp);
P = FP.REFS.pref;
PT = FP.REFS.thref;
rho = p ./ (Rd * pt) .* (p0 * p.^(-1)).^kappa;
R = p ./ (Rd * PT) .* (p0 * P.^(-1)).^kappa;
RT = (rho .* pt) - (R .* PT);

%% Compute Ri, Convective Parameter, and BVF
DDZ_BC = FP.REFS.DDZ_L;
dlrho = FP.REFS.dlrref + FP.REFS.sigma .* (DDZ_BC * (log(rho) - FP.REFS.lrref));
duj = FP.REFS.dujref + FP.REFS.sigma .* (DDZ_BC * real(uxz));

dlpt = FP.REFS.dlthref + FP.REFS.sigma .* (DDZ_BC * real(txz));
temp = p ./ (Rd * rho);
conv = temp .* dlpt;

Ri = ga * dlpt ./ (duj.^2);
RiREF = BS.ga * FP.REFS.dlthref(:,1);
RiREF = RiREF ./ (FP.REFS.dujref(:,1).^2);

xdex = 1:1:NX;
figure;
subplot(1,2,1); semilogx(Ri(:,xdex),1.0E-3*FP.REFS.ZTL(:,xdex),'ks');
hold on;
semilogx([0.25 0.25],[0.0 1.0E5],'k--','LineWidth',2.5);
semilogx(RiREF,1.0E-3*FP.REFS.ZTL(:,1),'r-s','LineWidth',1.5);
hold off;
grid on; grid minor;
xlabel('$Ri$');
ylabel('Height (km)');
title('Richardson Number');
xlim([0.1 1.0E4]);
ylim([0.0 30.0]);

subplot(1,2,2); plot(conv(:,xdex),1.0E-3*FP.REFS.ZTL(:,xdex),'ks');
hold on;
semilogx([0.0 0.0],[0.0 1.0E-3 * zH],'k--','LineWidth',2.5);
hold off;
grid on; grid minor;
xlabel('$S_p$');
%ylabel('Height (km)');
title('Convective Stability');
xlim([-0.01 0.025]);
ylim([0.0 30.0]);

fname = ['RI_CONV_N2_' TestCase num2str(hC)];
drawnow;
export_fig(fname);
%% Compute N and the local Fr number
%{
fig = figure('Position',[0 0 2000 1000]); fig.Color = 'w';
DDZ_BC = REFS.DDZ;
dlpres = REFS.dlpref + REFS.sigma .* (DDZ_BC * real(pxz));
NBVF = (ga .* dlpt);

Lv = 2.5E3;
FR = 2 * pi * abs(REFS.ujref + uxz) ./ (sqrt(NBVF) * Lv);

xdex = 1:1:NX;
plot(FR(:,xdex),1.0E-3*REFS.ZTL(:,xdex),'ks','LineWidth',1.5);
grid on; grid minor;
title('Local Froude Number');
xlabel('$Fr$');
%ylabel('\textsf{Altitude (km)}','Interpreter','latex');
ylim([0.0 25.0]);
%xlim([-1.0E-3 2.0E-3]);
drawnow;

fname = ['FROUDE_' TestCase num2str(hC)];
drawnow;
export_fig(fname);
%}
%% Debug
%{
figure;
subplot(1,2,1); surf(XI,ZI,uxzint); colorbar; xlim([-10000.0 25000.0]); ylim([0.0 2000.0]);
title('U (m/s)'); %zlim([-0.1 0.1]);
subplot(1,2,2); surf(XI,ZI,wxzint); colorbar; xlim([-10000.0 25000.0]); ylim([0.0 2000.0]);
title('W (m/s)');
figure;
subplot(1,2,1); surf(XI,ZI,pxzint); colorbar; xlim([-10000.0 25000.0]); ylim([0.0 2000.0]);
title('$(\ln p)^{\prime}$ (Pa)');
subplot(1,2,2); surf(XI,ZI,txzint); colorbar; xlim([-10000.0 25000.0]); ylim([0.0 2000.0]); zlim([-2.0E-3 2.0E-3]);
title('$(\ln \theta)^{\prime}$ (K)');
%
figure;
subplot(1,2,1); surf(REFSF(nn).XL,1.0E-3*REFSF(nn).ZTL,dlpt); colorbar; xlim([-10000.0 25000.0]); ylim([0.0 2000.0]);
title('$(\ln p)^{\prime}$ (Pa)');
subplot(1,2,2); surf(REFSF(nn).XL,1.0E-3*REFSF(nn).ZTL,duj); colorbar; xlim([-10000.0 25000.0]); ylim([0.0 2000.0]);
title('$(\ln \theta)^{\prime}$ (K)');
drawnow
%}

%% Plot the terrain forcing
%{
subplot(2,2,1); surf(REFS.XL,REFS.ZTL,reshape(FBC((1:OPS)),NZ,NX)); colorbar; xlim([-15000.0 15000.0]); ylim([0.0 1000.0]);
title('Total Horizontal Velocity U (m/s)');
subplot(2,2,2); surf(REFS.XL,REFS.ZTL,reshape(FBC((1:OPS) + OPS),NZ,NX)); colorbar; ylim([0.0 1000.0]);
title('Vertical Velocity W (m/s)');
subplot(2,2,3); surf(REFS.XL,REFS.ZTL,reshape(FBC((1:OPS) + 2*OPS),NZ,NX)); colorbar; ylim([0.0 1000.0]);
title('Perturbation Density (kg/m^3)');
subplot(2,2,4); surf(REFS.XL,REFS.ZTL,reshape(FBC((1:OPS) + 3*OPS),NZ,NX)); colorbar; ylim([0.0 1000.0]);
title('Perturbation Pressure (Pa)');
drawnow
%}

%% Save the data
%
close all;
fileStore = ['/media/jeguerra/DATA/' int2str(NXF(nn)) 'X' int2str(NZF(nn)) 'SpectralReferenceHER_LnP' char(TestCase) int2str(hC) '.mat'];
save(fileStore, '-v7.3');
%}
