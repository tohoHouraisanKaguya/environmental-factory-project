"""Reproduce the numerical changes required by the 2026-09-10 teacher review.

Standard-library only.  The output is an audit record, not vendor procurement data.
"""
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "计算成果" / "第14项附件" / "教师审阅复算.json"


def calculate():
    q_avg_h = 108000 / 24
    q_peak_h = 1.625 * 3600

    # Four radial primary clarifiers.  The selected D31 is checked on the net
    # settling area after deducting the D4.5 centre inlet well.
    primary_count = 4
    primary_diameter = 31.0
    primary_centre_well = 4.5
    primary_net_area_each = math.pi * (
        primary_diameter**2 - primary_centre_well**2
    ) / 4
    primary_net_area_total = primary_count * primary_net_area_each
    primary_surface_peak = q_peak_h / primary_net_area_total
    primary_surface_avg = q_avg_h / primary_net_area_total
    primary_depth = 3.0
    primary_hydraulic_retention_peak = (
        primary_net_area_total * primary_depth / q_peak_h
    )
    hopper_top, hopper_bottom, hopper_depth = 4.5, 1.0, 3.0
    hopper_volume = math.pi * hopper_depth / 12 * (
        hopper_top**2 + hopper_top * hopper_bottom + hopper_bottom**2
    )
    hopper_angle = math.degrees(
        math.atan(hopper_depth / ((hopper_top - hopper_bottom) / 2))
    )
    # Item 7's settled-sludge balance gives 375 m3/d total, or 93.75 m3/d
    # per tank.  Four-hour storage therefore requires 15.625 m3 per hopper.
    primary_sludge_each_m3_d = 93.75
    hopper_required = primary_sludge_each_m3_d * 4 / 24

    # Biological nitrogen and phosphorus audit.  Missing raw-water COD/TKN and
    # jar tests are handled as explicit conservative design scenarios.
    tn_removed = (44.4444444444 - 20.0) * 108000 / 1000
    net_vss = 3259.114
    assimilated_n = net_vss * 0.12
    denitrified_n = tn_removed - assimilated_n
    methanol_cod_factor = 1.50  # kgCOD equivalent per kg pure methanol
    denit_cod_factor = 2.86     # kgCOD per kg NO3-N reduced
    methanol_pure = denitrified_n * denit_cod_factor / methanol_cod_factor
    methanol_80 = methanol_pure / 0.80

    p_removed_after_primary = (5.1388888889 - 1.0) * 108000 / 1000
    biological_p_low = net_vss * 0.04
    biological_p_high = net_vss * 0.07
    p_gap_design = p_removed_after_primary - biological_p_low
    fe_p_molar_ratio = 2.0
    molar_p, molar_fecl3 = 30.973762, 162.204
    ferric_chloride_pure = p_gap_design / molar_p * fe_p_molar_ratio * molar_fecl3
    ferric_chloride_40 = ferric_chloride_pure / 0.40
    ferric_solution_density = 1.40  # kg/L, preliminary supplier-check value
    ferric_solution_volume = ferric_chloride_40 / ferric_solution_density / 1000
    ferric_solution_capacity = ferric_solution_volume * 1.20
    chemical_dry_solids = p_gap_design / molar_p * (
        150.815 + (fe_p_molar_ratio - 1) * 106.867
    )

    # Sanitaire Silver Series II 229 mm standard model: catalogue range
    # 0.8--6.8 Nm3/h.  A 5.0 Nm3/h preliminary duty replaces 7.8125.
    air_total = 30000.0
    diffuser_design_airflow = 5.0
    diffuser_count = math.ceil(air_total / diffuser_design_airflow)
    diffuser_per_series = diffuser_count // 4
    oxic_area_total = 4 * 54 * (7.5 * 3.5)  # equivalent 3.5 lanes per series
    diffuser_density = diffuser_count / oxic_area_total

    # Revised hydraulic anchor: A2/O floor at site grade EL 27.30 m.
    fine_screen_upstream = 34.30
    wet_well_low = 22.60
    pump_internal_loss = 0.2246521315 + 0.1330937923
    allowance = 0.80
    pump_head = fine_screen_upstream - wet_well_low + pump_internal_loss + allowance
    pump_flow = 2250 / 3600
    pump_selected_head = 13.0
    pump_input_power = 1000 * 9.81 * pump_flow * pump_selected_head / (0.82 * 0.95) / 1000
    pump_motor_check = pump_input_power * 1.10

    result = {
        "basis": {
            "average_flow_m3_d": 108000,
            "peak_flow_m3_s": 1.625,
            "screen_channels_total": 2,
            "screen_channels_normal_operation": 2,
            "pumps_total": 4,
            "pumps_duty": 3,
            "pumps_standby": 1,
        },
        "primary_clarifier": {
            "count": primary_count,
            "selected_net_diameter_m": primary_diameter,
            "centre_well_diameter_m": primary_centre_well,
            "net_area_each_m2": primary_net_area_each,
            "net_area_total_m2": primary_net_area_total,
            "surface_load_average_m3_m2_h": primary_surface_avg,
            "surface_load_peak_m3_m2_h": primary_surface_peak,
            "settling_depth_m": primary_depth,
            "retention_peak_h": primary_hydraulic_retention_peak,
            "hopper_top_diameter_m": hopper_top,
            "hopper_bottom_diameter_m": hopper_bottom,
            "hopper_depth_m": hopper_depth,
            "hopper_slope_angle_deg": hopper_angle,
            "hopper_volume_each_m3": hopper_volume,
            "hopper_required_four_hours_each_m3": hopper_required,
        },
        "nitrogen_and_carbon": {
            "tn_removed_kg_d": tn_removed,
            "net_biological_vss_kg_d": net_vss,
            "assimilated_n_kg_d": assimilated_n,
            "denitrified_n_design_kg_d": denitrified_n,
            "conservative_cod_demand_kg_d": denitrified_n * denit_cod_factor,
            "pure_methanol_capacity_kg_d": methanol_pure,
            "methanol_80pct_capacity_kg_d": methanol_80,
            "note": "maximum equipment capacity scenario; actual feed is nitrate/COD feedback-controlled",
        },
        "phosphorus_and_ferric_chloride": {
            "p_removed_after_primary_kg_d": p_removed_after_primary,
            "biological_p_range_kg_d": [biological_p_low, biological_p_high],
            "design_p_gap_kg_d": p_gap_design,
            "fe_to_p_molar_ratio": fe_p_molar_ratio,
            "pure_fecl3_kg_d": ferric_chloride_pure,
            "fecl3_solution_40pct_kg_d": ferric_chloride_40,
            "solution_volume_m3_d": ferric_solution_volume,
            "selected_metering_capacity_with_20pct_margin_m3_d": ferric_solution_capacity,
            "estimated_added_dry_solids_kg_d": chemical_dry_solids,
            "note": "course-stage conservative sizing; jar tests and supplier density govern final feed",
        },
        "aeration": {
            "total_air_m3_h": air_total,
            "diffuser_make_model": "Xylem Sanitaire Silver Series II 229 mm standard",
            "catalogue_airflow_range_Nm3_h_each": [0.8, 6.8],
            "design_airflow_Nm3_h_each": diffuser_design_airflow,
            "diffuser_count_total": diffuser_count,
            "diffuser_count_each_series": diffuser_per_series,
            "oxic_plan_area_m2": oxic_area_total,
            "diffuser_density_each_m2": diffuser_density,
            "blower_make_model": "AERZEN AT200-0.8 G5plus",
            "blower_configuration": "6 units, 5 duty + 1 standby",
            "normal_operating_airflow_each_m3_h": 6000,
            "catalogue_max_airflow_m3_h": 8400,
            "catalogue_pressure_kPa": 80,
            "design_header_pressure_kPa": 65,
        },
        "elevation_and_lift": {
            "site_grade_m": 27.30,
            "a2o_floor_m": 27.30,
            "a2o_water_level_m": 32.30,
            "fine_screen_upstream_level_m": fine_screen_upstream,
            "terminal_control_level_m": 30.40,
            "wet_well_low_level_m": wet_well_low,
            "required_pump_head_m": pump_head,
            "selected_pump_head_m": pump_selected_head,
            "pump_input_power_kW": pump_input_power,
            "motor_power_with_10pct_margin_kW": pump_motor_check,
            "selected_motor_kW": 132,
        },
    }

    assert 1.95 <= primary_surface_peak <= 2.00
    assert primary_hydraulic_retention_peak >= 1.5
    assert hopper_angle >= 55 and hopper_volume >= hopper_required
    assert diffuser_count == 6000 and diffuser_per_series == 1500
    assert diffuser_design_airflow <= 6.8
    assert pump_head <= pump_selected_head + 1e-9 and pump_motor_check < 132
    return result


def main():
    result = calculate()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
