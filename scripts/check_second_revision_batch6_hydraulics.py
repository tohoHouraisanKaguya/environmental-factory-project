#!/usr/bin/env python3
"""Group 08 course hydraulic design envelope; SI units, standard library only.

Reads frozen upstream files, never rewrites them. --write rebuilds only group 08
outputs; default verifies committed outputs. Water levels are peak design control
levels with explicit balancing head, not a calibrated unsteady network solution.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '第二次修改协作项目_2026-09-13' / '02_成果回收'
OUT = BASE / '第08组_全厂水力高程'
G = 9.81
N = 0.013
LAMBDA = 0.025  # course adopted value, sensitivity checked at 0.030


def source(group, pattern):
    return next(next(BASE.glob(f'第{group:02d}组_*')).glob(pattern))


def read_json(group):
    return json.loads(source(group, '*复算结果.json').read_text(encoding='utf-8'))


def ceil05(x):
    return math.ceil((x - 1e-10) * 20) / 20


def pipe(q, d, length, k, factor=LAMBDA):
    v = q / (math.pi * d * d / 4)
    hv = v * v / (2 * G)
    return v, factor * length / d * hv, k * hv


def channel(q, b, y, length, k):
    v = q / (b * y)
    radius = b * y / (b + 2 * y)
    return v, (N * v / radius ** (2 / 3)) ** 2 * length, k * v * v / (2 * G)


def weir(q, b):
    return (q / (1.84 * b)) ** (2 / 3)


def solve_depth(q, b, energy):
    yc = (q * q / (G * b * b)) ** (1 / 3)
    lo, hi = yc, energy
    for _ in range(100):
        mid = (lo + hi) / 2
        if mid + (q / (b * mid)) ** 2 / (2 * G) < energy:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def build():
    g2, g4, g5, g6 = (read_json(i) for i in (2, 4, 5, 6))
    layout_file = source(7, '*面积与控制路径.json')
    layout = json.loads(layout_file.read_text(encoding='utf-8'))
    route_file = source(7, '*管线中心线长度.csv')
    with route_file.open(encoding='utf-8-sig', newline='') as f:
        routes = {r['管段编号']: r for r in csv.DictReader(f)}
    q = g2['flow']['peak_m3_s']
    scale = g2['flow']['average_m3_s'] / q
    ras_ratio = g4['return_flows']['RAS_ratio']
    assert math.isclose(q,1.875) and math.isclose(ras_ratio,.75)
    assert g2['pump_scheme']['count']==6 and g4['a2o']['volume_total_m3']==63000
    records = []

    def row(path, stage, code, flow, diameter=0, width=0, depth=0,
            plan=None, extra=0, k=None, allowance=0, note=''):
        r = routes.get(code)
        if plan is None:
            plan = float(r['管道中心线长度_m']) if r else 0
        if k is None:
            # Four vertical elbows per buried inter-basin link, two per
            # submerged centre-feed. Entrance + exit + full-open gate = 1.7.
            k = 1.7 + 1.1 * (int(r['转弯数']) if r else 0) + (4.4 if extra else 0)
        method = 'Darcy' if diameter else 'Manning' if width else 'allowance'
        values = []
        for s in (scale, 1.0):
            if diameter:
                v, hf, hl = pipe(flow * s, diameter, plan + extra, k)
            elif width:
                v, hf, hl = channel(flow * s, width, depth, plan + extra, k)
            else:
                v, hf, hl = 0, 0, 0
            values.append((v, hf, hl))
        a, p = values
        result = dict(path=path, stage=stage, segment=code, method=method,
                      q_peak_m3_s=flow, q_average_m3_s=flow * scale,
                      diameter_m=diameter, width_m=width, depth_m=depth,
                      plan_length_m=plan, vertical_allowance_m=extra,
                      length_for_loss_m=plan + extra, lambda_=LAMBDA if diameter else 0,
                      manning_n=N if width else 0, local_k=k,
                      velocity_peak_m_s=p[0], velocity_average_m_s=a[0],
                      friction_peak_m=p[1], local_peak_m=p[2],
                      friction_average_m=a[1], local_average_m=a[2],
                      structure_allowance_m=allowance,
                      required_peak_m=p[1] + p[2] + allowance,
                      required_average_m=a[1] + a[2] + allowance, note=note)
        records.append(result)
        return result

    xs = [34, 78, 122, 166, 234, 278, 322, 366]
    # Stages connect control water surfaces; no pipe entrance/exit is counted
    # again in the adjoining unit allowance.
    names = ['细格栅前', '细格栅后', '沉砂入口', '沉砂主体', '初沉配水上游',
             '初沉配水下游', '初沉主体', '初沉集水槽', 'A2O入口', 'A2O主体',
             '二沉配水上游', '二沉配水下游', '二沉主体', '二沉集水槽',
             '接触池入口', '接触池出口', '计量上游', '计量下游', '出厂汇合井', '东厂界控制井']
    for tank in range(1, 9):
        p = f'T{tank}'
        line = 'A' if tank <= 4 else 'B'
        series = (tank + 1) // 2
        row(p, 0, '细格栅堵塞', q/2, allowance=0.15, k=0,
            note='沿用课程堵塞水头预算；未作为清洁栅条实测值')
        for code in ('W04', f'W05{line}'):
            row(p, 1, code, q/2, width=1.5, depth=1.0,
                k=0.5 + 0.5*int(routes[code]['转弯数']), note='每线独立1.5 m渠，峰值计算水深1.0 m')
        row(p, 2, '沉砂池内', q/2, width=3.8, depth=2.55, plan=30,
            k=2, allowance=0.25, note='0.25 m池内整流/曝气扰动及出口预算，管口另计')
        row(p, 3, f'W06{line}', q/2, diameter=1.2, extra=20)
        row(p, 4, '初沉自由配水堰', q/4, k=0,
            allowance=weir(q/4, 2.0)+0.10, note='每支2.0 m堰；h+0.10 m自由跌水，不称纯摩擦损失')
        row(p, 5, f'W07{line}F', q/2, diameter=1.2, k=0.1)
        row(p, 5, f'W07C{series}', q/4, diameter=0.9, extra=20, allowance=0.02)
        row(p, 6, '初沉集水系统', q/4, k=0, allowance=0.20,
            note='指形槽12×14 m，堰及槽内落差预算0.20 m；详见报告校核')
        row(p, 7, f'W08C{series}', q/4, diameter=0.9, extra=20)
        row(p, 8, 'A2O池内', q/4*(1+ras_ratio+2.5), k=0, allowance=0.30,
            note='保留池内分区/进出流0.30 m课程预算；不可将全部内回流计入二沉外管')
        row(p, 9, f'W09B{series}', q/4*(1+ras_ratio), diameter=1.2, extra=20)
        row(p, 10, '二沉自由配水堰', q/8*(1+ras_ratio), k=0,
            allowance=weir(q/8*(1+ras_ratio), 1.2)+0.10, note='每井4支；1.2 m等高堰，自由跌水至少0.10 m')
        row(p, 11, f'W10T{tank}', q/8*(1+ras_ratio), diameter=0.9, extra=20,
            allowance=0.02, note='附加20 m包络含中心竖管和进池高差；中心配水另留0.02 m')
        row(p, 12, '二沉堰槽', q/8, k=0, allowance=0.20)
        row(p, 13, f'W11T{tank}', q/8, diameter=0.7, extra=10,
            note='至埋地汇流管；10 m竖段额度，含4个转弯保守预算')
        # Shared effluent headers are split at every junction. Total line flow
        # occurs only downstream of all four joining branches.
        x = xs[tank-1]
        if line == 'A':
            points = [z for z in [34,78,122,166,270] if z >= x]
            for a,b in zip(points,points[1:]):
                contributors = sum(v <= a for v in xs[:4])
                row(p, 13, f'W11AH:{a}-{b}', q/8*contributors, diameter=1.2,
                    plan=b-a, k=1.5, note='按上游已汇入池数计流量；节点局部ζ=1.5课程包络')
        else:
            points = [234,270] if x == 234 else [z for z in [366,322,278,270] if z <= x]
            for a,b in zip(points,points[1:]):
                contributors = 1 if a == 234 else sum(v >= a for v in xs[4:])
                row(p, 13, f'W11BH:{a}-{b}', q/8*contributors, diameter=1.2,
                    plan=abs(b-a), k=1.5, note='B管向x270双向汇流，右侧最多3池，左侧1池')
        row(p, 13, f'W11{line}C', q/2, diameter=1.2, extra=10,
            note='接触池上升段，10 m竖段预算；出口速度头已计')
        row(p, 14, '接触池四廊道', q/2, width=2, depth=4.8, plan=180,
            k=3*1.5, allowance=0.10, note='三处折返；0.10 m进出池整流预算')
        row(p, 15, f'W12{line}', q/2, width=1.5, depth=1, k=0.5)
        row(p, 16, '长喉道自由跌水计量', q/2, k=0, allowance=0.75,
            note='水面落差预算；含临界控制、槽内损失和尾端消能，不把1.5yc当不可逆损失')
        row(p, 17, f'W13{line}', q/2, diameter=1.2, extra=10,
            note='本组定为DN1200连接管；计量后跌水井接埋管')
        row(p, 18, 'W14', q, diameter=1.5, k=1.7,
            note='地下满流管到东界控制井；厂外排口另列条件算例')

    stages = []
    for i in range(19):
        sums = {f'T{t}': sum(r['required_peak_m'] for r in records
                                if r['path'] == f'T{t}' and r['stage'] == i) for t in range(1,9)}
        worst = max(sums, key=sums.get)
        # 15% allowance on actual conduits; fixed structure/crest drops are
        # retained and rounded up. This reserve covers <=20% lambda growth.
        required = sums[worst]
        design = ceil05(required * (1.15 if i in (1,3,5,7,9,11,13,15,17,18) else 1))
        stages.append(dict(stage=i, start=names[i], end=names[i+1],
                           worst_path=worst, required_peak_m=required,
                           adopted_drop_m=design, reserve_m=design-required))
    levels = [0.0]*20
    levels[9] = 32.30
    for i in range(8,-1,-1):
        levels[i] = levels[i+1] + stages[i]['adopted_drop_m']
    for i in range(9,19):
        levels[i+1] = levels[i] - stages[i]['adopted_drop_m']
    for s in stages:
        s.update(upstream_el_m=levels[s['stage']], downstream_el_m=levels[s['stage']+1])

    paths = []
    for t in range(1,9):
        rs = [r for r in records if r['path'] == f'T{t}']
        peak = sum(r['required_peak_m'] for r in rs)
        avg = sum(r['required_average_m'] for r in rs)
        sensitive = peak + sum(r['friction_peak_m']*0.2 for r in rs if r['method']=='Darcy')
        paths.append(dict(path=f'T{t}', peak_required_m=peak,
                          average_capacity_check_m=avg, lambda030_required_m=sensitive,
                          adopted_total_m=sum(s['adopted_drop_m'] for s in stages),
                          peak_balancing_and_reserve_m=sum(s['adopted_drop_m'] for s in stages)-peak))
    balance = []
    for t in range(1,9):
        for i,s in enumerate(stages):
            rs = [r for r in records if r['path']==f'T{t}' and r['stage']==i]
            req = sum(r['required_peak_m'] for r in rs)
            sens = req + sum(r['friction_peak_m']*.2 for r in rs if r['method']=='Darcy')
            assert s['adopted_drop_m']+1e-9 >= sens, (t,i,sens)
            balance.append(dict(path=f'T{t}',stage=i,upstream_el_m=levels[i],
                                downstream_el_m=levels[i+1], required_peak_m=req,
                                balancing_head_m=s['adopted_drop_m']-req,
                                lambda030_margin_m=s['adopted_drop_m']-sens))
    # Explicit process geometry. Greater primary depth at sludge hopper is not
    # confused with nominal 3.5 m settling depth.
    floors = {0:levels[1]-1,1:levels[1]-1,2:levels[3]-2.55,3:levels[3]-2.55,
              4:levels[4]-1.5,5:levels[5]-1.5,6:levels[6]-3.5,
              7:levels[7]-0.6,8:27.30,9:27.30,10:levels[10]-2,
              11:levels[11]-2,12:levels[12]-4,13:levels[13]-0.6,
              14:levels[15]-4.8,15:levels[15]-4.8,16:levels[16]-1,
              17:levels[17]-1,18:24.5,19:24.5}
    nodes = [dict(node=name,water_peak_el_m=levels[i],floor_el_m=floors[i],
                  wall_top_el_m=max(levels[i]+0.5,27.3),
                  floor_below_site_m=27.3-floors[i],
                  note='负埋深表示高于地面；工艺内底不含结构板厚') for i,name in enumerate(names)]
    details = dict(primary_slope_low_floor_m=floors[6]-0.58,
                   primary_hopper_bottom_m=floors[6]-0.58-2,
                   secondary_inner_floor_m=floors[12]-0.775,
                   secondary_sump_bottom_m=floors[12]-0.775-0.5,
                   grit_floor_m=floors[3],a2o_floor_m=27.3)
    # Buried pipe barrel crowns at EL26 provide 1.3 m cover, submerged entries
    # and exits 0.5 m below adjoining water surface; vertical budgets verified.
    pipe_profile=[]
    for r in records:
        if r['method'] != 'Darcy':
            continue
        i=r['stage']; d=r['diameter_m']; center=26-d/2
        needed=max(0,levels[i]-.5-center)+max(0,levels[i+1]-.5-center)
        if r['vertical_allowance_m']==20:
            assert needed <=20, (r['segment'],needed)
        elif r['vertical_allowance_m']==10:
            # W11T has a down-leg; W11AC/BC an up-leg; W13 a down-leg.
            needed=max(0,(levels[i+1] if r['segment'].endswith('C') else levels[i])-.5-center)
            assert needed<=10
        else:
            needed=0
        assert min(levels[i],levels[i+1])-26 > .2
        pipe_profile.append(dict(path=r['path'],segment=r['segment'],diameter_m=d,
                                 barrel_invert_el_m=26-d,barrel_crown_el_m=26,
                                 cover_m=1.3,vertical_required_m=needed,
                                 vertical_budget_m=r['vertical_allowance_m'],
                                 note='水平埋管，端部竖向转接；局部最高点设排气；各交叉另作结构详图'))
    # Fixed inlet at 75% full at peak, average normal depth from same slope.
    def inlet_capacity(y):
        theta=2*math.acos(1-2*y/1.2)
        area=.6**2*(theta-math.sin(theta))/2
        radius=area/(.6*theta)
        return area*radius**(2/3)*math.sqrt(g2['influent_d1200']['slope'])/N
    lo,hi=.001,.9
    for _ in range(90):
        mid=(lo+hi)/2
        if inlet_capacity(mid)<q*scale: lo=mid
        else: hi=mid
    inlet_avg_y=(lo+hi)/2
    inlet=[]
    for label,flow,y in [('average',q*scale,inlet_avg_y),('peak',q,.9)]:
        slope=g2['influent_d1200']['slope']; incoming=23.3+y
        v,hf,hl=channel(flow/2,1.75,.8,4,.5)
        screen=.10*(flow/q)**2
        after=incoming-slope*14-screen-hf-hl
        # Reconcile inflow with the upstream locked 23.80 high operating level.
        inlet.append(dict(case=label,boundary_water_el_m=incoming,
                          coarse_front_el_m=incoming-slope*14,
                          coarse_loss_m=screen,channel_loss_m=hf+hl,
                          available_at_well_el_m=after,well_high_el_m=23.80,
                          margin_to_high_m=after-23.8))
        assert after>23.8
    # Pump branch includes 4 m horizontal/equipment plus the new vertical rise.
    # elevation, 11 m plan + explicit 2 m equipment transition, two plan elbows.
    branch_length=math.ceil(4+max(0,levels[0]-.5-22.0))
    v,phf,phl=pipe(q/4,.7,branch_length,4.3)
    v,dhf,dhl=pipe(q/2,1,13,1.7+2*1.1)
    pump_loss=phf+phl+dhf+dhl
    hreq=levels[0]-22.6+pump_loss+.8
    hsel=max(14,math.ceil(hreq*2)/2)
    power=q/4*G*hsel/.8
    motor=next(k for k in [90,110,132,160,200] if k>=power*1.1)
    pump=dict(count=6,duty=4,standby=2,flow_each_m3_h=q/4*3600,
              suction_min_el_m=22.6,discharge_control_el_m=levels[0],
              static_m=levels[0]-22.6,branch_loss_m=phf+phl,line_loss_m=dhf+dhl,
              line_plan_length_m=11,line_equipment_extra_m=2,branch_length_m=branch_length,
              reserve_m=.8,required_head_m=hreq,selected_head_m=hsel,
              assumed_pump_efficiency=.8,shaft_power_kW=power,
              shaft_power_with_margin_kW=power*1.1,motor_selected_kW=motor,
              note='泵轴功率与电输入功率分开；最低水位最大静扬程；采购须确认曲线及NPSH')
    assert 22.0+branch_length-4>=levels[0]-.5
    # Return sludge: each pool branch plus its half of RH, then RB.
    ras=[]
    for t in range(1,9):
        series=(t+1)//2; x=xs[t-1]; target=[50,150,250,350][series-1]
        parts=[pipe(q/8*ras_ratio,.5,36+6,5),
               pipe(q/8*ras_ratio,.7,abs(x-target),1.5),
               pipe(q/4*ras_ratio,.7,22+6,5)]
        loss=sum(a+b for _,a,b in parts)
        needed=levels[8]-levels[12]+loss+.5
        ras.append(dict(pool=f'T{t}',plan_m=36+abs(x-target)+22,
                        static_m=levels[8]-levels[12],dynamic_m=loss,
                        reserve_m=.5,required_m=needed))
    ras_h=max(3,ceil05(max(r['required_m'] for r in ras)))
    ras_selected=math.ceil(ras_h*2)/2
    ras_power=q/4*ras_ratio*G*ras_selected/.70*1.1
    ras_motor=next(p for p in [18.5,22,30,37] if p>=ras_power)
    ir_parts=pipe(q/4*2.5,1.2,80+4,4.0)
    ir_required=.30+sum(ir_parts[1:])+.30
    ir_selected=max(1.2,math.ceil(ir_required*10)/10)
    # Air: conservative density 1.293 kg/m3 at normal volume gives greater
    # rho*v^2 than the same mass flow in a 65 kPa(g), 42 C compressed line.
    # A00 longest single-direction path 826 m explicitly covers one isolated
    # ring section, rather than only the 150 m shortest normal supply route.
    air=[]
    for label,length in [('normal_shortest',150),('ring_isolation',826)]:
        total=0
        for flow,d,l,k in [(48000/3600,1.2,length,8),(12000/3600,.7,4+5,5)]:
            v=flow/(math.pi*d*d/4)
            total+=(.025*l/d+k)*1.293*v*v/2/1000
        air.append(dict(case=label,header_length_m=length,loss_kPa=total,
                        required_with_diffuser_and_reserve_kPa=4.75*9.81+5+total+3))
    assert max(r['required_with_diffuser_and_reserve_kPa'] for r in air)<65
    # Check outlet trough allowances using the new rectangular primary tank,
    # not the obsolete radial-primary ring-channel length.
    primary_h=weir(q/4,12*14)
    finger=channel(q/4/12,.4,.4,14,1)
    collector=channel(q/4,1.2,.6,14.5,1)
    primary_req=primary_h+.05+sum(finger[1:])+sum(collector[1:])
    secondary_h=weir(q/8,math.pi*37)
    ring=channel(q/16,.6,.6,math.pi*37/2,1)
    secondary_req=secondary_h+.10+sum(ring[1:])
    assert primary_req<.20 and secondary_req<.20
    # Every original external path is reconstructed independently of water-loss
    # arithmetic. This catches stale lengths even when totals happen to close.
    for t in range(1,9):
        plan=sum(r['plan_length_m'] for r in records if r['path']==f'T{t}'
                 and r['segment'].startswith('W'))
        # Includes W04 onwards; add W01/W02/W03, which are pump-front/discharge.
        plan+=sum(float(routes[c]['管道中心线长度_m']) for c in ('W01','W02','W03'))
        frozen=layout['control_paths']['all_water_paths'][t-1]['external_centerline_total_m']
        assert math.isclose(plan,frozen),(t,plan,frozen)
    # Long-throated rectangular control, not a Parshall calibration.
    flow=q/2; b=1.5; yc=(flow*flow/(G*b*b))**(1/3)
    approach_hv=(flow/b)**2/(2*G)
    crest=levels[16]+approach_hv-1.5*yc-.03
    sill_above_approach=crest-(levels[16]-1)
    avg_yc=((flow*scale)**2/(G*b*b))**(1/3)
    avg_y=solve_depth(flow*scale,b,sill_above_approach+1.5*avg_yc+.03*scale**2)
    meter=dict(width_m=b,throat_length_m=2.5,approach_depth_peak_m=1,
               critical_depth_peak_m=yc,critical_depth_average_m=avg_yc,
               approach_peak_el_m=levels[16],approach_average_el_m=levels[16]-1+avg_y,
               throat_floor_el_m=crest,throat_peak_water_el_m=crest+yc,
               downstream_peak_el_m=levels[17],crest_above_tail_m=crest-levels[17],
               entry_friction_budget_m=.03,adopted_water_drop_m=.75,
               calibration='课程临界能量初算；2.5 m喉道、渐变入口、尾端跌水消能；未宣称厂家标定精度')
    assert crest-levels[17]>.1
    assert 0.1<1.5*yc/2.5<.5
    contact_min_depth=4.8-(1-avg_y)
    contact_time_avg=2*45*8*contact_min_depth/(q*scale)/60
    assert contact_time_avg>30
    # Outside boundary only a declared scenario, not an invented surveyed length.
    ext=pipe(q,1.5,100,3)
    flood_ceiling=levels[19]-sum(ext[1:])-.1
    assert flood_ceiling>25
    final=dict(input_git_commit='10c36c6432fd37090353385b9132d690240aa4ba',
               status='课程设计输入冻结；工程采用条件见报告',
               anchor=dict(a2o_floor_el_m=27.3,a2o_water_el_m=32.3),
               total_drop_to_boundary_m=levels[0]-levels[19],
               drop_to_post_meter_m=levels[0]-levels[17],
               closure_error_m=abs(sum(s['adopted_drop_m'] for s in stages)-(levels[0]-levels[19])),
               worst_required_path=max(paths,key=lambda x:x['peak_required_m'])['path'],
               stages=stages,paths=paths,nodes=nodes,geometry=details,inlet=inlet,
               troughs=dict(primary_weir_head_m=primary_h,primary_total_m=primary_req,
                            secondary_weir_head_m=secondary_h,secondary_total_m=secondary_req,
                            adopted_drop_each_m=.20),
               pump=pump,ras=dict(paths=ras,selected_head_m=ras_selected,motor_kW=ras_motor),
               internal_recycle=dict(required_head_m=ir_required,selected_head_m=ir_selected,
                                     motor_kW=22,plan_length_m=80,vertical_m=4,local_k=4),
               air=dict(selected_kPa=65,cases=air,internal_distribution_budget_kPa=6-max(r['loss_kPa'] for r in air)),
               meter=meter,contact=dict(peak_outlet_depth_m=4.8,
                                       minimum_average_depth_m=contact_min_depth,
                                       average_minimum_contact_min=contact_time_avg,peak_contact_min=30.72),
               outfall=dict(external_assumed_length_m=100,external_loss_m=sum(ext[1:]),
                            flood_design_m=25,flood_limit_m=flood_ceiling,
                            note='厂外100 m仅条件算例；实际组号洪水18+0.5M及厂外长度/竖向待提交者核对'),
               input_hash_convention='UTF-8 text normalized to LF; excludes Windows checkout newline differences',
               input_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_text(encoding='utf-8-sig').encode('utf-8')).hexdigest()
                             for p in [source(i,'*复算结果.json') for i in (2,4,5,6)]+[layout_file,route_file]})
    assert final['closure_error_m']<1e-10
    assert math.isclose(layout['control_paths']['water']['external_centerline_total_m'],826)
    assert math.isclose(g5['grit']['net_dimensions_each_m'][2],2.55)
    assert math.isclose(g6['terminal_metering']['long_throat_width_m'],1.5)
    assert len({r['path'] for r in records})==8
    return final,records,balance,pipe_profile


def csv_text(rows):
    f=io.StringIO(newline='')
    w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n')
    w.writeheader(); w.writerows(rows)
    return f.getvalue()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    result,records,balance,pipe_profile=build()
    outputs={'第08组_复算结果.json':json.dumps(result,ensure_ascii=False,indent=2)+'\n',
             '第08组_逐段水力计算.csv':csv_text(records),
             '第08组_节点高程.csv':csv_text(result['nodes']),
             '第08组_路径平衡与余量.csv':csv_text(balance),
             '第08组_埋管与竖向接口.csv':csv_text(pipe_profile),
             '第08组_图14-1数据.csv':csv_text(result['stages'])}
    for name,content in outputs.items():
        p=OUT/name
        if args.write:
            p.write_text(content,encoding='utf-8',newline='')
        else:
            assert p.read_text(encoding='utf-8')==content,f'输出过期：{name}'
    print(json.dumps({k:result[k] for k in ['total_drop_to_boundary_m','drop_to_post_meter_m',
                                           'closure_error_m','worst_required_path','pump','ras',
                                           'internal_recycle','air','meter','outfall']},ensure_ascii=False,indent=2))
    print(f'PASS: 8 paths, {len(records)} reach rows, {len(balance)} stage checks; 6 reproducible outputs')


if __name__=='__main__':
    main()
