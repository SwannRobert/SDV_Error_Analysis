import numpy as np

def compute_dynamic_grid(axis_x_name, vec_x, axis_y_name, vec_y, fixed_params, 
                         error_target, IMAX=1000, dt=98, W=366, gamma=4.5, 
                         D_beam=265, zdef=0, ANG=70, size_d=None, size_cdf=None):
    """
    Universal engine.
    Computes the requested error (error_target) by sweeping axis_x_name and axis_y_name.
    """
    # 2D grid creation
    X_grid, Y_grid = np.meshgrid(vec_x, vec_y)
    shape_grid = X_grid.shape
    Z_result = np.full(shape_grid, np.nan)
    
    for i in range(shape_grid[0]):
        for j in range(shape_grid[1]):
            # 1. Initialize local state from fixed parameters
            state = fixed_params.copy()
            
            # 2. Overwrite with free grid variables
            state[axis_x_name] = X_grid[i, j]
            state[axis_y_name] = Y_grid[i, j]
            
            UM, VM = state['U'], state['V']
            U2I, V2I = state["u'"], state["v'"]
            dp_fixed = state.get('dp', None)  # May be None if randomly sampled
            
            U2, V2 = U2I**2, V2I**2
            UV = 0.3 * U2I * V2I  # UVI fixed at 0.3
            
            # 3. Vectorized kinematics
            Z1, Z2 = np.random.randn(IMAX), np.random.randn(IMAX)
            UT = np.sqrt(U2) * Z1
            VT = (UV / (np.sqrt(U2) + 1e-8)) * Z1 + np.sqrt(max(0.0, U2*V2 - UV**2)) / (np.sqrt(U2) + 1e-8) * Z2
            UI, VI = UM + UT, VM + VT
            
            # 4. Diameter handling (fixed if on axis, random otherwise)
            if dp_fixed is not None:
                dp = np.full(IMAX, dp_fixed)
            else:
                rand_vals = np.random.rand(IMAX)
                dp_indices = np.searchsorted(size_cdf, rand_vals)
                dp = size_d[dp_indices]
            
            # 5. Opto-geometrical filter
            y0 = (np.random.rand(IMAX) - 0.5) * D_beam
            y_final = y0 + dp * (VI / (UI + 1e-8))
            y_min_center, y_max_center = np.minimum(y0, y_final), np.maximum(y0, y_final)
            
            val = dp**2 - 4 * zdef**2 * np.tan(np.radians(gamma))**2
            
            trigger_hit = np.zeros(IMAX, dtype=bool)
            valid_val = val > 0
            if np.any(valid_val):
                d_dark = np.sqrt(val[valid_val])
                trigger_hit[valid_val] = (y_min_center[valid_val] - d_dark/2 <= dt/2) & (y_max_center[valid_val] + d_dark/2 >= -dt/2)
            
            is_clipped = (y_min_center - dp/2 < -W/2) | (y_max_center + dp/2 > W/2)
            
            accepted =  (np.abs(UI) >= 0.5) & ((np.abs(VI) / (np.abs(UI) + 1e-8)) <= np.tan(np.radians(ANG))) & trigger_hit & ~is_clipped
            
            IACC = np.sum(accepted)
            
            # 6. Extract requested error metric
            if IACC > 500:
                if error_target == 'eU':
                    Z_result[i, j] = np.mean(UI[accepted]) / (UM + 1e-8)
                elif error_target == 'eV':
                    Z_result[i, j] = np.mean(VI[accepted]) / (VM + 1e-8)
                elif error_target == "eu'":
                    URC = np.sqrt(np.maximum(0.0, np.var(UI[accepted], ddof=0)))
                    Z_result[i, j] = URC / (U2I + 1e-8)
                elif error_target == "ev'":
                    VRC = np.sqrt(np.maximum(0.0, np.var(VI[accepted], ddof=0)))
                    Z_result[i, j] = VRC / (V2I + 1e-8)
                elif error_target == 'eUV':
                    URC = np.sqrt(np.maximum(0.0, np.var(UI[accepted], ddof=0)))
                    VRC = np.sqrt(np.maximum(0.0, np.var(VI[accepted], ddof=0)))
                    UVC = np.mean(UT[accepted] * VT[accepted]) / (URC * VRC + 1e-8)
                    Z_result[i, j] = UVC / 0.3
                    
    return X_grid, Y_grid, Z_result


