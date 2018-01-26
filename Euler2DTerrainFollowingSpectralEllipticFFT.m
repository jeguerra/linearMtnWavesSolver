% Computes the semi-analytical solution to the steady, linearized Euler equations
% in terrain following coordinates using a coordinate transformation from
% XZ to alpha-eta both from -pi to pi. The vertical boundary condition is
% also tranformed in the vertical so that infinity maps to eta = pi. The
% reference state is a standard atmosphere of piece-wise linear temperature
% profiles with a smooth zonal jet given. Pressure and density initialized
% in hydrostatic balance.

clc
clear
close all
%addpath(genpath('MATLAB/'))

%% Create the dimensional XZ grid
NX = 300; % Expansion order matches physical grid
NXO = 80; % Expansion order
NZ = 100; % Expansion order matches physical grid
OPS = NX * NZ;
numVar = 4;

%% Set the test case and global parameters
%TestCase = 'ShearJetSchar'; BC = 0;
%TestCase = 'ShearJetScharCBVF'; BC = 0;
%TestCase = 'ClassicalSchar'; BC = 0;
TestCase = 'AndesMtn'; BC = 0;

z0 = 0.0;
gam = 1.4;
Rd = 287.06;
cp = 1004.5;
cv = cp - Rd;
ga = 9.80616;
p0 = 1.0E5;
if strcmp(TestCase,'ShearJetSchar') == true
    zH = 35000.0;
    l1 = - 1.0E4 * (2.0 * pi);
    l2 = 1.0E4 * (2.0 * pi);
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
    applyLateralRL = false;
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
    l1 = -60000.0;
    l2 = 60000.0;
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
    nu1 = hfactor * 1.0 * 1.0E-2; nu2 = hfactor * 1.0 * 1.0E-2;
    nu3 = hfactor * 1.0 * 1.0E-2; nu4 = hfactor * 1.0 * 1.0E-2;
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
    l1 = -60000.0;
    l2 = 60000.0;
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
    nu3 = hfactor * 1.0 * 1.0E-2; nu4 = hfactor * 1.0E-2;
    applyLateralRL = true;
    applyTopRL = true;
    aC = 5000.0;
    lC = 4000.0;
    hC = 10.0;
    mtnh = [int2str(hC) 'm'];
    hfilt = '';
    u0 = 10.0;
    uj = 0.0;
    b = 0.0;
elseif strcmp(TestCase,'AndesMtn') == true
    zH = 40000.0;
    l1 = - 1.0E5 * (2.0 * pi);
    l2 = 1.0E5 * (2.0 * pi);
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
    width = 100000.0;
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

%% Compute the LHS coefficient matrix and force vector for the test case
[LD,FF,REFS] = computeCoeffMatrixForceFFT(DS, BS, UJ, RAY, TestCase, NX, NZ, applyTopRL, applyLateralRL);

%% Get the boundary conditions
[FFBC,SOL,sysDex] = GetAdjust4CBC(BC,NX,NZ,OPS,FF);

%% Solve the system using the matlab linear solver
%
disp('Solve the raw system with matlab default \.');
tic
spparms('spumoni',2);
A = LD(sysDex,sysDex);
b = FFBC(sysDex,1);
clear LD FF FFBC;
sol = A \ b;
%[V,D] = eig(full(A));
clear A b;
toc
%}

%% Solve the system using residual non-linear line search solver
%{
disp('Solve the system with a La Cruz Raydan Algorithm.');
tic
x0 = 0.0 * FFBC(sysDex,1);
A = LD(sysDex,sysDex);
b = FFBC(sysDex,1);
[sol,rseq] = ResidualMtSolve((A'*A),(A'*b),x0,1.0E-6,100);
clear A b;
toc
%}
%% Solve the system with an iterative solver
%{
tic
A = LD(sysDex,sysDex);%' * LD(sysDex,sysDex);
%b = LD(sysDex,sysDex)' * FFBC(sysDex,1);
b = FFBC(sysDex,1);
disp('Solve the raw system with iterative solver.');
[L,U] = ilu(A,struct('type','ilutp','udiag',1,'droptol',1.0e-2));
sol = gmres(A,b,[],1.0E-4,50,L,U);
toc
%}

