function [LD, FF, RR, UREF, RREF, RTHREF] = evaluateJacobianOperatorCBC_FluxForm(RhoU, RhoW, Rho, RhoTheta, BS, REFS, RAY)
    OPS = REFS.NX * REFS.NZ;
    
    %% Unwrap the derivative matrices into operators onto a state 1D vector
    % Compute the vertical derivatives operator (Legendre expansion)
    DDXI_OP = spalloc(OPS, OPS, REFS.NZ^2);
    for cc=1:REFS.NX
        ddex = (1:REFS.NZ) + (cc - 1) * REFS.NZ;
        DDXI_OP(ddex,ddex) = REFS.DDZ_L;
    end

    % Compute the horizontal derivatives operator (Hermite expansion)
    DDA_OP = spalloc(OPS, OPS, REFS.NX^2);
    for rr=1:REFS.NZ
        ddex = (1:REFS.NZ:OPS) + (rr - 1);
        DDA_OP(ddex,ddex) = REFS.DDX_H;
    end
    
    %% Assemble the block global operator L
    SIGMA = spdiags(reshape(REFS.sigma,OPS,1), 0, OPS, OPS);
    U0 = spdiags(reshape(REFS.ujref,OPS,1), 0, OPS, OPS);
    DUDZ = spdiags(reshape(REFS.dujref,OPS,1), 0, OPS, OPS);
    DTHDZ = spdiags(reshape(REFS.dthref,OPS,1), 0, OPS, OPS);
    DLTHDZ = spdiags(reshape(REFS.dlthref,OPS,1), 0, OPS, OPS);
    THTZ = spdiags(reshape(REFS.thref,OPS,1), 0, OPS, OPS);
    ITHTZ = spdiags(reshape(REFS.thref.^(-1),OPS,1), 0, OPS, OPS);
    RDTZ = spdiags(reshape(REFS.pref ./ REFS.rref,OPS,1), 0, OPS, OPS);
    PGFTX = (BS.gam * RDTZ - U0.^2) * ITHTZ;
    PGFTZ = BS.gam * RDTZ * ITHTZ;
    U0DA = U0 * DDA_OP;
    
    unit = spdiags(ones(OPS,1),0, OPS, OPS);

    % Horizontal momentum LHS
    L11 = U0DA;
    L12 = sparse(OPS,OPS);
    L13 = sparse(OPS,OPS);
    L14 = PGFTX * DDA_OP;
    % Vertical momentum LHS
    L21 = sparse(OPS,OPS);
    L22 = U0DA;
    L23 = sparse(OPS,OPS);
    L24 = PGFTZ * SIGMA * DDXI_OP;
    % Continuity LHS
    L31 = DDA_OP;
    L32 = SIGMA * DDXI_OP;
    L33 = sparse(OPS,OPS);
    L34 = sparse(OPS,OPS);
    % Thermodynamic LHS
    L41 = sparse(OPS,OPS);
    L42 = sparse(OPS,OPS);
    L43 = -THTZ * U0DA;
    L44 = U0DA;

    %% Assemble the algebraic part (Rayleigh layer on the diagonal)
    % Horizontal momentum LHS
    B11 = sparse(OPS,OPS) + RAY.nu1 * spdiags(REFS.RL,0, OPS, OPS);
    B12 = DUDZ - U0 * DLTHDZ;
    B13 = sparse(OPS,OPS);
    B14 = sparse(OPS,OPS);
    % Vertical momentum LHS
    B21 = sparse(OPS,OPS);
    B22 = sparse(OPS,OPS) + RAY.nu2 * spdiags(REFS.RL,0, OPS, OPS);
    B23 = BS.ga * unit;
    B24 = BS.ga * (1.0 - BS.gam) * ITHTZ;
    % Continuity LHS (using density weighted change of variable in W)
    B31 = sparse(OPS,OPS);
    B32 = sparse(OPS,OPS);
    B33 = sparse(OPS,OPS) + RAY.nu3 * spdiags(REFS.RL,0, OPS, OPS);
    B34 = sparse(OPS,OPS);
    % Thermodynamic LHS
    B41 = sparse(OPS,OPS);
    B42 = DTHDZ;
    B43 = sparse(OPS,OPS);
    B44 = sparse(OPS,OPS) + RAY.nu4 * spdiags(REFS.RL,0, OPS, OPS);
    
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
    
    %% Assemble the LHS operator (reorder ru r rw rt)
    LD = [LD11 LD12 LD13 LD14 ; ...
          LD21 LD22 LD23 LD24 ; ...
          LD31 LD32 LD33 LD34 ; ...
          LD41 LD42 LD43 LD44];
      
    %% Assemble the force vector (reorder ru r rw rt)
    F11 = zeros(OPS,1);
    F21 = zeros(OPS,1);
    F31 = zeros(OPS,1);
    F41 = zeros(OPS,1);
    FF = [F11 ; F21 ; F31 ; F41];
        
    %% Recover U and W from the solution momenta
    UREF = reshape(REFS.ujref, OPS, 1);
    DUREF = reshape(REFS.dujref, OPS, 1);
    DRTREF = reshape(REFS.drthref, OPS, 1);
    RREF = reshape(REFS.rref, OPS, 1);
    RTHREF = reshape(REFS.rref .* REFS.thref, OPS, 1);
    RUT = (RREF .* UREF + RhoU);
    U = RUT ./ (RREF + Rho) - UREF;
    W = RhoW ./ (RREF + Rho);

    %% Get total velocity and other conserved quantities
    A = (BS.Rd / (BS.p0^(BS.Rd / BS.cp)))^BS.gam;
    UT = UREF + U;
    WT = W;
    RT = RREF + Rho;
    RTHT = RTHREF + RhoTheta;

    %% Get the metric quantities
    SIGMA = spdiags(reshape(REFS.sigma,OPS,1), 0, OPS, OPS);

    DDX = DDA_OP;
    DDZ = SIGMA * DDXI_OP;

    %% Evaluate the RHS force vector force vector
    UTM = spdiags(UT, 0, OPS, OPS);
    WTM = spdiags(WT, 0, OPS, OPS);
    RUTM = spdiags(RUT, 0 , OPS, OPS);
    RWTM = spdiags(RhoW, 0, OPS, OPS);
    RTHTM = spdiags(RTHT, 0 , OPS, OPS);

    R11 = UTM * DDX * RhoU + ...
          RUTM * DDX * U + ...
          A * BS.gam * (RTHTM.^(BS.gam - 1.0)) * DDX * RhoTheta + ...
          UTM * DDZ * RhoW + ...
          RWTM * (DUREF + DDZ * U) + ...
          RAY.nu1 * spdiags(REFS.RL,0, OPS, OPS) * RhoU;

    R21 = RUTM * DDX * W + WTM * DDX * RhoU + ...
          WTM * DDZ * RhoW + RWTM * DDZ * W + ...
          A * BS.gam * (RTHTM.^(BS.gam - 1.0)) * (DRTREF + DDZ * RhoTheta) + ...
          BS.ga * RT + ...
          RAY.nu2 * spdiags(REFS.RL,0, OPS, OPS) * RhoW;

    R31 = DDX * RhoU + ...
          DDZ * RhoW + ...
          RAY.nu3 * spdiags(REFS.RL,0, OPS, OPS) * Rho;

    R41 = UTM * DDX * RhoTheta + RTHTM * DDX * U + ...
          WTM * (DRTREF + DDZ * RhoTheta) + RTHTM * DDZ * W + ...
          RAY.nu4 * spdiags(REFS.RL,0, OPS, OPS) * RhoTheta;
      
    RR = [R11 ; R21 ; R31 ; R41];
    
    disp(['Residual in RhoU: ' num2str(norm(R11))]);
    disp(['Residual in RhoW: ' num2str(norm(R21))]);
    disp(['Residual in Rho: ' num2str(norm(R31))]);
    disp(['Residual in RhoTheta: ' num2str(norm(R41))]);

    S = svds(LD, 2);
    LB = 1.0 / max(S);
    disp(['Maximum Singular Value: ' num2str(max(S))]);

    disp(['Lower Error Bound in RhoU: ' num2str(LB * norm(R11))]);
    disp(['Lower Error Bound in RhoW: ' num2str(LB * norm(R21))]);
    disp(['Lower Error Bound in Rho: ' num2str(LB * norm(R31))]);
    disp(['Lower Error Bound in RhoTheta: ' num2str(LB * norm(R41))]);
end