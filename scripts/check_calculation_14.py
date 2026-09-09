"""Item 14: reproducible numerical audit, not a certificate of treatment compliance.

Standard library only. Run normally to write the numerical appendix and JSON;
use --check to verify committed artifacts without modifying them. Inputs and
criteria are inherited from items 01-11, not newly measured design conditions.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from check_calculation_10 import calculate as secondary
from check_calculation_11 import calculate as hydraulics
from check_calculation_13 import profile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "计算成果" / "第14项附件"


def calculate():
    q = 600000 * 180 / 1000  # item 01, m3/d
    peak = q / 86400 * 1.3
    loads = dict(BOD5=18000., SS=30000., TN=4800., TP=600.)
    limits = dict(BOD5=20., SS=20., TN=20., TP=1.)
    primary_capture = dict(BOD5=4500., SS=15000., TN=0., TP=45.)
    quality = {}
    for key, incoming in loads.items():
        after = incoming - primary_capture[key]
        allowed = q * limits[key] / 1000
        quality[key] = dict(incoming_kg_d=incoming,
                            incoming_mg_L=incoming / q * 1000,
                            primary_capture_kg_d=primary_capture[key],
                            after_primary_kg_d=after,
                            after_primary_mg_L=after / q * 1000,
                            allowed_kg_d_nominal=allowed,
                            remaining_removal_kg_d=after - allowed,
                            total_removal_percent=(incoming - allowed) / incoming * 100)
        assert abs(incoming - primary_capture[key] - after) < 1e-8

    s = secondary()
    h = hydraulics()
    elevation = profile()
    volume, mlss, srt = 48600., 3.5, 15.
    kd = 0.06 * 1.04 ** (15 - 20)
    vss = 0.5 * 11340 / (1 + kd * srt)
    # Item 08 VSS conversion is a separate estimate, not an added sludge stream.
    assimilated_n = vss * 0.12
    denit = 2640 - assimilated_n
    nit = 4800 - q * 8 / 1000  # conditional all-TN-ammonifiable scenario
    ot = 21 * (1 - 0.25) / (79 + 21 * (1 - 0.25)) * 100
    csm = 8.26 * (ot / 42 + 10 * 0.149 / 2.068)
    transfer = 0.8 * (0.95 * csm - 2) / 9.17 * 1.024 ** 5
    oxygen = {}
    for key, credit in (("assumed_denitrification", denit), ("no_denitrification_credit", 0.)):
        avg = (1.1 * 11340 + 4.57 * nit - 2.86 * credit) / 24
        demand = avg * 1.3 * 1.1
        air = demand / transfer / (0.3 * 0.25)
        capacity = 30000 * 0.3 * 0.25 * transfer
        oxygen[key] = dict(aor_average_kg_h=avg, aor_design_kg_h=demand,
                           sor_kg_h=demand / transfer, required_air_m3_h=air,
                           installed_air_m3_h=30000, field_capacity_kg_h=capacity,
                           capacity_margin_percent=(capacity / demand - 1) * 100,
                           capacity_sufficient=capacity >= demand,
                           working_6000_m3_h_units=math.ceil(air / 6000))
    # Counterfactual boundary tests must remain visible, not be asserted as passes.
    assert oxygen["assumed_denitrification"]["capacity_sufficient"]
    assert not oxygen["no_denitrification_credit"]["capacity_sufficient"]

    primary_waste = 15000 / (1000 * (1 - 0.96))
    q_bio = q - primary_waste
    loss = volume * mlss / srt
    # Separate whole-water sensitivity: no side-stream return or other water loss.
    xr_sensitivity = (q_bio * 1.75 * mlss - loss) / (q_bio * .75)
    qw_sensitivity = (loss - q_bio * .02) / (xr_sensitivity - .02)
    qe_sensitivity = q_bio - qw_sensitivity
    assert abs(q - primary_waste - qw_sensitivity - qe_sensitivity) < 1e-8

    primary_area = 4 * math.pi * 28 ** 2 / 4
    primary_net_area = 4 * math.pi * (28 ** 2 - 4.5 ** 2) / 4
    checks = []

    def check(name, actual, criterion, passes, source):
        checks.append(dict(name=name, actual=actual, criterion=criterion,
                           status="通过" if passes else "不通过/受限", source=source))

    for name, gap, count in (("粗格栅", .025, 44), ("细格栅", .010, 108)):
        velocity = peak / 2 * math.sqrt(math.sin(math.pi / 3)) / (gap * .8 * count)
        blocked_depth = peak / 2 * math.sqrt(math.sin(math.pi / 3)) / (gap * count * .75)
        check(name + "峰值流速 m/s", velocity, "0.6–1.0", .6 <= velocity <= 1., "04")
        check(name + "25%栅隙受阻所需水深 m", blocked_depth,
              "≤1.00（1.50平台减0.50）", blocked_depth <= 1., "04")
    check("提升工作泵总流量 m³/s", 3 * .625, "≥1.625；扬程另核", 3 * .625 >= peak, "05")
    check("湿井两格有效容积 m³", 16 * 10 * 1.2, "≥187.5", 192 >= .625 * 300, "05")
    check("湿井单格检修有效容积 m³", 96, "≥187.5", 96 >= .625 * 300, "05")
    check("沉砂峰值停留 min", 495 / peak / 60, "≥5", 495 / peak / 60 >= 5, "06")
    check("沉砂峰值水平流速 m/s", peak / 2 / (3.3 * 2.5), "≤0.10", peak / 2 / 8.25 <= .1, "06")
    check("沉砂鼓风运行容量 m³/h", 2 * 650, "≥1296", 1300 >= 1296, "06")
    for label, area in (("毛面积", primary_area), ("扣D4.5井净面积敏感性", primary_net_area)):
        load = peak * 3600 / area
        time = area * 3.5 / (peak * 3600)
        check("初沉峰值表面负荷/" + label, load, "1.5–4.5 m³/(m²·h)", 1.5 <= load <= 4.5, "07")
        check("初沉峰值停留/" + label, time, "0.5–2.0 h", .5 <= time <= 2, "07")
    for count in (4, 3):
        v = volume * count / 4
        check(f"生物{count}系列平均HRT h", v / q * 24, "10–23", 10 <= v / q * 24 <= 23, "08")
        check(f"生物{count}系列平均进水污泥负荷", 13500 / (v * mlss), "0.05–0.10 kgBOD5/(kgMLSS·d)",
              .05 <= 13500 / (v * mlss) <= .1, "08")
    check("二沉六池峰值固体负荷", s['solids_load_avg_peak_kg_m2_d'][1],
          "≤150 kg/(m²·d)", s['solids_load_avg_peak_kg_m2_d'][1] <= 150, "10")
    check("二沉五池外来水能力 m³/h", s['five_tank_capacity_m3_h'], "≥5850（全厂峰值）",
          s['five_tank_capacity_m3_h'] >= 5850, "10")
    # Course contrast Kz=1.5 is not substituted into the accepted main design.
    comparison_peak = q / 86400 * 1.5
    check("Kz=1.5对照：沉砂停留 min", 495 / comparison_peak / 60, "≥5",
          495 / comparison_peak / 60 >= 5, "01/06")
    contrast_solids = comparison_peak * 86400 * 1.75 * mlss / s['area_total_m2']
    check("Kz=1.5对照：二沉固体负荷", contrast_solids, "≤150 kg/(m²·d)", contrast_solids <= 150, "01/10")

    sources = {}
    for i in range(1, 14):
        for path in sorted((ROOT / "计算成果").glob(f"{i:02d}_*.md")):
            # Normalize CRLF/LF so a fresh clone has identical source fingerprints.
            sources[path.relative_to(ROOT).as_posix()] = hashlib.sha256(
                path.read_text(encoding='utf-8').encode('utf-8')).hexdigest()
    for name in ("check_calculation_10.py", "check_calculation_11.py", "check_calculation_13.py"):
        path = ROOT / 'scripts' / name
        sources[path.relative_to(ROOT).as_posix()] = hashlib.sha256(
            path.read_text(encoding='utf-8').encode('utf-8')).hexdigest()

    return dict(
        scope="课程计算数值总校核；不等于全厂达标、实测固体生成平衡或施工验证",
        inputs=dict(q_m3_d=q, q_average_m3_s=q / 86400, q_peak_m3_s=peak,
                    peak_hour_m3_h=peak * 3600, kz=1.3),
        quality_nominal=quality, secondary=s, hydraulics=h, elevation=elevation,
        water_balance=dict(primary_sludge_m3_d=primary_waste,
            nominal_secondary_q_m3_d=q, nominal_secondary_effluent_m3_d=s['effluent_m3_d'],
            nominal_interface_excess_m3_d=primary_waste,
            no_side_return_sensitivity=dict(bio_feed_m3_d=q_bio,
                return_concentration_kg_m3=xr_sensitivity, waste_m3_d=qw_sensitivity,
                effluent_m3_d=qe_sensitivity)),
        biological=dict(kd15_per_d=kd, net_biological_vss_kg_d=vss,
            net_biological_mlss_equivalent_kg_d=vss / .75,
            total_solid_loss_kg_d=loss,
            implied_unresolved_ss_conversion_kg_d=15000 + vss / .75 - loss,
            inventory_kg=volume * mlss, oxic_srt_inventory_proxy_d=srt * 28350 / volume,
            denitrification_required_kgN_d=denit, nitrogen_assimilation_assumption_kg_d=assimilated_n,
            nitrification_scenario_kgN_d=nit,
            denit_rate_required_kgN_kgMLVSS_d=denit / (13500 * mlss * .75),
            nitrification_rate_required_kgN_m3_d=nit / 28350,
            nitrogen_balance_residual_kg_d=4800 - (2160 + assimilated_n + denit),
            tp_biological_estimate_kg_d=[vss * .04, vss * .07],
            tp_unresolved_removal_kg_d=[447 - vss * .07, 447 - vss * .04],
            bod_tn_ratio=13500 / 4800, bod_equivalent_screening_gap_kg_d=4 * 4800 - 13500,
            net_alkalinity_consumption_kgCaCO3_d=7.14 * nit - 3.57 * denit,
            influent_alkalinity_boundary_mg_L=(7.14 * nit - 3.57 * denit) / q * 1000 + 70),
        oxygen=dict(transfer_factor=transfer, scenarios=oxygen),
        checks=checks, source_fingerprint_encoding='UTF-8 text with LF newlines', source_sha256=sources,
        missing_calculation_13=not any((ROOT / '计算成果').glob('13_*.md')))


def appendix(data):
    lines = ['# 第14项数值复算附件', '',
             '由 `scripts/check_calculation_14.py` 生成；公式、假定及未通过项的处置见第14项正文。', '',
             '## 取整与运行边界', '', '| 项目 | 复算值 | 继承的判据 | 结论 | 来源项 |',
             '| --- | ---: | --- | --- | --- |']
    for row in data['checks']:
        lines.append(f"| {row['name']} | {row['actual']:.6f} | {row['criterion']} | {row['status']} | {row['source']} |")
    lines += ['', '## 峰值主水线管表', '',
              '长度和阻力系数沿用第11项；二沉区长度为尚待最终平面落位替换的假定。', '',
              '| 管段 | Q m³/s | DN mm | 长度 m | Σζ | v m/s | hf m | hj m | 合计 m |',
              '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for row in data['hydraulics']['pipe_segments'].values():
        lines.append(f"| {row['name']} | {row['flow_m3_s']:.6f} | {row['diameter_m']*1000:.0f} | {row['length_m']:g} | {row['local_k']:g} | {row['velocity_m_s']:.4f} | {row['friction_m']:.4f} | {row['local_m']:.4f} | {row['loss_m']:.4f} |")
    lines += ['', '## 供氧情景', '',
              '| 情景 | 平均AOR kg/h | 峰值含余量AOR kg/h | SOR kg/h | 所需风量 m³/h | 现有供氧余量 |',
              '| --- | ---: | ---: | ---: | ---: | ---: |']
    for key, row in data['oxygen']['scenarios'].items():
        label = '采用假定反硝化回收' if key == 'assumed_denitrification' else '不计反硝化回收的边界'
        lines.append(f"| {label} | {row['aor_average_kg_h']:.2f} | {row['aor_design_kg_h']:.2f} | {row['sor_kg_h']:.2f} | {row['required_air_m3_h']:.2f} | {row['capacity_margin_percent']:.2f}% |")
    lines += ['', '## 第13项逐段高程复核', '',
              '| 管段 | 上游水位 m | 下游水位 m | 分配落差 m | A线需求 m | B线需求 m | A线余量 m |',
              '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for row in data['elevation']['profile']:
        lines.append(f"| {row['reach']} | {row['upstream_m']:.3f} | {row['downstream_m']:.3f} | {row['design_drop_m']:.3f} | {row['baseline_A_m']:.4f} | {row['baseline_B_m']:.4f} | {row['spare_A_m']:.4f} |")
    lines += ['', '三段暂留额度（沉砂、生物、消毒计量）余量为零，须按实际构造/设备验证；不得当作已测阻力。', '',
              '全精度质量收支、回流及来源指纹见同目录 `总校核结果.json`。', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = calculate()
    products = {'总校核结果.json': json.dumps(data, ensure_ascii=False, indent=2) + '\n',
                '数值与管渠复算表.md': appendix(data)}
    for name, content in products.items():
        path = OUT / name
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8') != content:
                raise SystemExit(f'需重新生成或核对来源变更：{path.relative_to(ROOT)}')
        else:
            OUT.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8', newline='\n')
    restricted = sum(row['status'] != '通过' for row in data['checks'])
    print(f"复算及附件一致性通过：{len(data['checks'])}项，其中{restricted}项为明确记录的检修/对照限制。")
    print('处理能力闭合状态：有保留项；不得将程序成功解释为全厂达标。')


if __name__ == '__main__':
    main()
