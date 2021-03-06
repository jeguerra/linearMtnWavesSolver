function mVec = computeAorATMulLogPLogTh(REFS, DOPS, xVec, sysDex, ntrans)
    %% Set the dimensions
    OPS = REFS.NX * REFS.NZ;

    %% Carry out the block multiply (TO DO: THIS CAN BE PARALLELIZED)
    if isempty(sysDex)
    sysDex = 1:(4 * OPS);
    end

    zVec = zeros(4 * OPS, 1);
    zVec(sysDex) = xVec;
    udex = 1:OPS;
    wdex = udex + OPS;
    pdex = udex + 2 * OPS;
    tdex = udex + 3 * OPS;
    
    if strcmp(ntrans, 'notransp')
        % Compute A * x
        q11 = DOPS.LD11 * zVec(udex, 1) + DOPS.LD12 * zVec(wdex, 1) + DOPS.LD13 * zVec(pdex, 1);
        q21 =                             DOPS.LD22 * zVec(wdex, 1) + DOPS.LD23 * zVec(pdex, 1) + DOPS.LD24 * zVec(tdex, 1);
        q31 = DOPS.LD31 * zVec(udex, 1) + DOPS.LD32 * zVec(wdex, 1) + DOPS.LD33 * zVec(pdex, 1);
        q41 =                             DOPS.LD42 * zVec(wdex, 1)                             + DOPS.LD44 * zVec(tdex, 1);
    elseif strcmp(ntrans, 'transp0')
        % Compute A' * x
        q11 = DOPS.LD11' * zVec(udex, 1)                              + DOPS.LD31' * zVec(pdex, 1);
        q21 = DOPS.LD12' * zVec(udex, 1) + DOPS.LD22' * zVec(wdex, 1) + DOPS.LD32' * zVec(pdex, 1) + DOPS.LD42' * zVec(tdex, 1);
        q31 = DOPS.LD13' * zVec(udex, 1) + DOPS.LD23' * zVec(wdex, 1) + DOPS.LD33' * zVec(pdex, 1);
        q41 =                              DOPS.LD24' * zVec(wdex, 1)                              + DOPS.LD44' * zVec(tdex, 1);
    elseif ntrans == 1
        % DEFAULT TO A * x
        q11 = DOPS.LD11 * zVec(udex, 1) + DOPS.LD12 * zVec(wdex, 1) + DOPS.LD13 * zVec(pdex, 1);
        q21 =                             DOPS.LD22 * zVec(wdex, 1) + DOPS.LD23 * zVec(pdex, 1) + DOPS.LD24 * zVec(tdex, 1);
        q31 = DOPS.LD31 * zVec(udex, 1) + DOPS.LD32 * zVec(wdex, 1) + DOPS.LD33 * zVec(pdex, 1);
        q41 =                             DOPS.LD42 * zVec(wdex, 1)                             + DOPS.LD44 * zVec(tdex, 1);
    elseif ntrans == 3
        % Compute A' * x
        q11 = DOPS.LD11' * zVec(udex, 1)                              + DOPS.LD31' * zVec(pdex, 1);
        q21 = DOPS.LD12' * zVec(udex, 1) + DOPS.LD22' * zVec(wdex, 1) + DOPS.LD32' * zVec(pdex, 1) + DOPS.LD42' * zVec(tdex, 1);
        q31 = DOPS.LD13' * zVec(udex, 1) + DOPS.LD23' * zVec(wdex, 1) + DOPS.LD33' * zVec(pdex, 1);
        q41 =                              DOPS.LD24' * zVec(wdex, 1)                              + DOPS.LD44' * zVec(tdex, 1);
    else
        % DEFAULT TO A * x
        q11 = DOPS.LD11 * zVec(udex, 1) + DOPS.LD12 * zVec(wdex, 1) + DOPS.LD13 * zVec(pdex, 1);
        q21 =                             DOPS.LD22 * zVec(wdex, 1) + DOPS.LD23 * zVec(pdex, 1) + DOPS.LD24 * zVec(tdex, 1);
        q31 = DOPS.LD31 * zVec(udex, 1) + DOPS.LD32 * zVec(wdex, 1) + DOPS.LD33 * zVec(pdex, 1);
        q41 =                             DOPS.LD42 * zVec(wdex, 1)                             + DOPS.LD44 * zVec(tdex, 1);
    end
        
    zVec = [q11; q21; q31; q41];
    mVec = zVec(sysDex);
end