def generate_experimental_fluid(IMAX, size_d, size_cdf, p_mean, p_high, p_low, 
                                p_angle_mean, p_angle_high, p_angle_low, UVO=0.3):
    """Generates the kinematic population (true fluid) in a vectorized way."""
    rand_vals = np.random.rand(IMAX)
    dp_indices = np.searchsorted(size_cdf, rand_vals)
    dp = size_d[dp_indices]
    
    U_mean_dp = np.polyval(p_mean, dp)
    U_rms_dp  = np.maximum((np.polyval(p_high, dp) - np.polyval(p_low, dp)) / 4.0, 0.05)
    
    V_mean_dp = U_mean_dp * np.tan(np.radians(np.polyval(p_angle_mean, dp)))
    V_rms_dp  = np.maximum(np.abs(U_mean_dp * np.tan(np.radians(np.polyval(p_angle_high, dp))) - 
                                  U_mean_dp * np.tan(np.radians(np.polyval(p_angle_low, dp)))) / 4.0, 0.05)
    
    U2, V2 = U_rms_dp**2, V_rms_dp**2
    UV = UVO * U_rms_dp * V_rms_dp
    
    Z1, Z2 = np.random.randn(IMAX), np.random.randn(IMAX)
    UT = np.sqrt(U2) * Z1
    VT = (UV / (np.sqrt(U2) + 1e-8)) * Z1 + np.sqrt(np.maximum(0.0, U2*V2 - UV**2)) / (np.sqrt(U2) + 1e-8) * Z2
         
    UI, VI = U_mean_dp + UT, V_mean_dp + VT
    y0 = (np.random.rand(IMAX) - 0.5)  # Normalized position before multiplying by D_beam
    
    return UI, VI, dp, y0


def run_mode_2_zdef_sweep(zdef_array, UI, VI, dp, y0_norm, dt=98, W=366, gamma=4.5, D_beam=265, ANG=70):
    """
    Applies the optical filter on the SAME fluid for different zdef values.
    Returns absolute errors on U and V. 

    """
    y0 = y0_norm * D_beam
    delta_y = dp * (VI / (UI + 1e-8))
    y_final = y0 + delta_y
    y_min_center, y_max_center = np.minimum(y0, y_final), np.maximum(y0, y_final)
    
    U_true, V_true = np.mean(UI), np.mean(VI)
    
    err_U = np.zeros(len(zdef_array))
    err_V = np.zeros(len(zdef_array))
    acc_rates = np.zeros(len(zdef_array))
    
    for idx, zdef in enumerate(zdef_array):
        val = dp**2 - 4 * zdef**2 * np.tan(np.radians(gamma))**2
        trigger_hit = np.zeros(len(UI), dtype=bool)
        valid_val = val > 0
        if np.any(valid_val):
            d_dark = np.sqrt(val[valid_val])
            trigger_hit[valid_val] = (y_min_center[valid_val] - d_dark/2 <= dt/2) & \
                                     (y_max_center[valid_val] + d_dark/2 >= -dt/2)
                                     
        is_clipped = (y_min_center - dp/2 < -W/2) | (y_max_center + dp/2 > W/2)
        accepted = (np.abs(UI) >= 0.5) & ((np.abs(VI) / (np.abs(UI) + 1e-8)) <= np.tan(np.radians(ANG))) & trigger_hit & ~is_clipped
        
        IACC = np.sum(accepted)
        acc_rates[idx] = IACC / len(UI)
        if IACC > 500:
            err_U[idx] = np.abs(np.mean(UI[accepted]) - U_true)
            err_V[idx] = np.abs(np.mean(VI[accepted]) - V_true)
        else:
            err_U[idx], err_V[idx] = np.nan, np.nan
            
    return err_U, err_V, acc_rates, accepted  # also returns "accepted" array from last zdef