% Use the NCL hotcold colormap
cmap = load('NCLcolormap254.txt');
cmap = cmap(:,1:3);

%% Plot the solution frequency space
SOL(sysDex) = sol;
uxz = real(reshape(SOL((1:OPS)),NZ,NX));
whxz = real(reshape(SOL((1:OPS) + OPS),NZ,NX));
rxz = real(reshape(SOL((1:OPS) + 2*OPS),NZ,NX));
pxz = real(reshape(SOL((1:OPS) + 3*OPS),NZ,NX));
%% Convert \hat{w} to w using the reference density profile
wf = sqrt(REFS.rref0) * REFS.rref.^(-0.5);
wxz = wf .* whxz;
%
kdex = find(REFS.KF(1,:) >= 0.0);
rad2len = 1. / (2. * pi);
wlen = rad2len * REFS.KF(:,kdex);
%
fig = figure('Position',[0 0 1800 1200]); fig.Color = 'w';
colormap(cmap);
contourf(wlen,REFS.ZTL(:,kdex),2*uxz(:,kdex),21); colorbar; grid on;
xlim([0.0 0.4E-3]);
ylim([0.0 zH]);
title('Total Horizontal Velocity U (m/s)','FontWeight','normal','Interpreter','latex');
fig.CurrentAxes.FontSize = 24; fig.CurrentAxes.LineWidth = 1.5;

fig = figure('Position',[0 0 1800 1200]); fig.Color = 'w';
contourf(wlen,REFS.ZTL(:,kdex),2*wxz(:,kdex),21); colorbar; grid on;
xlim([0.0 0.4E-3]);
ylim([0.0 zH]);
title('Vertical Velocity W (m/s)','FontWeight','normal','Interpreter','latex');
fig.CurrentAxes.FontSize = 24; fig.CurrentAxes.LineWidth = 1.5;
%
fig = figure('Position',[0 0 1800 1200]); fig.Color = 'w';
colormap(cmap);
subplot(1,2,1); contourf(wlen,REFS.ZTL(:,kdex),2*rxz(:,kdex),21); colorbar; grid on;
xlim([0.0 0.4E-3]);
ylim([0.0 zH]);
title('Perturbation Log Density $(kg/m^3)$','FontWeight','normal','Interpreter','latex');
fig.CurrentAxes.FontSize = 24; fig.CurrentAxes.LineWidth = 1.5;
subplot(1,2,2); contourf(wlen,REFS.ZTL(:,kdex),2*pxz(:,kdex),21); colorbar; grid on;
xlim([0.0 0.4E-3]);
ylim([0.0 zH]);
title('Perturbation Log Pressure (Pa)','FontWeight','normal','Interpreter','latex');
fig.CurrentAxes.FontSize = 24; fig.CurrentAxes.LineWidth = 1.5;
drawnow
%}
%% Plot the solution using the IFFT to recover the solution in physical space
SOL(sysDex) = sol;
uxz = real(ifft(reshape(SOL((1:OPS)),NZ,NX),[],2));
whxz = real(ifft(reshape(SOL((1:OPS) + OPS),NZ,NX),[],2));
rxz = real(ifft(reshape(SOL((1:OPS) + 2*OPS),NZ,NX),[],2));
pxz = real(ifft(reshape(SOL((1:OPS) + 3*OPS),NZ,NX),[],2));
%% Convert \hat{w} to w using the reference density profile
wf = sqrt(REFS.rref0) * REFS.rref.^(-0.5);
wxz = wf .* whxz;
%
fig = figure('Position',[0 0 1800 1200]); fig.Color = 'w';
colormap(cmap);
subplot(1,2,1); contourf(REFS.XL,REFS.ZTL,(REFS.ujref + uxz),21); colorbar; 
xlim([l1 l2]);
ylim([0.0 zH]);
disp(['U MAX: ' num2str(max(max(uxz)))]);
disp(['U MIN: ' num2str(min(min(uxz)))]);
title('Total Horizontal Velocity U (m/s)');
subplot(1,2,2); contourf(REFS.XL,REFS.ZTL,wxz,21); colorbar;
xlim([l1 l2]);
ylim([0.0 zH]);
title('Vertical Velocity W (m/s)');
%
fig = figure('Position',[0 0 1800 1200]); fig.Color = 'w';
colormap(cmap);
subplot(1,2,1); contourf(REFS.XL,REFS.ZTL,rxz,21); colorbar;
xlim([l1 l2]);
ylim([0.0 zH]);
title('Perturbation Log Density (kg/m^3)');
subplot(1,2,2); contourf(REFS.XL,REFS.ZTL,pxz,21); colorbar;
xlim([l1 l2]);
ylim([0.0 zH]);
title('Perturbation Log Pressure (Pa)');
drawnow
%}

