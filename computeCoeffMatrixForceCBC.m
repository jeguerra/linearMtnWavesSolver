function [LD,FF,REFS] = computeCoeffMatrixForceCBC(DS, BS, UJ, RAY, TestCase, NX, NZ, applyLateralRL)
    %% Compute the Hermite and Legendre points and derivatives for this grid
    [xh,DDX_H] = herdif(NX, 1, 0.5 * DS.L);
    % fix the diagonal
    DDX_H(1:NX+1:end) = 1.0E-8 * ones(NX,1);
    
    [zlc, ~] = chebdif(NZ, 1);
    %DDZ_L = (1.0 / DS.zH) * DDZ_L;
    zl = DS.zH * 0.5 * (zlc + 1.0);
    zlc = 0.5 * (zlc + 1.0);
    DDZ_L = (1.0 / DS.zH) * poldif(zlc, 1);
       
    %% Compute the terrain and derivatives
    [ht,dhdx] = computeTopoDerivative(TestCase,xh,DS);
    
    %% XZ grid for Legendre nodes in the vertical
    [HTZL,~] = meshgrid(ht,zl);
    [XL,ZL] = meshgrid(xh,zl);
  
    %% Gal-Chen, Sommerville coordinate
    %{
    dzdh = (1.0 - ZL / DS.zH);
    dxidz = (DS.zH - HTZL);
    sigma = DS.zH * dxidz.^(-1);
    %}
    %% 8th Order Guellrich coordinate
    %{
    eta = ZL / DS.zH;
    ang = 0.5 * pi * eta;
    AR = 0.1;
    power = 8;
    fxi = cos(ang).^power + AR * eta;
    dfdxi = -(0.5 * power) * pi * sin(ang) .* cos(ang).^(power-1) + AR;
    dzdh = (1.0 - eta) .* fxi;
    dxidz = DS.zH + HTZL .* ((1.0 - eta) .* dfdxi - fxi);
    sigma = DS.zH * dxidz.^(-1);
    %}
    %% High Order Improved Guellrich coordinate
    % 3 parameter function
    eta = ZL / DS.zH;
    ang = 0.5 * pi * eta;
    AR = 1.0E-3;
    p = 20;
    q = 5;
    fxi = exp(-p/q * eta) .* cos(ang).^p + AR * eta .* (1.0 - eta);
    dfdxi = -p/q * exp(-p/q * eta) .* cos(ang).^p ...
            -(0.5 * p) * pi * exp(-p/q * eta) .* sin(ang) .* cos(ang).^(p-1) ...
            -AR * (1.0 - 2 * eta);
    dzdh = fxi;
    dxidz = DS.zH + HTZL .* (dfdxi - fxi);
    sigma = DS.zH * dxidz.^(-1);
    %}
    % Adjust Z with terrain following coords
    ZTL = (dzdh .* HTZL) + ZL;
    % Make the global array of terrain derivative features
    DZT = ZTL;
    for rr=1:size(DZT,1)
        DZT(rr,:) = dhdx;
    end

    %% Compute the reference state initialization
    if strcmp(TestCase,'ShearJetSchar') == true
        [lpref,lrref,dlpref,dlrref] = computeBackgroundPressure(BS, DS.zH, zl, ZTL);
        [ujref,dujref] = computeJetProfile(UJ, BS.p0, lpref, dlpref);
    elseif strcmp(TestCase,'ClassicalSchar') == true
        [lpref,lrref,dlpref,dlrref] = computeBackgroundPressureCBVF(BS, ZTL, DDZ_L);
        [ujref,dujref] = computeJetProfileUniform(UJ, lpref);
    elseif strcmp(TestCase,'NonhydroMtn') == true
        [lpref,lrref,dlpref,dlrref] = computeBackgroundPressureCBVF(BS, ZTL, DDZ_L);
        [ujref,dujref] = computeJetProfileUniform(UJ, lpref);
    end
    
    %% Compute the vertical profiles of density and pressure
    pref = exp(lpref);
    rref = exp(lrref);
    rref0 = max(max(rref));
    rsc = sqrt(rref0) * rref.^(-0.5);

