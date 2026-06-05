import numpy as np
import os
import streamlit as st

@st.cache_data
def load_experimental_series(data_folder, series_id):
    """
    Loads the .txt files for a specific series and computes the polynomials.
    The results are cached to avoid re-reading the disk on every click.
    """
    suffix = f"_{series_id}.txt"
    
    # 1. Size distribution
    size_file = os.path.join(data_folder, f'size_distribution{suffix}')
    if not os.path.exists(size_file):
        # Fallback if the file has no number (single distribution)
        size_file = os.path.join(data_folder, 'size_distribution.txt')
        
    data_size = np.loadtxt(size_file)
    size_d = data_size[:, 0]
    size_prob = data_size[:, 1]
    size_cdf = np.cumsum(size_prob) / np.sum(size_prob)
    
    # 2. Utility function to load and fit
    def get_poly(filename):
        filepath = os.path.join(data_folder, filename)
        if os.path.exists(filepath):
            data = np.loadtxt(filepath)
            # Exact equivalent of MATLAB polyfit(..., 3)
            return np.polyfit(data[:, 0], data[:, 1], 3)
        else:
            raise FileNotFoundError(f"File not found: {filepath}")
    
    # 3. Polynomial computation
    p_mean = get_poly(f'U_mean{suffix}')
    p_high = get_poly(f'U_high{suffix}')
    p_low  = get_poly(f'U_low{suffix}')

    p_angle_mean = get_poly(f'angle_mean{suffix}')
    p_angle_high = get_poly(f'angle_high{suffix}')
    p_angle_low  = get_poly(f'angle_low{suffix}')
    
    return size_d, size_cdf, p_mean, p_high, p_low, p_angle_mean, p_angle_high, p_angle_low