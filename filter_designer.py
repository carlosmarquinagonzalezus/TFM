from scipy.signal import butter, cheby1, cheby2, ellip, sosfreqz
import numpy as np
from real2fix_point import real2fix_point

# Calculates filter coefficients
def calc_filter_coeffs(filter_order, filter_type, filter_wn, filter_response, filter_ripple, filter_att_stopband, fs):

    filter_map = {
        'butter': butter,
        'cheby1': cheby1,
        'cheby2': cheby2,
        'ellip' : ellip
    }

    if filter_type not in filter_map:
        raise ValueError(f"Unknown filter type [{filter_type}]. Use: 'butter', 'cheby1', 'cheby2', 'ellip'")

    design_func = filter_map[filter_type]

    match filter_type:
        case 'butter':
            sos = design_func(filter_order, filter_wn, filter_response, output='sos', fs=fs)
        case 'cheby1':
            sos = design_func(filter_order, filter_ripple, filter_wn, filter_response, output='sos', fs=fs)
        case 'cheby2':
            sos = design_func(filter_order, filter_att_stopband, filter_wn, filter_response, output='sos', fs=fs)
        case 'ellip':
            sos = design_func(filter_order, filter_ripple, filter_att_stopband, filter_wn, filter_response, output='sos', fs=fs)

    w,h = sosfreqz(sos,worN=2**20,fs=fs)
    return w, h, sos

# External API for GUI
def run_filter_from_gui(order, ftype, wn, response, ripple=None, min_att=None, fs=None):
    """
    Called by GUI to compute and return w, h and the auto-generated filename.
    """
    w, h, sos = calc_filter_coeffs(order, ftype, wn, response, ripple, min_att, fs)

    # Generate filename
    if isinstance(wn, (list, tuple, np.ndarray)):
        wn_str = "_".join([str(round(v, 5)) for v in wn])
    else:
        wn_str = str(round(wn, 5))

    filename = f"{ftype}_{response}_n{order}_wn_{wn_str}"
    if ripple is not None:
        filename += f"_rp_{ripple}"
    if min_att is not None:
        filename += f"_min_att_{min_att}"
    filename += ".csv"

    return w, h, filename