%% Interpolate to a regular grid using Hermite and Legendre transforms'
%
NXI = 600;
NZI = 300;
[uxzint, XINT, ZINT, ZLINT] = HerTransLegInterp(REFS, DS, RAY, real(uxz), NXI, NZI, 0, 0);
[wxzint, ~, ~] = HerTransLegInterp(REFS, DS, RAY, real(wxz), NXI, NZI, 0, 0);
[rxzint, ~, ~] = HerTransLegInterp(REFS, DS, RAY, real(rxz), NXI, NZI, 0, 0);
[pxzint, ~, ~] = HerTransLegInterp(REFS, DS, RAY, real(pxz), NXI, NZI, 0, 0);

XI = l2 * XINT;
ZI = ZINT;
%} 

% Use the NCL hotcold colormap
cmap = load('NCLcolormap254.txt');
cmap = cmap(:,1:3);

% INTERPOLATED GRID PLOTS
%
width = 0.0;
depth = 0.0;
% Compute the reference state initialization
%
if strcmp(TestCase,'ShearJetSchar') == true
    [lpref, lrref, dlpref, dlrref] = computeBackgroundPressure(BS, zH, ZINT(:,1), ZINT, RAY);
    %[ujref,dujref] = computeJetProfile(UJ, BS.p0, lpref, dlpref);
    [lprefU,~,dlprefU,~] = computeBackgroundPressure(BS, zH, ZINT(:,1), ZLINT, RAY);
    [ujref,dujref] = computeJetProfile(UJ, BS.p0, lprefU, dlprefU);
elseif strcmp(TestCase,'ShearJetScharCBVF') == true
    [lpref, lrref, dlpref, dlrref] = computeBackgroundPressureCBVF(BS, ZINT);
    [lprefU,~,dlprefU,~] = computeBackgroundPressureCBVF(BS, ZLINT);
    [ujref,dujref] = computeJetProfile(UJ, BS.p0, lprefU, dlprefU);
elseif strcmp(TestCase,'ClassicalSchar') == true
    [lpref, lrref, dlpref, dlrref] = computeBackgroundPressureCBVF(BS, ZINT);
    [ujref, ~] = computeJetProfileUniform(UJ, lpref);
elseif strcmp(TestCase,'AndesMtn') == true
    [lpref, lrref, dlpref, dlrref] = computeBackgroundPressure(BS, zH, ZINT(:,1), ZINT, RAY);
    [lprefU,~,dlprefU,~] = computeBackgroundPressure(BS, zH, ZINT(:,1), ZLINT, RAY);
    [ujref,dujref] = computeJetProfile(UJ, BS.p0, lprefU, dlprefU);
end
%}
dlthref = 1.0 / BS.gam * dlpref - dlrref;

