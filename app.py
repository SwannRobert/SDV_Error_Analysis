import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import pandas as pd

# Importing physics engine and data loader
from physics_engine import compute_dynamic_grid, generate_experimental_fluid, run_mode_2_zdef_sweep
from data_loader import load_experimental_series

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(page_title="Dashboard", layout="wide")

DATA_FOLDER = "./exp_data"

# =============================================================================
# SIDEBAR: GLOBAL INSTRUMENT PARAMETERS
# =============================================================================
st.sidebar.title("Optical Parameters")
st.sidebar.markdown("These parameters define the measurement volume geometry and apply to both modes.")

dt = st.sidebar.number_input("Interfringe spacing dt (µm)", value=98.0)
W = st.sidebar.number_input("Slit width W (µm)", value=366.0)
D_beam = st.sidebar.number_input("Beam diameter D_beam (µm)", value=265.0)
gamma = st.sidebar.number_input("Scattering angle gamma (°)", value=4.5)
ANG = st.sidebar.slider("Acceptance angle limit (°)", min_value=10, max_value=90, value=70)
U_min = st.sidebar.slider("Minimum mesurable velocity (m/s)", min_value=0.0, max_value=0.5, value=0, step=0.01)

st.title("SDV Simulation - V1")
st.markdown("---")

# Check if data folder exists
if not os.path.exists(DATA_FOLDER):
    st.error(f"The folder '{DATA_FOLDER}' does not exist. Please create it and add your .txt files.")
    st.stop()

# =============================================================================
# MAIN TABS
# =============================================================================
tab1, tab2 = st.tabs(["Mode 1: Parametric", "Mode 2: Experimental data"])

# -----------------------------------------------------------------------------
# MODE 1: PARAMETRIC GRIDS
# -----------------------------------------------------------------------------
with tab1:
    st.header("Dynamic variables")
    st.markdown("Select the variable to analyze (Z) and the two fluid parameters to vary (X and Y).")
    
    try:
        size_d_m1, size_cdf_m1, _, _, _, _, _, _ = load_experimental_series(DATA_FOLDER, "1")
    except Exception as e:
        st.warning(f"Unable to load default distribution for Mode 1: {e}. Ensure files ending with '_1.txt' exist.")
        size_d_m1, size_cdf_m1 = None, None

    col1, col2, col3 = st.columns(3)
    with col1:
        error_target = st.selectbox("Error to analyze (Z axis)", ['eU', 'eV', "eu'", "ev'", 'eUV'])
    with col2:
        axis_x_name = st.selectbox("X-axis variable", ['U', 'V', "u'", "v'", 'dp'], index=0)
    with col3:
        options_y = [opt for opt in ['U', 'V', "u'", "v'", 'dp'] if opt != axis_x_name]
        axis_y_name = st.selectbox("Y-axis variable", options_y, index=1)

    st.subheader("Fixed Fluid Parameters")
    col_f1, col_f2, col_f3 = st.columns(3)
    cols_f = [col_f1, col_f2, col_f3]
    col_idx = 0
    
    fixed_params = {}
    all_vars = ['U', 'V', "u'", "v'", 'dp']
    
    for var in all_vars:
        if var not in [axis_x_name, axis_y_name]:
            with cols_f[col_idx % 3]:
                if var == 'U': fixed_params['U'] = st.slider("Fixed velocity U (m/s)", 0.1, 20.0, 1.0)
                elif var == 'V': fixed_params['V'] = st.slider("Fixed velocity V (m/s)", 0.1, 20.0, 0.0)
                elif var == "u'": fixed_params["u'"] = st.slider("Fixed fluctuation u'", 0.1, 10.0, 1.0)
                elif var == "v'": fixed_params["v'"] = st.slider("Fixed fluctuation v'", 0.1, 10.0, 2.0)
                elif var == 'dp':
                    use_dist = st.checkbox("Sample dp from real distribution", value=True)
                    if not use_dist:
                        fixed_params['dp'] = st.slider("Fixed particle diameter dp (µm)", 20.0, 350.0, 100.0)
            col_idx += 1

    st.subheader("Computation Resolution")
    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1: IMAX_m1 = st.number_input("Particles per point (IMAX)", 100, 100000, 10000, step=1000)
    with col_r2: resolution = st.slider("Grid resolution (N x N)", 10, 40, 20)
    with col_r3: zdef_m1 = st.slider("Defocus z_def (µm)", 0, 400, 0, step=30)

    plot_type = st.radio("Visualization Type", ["3D Surface", "2D Contour Lines"], horizontal=True)

    def get_vector(var_name, n_points):
        if var_name in ['U', 'V']: return np.linspace(0.1, 10.0, n_points)
        elif var_name in ["u'", "v'"]: return np.linspace(0.1, 8.0, n_points)
        elif var_name == 'dp': return np.linspace(20.0, 350.0, n_points)

    if st.button("Run simulation", type="primary"):
        if size_d_m1 is None:
            st.error("Missing data to run Mode 1.")
        else:
            with st.spinner(f"Vectorized simulation of {resolution**2 * IMAX_m1} particles in progress..."):
                vec_x = get_vector(axis_x_name, resolution)
                vec_y = get_vector(axis_y_name, resolution)
                
                X, Y, Z = compute_dynamic_grid(
                    axis_x_name, vec_x, axis_y_name, vec_y, fixed_params, error_target, 
                    IMAX=IMAX_m1, dt=dt, W=W, gamma=gamma, D_beam=D_beam, zdef=zdef_m1, ANG=ANG, 
                    size_d=size_d_m1, size_cdf=size_cdf_m1
                )
                
                # Divergent color scale centered around 1.0 for measurement ratios
                if plot_type == "3D Surface":
                    fig = go.Figure(data=[go.Surface(
                        z=Z, x=X, y=Y, 
                        colorscale='RdBu_r', cmin=0.5, cmax=1.5
                    )])
                    fig.update_layout(
                        title=f"Error ratio: {error_target} = f({axis_x_name}, {axis_y_name})",
                        scene=dict(xaxis_title=axis_x_name, yaxis_title=axis_y_name, zaxis_title=error_target),
                        height=700, margin=dict(l=0, r=0, b=0, t=50)
                    )
                else:
                    fig = go.Figure(data=[go.Contour(
                        z=Z, x=vec_x, y=vec_y, 
                        colorscale='RdBu_r', zmin=0.5, zmax=1.5, contours=dict(showlabels=True)
                    )])
                    fig.update_layout(
                        title=f"Error ratio contours: {error_target} = f({axis_x_name}, {axis_y_name})",
                        xaxis_title=axis_x_name,
                        yaxis_title=axis_y_name,
                        height=600, margin=dict(l=50, r=50, b=50, t=50)
                    )
                st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# MODE 2: EXPERIMENTAL AND SPATIAL BIAS
