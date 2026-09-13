"""Recalculate the frozen interfaces for second-revision batches 1 and 2.

The script does not modify either public Word source or the public status
workbook.  With ``--write`` it emits only the three group calculation JSON
attachments under ``02_成果回收``.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "第二次修改协作项目_2026-09-13" / "02_成果回收"
G = 9.81


def pipe(flow_m3_s: float, diameter_m: float, length_m: float, local_k: float, friction: float = 0.020) -> dict:
    area = math.pi * diameter_m**2 / 4
    velocity = flow_m3_s / area
    velocity_head = velocity**2 / (2 * G)
    friction_loss = friction * length_m / diameter_m * velocity_head
    local_loss = local_k * velocity_head
    return {
        "flow_m3_s": flow_m3_s,
        "diameter_m": diameter_m,
        "length_m": length_m,
        "local_k": local_k,
        "friction_factor": friction,
        "velocity_m_s": velocity,
        "friction_loss_m": friction_loss,
        "local_loss_m": local_loss,
        "total_loss_m": friction_loss + local_loss,
    }


def group02() -> dict:
    average_m3_d = 108_000.0
    average_m3_h = average_m3_d / 24
    average_m3_s = average_m3_h / 3_600
    kz = 1.50
    peak_m3_h = average_m3_h * kz
    peak_m3_s = peak_m3_h / 3_600
    line_peak_m3_s = peak_m3_s / 2
    pump_peak_m3_s = line_peak_m3_s / 2
    line_average_m3_s = average_m3_s / 2

    internal = pipe(pump_peak_m3_s, 0.70, 12.0, 4.3)
    discharge = pipe(line_peak_m3_s, 1.00, 35.0, 2.0)
    static_lift = 34.30 - 22.60
    allowance = 0.80
    required_head = static_lift + internal["total_loss_m"] + discharge["total_loss_m"] + allowance
    selected_head = 14.0
    hydraulic_input_kw = 1000 * G * pump_peak_m3_s * selected_head / 0.80 / 1000
    design_input_kw = hydraulic_input_kw * 1.10
    motor_kw = 90.0

    wet_well_required_each = pump_peak_m3_s * 5 * 60
    wet_well_each = 16.0 * 10.0 * 1.20

    diameter = 1.20
    depth = 0.75 * diameter
    theta = 2 * math.acos((diameter / 2 - depth) / (diameter / 2))
    area = diameter**2 / 8 * (theta - math.sin(theta))
    wetted_perimeter = diameter / 2 * theta
    hydraulic_radius = area / wetted_perimeter
    sewer_velocity = peak_m3_s / area
    manning_n = 0.013
    sewer_slope = (sewer_velocity * manning_n / hydraulic_radius ** (2 / 3)) ** 2

    result = {
        "flow": {
            "average_m3_d": average_m3_d,
            "average_m3_h": average_m3_h,
            "average_m3_s": average_m3_s,
            "kz": kz,
            "peak_m3_h": peak_m3_h,
            "peak_m3_s": peak_m3_s,
            "line_average_m3_h": line_average_m3_s * 3600,
            "line_peak_m3_h": line_peak_m3_s * 3600,
            "line_peak_m3_s": line_peak_m3_s,
        },
        "pump_scheme": {
            "lines": 2,
            "count": 6,
            "duty": 4,
            "standby": 2,
            "arrangement": "每条水线2用1备，共4用2备；不采用3用1备",
            "flow_each_m3_h": pump_peak_m3_s * 3600,
            "flow_each_m3_s": pump_peak_m3_s,
            "average_line_pumps_equivalent": line_average_m3_s / pump_peak_m3_s,
            "control": "定速泵台数及液位启停调节；平均日每线1台连续加第2台间歇，最高时每线2台全开",
            "head_required_m": required_head,
            "head_selected_m": selected_head,
            "efficiency_assumed": 0.80,
            "hydraulic_input_power_kW": hydraulic_input_kw,
            "power_with_10pct_kW": design_input_kw,
            "motor_selected_kW": motor_kw,
            "internal_branch": internal,
            "line_discharge": discharge,
        },
        "wet_well": {
            "cells": 2,
            "pumps_per_cell": 3,
            "cell_dimensions_m": [16.0, 10.0, 1.20],
            "volume_each_m3": wet_well_each,
            "required_largest_pump_5min_m3": wet_well_required_each,
            "start_frequency_limit_per_h": 6,
        },
        "influent_d1200": {
            "diameter_m": diameter,
            "depth_ratio": 0.75,
            "water_depth_m": depth,
            "area_m2": area,
            "wetted_perimeter_m": wetted_perimeter,
            "hydraulic_radius_m": hydraulic_radius,
            "peak_velocity_m_s": sewer_velocity,
            "manning_n": manning_n,
            "slope": sewer_slope,
            "slope_permille": sewer_slope * 1000,
            "site_grade_el_m": 27.30,
            "invert_el_m": 23.30,
            "invert_depth_m": 4.00,
        },
        "screens": {
            "coarse": {"count": 2, "gap_mm": 25, "openings": 48, "channel_width_m": 1.75, "design_flow_each_m3_s": line_peak_m3_s},
            "fine": {"count": 2, "gap_mm": 10, "openings": 122, "channel_width_m": 2.10, "design_flow_each_m3_s": line_peak_m3_s},
            "maintenance_boundary": "维持两条独立水线；单线停运时不得宣称另一台格栅可承担全厂峰值，须限流或启用另设超越/备用通道。",
        },
    }

    assert math.isclose(peak_m3_s, 1.875)
    assert math.isclose(4 * result["pump_scheme"]["flow_each_m3_s"], peak_m3_s)
    assert wet_well_each >= wet_well_required_each
    assert required_head <= selected_head
    assert design_input_kw <= motor_kw
    assert 0.6 <= internal["velocity_m_s"] <= 2.5
    assert 0.6 <= discharge["velocity_m_s"] <= 2.5
    assert math.isclose(result["influent_d1200"]["invert_depth_m"], 4.0)
    return result


def group03() -> dict:
    q = 108_000.0
    t = 15.0
    s0 = 125.0
    se = 20.0
    x = 3.50
    y = 0.70
    yt = 0.40
    srt = 20.0
    ras = 0.75
    internal_recycle = 2.50
    kde20 = 0.045
    kde_t = kde20 * 1.08 ** (t - 20)
    delta_xv = q * (s0 - se) * y * yt / 1000
    influent_tn = 44.44444444444444
    effluent_tn = 20.0
    nitrogen_before_assimilation = q * (influent_tn - effluent_tn) / 1000
    denitrification_n = nitrogen_before_assimilation - 0.12 * delta_xv
    required_anoxic_volume = denitrification_n / (kde_t * x)
    selected_anoxic_volume = 21_600.0
    capacity_n = selected_anoxic_volume * kde_t * x

    pure_methanol_ratio = 160 / 84
    product_fraction = 0.80
    capacity_factor = 1.20
    methanol_80 = denitrification_n * pure_methanol_ratio / product_fraction * capacity_factor
    methanol_peak_kg_h = methanol_80 * 1.50 / 24

    tp_after_primary = 555.0
    target_tp = 108.0
    biological_removal_fraction = 0.60
    tp_after_biological = tp_after_primary * (1 - biological_removal_fraction)
    chemical_p = tp_after_biological - target_tp
    fe_p_molar_ratio = 1.50
    p_molar_mass = 30.973761998
    fecl3_molar_mass = 162.204
    fepo4_molar_mass = 150.816
    feoh3_molar_mass = 106.867
    p_kmol = chemical_p / p_molar_mass
    pure_fecl3 = p_kmol * fe_p_molar_ratio * fecl3_molar_mass
    fecl3_solution = pure_fecl3 / 0.40 / 1400
    fecl3_capacity = fecl3_solution * 1.20
    chemical_solids = p_kmol * fepo4_molar_mass + p_kmol * (fe_p_molar_ratio - 1) * feoh3_molar_mass

    nitrification_upper = q * (influent_tn - 8.0) / 1000
    alkalinity_nitrification = 7.14 * nitrification_upper
    alkalinity_denitrification_credit = 3.57 * denitrification_n
    alkalinity_ferric = p_kmol * fe_p_molar_ratio * 3 * 50
    residual_alkalinity = 70 * q / 1000
    alkalinity_required = alkalinity_nitrification - alkalinity_denitrification_credit + alkalinity_ferric + residual_alkalinity
    required_influent_alkalinity = alkalinity_required / q * 1000
    assumed_influent_alkalinity = 100.0
    deficit = max(0.0, required_influent_alkalinity - assumed_influent_alkalinity)
    nahco3 = deficit * q / 1000 * 84 / 50 / 0.99
    nahco3_capacity = nahco3 * 1.20

    result = {
        "method": {
            "denitrification": "HJ 576-2010 6.4.2式(8)-(10)，并由6.5.2用于A2/O",
            "external_carbon": "HJ 576-2010 6.8.1；商品甲醇按化学计量并加20%课程容量系数",
            "chemical_phosphorus": "HJ 576-2010 6.8.2及GB 50014-2021 7.10；投加量最终以试验确定",
            "alkalinity": "HJ 576-2010 5.2.3；硝化7.14、反硝化回补3.57 kgCaCO3/kgN",
        },
        "frozen_parameters": {
            "design_temperature_C": t,
            "MLSS_kg_m3": x,
            "MLVSS_MLSS_fraction": y,
            "MLVSS_kg_m3": x * y,
            "system_SRT_d": srt,
            "total_HRT_h": 14.0,
            "anaerobic_HRT_h": 1.5,
            "anoxic_HRT_h": 4.8,
            "oxic_HRT_h": 7.7,
            "RAS_ratio": ras,
            "internal_recycle_ratio": internal_recycle,
            "DO_anaerobic_mg_L_max": 0.2,
            "DO_anoxic_mg_L_range": [0.2, 0.5],
            "DO_oxic_mg_L_min": 2.0,
            "total_yield_MLSS_per_BOD5": yt,
            "Kde20_kgN_kgMLSS_d": kde20,
            "Kde15_kgN_kgMLSS_d": kde_t,
        },
        "denitrification": {
            "delta_Xv_kg_d": delta_xv,
            "nitrogen_before_assimilation_kgN_d": nitrogen_before_assimilation,
            "assimilation_credit_kgN_d": 0.12 * delta_xv,
            "required_kgN_d": denitrification_n,
            "required_anoxic_volume_m3": required_anoxic_volume,
            "selected_anoxic_volume_m3": selected_anoxic_volume,
            "selected_capacity_kgN_d": capacity_n,
            "capacity_margin_percent": (capacity_n / denitrification_n - 1) * 100,
        },
        "methanol_80pct": {
            "pure_stoichiometric_kg_per_kgN": pure_methanol_ratio,
            "product_capacity_factor": capacity_factor,
            "calculated_capacity_kg_d": methanol_80,
            "selected_storage_feed_capacity_kg_d": math.ceil(methanol_80 / 100) * 100,
            "peak_meter_requirement_kg_h": methanol_peak_kg_h,
            "meter_configuration": "2台100%容量计量泵，单台不小于450 kg/h；按NOx反馈调节",
            "storage_days": [7, 14],
        },
        "chemical_phosphorus": {
            "biological_TP_removal_fraction_lower_bound": biological_removal_fraction,
            "TP_after_biological_kgP_d": tp_after_biological,
            "chemical_P_required_kgP_d": chemical_p,
            "Fe_P_molar_ratio": fe_p_molar_ratio,
            "pure_FeCl3_kg_d": pure_fecl3,
            "FeCl3_40pct_solution_m3_d": fecl3_solution,
            "selected_capacity_m3_d": math.ceil(fecl3_capacity * 10) / 10,
            "meter_configuration": "2台100%容量计量泵，单台不小于0.15 m3/h；最终按烧杯试验修正",
            "chemical_dry_solids_kg_d": chemical_solids,
        },
        "alkalinity_upper_boundary": {
            "warning": "进水TKN/NH4-N和实测碱度缺失；下列仅以TN代NH4-N的课程容量上界，不是固定运行投加量。",
            "nitrification_upper_kgN_d": nitrification_upper,
            "required_influent_alkalinity_mg_L_as_CaCO3": required_influent_alkalinity,
            "assumed_influent_alkalinity_mg_L_as_CaCO3": assumed_influent_alkalinity,
            "NaHCO3_99pct_kg_d": nahco3,
            "selected_capacity_with_20pct_kg_d": math.ceil(nahco3_capacity / 100) * 100,
        },
    }

    assert 0.65 <= y <= 0.70
    assert 10 <= srt <= 25
    assert 0.03 <= kde20 <= 0.06
    assert selected_anoxic_volume >= required_anoxic_volume
    assert result["denitrification"]["capacity_margin_percent"] > 0
    assert chemical_p > 0
    return result


def group05(g02: dict) -> dict:
    q_avg_h = g02["flow"]["average_m3_h"]
    q_peak_h = g02["flow"]["peak_m3_h"]
    line_peak_s = g02["flow"]["line_peak_m3_s"]

    grit_l, grit_b, grit_h, grit_count = 30.0, 3.80, 2.55, 2
    grit_volume_each = grit_l * grit_b * grit_h
    grit_velocity = line_peak_s / (grit_b * grit_h)
    grit_peak_min = grit_volume_each / line_peak_s / 60
    grit_average_min = grit_volume_each / (q_avg_h / 3600 / grit_count) / 60

    primary_count, primary_l, primary_b, primary_h = 4, 58.0, 14.5, 3.5
    primary_area_each = primary_l * primary_b
    primary_area_total = primary_count * primary_area_each
    primary_q_each_peak_s = q_peak_h / 3600 / primary_count
    hopper_top_length, hopper_bottom_length, hopper_depth = 3.0, 0.8, 2.0
    hopper_mid_length = (hopper_top_length + hopper_bottom_length) / 2
    hopper_volume = hopper_depth / 6 * (
        primary_b * hopper_top_length
        + 4 * primary_b * hopper_mid_length
        + primary_b * hopper_bottom_length
    )
    hopper_angle = math.degrees(math.atan(hopper_depth / ((hopper_top_length - hopper_bottom_length) / 2)))

    secondary_count, secondary_d, centre_d, secondary_h = 8, 37.0, 6.0, 3.1
    secondary_area_each = math.pi / 4 * (secondary_d**2 - centre_d**2)
    secondary_area_total = secondary_count * secondary_area_each
    total_mlss = 4.3789964586
    ras = 0.75
    provisional_daily_chemical_solids = 2768.8388446
    solids_peak = (
        q_peak_h * 24 * (1 + ras) * total_mlss + provisional_daily_chemical_solids
    ) / secondary_area_total
    periphery_depth = secondary_h + 0.50 + 0.40
    slope_drop = (secondary_d / 2 - centre_d / 2) * 0.05
    centre_depth = periphery_depth + slope_drop + 0.50
    base_storage = secondary_area_each * 0.40
    wedge_storage = math.pi * slope_drop / 3 * ((secondary_d / 2) ** 2 + (secondary_d / 2) * (centre_d / 2) + (centre_d / 2) ** 2) - math.pi * (centre_d / 2) ** 2 * slope_drop
    sump_storage = math.pi * centre_d**2 / 4 * 0.50

    result = {
        "grit": {
            "count": grit_count,
            "net_dimensions_each_m": [grit_l, grit_b, grit_h],
            "volume_each_m3": grit_volume_each,
            "width_depth_ratio": grit_b / grit_h,
            "length_width_ratio": grit_l / grit_b,
            "peak_velocity_m_s": grit_velocity,
            "retention_peak_min": grit_peak_min,
            "retention_average_min": grit_average_min,
            "floor": "平底；池内不设局部砂斗；吸砂机沿池长往复排砂至池外砂水分离器",
            "elevation_interface": {"water_el_m": 33.75, "floor_el_m": 31.20},
        },
        "primary": {
            "count": primary_count,
            "type": "平流式",
            "net_dimensions_each_m": [primary_l, primary_b, primary_h],
            "area_each_m2": primary_area_each,
            "area_total_m2": primary_area_total,
            "surface_load_average_m3_m2_h": q_avg_h / primary_area_total,
            "surface_load_peak_m3_m2_h": q_peak_h / primary_area_total,
            "retention_average_h": primary_area_total * primary_h / q_avg_h,
            "retention_peak_h": primary_area_total * primary_h / q_peak_h,
            "horizontal_velocity_peak_m_s": primary_q_each_peak_s / (primary_b * primary_h),
            "length_width_ratio": primary_l / primary_b,
            "length_depth_ratio": primary_l / primary_h,
            "floor_slope": 0.01,
            "scraper_direction": "桁车式刮泥机沿58 m池长运行，坡向进水端横向条形泥斗",
            "transverse_hopper": {
                "top_m": [primary_b, hopper_top_length],
                "bottom_m": [primary_b, hopper_bottom_length],
                "depth_m": hopper_depth,
                "longitudinal_wall_angle_deg": hopper_angle,
                "side_walls": "沿14.5 m池宽竖直贯通，不缩成0.8 m方形下口",
                "volume_m3": hopper_volume,
                "four_hour_required_m3": 15.625,
            },
            "elevation_interface": {
                "water_el_m": 33.00,
                "nominal_settling_floor_el_m": 29.50,
                "hopper_lip_floor_el_m": 28.92,
                "hopper_bottom_el_m": 26.92,
                "note": "沉淀有效水深按3.5 m名义水平面计；0.01池底纵坡及泥斗列入污泥区。",
            },
        },
        "secondary": {
            "count": secondary_count,
            "type": "辐流式",
            "net_diameter_m": secondary_d,
            "centre_well_diameter_m": centre_d,
            "settling_depth_m": secondary_h,
            "net_area_each_m2": secondary_area_each,
            "net_area_total_m2": secondary_area_total,
            "surface_load_average_m3_m2_h": q_avg_h / secondary_area_total,
            "surface_load_peak_m3_m2_h": q_peak_h / secondary_area_total,
            "nominal_external_retention_average_h": secondary_area_total * secondary_h / q_avg_h,
            "nominal_external_retention_peak_h": secondary_area_total * secondary_h / q_peak_h,
            "D_h": secondary_d / secondary_h,
            "provisional_total_MLSS_kg_m3": total_mlss,
            "provisional_daily_chemical_solids_kg_d": provisional_daily_chemical_solids,
            "provisional_peak_SLR_kg_m2_d": solids_peak,
            "SLR_status": "待第04组按第03组新参数重算总MLSS后替换；几何尺寸先冻结",
            "depth_components_m": {
                "settling": secondary_h,
                "buffer": 0.50,
                "peripheral_sludge_storage": 0.40,
                "peripheral_total": periphery_depth,
                "slope_drop": slope_drop,
                "centre_sump": 0.50,
                "centre_total": centre_depth,
            },
            "storage_each_m3": {
                "base": base_storage,
                "slope_wedge": wedge_storage,
                "centre_sump": sump_storage,
                "total": base_storage + wedge_storage + sump_storage,
            },
            "elevation_interface": {"water_el_m": 31.40, "peripheral_floor_el_m": 27.40, "inner_floor_el_m": 26.625, "sump_bottom_el_m": 26.125},
        },
    }

    assert 0.6 <= grit_b / grit_h <= 1.5
    assert grit_velocity <= 0.10
    assert grit_peak_min >= 5.0
    assert primary_l / primary_b >= 4.0
    assert primary_l / primary_h >= 8.0
    assert 0.005 <= result["primary"]["horizontal_velocity_peak_m_s"] <= 0.010
    assert hopper_angle >= 55
    assert hopper_volume >= 15.625
    assert 6 <= secondary_d / secondary_h <= 12
    assert solids_peak <= 150
    assert math.isclose(centre_depth, 5.275)
    return result


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    path.write_bytes(payload.encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    g02 = group02()
    g03 = group03()
    g05 = group05(g02)
    all_results = {"group02": g02, "group03": g03, "group05": g05}
    if args.write:
        write_json(RESULTS / "第02组_流量工艺顺序与提升系统" / "第02组_复算结果.json", g02)
        write_json(RESULTS / "第03组_脱氮除磷方法与参数" / "第03组_复算结果.json", g03)
        write_json(RESULTS / "第05组_沉砂初沉二沉结构" / "第05组_复算结果.json", g05)
    print(json.dumps(all_results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