fig = figure('Position',[0 0 1800 1200]); fig.Color = 'w';
colormap(cmap);
contourf(1.0E-3 * XI,1.0E-3 * ZI,ujref + uxzint,31); colorbar; grid on;
%hold on; area(1.0E-3 * XI(1,:),1.0E-3 * ZI(1,:),'FaceColor','k'); hold off;
xlim(1.0E-3 * [l1 + width l2 - width]);
ylim(1.0E-3 * [0.0 zH - depth]);
disp(['U MAX: ' num2str(max(max(uxz)))]);
disp(['U MIN: ' num2str(min(min(uxz)))]);
title('Total Horizontal Velocity U $(m~s^{-1})$','FontWeight','normal','Interpreter','latex');
xlabel('Distance (km)');
ylabel('Elevation (km)');
fig.CurrentAxes.FontSize = 30; fig.CurrentAxes.LineWidth = 1.5;
screen2png(['UREferenceSolution' mtnh '.png']);
fig = figure('Position',[0 0 1800 1200]); fig.Color = 'w';
colormap(cmap);
contourf(1.0E-3 * XI,1.0E-3 * ZI,wxzint,31); colorbar; grid on;
%hold on; area(1.0E-3 * XI(1,:),1.0E-3 * ZI(1,:),'FaceColor','k'); hold off;
xlim(1.0E-3 * [l1 + width l2 - width]);
ylim(1.0E-3 * [0.0 zH - depth]);
title('Vertical Velocity W $(m~s^{-1})$','FontWeight','normal','Interpreter','latex');
xlabel('Distance (km)');
fig.CurrentAxes.FontSize = 30; fig.CurrentAxes.LineWidth = 1.5;
screen2png(['WREferenceSolution_LnP' mtnh '.png']);
fig = figure('Position',[0 0 1600 1200]); fig.Color = 'w';
colormap(cmap);
subplot(1,2,1); contourf(1.0E-3 * XI,1.0E-3 * ZI,rxzint,31); colorbar; grid on;
xlim(1.0E-3 * [l1 + width l2 - width]);
ylim(1.0E-3 * [0.0 zH - depth]);
title('Perturbation Log Density $(kg m^{-3})$','FontWeight','normal','Interpreter','latex');
fig.CurrentAxes.FontSize = 30; fig.CurrentAxes.LineWidth = 1.5;
subplot(1,2,2); contourf(1.0E-3 * XI,1.0E-3 * ZI,pxzint,31); colorbar; grid on;
xlim(1.0E-3 * [l1 + width l2 - width]);
ylim(1.0E-3 * [0.0 zH - depth]);
title('Perturbation Log Pressure (Pa)','FontWeight','normal','Interpreter','latex');
fig.CurrentAxes.FontSize = 30; fig.CurrentAxes.LineWidth = 1.5;
drawnow
%}
%% Compute the local Ri number and plot ...
%
DDZ_BC = REFS.DDZ;
dlrho = REFS.dlrref + REFS.sigma .* (DDZ_BC * real(rxz));
duj = REFS.dujref + REFS.sigma .* (DDZ_BC * real(uxz));
Ri = -ga * dlrho ./ (duj.^2);

RiREF = -BS.ga * REFS.dlrref(:,1);
RiREF = RiREF ./ (REFS.dujref(:,1).^2);

xdex = 1:1:NX;
fig = figure('Position',[0 0 800 1200]); fig.Color = 'w';
semilogx(Ri(:,xdex),1.0E-3*REFS.ZTL(:,xdex),'ks','LineWidth',1.5);
hold on;
semilogx([0.25 0.25],[0.0 1.0E5],'k--','LineWidth',1.5);
semilogx(RiREF,1.0E-3*REFS.ZTL(:,1),'r-s','LineWidth',1.5);
hold off;
grid on;
xlabel('Ri','FontSize',30);
%ylabel('Altitude (km)','FontSize',30);
ylim([0.0 1.0E-3*zH]);
xlim([0.1 1.0E4]);
fig.CurrentAxes.FontSize = 30; fig.CurrentAxes.LineWidth = 1.5;
drawnow;

pt = mtit([mtnh ' Mountain'],'FontSize',36,'FontWeight','normal','Interpreter','tex');