# -----------------------------------------------------------------------------
with tab2:
    st.header("Experimental data")
    st.markdown("Explore optical bias as a function of injector geometry.")
    
    MAPPING_SERIES = {
        ("Z=0.19D", "0"): "1",
        ("Z=0.19D", "0.05D"): "2",
        ("Z=1.19D", "0"): "3",
        ("Z=1.19D", "0.25D"): "4",
        ("Z=2.19D", "0"): "5",   
        ("Z=2.19D", "0.45D"): "6"
    }
    
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        z_choice = st.selectbox("Axial Position (Z)", ["Z=0.19D", "Z=1.19D", "Z=2.19D"])
        r_options = [k[1] for k in MAPPING_SERIES.keys() if k[0] == z_choice]
        r_choice = st.selectbox("Radial Position (R)", r_options)
        serie_id = MAPPING_SERIES[(z_choice, r_choice)]
        
    with col_m2:
        IMAX_m2 = st.number_input("Number of particles", 10000, 500000, 100000, step=50000)
    with col_m3:
        zdef_single = st.slider("Instrument defocus (z_def µm)", 0, 300, 0, step=30)
        
    if st.button("Analyze this spatial position", type="primary"):
        try:
            size_d, size_cdf, p_mean, p_high, p_low, p_angle_mean, p_angle_high, p_angle_low = load_experimental_series(DATA_FOLDER, serie_id)
            
            with st.spinner(f"Simulating position {z_choice}, r={r_choice} (Series {serie_id})..."):
                
                UI, VI, dp, y0_norm = generate_experimental_fluid(
                    IMAX_m2, size_d, size_cdf, p_mean, p_high, p_low, p_angle_mean, p_angle_high, p_angle_low
                )
                
                _, _, _, acc = run_mode_2_zdef_sweep(
                    [zdef_single], UI, VI, dp, y0_norm, dt=dt, W=W, gamma=gamma, D_beam=D_beam, ANG=ANG
                )
                
                # TRUE STATISTICS
                U_t, V_t = np.mean(UI), np.mean(VI)
                up_t, vp_t = np.std(UI, ddof=0), np.std(VI, ddof=0)
                
                u_fluc_t = UI - U_t
                v_fluc_t = VI - V_t
                uv_cov_t = np.mean(u_fluc_t * v_fluc_t)
                uv_cor_t = uv_cov_t / (up_t * vp_t + 1e-8)
                
                # MEASURED STATISTICS
                if np.sum(acc) > 20:
                    U_m, V_m = np.mean(UI[acc]), np.mean(VI[acc])
                    up_m, vp_m = np.std(UI[acc], ddof=0), np.std(VI[acc], ddof=0)
                    
                    u_fluc_m = UI[acc] - U_m
                    v_fluc_m = VI[acc] - V_m
                    uv_cov_m = np.mean(u_fluc_m * v_fluc_m)
                    uv_cor_m = uv_cov_m / (up_m * vp_m + 1e-8)
                else:
                    U_m = V_m = up_m = vp_m = uv_cov_m = uv_cor_m = np.nan
                
                st.markdown(f"### Local Instrumental Bias (z_def = {zdef_single} µm)")
                
                # ROW 1
                kpi1, kpi2, kpi3 = st.columns(3)
                kpi1.metric("Axial Velocity (U)", f"{U_t:.2f} m/s", f"{U_m - U_t:.3f} m/s", delta_color="off")
                kpi2.metric("Radial Velocity (V)", f"{V_t:.2f} m/s", f"{V_m - V_t:.3f} m/s", delta_color="off")
                kpi3.metric("Covariance (u'v')", f"{uv_cov_t:.3f} m²/s²", f"{uv_cov_m - uv_cov_t:.4f} m²/s²", delta_color="off")
                
                # ROW 2
                kpi4, kpi5, kpi6 = st.columns(3)
                kpi4.metric("Fluctuation (u')", f"{up_t:.2f} m/s", f"{up_m - up_t:.3f} m/s", delta_color="off")
                kpi5.metric("Fluctuation (v')", f"{vp_t:.2f} m/s", f"{vp_m - vp_t:.3f} m/s", delta_color="off")
                kpi6.metric("Correlation (UV)", f"{uv_cor_t:.3f}", f"{uv_cor_m - uv_cor_t:.3f}", delta_color="off")
                
                st.caption(f"*Optical acceptance rate at this location: {(np.sum(acc)/IMAX_m2)*100:.1f} %*")
                
                # SCATTER PLOTS
                st.subheader("Velocity Distributions and Acceptance Volume")
                col_scat1, col_scat2 = st.columns(2)
                
                max_points = min(4000, len(UI))
                display_mask = np.random.choice(len(UI), max_points, replace=False)
                UI_disp, VI_disp, dp_disp, acc_disp = UI[display_mask], VI[display_mask], dp[display_mask], acc[display_mask]
                rej_disp = ~acc_disp
                
                with col_scat1:
                    st.markdown("### 3D Scatter Plot")
                    fig3d = go.Figure()
                    if np.any(rej_disp):
                        fig3d.add_trace(go.Scatter3d(
                            x=UI_disp[rej_disp], y=VI_disp[rej_disp], z=dp_disp[rej_disp],
                            mode='markers', marker=dict(size=2.5, color='red', opacity=0.4), name="Rejected"
                        ))
                    if np.any(acc_disp):
                        fig3d.add_trace(go.Scatter3d(
                            x=UI_disp[acc_disp], y=VI_disp[acc_disp], z=dp_disp[acc_disp],
                            mode='markers', marker=dict(size=3, color='green', opacity=0.9), name="Validated"
                        ))
                    fig3d.update_layout(scene=dict(xaxis_title='U (m/s)', yaxis_title='V (m/s)', zaxis_title='dp (µm)'), height=500, margin=dict(l=0, r=0, b=0, t=30))
                    st.plotly_chart(fig3d, use_container_width=True)

                with col_scat2:
                    st.markdown("### 2D Scatter Plot")
                    fig2d = go.Figure()
                    if np.any(rej_disp):
                        fig2d.add_trace(go.Scatter(
                            x=VI_disp[rej_disp], y=UI_disp[rej_disp],
                            mode='markers', marker=dict(size=4, color='red', opacity=0.4), name="Rejected"
                        ))
                    if np.any(acc_disp):
                        fig2d.add_trace(go.Scatter(
                            x=VI_disp[acc_disp], y=UI_disp[acc_disp],
                            mode='markers', marker=dict(size=4, color='green', opacity=0.8), name="Validated"
                        ))
                    fig2d.update_layout(xaxis_title='Radial Velocity V (m/s)', yaxis_title='Axial Velocity U (m/s)', height=500, margin=dict(l=0, r=0, b=0, t=30))
                    st.plotly_chart(fig2d, use_container_width=True)

                # LONGITUDINAL PROFILE (WITH SUBPLOTS)
                st.markdown("---")
                st.subheader("Longitudinal Error Profile (R=0)")
                
                z_positions = [0.19, 1.19, 2.19]
                series_axe_central = ["1", "3", "5"]
                
                err_p_U, err_p_V = [], []
                err_p_up, err_p_vp = [], []
                err_p_uv_cov, err_p_uv_cor = [], []
                
                for s_id in series_axe_central:
                    sd, scdf, pm, ph, pl, pam, pah, pal = load_experimental_series(DATA_FOLDER, s_id)
                    UI_c, VI_c, dp_c, y0_c = generate_experimental_fluid(30000, sd, scdf, pm, ph, pl, pam, pah, pal)
                    _, _, _, acc_c = run_mode_2_zdef_sweep([zdef_single], UI_c, VI_c, dp_c, y0_c, dt=dt, W=W, gamma=gamma, D_beam=D_beam, ANG=ANG)
                    
                    if np.sum(acc_c) > 20:
                        U_ct, V_ct = np.mean(UI_c), np.mean(VI_c)
                        up_ct, vp_ct = np.std(UI_c, ddof=0), np.std(VI_c, ddof=0)
                        cov_ct = np.mean((UI_c - U_ct) * (VI_c - V_ct))
                        cor_ct = cov_ct / (up_ct * vp_ct + 1e-8)
                        
                        U_cm, V_cm = np.mean(UI_c[acc_c]), np.mean(VI_c[acc_c])
                        up_cm, vp_cm = np.std(UI_c[acc_c], ddof=0), np.std(VI_c[acc_c], ddof=0)
                        cov_cm = np.mean((UI_c[acc_c] - U_cm) * (UI_c[acc_c] - V_cm))
                        cor_cm = cov_cm / (up_cm * vp_cm + 1e-8)
                        
                        err_p_U.append(np.abs(U_cm - U_ct))
                        err_p_V.append(np.abs(V_cm - V_ct))
                        err_p_up.append(np.abs(up_cm - up_ct))
                        err_p_vp.append(np.abs(vp_cm - vp_ct))
                        err_p_uv_cov.append(np.abs(cov_cm - cov_ct))
                        err_p_uv_cor.append(np.abs(cor_cm - cor_ct))
                    else:
                        err_p_U.append(np.nan)
                        err_p_V.append(np.nan)
                        err_p_up.append(np.nan)
                        err_p_vp.append(np.nan)
                        err_p_uv_cov.append(np.nan)
                        err_p_uv_cor.append(np.nan)

                # Creation of the 3 subplots for appropriate unit separation
                fig_prof = make_subplots(
                    rows=3, cols=1, 
                    shared_xaxes=True, 
                    vertical_spacing=0.08,
                    subplot_titles=("Velocity & Fluctuation Errors (m/s)", "Covariance Error (m²/s²)", "Correlation Error (Dimensionless)")
                )
                
                # Row 1: Velocities
                fig_prof.add_trace(go.Scatter(x=z_positions, y=err_p_U, mode='lines+markers', name='|ΔU|', line=dict(color='blue')), row=1, col=1)
                fig_prof.add_trace(go.Scatter(x=z_positions, y=err_p_V, mode='lines+markers', name='|ΔV|', line=dict(color='cyan')), row=1, col=1)
                fig_prof.add_trace(go.Scatter(x=z_positions, y=err_p_up, mode='lines+markers', name="|Δu'|", line=dict(color='red', dash='dash')), row=1, col=1)
                fig_prof.add_trace(go.Scatter(x=z_positions, y=err_p_vp, mode='lines+markers', name="|Δv'|", line=dict(color='orange', dash='dash')), row=1, col=1)
                
                # Row 2: Covariance
                fig_prof.add_trace(go.Scatter(x=z_positions, y=err_p_uv_cov, mode='lines+markers', name="|Δu'v'|", line=dict(color='purple', dash='dot')), row=2, col=1)
                
                # Row 3: Correlation
                fig_prof.add_trace(go.Scatter(x=z_positions, y=err_p_uv_cor, mode='lines+markers', name="|ΔUV|", line=dict(color='black', dash='dot')), row=3, col=1)
                
                fig_prof.update_layout(
                    height=700, margin=dict(l=0, r=0, b=0, t=30),
                    legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1)
                )
                fig_prof.update_yaxes(title_text="|Error|", row=1, col=1)
                fig_prof.update_yaxes(title_text="|Error|", row=2, col=1)
                fig_prof.update_yaxes(title_text="|Error|", row=3, col=1)
                fig_prof.update_xaxes(
                    title_text="Axial Position Z (in multiples of D)", 
                    row=3, col=1, 
                    tickmode='array', tickvals=z_positions, ticktext=['0.19D', '1.19D', '2.19D']
                )
                
                st.plotly_chart(fig_prof, use_container_width=True)
                
        except Exception as e:
            st.error(f"Computation error: {e}. Check that the files {serie_id}.txt are present in the data folder.")

    # =========================================================================
    # GLOBAL SUMMARY TABLE OF THE 6 POSITIONS (WITH SIZE CLASSES)
    # =========================================================================
    st.markdown("---")
    st.subheader("Global Bias Mapping (Summary Tables)")
    
    if st.button("Generate tables for all 6 positions", type="secondary"):
        with st.spinner(f"Vectorial computation of the 6 spatial positions at z_def={zdef_single} µm..."):
            
            global_results = []
            class_results = []
            
            for (z_name, r_name), s_id in MAPPING_SERIES.items():
                try:
                    sd, scdf, pm, ph, pl, pam, pah, pal = load_experimental_series(DATA_FOLDER, s_id)
                    UI_g, VI_g, dp_g, y0_g = generate_experimental_fluid(
                        IMAX_m2, sd, scdf, pm, ph, pl, pam, pah, pal
                    )
                    
                    _, _, _, acc_g = run_mode_2_zdef_sweep(
                        [zdef_single], UI_g, VI_g, dp_g, y0_g, dt=dt, W=W, gamma=gamma, D_beam=D_beam, ANG=ANG
                    )
                    
                    # 1. GLOBAL STATISTICS
                    if np.sum(acc_g) > 20:
                        U_t, V_t = np.mean(UI_g), np.mean(VI_g)
                        up_t, vp_t = np.std(UI_g, ddof=0), np.std(VI_g, ddof=0)
                        cov_t = np.mean((UI_g - U_t) * (VI_g - V_t))
                        cor_t = cov_t / (up_t * vp_t + 1e-8)
                        
                        U_m, V_m = np.mean(UI_g[acc_g]), np.mean(VI_g[acc_g])
                        up_m, vp_m = np.std(UI_g[acc_g], ddof=0), np.std(VI_g[acc_g], ddof=0)
                        cov_m = np.mean((UI_g[acc_g] - U_m) * (VI_g[acc_g] - V_m))
                        cor_m = cov_m / (up_m * vp_m + 1e-8)
                        
                        eU, eV = U_m - U_t, V_m - V_t
                        eup, evp = up_m - up_t, vp_m - vp_t
                        ecov, ecor = cov_m - cov_t, cor_m - cor_t
                        
                        eU_pct = (eU / (np.abs(U_t) + 1e-8)) * 100
                        eV_pct = (eV / (np.abs(V_t) + 1e-8)) * 100
                        eup_pct = (eup / (up_t + 1e-8)) * 100
                        evp_pct = (evp / (vp_t + 1e-8)) * 100
                        ecov_pct = (ecov / (np.abs(cov_t) + 1e-8)) * 100
                        ecor_pct = (ecor / (np.abs(cor_t) + 1e-8)) * 100
                        
                        taux_acc = (np.sum(acc_g) / len(UI_g)) * 100
                    else:
                        eU = eV = eup = evp = ecov = ecor = np.nan
                        eU_pct = eV_pct = eup_pct = evp_pct = ecov_pct = ecor_pct = np.nan
                        taux_acc = 0.0
                        
                    global_results.append({
                        "Axial Plane Z": z_name, "Radius R": r_name, "TXT Series": s_id,
                        "Bias U (m/s)": eU, "Err U (%)": eU_pct,
                        "Bias V (m/s)": eV, "Err V (%)": eV_pct,
                        "Bias u' (m/s)": eup, "Err u' (%)": eup_pct,
                        "Bias v' (m/s)": evp, "Err v' (%)": evp_pct,
                        "Bias u'v' (m²/s²)": ecov, "Err u'v' (%)": ecov_pct,
                        "Bias UV": ecor, "Err UV (%)": ecor_pct,
                        "Acceptance Rate": taux_acc
                    })
                    
                    # 2. STATISTICS BY SIZE CLASS
                    size_classes = {
                        "< 80 µm": dp_g < 80,
                        "80 - 150 µm": (dp_g >= 80) & (dp_g <= 150),
                        "> 150 µm": dp_g > 150
                    }
                    
                    for class_name, mask in size_classes.items():
                        UI_c = UI_g[mask]
                        VI_c = VI_g[mask]
                        acc_c = acc_g[mask]
                        
                        if np.sum(acc_c) > 20 and len(UI_c) > 20:
                            U_tc, V_tc = np.mean(UI_c), np.mean(VI_c)
                            up_tc, vp_tc = np.std(UI_c, ddof=0), np.std(VI_c, ddof=0)
                            cov_tc = np.mean((UI_c - U_tc) * (VI_c - V_tc))
                            cor_tc = cov_tc / (up_tc * vp_tc + 1e-8)
                            
                            U_mc, V_mc = np.mean(UI_c[acc_c]), np.mean(VI_c[acc_c])
                            up_mc, vp_mc = np.std(UI_c[acc_c], ddof=0), np.std(VI_c[acc_c], ddof=0)
                            cov_mc = np.mean((UI_c[acc_c] - U_mc) * (VI_c[acc_c] - V_mc))
                            cor_mc = cov_mc / (up_mc * vp_mc + 1e-8)
                            
                            eU_c, eV_c = U_mc - U_tc, V_mc - V_tc
                            eup_c, evp_c = up_mc - up_tc, vp_mc - vp_tc
                            ecov_c, ecor_c = cov_mc - cov_tc, cor_mc - cor_tc
                            
                            eU_pct_c = (eU_c / (np.abs(U_tc) + 1e-8)) * 100
                            eV_pct_c = (eV_c / (np.abs(V_tc) + 1e-8)) * 100
                            eup_pct_c = (eup_c / (up_tc + 1e-8)) * 100
                            evp_pct_c = (evp_c / (vp_tc + 1e-8)) * 100
                            ecov_pct_c = (ecov_c / (np.abs(cov_tc) + 1e-8)) * 100
                            ecor_pct_c = (ecor_c / (np.abs(cor_tc) + 1e-8)) * 100
                            
                            taux_acc_c = (np.sum(acc_c) / len(UI_c)) * 100
                        else:
                            eU_c = eV_c = eup_c = evp_c = ecov_c = ecor_c = np.nan
                            eU_pct_c = eV_pct_c = eup_pct_c = evp_pct_c = ecov_pct_c = ecor_pct_c = np.nan
                            taux_acc_c = 0.0 if len(UI_c) > 0 else np.nan
                            
                        class_results.append({
                            "Axial Plane Z": z_name, "Radius R": r_name, "TXT Series": s_id, "Size Class": class_name,
                            "Bias U (m/s)": eU_c, "Err U (%)": eU_pct_c,
                            "Bias V (m/s)": eV_c, "Err V (%)": eV_pct_c,
                            "Bias u' (m/s)": eup_c, "Err u' (%)": eup_pct_c,
                            "Bias v' (m/s)": evp_c, "Err v' (%)": evp_pct_c,
                            "Bias u'v' (m²/s²)": ecov_c, "Err u'v' (%)": ecov_pct_c,
                            "Bias UV": ecor_c, "Err UV (%)": ecor_pct_c,
                            "Acceptance Rate": taux_acc_c
                        })
                        
                except Exception as e:
                    global_results.append({
                        "Axial Plane Z": z_name, "Radius R": r_name, "TXT Series": s_id,
                        "Bias U (m/s)": np.nan, "Err U (%)": np.nan, "Bias V (m/s)": np.nan, "Err V (%)": np.nan,
                        "Bias u' (m/s)": np.nan, "Err u' (%)": np.nan, "Bias v' (m/s)": np.nan, "Err v' (%)": np.nan,
                        "Bias u'v' (m²/s²)": np.nan, "Err u'v' (%)": np.nan, "Bias UV": np.nan, "Err UV (%)": np.nan,
                        "Acceptance Rate": np.nan
                    })
                    
            st.session_state['df_global'] = pd.DataFrame(global_results)
            st.session_state['df_classes'] = pd.DataFrame(class_results)

    # --- TAB UI CREATION ---
    if 'df_global' in st.session_state and 'df_classes' in st.session_state:
        tab_global, tab_classes = st.tabs(["Global Overview", "Analysis by Size Class"])
        
        format_dict = {
            "Bias U (m/s)": "{:+.3f}", "Err U (%)": "{:+.1f} %",
            "Bias V (m/s)": "{:+.3f}", "Err V (%)": "{:+.1f} %",
            "Bias u' (m/s)": "{:+.3f}", "Err u' (%)": "{:+.1f} %",
            "Bias v' (m/s)": "{:+.3f}", "Err v' (%)": "{:+.1f} %",
            "Bias u'v' (m²/s²)": "{:+.4f}", "Err u'v' (%)": "{:+.1f} %",
            "Bias UV": "{:+.3f}", "Err UV (%)": "{:+.1f} %",
            "Acceptance Rate": "{:.1f} %"
        }
        
        with tab_global:
            styled_global = st.session_state['df_global'].style.format(format_dict, na_rep="NaN")
            st.dataframe(styled_global, use_container_width=True, hide_index=True)
            
            # Export Module for Global Table
            csv_global = st.session_state['df_global'].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Global Data as CSV",
                data=csv_global,
                file_name="sdv_global_bias.csv",
                mime="text/csv",
            )
            
        with tab_classes:
            styled_classes = st.session_state['df_classes'].style.format(format_dict, na_rep="NaN")
            st.dataframe(styled_classes, use_container_width=True, hide_index=True)
            
            # Export Module for Size Class Table
            csv_classes = st.session_state['df_classes'].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Size Class Data as CSV",
                data=csv_classes,
                file_name="sdv_class_bias.csv",
                mime="text/csv",
            )
            
            st.markdown("---")
            st.subheader("Relative Error Trends by Particle Size Class")
            
            param_choice = st.selectbox("Select variable for relative error trend plot", ["U", "V", "u'", "v'", "u'v'", "UV"])
            fig_size_trends = go.Figure()
            
            class_order = ["< 80 µm", "80 - 150 µm", "> 150 µm"]
            df_classes = st.session_state['df_classes']
            
            for series_name in df_classes["TXT Series"].unique():
                df_series = df_classes[df_classes["TXT Series"] == series_name]
                
                if not df_series.empty:
                    df_series = df_series.set_index("Size Class").reindex(class_order).reset_index()
                    
                    z_lbl = df_series["Axial Plane Z"].iloc[0]
                    r_lbl = df_series["Radius R"].iloc[0]
                    y_col = f"Err {param_choice} (%)"
                    
                    fig_size_trends.add_trace(go.Scatter(
                        x=df_series["Size Class"],
                        y=df_series[y_col],
                        mode="lines+markers",
                        name=f"Series {series_name} ({z_lbl}, R={r_lbl})"
                    ))
                    
            fig_size_trends.update_layout(
                xaxis_title="Particle Size Class",
                yaxis_title=f"Relative Error on {param_choice} (%)",
                height=500,
                margin=dict(l=0, r=0, b=0, t=30)
            )
            # Add a strong zero line to visually separate over/under estimation
            fig_size_trends.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black')
            
            st.plotly_chart(fig_size_trends, use_container_width=True)
