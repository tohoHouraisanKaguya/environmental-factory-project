"""Reproduce calculation 10; standard library only, units are SI or stated."""
import json
import math


def calculate():
    q = 108000.0  # m3/d, nominal secondary-stage interface from item 08
    peak = 5850.0  # m3/h; not an actual maximum-day volume
    r, x, xe = 0.75, 3.5, 0.020
    inventory, srt = 48600 * x, 15.0
    loss = inventory / srt
    xu = ((1 + r) * q * x - loss) / (r * q)
    waste = (loss - q * xe) / (xu - xe)
    effluent = q - waste
    count, diameter, feedwell, depth = 6, 36.0, 6.0, 3.0
    area = math.pi * (diameter**2 - feedwell**2) / 4
    area_total = count * area
    water_residual = (1 + r) * q - (effluent + r * q + waste)
    solids_residual = (1 + r) * q * x - ((r * q + waste) * xu + effluent * xe)
    loss_residual = loss - (waste * xu + effluent * xe)
    avg_h, peak_h = q / 24 / count, peak / count
    solid_peak = peak * 24 * (1 + r) * x / area_total
    weir_length = 2 * math.pi * 34
    notches = 1068  # 534 inner, 534 outer
    weir_head = ((peak_h / 3600) / notches / 1.4)**0.4
    trough_v = peak_h / 3600 / (0.8 * 0.6)
    trough_radius = 0.8 * 0.6 / (0.8 + 2 * 0.6)
    trough_gradient = (0.013 * trough_v / trough_radius**(2/3))**2
    trough_loss = trough_gradient * math.pi * 34 / 2 + trough_v**2 / (2 * 9.81)
    ports_area = 72 * 0.25 * 0.25
    mixed_peak = peak_h * (1 + r) / 3600
    ports_head = (mixed_peak / (0.62 * ports_area))**2 / (2 * 9.81)
    store_required = 2 * peak_h * (1 + r) * x / ((x + xu) / 2)
    hopper = math.pi * 3.5 / 12 * (6**2 + 6*1.2 + 1.2**2)
    slope_volume = math.pi * 0.05 * (18*(18**2-3**2) - 2/3*(18**3-3**3))
    store_available = 2 * area + slope_volume + hopper
    assert abs(water_residual) < 1e-8
    assert abs(solids_residual) < 1e-7
    assert abs(loss_residual) < 1e-8
    assert 0.6 <= peak / area_total <= 1.5
    assert solid_peak <= 150
    assert 1.5 <= area_total * depth / peak <= 4
    assert 6 <= diameter / depth <= 12
    assert peak_h / 3.6 / weir_length <= 1.7
    assert 0.1 <= ports_area / (math.pi * feedwell * 1.5) <= 0.2
    assert store_available >= store_required
    assert math.degrees(math.atan(3.5 / ((6-1.2)/2))) >= 55
    assert trough_loss < 0.10
    assert 5 * area * 150 / (24 * (1+r) * x) < peak
    return {
        'return_concentration_kg_m3': xu,
        'waste_m3_d': waste, 'effluent_m3_d': effluent,
        'waste_solids_kg_d': waste * xu, 'effluent_solids_kg_d': effluent * xe,
        'area_per_tank_m2': area, 'area_total_m2': area_total,
        'settling_volume_total_m3': area_total * depth,
        'surface_load_avg_peak_m_h': [q / 24 / area_total, peak / area_total],
        'solids_load_avg_peak_kg_m2_d': [q*(1+r)*x/area_total, solid_peak],
        'nominal_settling_time_avg_peak_h': [area_total*depth/(q/24), area_total*depth/peak],
        'mixed_flow_time_avg_peak_h': [area_total*depth/(q/24*(1+r)), area_total*depth/(peak*(1+r))],
        'weir_length_m': weir_length, 'weir_head_peak_m': weir_head,
        'trough_gradient': trough_gradient, 'trough_loss_upper_m': trough_loss,
        'feedwell_port_velocity_m_s': mixed_peak / ports_area,
        'feedwell_port_loss_m': ports_head,
        'sludge_volume_required_available_m3': [store_required, store_available],
        'hopper_m3': hopper, 'slope_volume_m3': slope_volume,
        'five_tank_capacity_m3_h': 5*area*150/(24*(1+r)*x),
        'two_tank_line_capacity_m3_h': 2*area*150/(24*(1+r)*x),
        'mlss_ceiling_peak_kg_m3': 150*area_total/(24*peak*(1+r)),
        'balance_residuals': [water_residual, solids_residual, loss_residual],
    }


if __name__ == '__main__':
    print(json.dumps(calculate(), ensure_ascii=False, indent=2))
