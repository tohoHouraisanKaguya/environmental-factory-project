"""Reproduce calculation 11 hydraulics; standard library only, SI units."""
import json
import math


G = 9.81
LAMBDA = 0.020
MANNING_N = 0.013


def pipe(name, flow, diameter, length, local_k):
    area = math.pi * diameter**2 / 4
    velocity = flow / area
    velocity_head = velocity**2 / (2 * G)
    friction = LAMBDA * length / diameter * velocity_head
    local = local_k * velocity_head
    return {
        "name": name,
        "flow_m3_s": flow,
        "diameter_m": diameter,
        "length_m": length,
        "local_k": local_k,
        "velocity_m_s": velocity,
        "friction_m": friction,
        "local_m": local,
        "loss_m": friction + local,
    }


def rectangular_normal_depth(flow, width, gradient, n=MANNING_N):
    def capacity(depth):
        area = width * depth
        radius = area / (width + 2 * depth)
        return area * radius ** (2 / 3) * math.sqrt(gradient) / n

    low, high = 1e-6, 5.0
    for _ in range(100):
        mid = (low + high) / 2
        if capacity(mid) < flow:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def circular_segment(flow, diameter, depth_ratio, n=MANNING_N):
    radius = diameter / 2
    depth = depth_ratio * diameter
    theta = 2 * math.acos((radius - depth) / radius)
    area = radius**2 * (theta - math.sin(theta)) / 2
    wetted = radius * theta
    hydraulic_radius = area / wetted
    velocity = flow / area
    gradient = (flow * n / (area * hydraulic_radius ** (2 / 3))) ** 2
    return area, hydraulic_radius, velocity, gradient


def circular_flow(diameter, depth_ratio, gradient, n=MANNING_N):
    radius = diameter / 2
    depth = depth_ratio * diameter
    theta = 2 * math.acos((radius - depth) / radius)
    area = radius**2 * (theta - math.sin(theta)) / 2
    hydraulic_radius = area / (radius * theta)
    return area * hydraulic_radius ** (2 / 3) * math.sqrt(gradient) / n


def ratio_for_flow(flow, diameter, gradient):
    low, high = 1e-6, 0.999999
    for _ in range(100):
        mid = (low + high) / 2
        if circular_flow(diameter, mid, gradient) < flow:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def rectangular_weir_head(flow, width, coefficient=1.84):
    return (flow / (coefficient * width)) ** (2 / 3)


