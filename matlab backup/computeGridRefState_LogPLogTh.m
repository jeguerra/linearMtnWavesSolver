function [REFS, DOPS] = computeGridRefState_LogPLogTh(DS, BS, UJ, RAY, TestCase, NX, NZ, applyTopRL, applyLateralRL)
    %% Compute the Hermite and Legendre points and derivatives for this grid
    % Set the boundary indices and operator dimension
    OPS = NX*NZ;
    
    % Set the domain scale
    dscale = 0.5 * DS.L;
    %
    %% Get the Hermite Function derivative matrix and grid (ALTERNATE METHOD)
    % compute nodes/weights forward transform
    [xo,~,w] = hegs(NX);
    b = max(xo) / dscale;
    xh = (1.0 / b) * xo;

    W = spdiags(w, 0, NX, NX);

    [~, HT] = hefunm(NX-1, xo);
    [~, HTD] = hefunm(NX, xo);
    
    %% Compute the coefficients of spectral derivative in matrix form
    SDIFF = zeros(NX+1,NX);
    SDIFF(1,2) = sqrt(0.5);
    SDIFF(NX + 1,NX) = -sqrt(NX * 0.5);
    SDIFF(NX,NX-1) = -sqrt((NX - 1) * 0.5);

    for cc = NX-2:-1:1
        SDIFF(cc+1,cc+2) = sqrt((cc + 1) * 0.5);
        SDIFF(cc+1,cc) = -sqrt(cc * 0.5);
    end

    % Hermite function spectral transform in matrix form
    STR_H = HT * W;
    % Hermite function spatial derivative based on spectral differentiation
    DDX_H = b * HTD' * SDIFF * STR_H;
    %DDX2_H = b * HTD' * SDIFF * SDIFF * STR_H;
    
    %% Get the Legendre nodes and compute the vertical derivative matrix
    %{
    [zlc,w]=legslb(NZ);
    zl = DS.zH * (0.5 * (zlc + 1.0));
    W = spdiags(w, 0, NZ, NZ);
    s = [(0:NZ-2)'+ 0.5;(NZ-1)/2];
    S = spdiags(s, 0, NZ, NZ);

    [~, HTD] = lepolym(NZ-1, zlc);
    
    %% Compute the coefficients of spectral derivative in matrix form
    NM = NZ;
    SDIFF = zeros(NM,NM);
    SDIFF(NM,NM) = 0.0;
    SDIFF(NM-1,NM) = 2 * NM - 1;

    k = NM - 1;
    for kk = NM-2:-1:1
        A = 2 * k - 3;
        B = 2 * k + 1;
        SDIFF(kk,:) = A / B * SDIFF(kk+2,:);
        SDIFF(kk,kk+1) = A;

        k = k - 1;
    end

    % Legendre spectral transform in matrix form
    STR_L = S * HTD * W;
    % Legendre spatial derivative based on spectral differentiation
    DDZ_L = (2.0 / DS.zH) * HTD' * SDIFF * STR_L;
    %}
    %% Get the Chebyshev nodes and compute the vertical derivative matrix
    %
    [zlc,w]=cheblb(NZ);
    zl = DS.zH * (0.5 * (1.0 - zlc));
    W = spdiags(w, 0, NZ, NZ);

    HTD = chebpolym(NZ-1, zlc);

    %% Compute scaling for the forward transform
    s = ones(NZ,1);
    for ii=1:NZ-1
        s(ii) = ((HTD(:,ii))' * W * HTD(:,ii))^(-1);
    end
    s(NZ) = 1.0 / pi;
    S = spdiags(s, 0, NZ, NZ);
    
    %% Compute the coefficients of spectral derivative in matrix form
    NM = NZ;
    SDIFF = zeros(NM,NM);
    SDIFF(NM,NM) = 0.0;
    SDIFF(NM-1,NM) = 2.0 * NM;

    for kk = NM-2:-1:1
        A = 2 * kk;
        B = 1;
        if kk > 1
          c = 1.0;
        else
          c = 2.0;
        end
        SDIFF(kk,:) = B / c * SDIFF(kk+2,:);
        SDIFF(kk,kk+1) = A / c;
    end

    % Chebyshev spectral transform in matrix form
    STR_L = S * HTD * W;
    % Chebyshev spatial derivative based on spectral differentiation
    DDZ_L = - (2.0 / DS.zH) * HTD' * SDIFF * STR_L;
    %DDZ2_L = - (2.0 / DS.zH) * HTD' * SDIFF * SDIFF * STR_L;
    %}
    
    %% Compute the terrain and derivatives
    [ht,dhdx] = computeTopoDerivative(TestCase, xh', DS, RAY);
    
    %% XZ grid for Legendre nodes in the vertical
    [HTZL,~] = meshgrid(ht,zl);
    [XL,ZL] = meshgrid(xh,zl);
  
    %% Gal-Chen, Sommerville coordinate
    %{
    dzdh = (1.0 - ZL / DS.zH);
    dxidz = (DS.zH - HTZL);
    sigma = DS.zH * dxidz.^(-1);
    %}
    %% High Order Improved Guellrich coordinate
    % 3 parameter function
    xi = ZL / DS.zH;
    ang = 0.5 * pi * xi;
    AR = 1.0E-3;
    p = 20;
    q = 5;
    fxi = exp(-p/q * xi) .* cos(ang).^p + AR * xi .* (1.0 - xi);
    dfdxi = -p/q * exp(-p/q * xi) .* cos(ang).^p ...
            -(0.5 * p) * pi * exp(-p/q * xi) .* sin(ang) .* cos(ang).^(p-1) ...
            -AR * (1.0 - 2 * xi);
    dzdh = fxi;
    dxidz = DS.zH + HTZL .* (dfdxi - fxi);
    sigma = DS.zH * dxidz.^(-1);
    %}
    % Adjust Z with terrain following coords
    ZTL = (dzdh .* HTZL) + ZL;
    % Make the global array of terrain derivative features
    DZT = ZTL;
    for rr=1:size(DZT,1)
        DZT(rr,:) = fxi(rr,:) .* dhdx;
    end
    
    %% Compute the Rayleigh field
    [rayField, ~] = computeRayleighXZ(DS,1.0,RAY.depth,RAY.width,XL,ZL,applyTopRL,applyLateralRL);
    %[rayField, ~] = computeRayleighPolar(DS,1.0,RAY.depth,XL,ZL);
    %[rayField, ~] = computeRayleighEllipse(DS,1.0,RAY.depth,RAY.width,XL,ZL);
    RL = reshape(rayField,OPS,1);

    %% Compute the reference state initialization
    if strcmp(TestCase,'ShearJetSchar') == true
        [lpref,lrref,dlpref,dlrref] = computeBackgroundPressure(BS, DS.zH, zl, ZTL, RAY);
        [ujref,dujref] = computeJetProfile(UJ, BS.p0, lpref, dlpref);
    elseif strcmp(TestCase,'ShearJetScharCBVF') == true
        [lpref,lrref,dlpref,dlrref] = computeBackgroundPressureCBVF(BS, ZTL);
        [ujref,dujref] = computeJetProfile(UJ, BS.p0, lpref, dlpref);
    elseif strcmp(TestCase,'ClassicalSchar') == true
        [lpref,lrref,dlpref,dlrref] = computeBackgroundPressureCBVF(BS, ZTL);
        [ujref,dujref] = computeJetProfileUniform(UJ, lpref);
    elseif strcmp(TestCase,'AndesMtn') == true
        [lpref,lrref,dlpref,dlrref] = computeBackgroundPressure(BS, DS.zH, zl, ZTL, RAY);
        [ujref,dujref] = computeJetProfile(UJ, BS.p0, lpref, dlpref);
    end
    
    %% Compute the vertical profiles of density and pressure
    pref = exp(lpref);
    rref = exp(lrref);
    rref0 = max(max(rref));
    % Background potential temperature profile
    dlthref = 1.0 / BS.gam * dlpref - dlrref;
    %dthref = exp(dlthref);
    lthref = 1.0 / BS.gam * lpref - lrref + ...
        BS.Rd / BS.cp * log(BS.p0) - log(BS.Rd);
    thref = exp(lthref);
    thref0 = min(min(thref));
    
    %% Unwrap the derivative matrices into operator for 2D implementation
    
    % Compute the vertical derivatives operator (Lagrange expansion)
    DDXI_OP = spalloc(OPS, OPS, NX * NZ^2);
    for cc=1:NX
        ddex = (1:NZ) + (cc - 1) * NZ;
        DDXI_OP(ddex,ddex) = DDZ_L;
    end
    SIGMA = spdiags(reshape(sigma,OPS,1), 0, OPS, OPS);
    DDZ_OP = SIGMA * DDXI_OP; clear DDXI_OP;

    % Compute the horizontal derivatives operator (Hermite Function expansion)
    DDX_OP = spalloc(OPS, OPS, NZ * NX^2);
    for rr=1:NZ
        ddex = (1:NZ:OPS) + (rr - 1);
        DDX_OP(ddex,ddex) = DDX_H;
    end
    
    %% Assemble the block global operator L
    U0 = spdiags(reshape(ujref,OPS,1), 0, OPS, OPS);
    DUDZ = spdiags(reshape(dujref,OPS,1), 0, OPS, OPS);
    DLPDZ = spdiags(reshape(dlpref,OPS,1), 0, OPS, OPS);
    DLRDZ = spdiags(reshape(dlrref,OPS,1), 0, OPS, OPS);
    DLPTDZ = (1.0 / BS.gam * DLPDZ - DLRDZ);
    POR = spdiags(reshape(pref ./ rref,OPS,1), 0, OPS, OPS);
    U0DX = U0 * DDX_OP;
    unit = spdiags(ones(OPS,1),0, OPS, OPS);
    RAYM = spdiags(RL,0, OPS, OPS);
    
    % Horizontal momentum LHS
    LD11 = U0DX + RAY.nu1 * RAYM;
    LD12 = DUDZ;
    LD13 = POR * DDX_OP;
    %LD14 = ZSPR;
    % Vertical momentum LHS
    %LD21 = ZSPR;
    LD22 = U0DX + RAY.nu2 * RAYM;
    LD23 = POR * DDZ_OP + BS.ga * (1.0 / BS.gam - 1.0) * unit;
    LD24 = - BS.ga * unit;
    % Continuity (log pressure) LHS
    LD31 = BS.gam * DDX_OP;
    LD32 = BS.gam * DDZ_OP + DLPDZ;
    LD33 = U0DX + RAY.nu3 * RAYM;
    %LD34 = ZSPR;
    % Thermodynamic LHS
    %LD41 = ZSPR;
    LD42 = DLPTDZ;
    %LD43 = ZSPR;
    LD44 = U0DX + RAY.nu4 * RAYM;
    
    DOPS = struct('LD11', LD11, 'LD12', LD12, 'LD13', LD13, ...
                  'LD22', LD22, 'LD23', LD23, 'LD24', LD24, ...
                  'LD31', LD31, 'LD32', LD32, 'LD33', LD33, ...
                  'LD42', LD42, 'LD44', LD44);
              
    %%
    REFS = struct('DDX_OP',DDX_OP,'DDZ_OP',DDZ_OP,'ujref',ujref,'dujref',dujref,'STR_H',STR_H,'STR_L',STR_L, ...
        'lpref',lpref,'dlpref',dlpref,'lrref',lrref,'dlrref',dlrref,'lthref',lthref,'dlthref',dlthref, ...
        'pref',pref,'rref',rref,'thref',thref,'XL',XL,'xi',xi,'ZTL',ZTL,'DZT',DZT,'DDZ_L',DDZ_L, 'RL', RL, ...
        'DDX_H',DDX_H,'sigma',sigma,'NX',NX,'NZ',NZ,'TestCase',TestCase,'rref0',rref0,'thref0',thref0);
  
end