%{
    %% Plot background fields including mean Ri number
    fig = figure('Position',[0 0 1600 1200]); fig.Color = 'w';
    subplot(2,2,1);
    plot(ujref(:,1),1.0E-3*zl,'k-s','LineWidth',1.5); grid on;
    xlabel('Speed (m s^{-1})','FontSize',30);
    ylabel('Altitude (km)','FontSize',30);
    ylim([0.0 30.0]);
    fig.CurrentAxes.FontSize = 30; fig.CurrentAxes.LineWidth = 1.5;
    drawnow;
    
    subplot(2,2,2);
    plot(pref(:,1) ./ (rref(:,1) * BS.Rd),1.0E-3*zl,'k-s','LineWidth',1.5); grid on;
    %title('Temperature Profile','FontSize',30);
    xlabel('Temperature (K)','FontSize',30);
    ylabel('Altitude (km)','FontSize',30);
    ylim([0.0 30.0]);
    fig.CurrentAxes.FontSize = 30; fig.CurrentAxes.LineWidth = 1.5;
    drawnow;
    
    subplot(2,2,3);
    plot(0.01*pref(:,1),1.0E-3*zl,'k-s','LineWidth',1.5); grid on;
    xlabel('Pressure (hPa)','FontSize',30);
    ylabel('Altitude (km)','FontSize',30);
    ylim([0.0 30.0]);
    fig.CurrentAxes.FontSize = 30; fig.CurrentAxes.LineWidth = 1.5;
    drawnow;
    
    subplot(2,2,4);
    plot(rref(:,1),1.0E-3*zl,'k-s','LineWidth',1.5); grid on;
    xlabel('Density (kg m^{-3})','FontSize',30);
    ylabel('Altitude (km)','FontSize',30);
    ylim([0.0 30.0]);
    fig.CurrentAxes.FontSize = 30; fig.CurrentAxes.LineWidth = 1.5;
    drawnow;
    dirname = '../ShearJetSchar/';
    fname = [dirname 'BACKGROUND_PROFILES'];
    screen2png(fname);
    
    fig = figure('Position',[0 0 1200 1200]); fig.Color = 'w';
    Ri = -BS.ga * dlrref(:,1);
    Ri = Ri ./ (dujref(:,1).^2);
    semilogx(Ri,1.0E-3*zl,'k-s','LineWidth',1.5); grid on;
    xlabel('Ri','FontSize',30);
    ylabel('Altitude (km)','FontSize',30);
    ylim([0.0 20.0]);
    xlim([0.1 1.0E4]);
    fig.CurrentAxes.FontSize = 30; fig.CurrentAxes.LineWidth = 1.5;
    drawnow;
    dirname = '../ShearJetSchar/';
    fname = [dirname 'RICHARDSON_NUMBER'];
    screen2png(fname);
    pause
%}
    
    REFS = struct('ujref',ujref,'dujref',dujref, ...
        'lpref',lpref,'dlpref',dlpref,'lrref',lrref,'dlrref',dlrref, ...
        'pref',pref,'rref',rref,'XL',XL,'ZTL',ZTL,'DZT',DZT,'DDZ',DDZ_L, ...
        'sig',sigma,'NX',NX,'NZ',NZ,'TestCase',TestCase,'rref0',rref0);
    
    %% Compute the Rayleigh field
    rayField = computeRayleighXZ(DS,1.0,RAY.depth,RAY.width,XL,ZL,applyLateralRL);
    RL = reshape(rayField,NX*NZ,1);

    %% Unwrap the derivative matrices into operators onto a state 1D vector
    % Compute the vertical derivatives operator (Legendre expansion)
    DDZ_OP = zeros(NX*NZ);
    for cc=1:NX
        ddex = (1:NZ) + (cc - 1) * NZ;
        DDZ_OP(ddex,ddex) = DDZ_L;
    end
    DDZ_OP = sparse(DDZ_OP);

    % Compute the horizontal derivatives operator (Hermite expansion)
    DDX_OP = zeros(NX*NZ);
    for rr=1:NZ
        ddex = (1:NZ:NX*NZ) + (rr - 1);
        DDX_OP(ddex,ddex) = DDX_H;
    end
    DDX_OP = sparse(DDX_OP);

    %% Assemble the block global operator L
    OPS = NX*NZ;
    U0 = spdiags(reshape(ujref,OPS,1), 0, OPS, OPS);
    DU0DZ = spdiags(reshape(dujref,OPS,1), 0, OPS, OPS);
    DLPDZ = spdiags(reshape(dlpref,OPS,1), 0, OPS, OPS);
    DLRDZ = spdiags(reshape(dlrref,OPS,1), 0, OPS, OPS);
    POR = spdiags(reshape(pref ./ rref,OPS,1), 0,  OPS, OPS);
    RSC = spdiags(reshape(rsc,OPS,1), 0, OPS, OPS);
    U0DX = U0 * DDX_OP;
    unit = spdiags(ones(OPS,1),0, OPS, OPS);
    SIGMA = spdiags(reshape(sigma,OPS,1), 0, OPS, OPS);

    % Horizontal momentum LHS
    L11 = U0DX;
    L12 = sparse(OPS,OPS);
    L13 = sparse(OPS,OPS);
    L14 = POR * DDX_OP;
    % Vertical momentum LHS
    L21 = sparse(OPS,OPS);
    L22 = RSC * U0DX;
    L23 = sparse(OPS,OPS);
    L24 = POR * SIGMA * DDZ_OP;
    % Continuity LHS
    L31 = DDX_OP;
    L32 = SIGMA * RSC * DDZ_OP;
    L33 = U0DX;
    L34 = sparse(OPS,OPS);
    % Thermodynamic LHS
    L41 = sparse(OPS,OPS);
    L42 = sparse(OPS,OPS);
    L43 = -BS.gam * U0DX;
    L44 = U0DX;

    %% Assemble the algebraic part (Rayleigh layer on the diagonal)
    % Horizontal momentum LHS
    B11 = sparse(OPS,OPS) + RAY.nu1 * spdiags(RL,0, OPS, OPS);
    B12 = SIGMA * RSC * DU0DZ;
    B13 = sparse(OPS,OPS);
    B14 = sparse(OPS,OPS);
    % Vertical momentum LHS
    B21 = sparse(OPS,OPS);
    B22 = sparse(OPS,OPS) + RAY.nu2 * RSC * spdiags(RL,0, OPS, OPS);
    B23 = BS.ga * unit;
    B24 = -BS.ga * unit;
    % Continuity LHS
    B31 = sparse(OPS,OPS);
    %B32 = sparse(OPS,OPS);
    B32 = SIGMA * 0.5 * RSC * DLRDZ;
    B33 = sparse(OPS,OPS) + RAY.nu3 * spdiags(RL,0, OPS, OPS);
    B34 = sparse(OPS,OPS);
    % Thermodynamic LHS
    B41 = sparse(OPS,OPS);
    B42 = SIGMA * RSC * (DLPDZ - BS.gam * DLRDZ);
    B43 = sparse(OPS,OPS) - BS.gam * B33;
    B44 = sparse(OPS,OPS) + RAY.nu4 * spdiags(RL,0, OPS, OPS);

    %% Adjust the operator for the coupled BC
    bdex = 1:NZ:OPS;
    GPHI = spdiags(DZT(1,:)', 0, NX, NX);
    RSBC = spdiags(rsc(1,:)', 0, NX, NX);
    
    % THE BOUNDARY CONDITION MUST BE ON W AND LN(RHO)...
    %B21(bdex,bdex) = (-GPHI);
    %B22(bdex,bdex) = speye(NX,NX);
    
    B31(bdex,bdex) = (-GPHI);
    %B32(bdex,bdex) = speye(NX,NX);
    B32(bdex,bdex) = RSBC;
    
    %% Assemble the left hand side operator
    LD11 = L11 + B11;
    LD12 = L12 + B12;
    LD13 = L13 + B13;
    LD14 = L14 + B14;

    LD21 = L21 + B21;
    LD22 = L22 + B22;
    LD23 = L23 + B23;
    LD24 = L24 + B24;

    LD31 = L31 + B31;
    LD32 = L32 + B32;
    LD33 = L33 + B33;
    LD34 = L34 + B34;

    LD41 = L41 + B41;
    LD42 = L42 + B42;
    LD43 = L43 + B43;
    LD44 = L44 + B44;

    LD = [LD11 LD12 LD13 LD14 ; ...
          LD21 LD22 LD23 LD24 ; ...
          LD31 LD32 LD33 LD34 ; ...
          LD41 LD42 LD43 LD44];

    %% Assemble the force vector
    U0 = reshape(ujref,OPS,1);
    DU0DZ = reshape(dujref,OPS,1);
    DLPDZ = reshape(dlpref,OPS,1);
    DLRDZ = reshape(dlrref,OPS,1);
    h_hat = 1.0 / DS.L * reshape(dzdh .* DZT,OPS,1);
    SIGMA = reshape(sigma,OPS,1);
    
    F11 = h_hat .* (SIGMA .* U0 .* DU0DZ - BS.ga);
    F21 = zeros(OPS,1);
    F31 = h_hat .* SIGMA .* (U0 .* DLRDZ + DU0DZ);
    F41 = U0 .* h_hat .* SIGMA .* (DLPDZ - BS.gam * DLRDZ);
    
    %% Adjust the force vector for the coupled BC
    %F21(bdex) = (ujref(1,:) .* DZT(1,:))';
    F31(bdex) = (ujref(1,:) .* DZT(1,:))';
    
    FF = [F11 ; F21 ; F31 ; F41];
end