dirname = '../ShearJetSchar/';
fname = [dirname 'RI_TEST_' TestCase num2str(hC)];
drawnow;
screen2png(fname);

%% Compute the local convective stability parameter and plot...
%
DDZ_BC = REFS.DDZ;
dlpres = REFS.dlpref + REFS.sigma .* (DDZ_BC * real(pxz));
rho = exp(lrho);
dlpt = 1 / gam * dlpres - dlrho;
temp = p ./ (Rd * rho);
conv = temp .* dlpt;

xdex = 1:1:NX;
fig = figure('Position',[0 0 800 1200]); fig.Color = 'w';
plot(conv(:,xdex),1.0E-3*REFS.ZTL(:,xdex),'ks','LineWidth',1.5);
grid on;
xlabel('$\frac{T}{\theta} \frac{d \theta}{d z}$','FontSize',30,'Interpreter','latex');
%ylabel('Altitude (km)','FontSize',30);
ylim([0.0 1.0E-3*zH]);
%xlim([0.1 1.0E3]);
fig.CurrentAxes.FontSize = 30; fig.CurrentAxes.LineWidth = 1.5;
drawnow;

pt = mtit([mtnh ' Mountain'],'FontSize',36,'FontWeight','normal','Interpreter','tex');

dirname = '../ShearJetSchar/';
fname = [dirname 'CONV_TEST_' TestCase num2str(hC)];
drawnow;
screen2png(fname);

%% Compute the local and reference N
%
DDZ_BC = REFS.DDZ;
dlpres = REFS.dlpref + REFS.sigma .* (DDZ_BC * real(pxz));
rho = exp(lrho);
dlpt = 1 / gam * dlpres - dlrho;
NBVF = sqrt(ga .* dlpt);

NBVF_REF = sqrt(ga * (1 / gam * REFS.dlpref - REFS.dlrref));

xdex = 1:1:NX;
fig = figure('Position',[0 0 800 1200]); fig.Color = 'w';
plot(NBVF(:,xdex),1.0E-3*REFS.ZTL(:,xdex),'ks','LineWidth',1.5); hold on;
plot(NBVF_REF(:,1),1.0E-3*REFS.ZTL(:,1),'ro-','LineWidth',1.5); hold off;
grid on;
xlabel('$\mathcal{N}$','FontSize',30,'Interpreter','latex');
%ylabel('Altitude (km)','FontSize',30);
ylim([0.0 1.0E-3*zH]);
%xlim([0.1 1.0E3]);
fig.CurrentAxes.FontSize = 30; fig.CurrentAxes.LineWidth = 1.5;
drawnow;

pt = mtit([mtnh ' Mountain'],'FontSize',36,'FontWeight','normal','Interpreter','tex');

dirname = '../ShearJetSchar/';
fname = [dirname 'NBVF_TEST_' TestCase num2str(hC)];
drawnow;
screen2png(fname);

%{
subplot(2,2,1); surf(REFS.XL,REFS.ZTL,uxz); colorbar; xlim([-20000.0 20000.0]); ylim([0.0 15000.0]);
title('Total Horizontal Velocity U (m/s)');
subplot(2,2,2); surf(REFS.XL,REFS.ZTL,wxz); colorbar; xlim([-20000.0 20000.0]); ylim([0.0 15000.0]);
title('Vertical Velocity W (m/s)');
subplot(2,2,3); surf(REFS.XL,REFS.ZTL,exp(rxz)); colorbar; xlim([-20000.0 20000.0]); ylim([0.0 15000.0]);
title('Perturbation Density (kg/m^3)');
subplot(2,2,4); surf(REFS.XL,REFS.ZTL,exp(pxz)); colorbar; xlim([-20000.0 20000.0]); ylim([0.0 15000.0]);
title('Perturbation Pressure (Pa)');
drawnow
%}

%% Debug
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
%{
close all
fileStore = [int2str(NX) 'X' int2str(NZ) 'SpectralReferenceFFT' int2str(hC) '.mat'];
save(fileStore);
%}