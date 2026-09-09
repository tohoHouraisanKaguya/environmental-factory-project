"""Course hydraulic profile, SI units. Run with --write to export CSV/JSON.

25 m flood is the explicit task-sheet value, not an inferred group number.
External pipe length and disinfection head allowance remain design assumptions.
"""
import csv
import json
import math
import sys
from pathlib import Path
from check_calculation_11 import calculate, pipe


def profile():
    upstream = calculate()
    p = upstream['pipe_segments']
    # Reverse order: downstream to upstream. Design drops include the listed
    # baseline exactly once; spare head covers additional fittings/free drops.
    reaches = [
        ('消毒计量预留', 0.50, 0.50, 0.50),
        ('二沉出水支管及干管', 0.30,
         p['secondary_outlet']['loss_m'] + p['effluent_header_a']['loss_m'],
         p['secondary_outlet']['loss_m'] + p['effluent_header_b']['loss_m']),
        ('二沉锯齿堰及环槽', 0.20, 0.0318567253 + 0.0355 + 0.10,
         0.0318567253 + 0.0355 + 0.10),
        ('二沉进水支管及中心挡板', 0.15, p['secondary_branch']['loss_m'] + 0.0015,
         p['secondary_branch']['loss_m'] + 0.0015),
        ('二沉配水自由堰', 0.50,
         upstream['distribution_weir_head_avg_peak_m']['secondary'][1] + 0.10,
         upstream['distribution_weir_head_avg_peak_m']['secondary'][1] + 0.10),
        ('生物出口支管及混合液总管', 0.35,
         p['bio_to_secondary']['loss_m'] + p['mixed_header']['loss_m'],
         p['bio_to_secondary']['loss_m'] + p['mixed_header']['loss_m']),
        ('生物池内部', 0.30, 0.30, 0.30),
        ('初沉出水至生物入口', 0.20, p['primary_to_bio']['loss_m'], p['primary_to_bio']['loss_m']),
        ('初沉锯齿堰及环槽', 0.20, 0.0417039617 + 0.0696583553 + 0.05,
         0.0417039617 + 0.0696583553 + 0.05),
        ('初沉支管及池内进水', 0.15, p['primary_branch']['loss_m'] + 0.020,
         p['primary_branch']['loss_m'] + 0.020),
        ('初沉配水自由堰', 0.45,
         upstream['distribution_weir_head_avg_peak_m']['primary'][1] + 0.10,
         upstream['distribution_weir_head_avg_peak_m']['primary'][1] + 0.10),
        ('沉砂出口至初沉配水', 0.25, p['grit_to_primary_a']['loss_m'], p['grit_to_primary_b']['loss_m']),
        ('曝气沉砂池内部', 0.25, 0.25, 0.25),
        ('细栅至沉砂连接渠', 0.15, *upstream['fine_to_grit_channel']['loss_A_B_m']),
        ('细格栅堵塞工况', 0.15, 0.121, 0.121),
    ]
    level = 26.0
    rows = []
    for name, drop, loss_a, loss_b in reaches:
        assert drop + 1e-9 >= max(loss_a, loss_b), name
        rows.append(dict(reach=name,downstream_m=round(level,6),upstream_m=round(level+drop,6),
                         design_drop_m=drop,baseline_A_m=loss_a,baseline_B_m=loss_b,
                         spare_A_m=drop-loss_a,spare_B_m=drop-loss_b))
        level += drop
    # Clear-water chamber to river: 28 m inside boundary + assumed 100 m outside.
    internal = p['final_outlet']['loss_m']
    external = pipe('厂外排水',1.625,1.5,100,3)['loss_m']
    outlet_reserve = 0.10
    flood_limit = 26.0-internal-external-outlet_reserve
    gradient_external = 0.020/1.5*(1.625/(math.pi*1.5**2/4))**2/(2*9.81)
    max_external_length = (26-25-outlet_reserve-internal-3*(1.625/(math.pi*1.5**2/4))**2/(2*9.81))/gradient_external
    wet_low, wet_high, wet_floor = 22.6,23.8,20.4
    pump_losses = p['pump_internal']['loss_m'] + p['pump_to_fine']['loss_m']
    head = level-wet_low+pump_losses+0.8
    selected_head = math.ceil(head*2)/2
    power = 1000*9.81*0.625*selected_head/(0.82*0.95)/1000
    volume = 16*10*(wet_high-wet_low)
    inlet_avg = 23.3+1.2*upstream['incoming_D1200']['average_depth_ratio_at_same_gradient']
    inlet_peak = 23.3+1.2*0.75
    # Budget from incoming water surface to wet well; do not count in pump head.
    inlet_loss_peak = 0.30
    inlet_loss_avg = inlet_loss_peak*(1.25/1.625)**2
    assert inlet_peak-inlet_loss_peak > wet_high
    assert inlet_avg-inlet_loss_avg > wet_high
    assert volume >= 0.625*300
    assert abs((wet_low-wet_floor)-2.2)<1e-9
    assert flood_limit > 25
    assert selected_head >= head
    assert power*1.10 <= 90
    assert abs(level-30.1)<1e-8
    # Confirm independently the accumulated profile and a back-calculated balance.
    assert abs(sum(r['design_drop_m'] for r in rows)-(level-26))<1e-8
    assert abs(head-(level-wet_low+pump_losses+0.8)) < 1e-8
    primary_crest=29.3-upstream['distribution_weir_head_avg_peak_m']['primary'][1]
    secondary_crest=27.65-upstream['distribution_weir_head_avg_peak_m']['secondary'][1]
    assert primary_crest-28.85 >= 0.10
    assert secondary_crest-27.15 >= 0.10
    assert 28.7-0.0417039617-(28.5+0.0696583553) >= 0.05
    assert 27.0-0.0318567253-(26.8+0.0355) >= 0.10
    return dict(flood_design_m=25.0,profile=list(reversed(rows)),fine_screen_inlet_m=level,
                flood_ceiling_with_0_1m_reserve_m=flood_limit,
                max_external_length_at_flood25_m=max_external_length,
                external_assumed_m=100,external_loss_m=external,internal_outfall_loss_m=internal,
                inlet_average_peak_m=[inlet_avg,inlet_peak],wet_well_low_high_bottom_m=[wet_low,wet_high,wet_floor],
                inlet_margin_average_peak_m=[inlet_avg-inlet_loss_avg-wet_high,inlet_peak-inlet_loss_peak-wet_high],
                effective_storage_m3=volume,pump_loss_m=pump_losses,
                pump_required_head_m=head,pump_selected_head_m=selected_head,
                electrical_power_per_pump_kW=power,motor_selected_kW=90,
                ras_head_with_0_5m_margin=28.3-27+upstream['return_sludge']['worst_loss_m']+0.5,
                internal_recycle_head_with_0_3m_margin=0.3+upstream['internal_recycle']['loss_m']+0.3,
                flood_scenarios=[dict(group=m,water_level_m=18+0.5*m,
                    sufficient=(18+0.5*m <= flood_limit),
                    required_profile_raise_m=max(0,18+0.5*m-flood_limit)) for m in (6,14,15,16,18)])


if __name__ == '__main__':
    result = profile()
    if '--write' in sys.argv:
        out = Path(__file__).resolve().parents[1]/'计算成果'/'第13项附件'
        out.mkdir(parents=True,exist_ok=True)
        with (out/'高程复核.json').open('w',encoding='utf-8',newline='\n') as f:
            json.dump(result,f,ensure_ascii=False,indent=2)
            f.write('\n')
        with (out/'分段高程表.csv').open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(result['profile'][0]),lineterminator='\n')
            w.writeheader()
            w.writerows(result['profile'])
    print(json.dumps(result,ensure_ascii=False,indent=2))
