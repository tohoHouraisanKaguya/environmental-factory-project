#!/usr/bin/env python3
"""Reproduce and verify the frozen calculations for revision batches 3 and 4."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "第二次修改协作项目_2026-09-13" / "02_成果回收"


def velocity(flow_m3_s: float, diameter_m: float) -> float:
    return flow_m3_s / (math.pi * diameter_m**2 / 4)


def batch3() -> dict:
    q_avg_d = 108_000.0
    q_avg_h = q_avg_d / 24
    kz = 1.5
    q_peak_h = q_avg_h * kz
    q_peak_d_equiv = q_avg_d * kz
    series = 4

    volume = 63_000.0
    mlss_base = 3.5
    mlvss_fraction = 0.70
    srt = 20.0
    chemical_solids = 751.7473338079983
    chemical_inventory = chemical_solids * srt
    chemical_mlss = chemical_inventory / volume
    mlss_total = mlss_base + chemical_mlss

    ras_ratio = 0.75
    ir_ratio = 2.50

    bod_removed = q_avg_d * (125.0 - 20.0) / 1000
    delta_xv = 3175.2
    assimilation_n = 0.12 * delta_xv
    nitrification_n = 3936.0 - assimilation_n
    denitrification_n = 2258.976
    methanol_cod = 6500.0 * 0.80 * 1.50
    oxygen_parts = {
        "carbonaceous_kg_d": 1.47 * bod_removed,
        "external_methanol_COD_kg_d": methanol_cod,
        "biomass_credit_kg_d": -1.42 * delta_xv,
        "nitrification_kg_d": 4.57 * nitrification_n,
        "denitrification_credit_kg_d": -0.62 * 4.57 * denitrification_n,
    }
    aor_daily = sum(oxygen_parts.values())
    aor_design_hourly = aor_daily / 24 * kz * 1.10

    alpha = 0.80
    beta = 0.95
    temperature = 25.0
    do = 2.0
    c_standard = 9.17
    c_mid_depth = 9.29844016842796
    transfer_factor = (
        alpha
        * (beta * c_mid_depth - do)
        * 1.024 ** (temperature - 20)
        / c_standard
    )
    sor_hourly = aor_design_hourly / transfer_factor
    ea = 0.25
    air_hj20_required = sor_hourly / (0.28 * ea)
    air_n0_required = air_hj20_required * 273.15 / 293.15
    air_n0_selected = 48_000.0
    air_hj20_selected = air_n0_selected * 293.15 / 273.15
    field_oxygen_capacity = air_hj20_selected * 0.28 * ea * transfer_factor

    air_each_n0 = 12_000.0
    inlet_actual_42 = (
        air_each_n0
        * 315.15
        / 273.15
        * 101.325
        / (98.325 - 8.20)
    )
    air_actual_total = inlet_actual_42 * 4 / 3600

    secondary_area = 8375.486014470389
    slr_average = (
        q_avg_d * (1 + ras_ratio) * mlss_total + chemical_solids
    ) / secondary_area
    slr_peak = (
        q_peak_d_equiv * (1 + ras_ratio) * mlss_total
        + kz * chemical_solids
    ) / secondary_area

    result = {
        "basis": {
            "input_git_commit": "c378540",
            "average_flow_m3_d": q_avg_d,
            "average_flow_m3_h": q_avg_h,
            "kz": kz,
            "peak_flow_m3_h": q_peak_h,
            "series": series,
        },
        "a2o": {
            "dimensions_each_m": [70.0, 45.0, 5.0],
            "volume_each_m3": volume / series,
            "volume_total_m3": volume,
            "hrt_average_h": volume / q_avg_h,
            "hrt_peak_h": volume / q_peak_h,
            "zone_hrt_h": {"anaerobic": 1.5, "anoxic": 4.8, "oxic": 7.7},
            "zone_volume_total_m3": {
                "anaerobic": 6750.0,
                "anoxic": 21600.0,
                "oxic": 34650.0,
            },
            "zone_equivalent_path_each_series_m": {
                "anaerobic": 45.0,
                "anoxic": 144.0,
                "oxic": 231.0,
            },
            "MLSS_base_kg_m3": mlss_base,
            "MLVSS_MLSS_fraction": mlvss_fraction,
            "MLVSS_kg_m3": mlss_base * mlvss_fraction,
            "SRT_d": srt,
            "BOD5_MLSS_load_kg_kg_d": 13_500.0 / (volume * mlss_base),
            "BOD5_MLVSS_load_kg_kg_d": 13_500.0 / (volume * mlss_base * mlvss_fraction),
        },
        "return_flows": {
            "RAS_ratio": ras_ratio,
            "RAS_average": {
                "total_m3_h": q_avg_h * ras_ratio,
                "per_line_m3_h": q_avg_h * ras_ratio / 2,
                "per_series_m3_h": q_avg_h * ras_ratio / series,
            },
            "RAS_peak": {
                "total_m3_h": q_peak_h * ras_ratio,
                "per_line_m3_h": q_peak_h * ras_ratio / 2,
                "per_series_m3_h": q_peak_h * ras_ratio / series,
                "per_secondary_pool_m3_h": q_peak_h * ras_ratio / 8,
            },
            "internal_recycle_ratio": ir_ratio,
            "internal_recycle_average": {
                "total_m3_h": q_avg_h * ir_ratio,
                "per_line_m3_h": q_avg_h * ir_ratio / 2,
                "per_series_m3_h": q_avg_h * ir_ratio / series,
            },
            "internal_recycle_peak": {
                "total_m3_h": q_peak_h * ir_ratio,
                "per_line_m3_h": q_peak_h * ir_ratio / 2,
                "per_series_m3_h": q_peak_h * ir_ratio / series,
            },
            "RAS_pumps": {
                "count": 6,
                "duty": 4,
                "standby": 2,
                "arrangement": "两条水线各2用1备；每条线的备用泵经阀组择一接入两系列",
                "flow_each_m3_h": 1266.0,
                "head_selected_m": 3.0,
                "motor_selected_kW": 18.5,
                "branch_DN_mm": 500,
                "series_header_DN_mm": 700,
            },
            "internal_recycle_pumps": {
                "count": 6,
                "duty": 4,
                "standby": 2,
                "arrangement": "两条水线各2用1备；共用取水廊道和阀门切换矩阵",
                "flow_each_m3_h": 4219.0,
                "head_selected_m": 1.2,
                "motor_selected_kW": 22.0,
                "series_pipe_DN_mm": 1200,
            },
        },
        "solids_and_secondary_check": {
            "base_MLSS_kg_m3": mlss_base,
            "base_inventory_kg": volume * mlss_base,
            "base_waste_solids_kg_d_at_20d": volume * mlss_base / srt,
            "chemical_dry_solids_kg_d": chemical_solids,
            "chemical_inventory_kg_at_20d": chemical_inventory,
            "chemical_MLSS_increment_kg_m3": chemical_mlss,
            "total_MLSS_to_secondary_kg_m3": mlss_total,
            "total_waste_solids_kg_d_at_20d": volume * mlss_total / srt,
            "secondary_area_total_m2": secondary_area,
            "SLR_average_kg_m2_d": slr_average,
            "SLR_peak_kg_m2_d": slr_peak,
            "fresh_chemical_solids_location": "A2/O出水后、二沉池前；峰时按Kz同步放大",
        },
        "aeration": {
            "oxygen_equation": "HJ 576-2010式(15)，外加甲醇COD单列，反硝化氧当量只扣一次",
            "oxygen_parts": oxygen_parts,
            "AOR_average_kg_d": aor_daily,
            "AOR_average_kg_h": aor_daily / 24,
            "peak_factor": kz,
            "equipment_margin_factor": 1.10,
            "AOR_design_kg_h": aor_design_hourly,
            "alpha": alpha,
            "beta": beta,
            "temperature_C": temperature,
            "DO_mg_L": do,
            "transfer_factor": transfer_factor,
            "SOR_design_kg_h": sor_hourly,
            "EA_design_fraction": ea,
            "air_required_m3_h_at_20C_101325Pa": air_hj20_required,
            "air_required_Nm3_h_at_0C_101325Pa": air_n0_required,
            "air_selected_Nm3_h_at_0C_101325Pa": air_n0_selected,
            "field_oxygen_capacity_kg_h": field_oxygen_capacity,
            "capacity_margin_fraction": field_oxygen_capacity / aor_design_hourly - 1,
            "diffuser": {
                "reference": "229 mm盘式微孔曝气器；厂家样本0.8-6.8 Nm3/h·盘，SOTE 6%-8%/m",
                "count": 9600,
                "count_per_series": 2400,
                "flow_each_Nm3_h": 5.0,
                "density_each_m2_of_oxic_floor": 9600 / 6930.0,
            },
            "blower": {
                "reference_size": "AERZEN AT 400-0.8 G5或等效",
                "count": 6,
                "duty": 4,
                "standby": 2,
                "flow_each_Nm3_h_at_0C": air_each_n0,
                "design_pressure_kPa_g": 65.0,
                "reference_suction_conditions_envelope_m3_h": [5400.0, 16200.0],
                "actual_inlet_each_m3_h_at_42C_filter_and_saturated": inlet_actual_42,
                "reference_max_assembly_power_kW": 330.0,
                "main_header_DN_mm": 1200,
                "main_header_velocity_m_s": air_actual_total / (math.pi * 1.2**2 / 4),
                "series_branch_DN_mm": 700,
                "series_branch_velocity_m_s": (inlet_actual_42 / 3600) / (math.pi * 0.7**2 / 4),
            },
            "pressure_budget_kPa": {
                "static_at_4_75m": 4.75 * 9.81,
                "diffuser": 5.0,
                "pipe_and_valves": 6.0,
                "allowance": 3.0,
                "required": 4.75 * 9.81 + 5.0 + 6.0 + 3.0,
                "selected": 65.0,
            },
        },
    }

    assert math.isclose(result["a2o"]["hrt_average_h"], 14.0)
    assert result["aeration"]["field_oxygen_capacity_kg_h"] >= aor_design_hourly
    assert 5400 <= air_each_n0 <= 16_200
    assert slr_peak <= 150.0
    assert result["return_flows"]["RAS_peak"]["per_series_m3_h"] <= 1266.0
    assert result["return_flows"]["internal_recycle_peak"]["per_series_m3_h"] <= 4219.0
    return result


def batch4(b3: dict) -> dict:
    q_avg_h = 4500.0
    q_peak_h = 6750.0
    ras_ratio = b3["return_flows"]["RAS_ratio"]
    mixed_peak_series_m3_h = q_peak_h * (1 + ras_ratio) / 4
    mixed_peak_well_m3_h = mixed_peak_series_m3_h * 2
    mixed_peak_branch_m3_h = mixed_peak_well_m3_h / 4
    branch_q_m3_s = mixed_peak_branch_m3_h / 3600

    weir_width = 1.20
    weir_coefficient = 1.84
    weir_head = (branch_q_m3_s / (weir_coefficient * weir_width)) ** (2 / 3)

    contact_volume = 2 * 45.0 * 8.0 * 4.8

    chlorine_nominal = 5.0
    chlorine_capacity = 15.0
    naocl_fraction = 0.10
    available_chlorine_factor = 70.906 / 74.442
    available_chlorine_fraction = naocl_fraction * available_chlorine_factor
    solution_density = 1200.0
    effective_chlorine_avg_nominal_kg_d = q_avg_h * 24 * chlorine_nominal / 1000
    effective_chlorine_avg_capacity_kg_d = q_avg_h * 24 * chlorine_capacity / 1000
    effective_chlorine_peak_capacity_kg_h = q_peak_h * chlorine_capacity / 1000
    solution_avg_nominal_m3_d = (
        effective_chlorine_avg_nominal_kg_d
        / (available_chlorine_fraction * solution_density)
    )
    solution_avg_capacity_m3_d = (
        effective_chlorine_avg_capacity_kg_d
        / (available_chlorine_fraction * solution_density)
    )
    solution_peak_capacity_m3_h = (
        effective_chlorine_peak_capacity_kg_h
        / (available_chlorine_fraction * solution_density)
    )

    result = {
        "basis": {
            "input_git_commit": "c378540",
            "average_flow_m3_h": q_avg_h,
            "peak_flow_m3_h": q_peak_h,
            "A2O_series": 4,
            "secondary_pools": 8,
            "secondary_net_diameter_m": 37.0,
            "RAS_ratio": ras_ratio,
        },
        "distribution": {
            "selected_scheme": "2座二沉配水井，每井接收2个A2/O系列并向4座二沉池等量配水",
            "well_count": 2,
            "secondary_pools_per_well": 4,
            "A2O_series_per_well": 2,
            "external_flow_peak_per_well_m3_h": q_peak_h / 2,
            "mixed_flow_peak_per_A2O_series_m3_h": mixed_peak_series_m3_h,
            "mixed_flow_peak_per_well_m3_h": mixed_peak_well_m3_h,
            "mixed_flow_peak_per_secondary_branch_m3_h": mixed_peak_branch_m3_h,
            "external_flow_peak_per_secondary_outlet_m3_h": q_peak_h / 8,
            "pipes": {
                "A2O_series_inlet_to_well": {
                    "count": 4,
                    "DN_mm": 1200,
                    "flow_each_m3_s": mixed_peak_series_m3_h / 3600,
                    "velocity_m_s": velocity(mixed_peak_series_m3_h / 3600, 1.2),
                },
                "optional_common_section_in_well": {
                    "count": 2,
                    "DN_mm": 1500,
                    "flow_each_m3_s": mixed_peak_well_m3_h / 3600,
                    "velocity_m_s": velocity(mixed_peak_well_m3_h / 3600, 1.5),
                },
                "secondary_inlet_branch": {
                    "count": 8,
                    "DN_mm": 900,
                    "flow_each_m3_s": branch_q_m3_s,
                    "velocity_m_s": velocity(branch_q_m3_s, 0.9),
                },
                "secondary_outlet_branch": {
                    "count": 8,
                    "DN_mm": 700,
                    "flow_each_m3_s": q_peak_h / 8 / 3600,
                    "velocity_m_s": velocity(q_peak_h / 8 / 3600, 0.7),
                },
                "secondary_outlet_header_per_line": {
                    "count": 2,
                    "DN_mm": 1200,
                    "flow_each_m3_s": q_peak_h / 2 / 3600,
                    "velocity_m_s": velocity(q_peak_h / 2 / 3600, 1.2),
                },
            },
            "equal_weir_each_branch": {
                "type": "等高矩形薄壁堰，设闸门与流量测量",
                "count_per_well": 4,
                "width_each_m": weir_width,
                "course_coefficient": weir_coefficient,
                "peak_head_m": weir_head,
                "adopted_head_budget_m": 0.35,
            },
            "maintenance": "两井入口及出水设联络和隔离；单井检修时限流运行，不宣称另一井可独立承担全厂最高时流量",
        },
        "contact_tank": {
            "cells": 2,
            "net_dimensions_each_m": [45.0, 8.0, 4.8],
            "net_volume_each_m3": contact_volume / 2,
            "net_volume_total_m3": contact_volume,
            "required_volume_at_peak_30min_m3": q_peak_h * 0.5,
            "volume_margin_fraction": contact_volume / (q_peak_h * 0.5) - 1,
            "contact_time_peak_min": contact_volume / q_peak_h * 60,
            "contact_time_average_min": contact_volume / q_avg_h * 60,
            "lanes_per_cell": 4,
            "net_lane_width_m": 2.0,
            "equivalent_flow_path_each_cell_m": 180.0,
            "dimension_note": "8.0 m为扣除隔墙后的净水宽；3道0.20 m隔墙时结构池内总宽至少8.60 m",
        },
        "disinfection": {
            "medium": "二沉池澄清出水",
            "chemical": "次氯酸钠",
            "GB50014_dose_without_test_mg_L": [5.0, 15.0],
            "nominal_effective_chlorine_mg_L": chlorine_nominal,
            "equipment_capacity_effective_chlorine_mg_L": chlorine_capacity,
            "product_assumption": {
                "NaOCl_mass_fraction": naocl_fraction,
                "available_chlorine_factor_Cl2_per_NaOCl": available_chlorine_factor,
                "available_chlorine_mass_fraction": available_chlorine_fraction,
                "density_kg_m3": solution_density,
                "note": "若供货证书直接标10%有效氯，则按证书重算，不再乘0.9525",
            },
            "effective_chlorine_average_nominal_kg_d": effective_chlorine_avg_nominal_kg_d,
            "effective_chlorine_average_capacity_kg_d": effective_chlorine_avg_capacity_kg_d,
            "effective_chlorine_peak_capacity_kg_h": effective_chlorine_peak_capacity_kg_h,
            "solution_average_nominal_m3_d": solution_avg_nominal_m3_d,
            "solution_average_capacity_m3_d": solution_avg_capacity_m3_d,
            "solution_peak_capacity_m3_h": solution_peak_capacity_m3_h,
            "metering_pumps": {
                "count": 2,
                "duty": 1,
                "standby": 1,
                "capacity_each_m3_h": 1.0,
                "control": "流量前馈加余氯反馈；最终剂量按消毒需求和微生物试验校准",
            },
            "storage": {
                "maximum_days": 7,
                "working_volume_total_m3_at_average_flow_and_15mg_L": solution_avg_capacity_m3_d * 7,
                "selected_split": "2座工作容积约50 m3储罐；低温、避光，库存不超过7 d",
            },
        },
        "terminal_metering": {
            "channels": 2,
            "design_flow_each_m3_s": q_peak_h / 2 / 3600,
            "long_throat_width_m": 1.5,
            "critical_depth_m": ((q_peak_h / 2 / 3600) ** 2 / (9.81 * 1.5**2)) ** (1 / 3),
        },
        "frozen_process_order": "初沉池→A2/O→二沉配水井→二沉池→接触池（次氯酸钠）→计量/控制井",
        "elevation_interface_m": {
            "A2O_water": 32.30,
            "secondary_distribution_upstream": 31.95,
            "secondary_distribution_downstream": 31.55,
            "secondary_water": 31.40,
            "contact_tank_water": 30.90,
            "control_well_water": 30.40,
        },
    }

    assert result["distribution"]["well_count"] * result["distribution"]["secondary_pools_per_well"] == 8
    assert math.isclose(result["contact_tank"]["contact_time_peak_min"], 30.72)
    assert result["contact_tank"]["contact_time_peak_min"] >= 30.0
    assert result["distribution"]["equal_weir_each_branch"]["peak_head_m"] <= 0.35
    assert result["disinfection"]["metering_pumps"]["capacity_each_m3_h"] >= solution_peak_capacity_m3_h
    assert result["disinfection"]["storage"]["working_volume_total_m3_at_average_flow_and_15mg_L"] <= 100.0
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write the two versioned JSON outputs")
    args = parser.parse_args()

    b3 = batch3()
    b4 = batch4(b3)
    if args.write:
        targets = [
            (
                OUTPUT / "第04组_A2O回流曝气与鼓风机" / "第04组_复算结果.json",
                b3,
            ),
            (
                OUTPUT / "第06组_二沉配水与消毒" / "第06组_复算结果.json",
                b4,
            ),
        ]
        for path, data in targets:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
            print(path.relative_to(ROOT))
    else:
        print(json.dumps({"batch3": b3, "batch4": b4}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