def calculate():
    q_avg, q_peak = 1.250, 1.625
    q_line_avg, q_line_peak = q_avg / 2, q_peak / 2
    return_ratio = 0.75

    # Fixed incoming D1200: calculate the gradient needed at h/D=0.75.
    inlet_peak = circular_segment(q_peak, 1.20, 0.75)
    inlet_gradient = inlet_peak[3]
    inlet_avg_ratio = ratio_for_flow(q_avg, 1.20, inlet_gradient)

    # Fine-screen outlet channel; item 12 supplies the A/B external lengths.
    channel_width, channel_gradient = 1.50, 0.00030
    channel_peak_depth = rectangular_normal_depth(q_line_peak, channel_width, channel_gradient)
    channel_avg_depth = rectangular_normal_depth(q_line_avg, channel_width, channel_gradient)
    channel_peak_velocity = q_line_peak / (channel_width * channel_peak_depth)
    channel_local = 1.5 * channel_peak_velocity**2 / (2 * G)
    channel_loss_a = channel_gradient * (18.0 + 66.5) + channel_local
    channel_loss_b = channel_gradient * (18.0 + 18.5) + channel_local

    # Main water line, all at peak-hour flow. Lengths through the biological stage
    # reconcile item 12's route skeleton with item 10's six-tank arrangement.
    segments = {
        "pump_internal": pipe("单泵内部出水支管", 0.625, 0.80, 12.0, 4.3),
        "pump_to_fine": pipe("泵站至细格栅单线总管", q_line_peak, 1.00, 22.0, 2.0),
        "grit_to_primary_a": pipe("沉砂A至初沉配水井", q_line_peak, 1.20, 111.5, 3.0),
        "grit_to_primary_b": pipe("沉砂B至初沉配水井", q_line_peak, 1.20, 39.5, 2.5),
        "primary_branch": pipe("初沉配水井至单池", q_line_peak / 2, 0.90, 50.0, 2.0),
        "primary_to_bio": pipe("初沉池至单系列生物池", q_line_peak / 2, 0.90, 17.0, 1.5),
        "bio_to_secondary": pipe(
            "单系列生物池至二沉配水井", q_line_peak / 2 * (1 + return_ratio), 1.00, 50.0, 2.5
        ),
        "mixed_header": pipe(
            "单线混合液汇流管", q_line_peak * (1 + return_ratio), 1.40, 20.0, 1.5
        ),
        "secondary_branch": pipe(
            "二沉配水井至单池中心", q_line_peak * (1 + return_ratio) / 3, 1.00, 60.0, 2.0
        ),
        "secondary_outlet": pipe("单座二沉池出水支管", q_line_peak / 3, 0.80, 60.0, 2.0),
        "effluent_header_a": pipe("A线二沉出水干管", q_line_peak, 1.20, 261.0, 3.0),
        "effluent_header_b": pipe("B线二沉出水干管", q_line_peak, 1.20, 101.0, 2.5),
        "final_outlet": pipe("消毒预留至东厂界总管", q_peak, 1.50, 28.0, 1.0),
    }

    primary_weir_avg = rectangular_weir_head(q_line_avg / 2, 1.50)
    primary_weir_peak = rectangular_weir_head(q_line_peak / 2, 1.50)
    mixed_line_avg = q_line_avg * (1 + return_ratio)
    mixed_line_peak = q_line_peak * (1 + return_ratio)
    secondary_weir_avg = rectangular_weir_head(mixed_line_avg / 3, 1.50)
    secondary_weir_peak = rectangular_weir_head(mixed_line_peak / 3, 1.50)

    common_keys = [
        "pump_to_fine", "primary_branch", "primary_to_bio", "bio_to_secondary",
        "mixed_header", "secondary_branch", "secondary_outlet", "final_outlet",
    ]
    distribution_transition_allowance = 0.05 + 0.05
    connector_a = sum(segments[k]["loss_m"] for k in common_keys)
    connector_a += channel_loss_a + segments["grit_to_primary_a"]["loss_m"]
    connector_a += segments["effluent_header_a"]["loss_m"]
    connector_a += primary_weir_peak + secondary_weir_peak + distribution_transition_allowance
    connector_b = sum(segments[k]["loss_m"] for k in common_keys)
    connector_b += channel_loss_b + segments["grit_to_primary_b"]["loss_m"]
    connector_b += segments["effluent_header_b"]["loss_m"]
    connector_b += primary_weir_peak + secondary_weir_peak + distribution_transition_allowance

    # Unit-internal values inherited or checked here, listed separately from connectors.
    primary_trough_v = (q_line_peak / 2) / (0.80 * 0.60)
    primary_trough_r = 0.80 * 0.60 / (0.80 + 2 * 0.60)
    primary_trough_i = (MANNING_N * primary_trough_v / primary_trough_r ** (2 / 3)) ** 2
    primary_trough_loss = primary_trough_i * (math.pi * 26 / 2) + primary_trough_v**2 / (2 * G)
    primary_notch_head = ((q_line_peak / 2) / 817 / 1.4) ** 0.4
    secondary_notch_head = ((q_line_peak / 3) / 1068 / 1.4) ** 0.4
    inherited_unit_losses = {
        "fine_screen_blocked_m": 0.121,
        "grit_allowance_m": 0.250,
        "primary_trough_and_velocity_m": primary_trough_loss,
        "primary_notch_head_m": primary_notch_head,
        "bio_stage_allowance_m": 0.300,
        "secondary_trough_m": 0.0355,
        "secondary_notch_head_m": secondary_notch_head,
    }
    unit_total = sum(inherited_unit_losses.values())

    # Return sludge, waste sludge, internal recycle and air-network interfaces.
    ras_branch = pipe("单池回流污泥支管", q_line_peak * return_ratio / 3, 0.50, 35.0, 4.0)
    ras_header = pipe("单线回流污泥干管", q_line_peak * return_ratio, 0.90, 165.0, 3.0)
    ras_to_bio = pipe("回流污泥至单系列厌氧段", q_line_peak * return_ratio / 2, 0.70, 25.0, 2.0)
    ras_loss = ras_branch["loss_m"] + ras_header["loss_m"] + ras_to_bio["loss_m"]
    internal_recycle = pipe("单系列内回流", q_line_peak / 2 * 2.5, 1.20, 80.0, 4.0)
    waste_flow = (1146.5445462114903 / 6) / (2 * 3600)  # each tank, 2 h/d
    waste_branch = pipe("单池剩余污泥间歇排放", waste_flow, 0.20, 35.0, 4.0)
    waste_header = pipe("单线剩余污泥共用管", waste_flow, 0.25, 100.0, 2.0)
    cross_connect = pipe("两线检修联络管", q_peak, 1.50, 20.0, 3.0)

    air_main_flow, air_series_flow = 30000 / 3600, 7500 / 3600
    air_density = 1.20
    air_main = pipe("空气母管至中央分流", air_main_flow, 1.00, 20.0, 2.0)
    air_ring = pipe("半环空气干管", air_main_flow / 2, 1.00, 110.0, 2.0)
    air_branch = pipe("系列空气支管", air_series_flow, 0.75, 30.0, 4.0)
    air_loss_pa = sum(
        (LAMBDA * item["length_m"] / item["diameter_m"] + item["local_k"])
        * air_density * item["velocity_m_s"]**2 / 2
        for item in (air_main, air_ring, air_branch)
    )

    # Assertions encode the adopted preliminary design criteria.
    assert 0.0020 < inlet_gradient < 0.0022
    assert 0.5 < inlet_avg_ratio < 0.75
    assert channel_peak_depth < 1.0 and channel_peak_velocity >= 0.6
    for key in ["pump_to_fine", "grit_to_primary_a", "grit_to_primary_b", "primary_branch",
                "primary_to_bio", "bio_to_secondary", "mixed_header", "secondary_branch",
                "secondary_outlet", "effluent_header_a", "effluent_header_b", "final_outlet"]:
        assert 0.5 <= segments[key]["velocity_m_s"] <= 1.5, key
    assert ras_loss < 1.0
    assert 0.8 <= waste_branch["velocity_m_s"] <= 0.9
    assert 0.5 <= waste_header["velocity_m_s"] <= 0.6
    assert 0.8 <= internal_recycle["velocity_m_s"] <= 1.0
    assert 0.8 <= cross_connect["velocity_m_s"] <= 1.0
    assert air_loss_pa < 1000

    return {
        "incoming_D1200": {
            "peak_depth_ratio": 0.75,
            "peak_velocity_m_s": inlet_peak[2],
            "required_gradient": inlet_gradient,
            "average_depth_ratio_at_same_gradient": inlet_avg_ratio,
        },
        "fine_to_grit_channel": {
            "width_m": channel_width,
            "gradient": channel_gradient,
            "average_depth_m": channel_avg_depth,
            "peak_depth_m": channel_peak_depth,
            "peak_velocity_m_s": channel_peak_velocity,
            "loss_A_B_m": [channel_loss_a, channel_loss_b],
        },
        "pipe_segments": segments,
        "distribution_weir_head_avg_peak_m": {
            "primary": [primary_weir_avg, primary_weir_peak],
            "secondary": [secondary_weir_avg, secondary_weir_peak],
        },
        "connector_distribution_loss_A_B_m": [connector_a, connector_b],
        "unit_internal_losses": inherited_unit_losses,
        "unit_internal_total_m": unit_total,
        "preliminary_total_A_B_m": [connector_a + unit_total, connector_b + unit_total],
        "return_sludge": {
            "branch": ras_branch,
            "header": ras_header,
            "to_bio": ras_to_bio,
            "worst_loss_m": ras_loss,
        },
        "internal_recycle": internal_recycle,
        "waste_sludge_2h_per_day": {"branch": waste_branch, "header": waste_header},
        "maintenance_cross_connect": cross_connect,
        "air_network": {
            "main": {key: air_main[key] for key in ("flow_m3_s", "diameter_m", "length_m", "velocity_m_s")},
            "half_ring": {key: air_ring[key] for key in ("flow_m3_s", "diameter_m", "length_m", "velocity_m_s")},
            "series_branch": {key: air_branch[key] for key in ("flow_m3_s", "diameter_m", "length_m", "velocity_m_s")},
            "friction_and_local_loss_kPa": air_loss_pa / 1000,
        },
    }


if __name__ == "__main__":
    print(json.dumps(calculate(), ensure_ascii=False, indent=2))
