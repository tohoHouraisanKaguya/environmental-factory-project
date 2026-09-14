"""Independent physical/accounting checks for group 08 (no external packages)."""
import math
import unittest

import check_second_revision_batch6_hydraulics as h


class HydraulicChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result, cls.rows, cls.balance, cls.profiles = h.build()

    def test_darcy_against_energy_equation(self):
        v,hf,hl = h.pipe(.9375,1.2,120,8.3)
        self.assertAlmostEqual(v,.9375/(math.pi*.6**2))
        self.assertAlmostEqual(hf+hl,(.025*100+8.3)*v*v/(2*9.81))
        half = h.pipe(.9375/2,1.2,120,8.3)
        self.assertAlmostEqual(sum(half[1:]),(hf+hl)/4)

    def test_headers_conserve_contributing_flow(self):
        a = {r['segment']:r['q_peak_m3_s'] for r in self.rows
             if r['path']=='T1' and r['segment'].startswith('W11AH:')}
        self.assertEqual(list(a.values()),[.234375,.46875,.703125,.9375])
        b = {r['segment']:r['q_peak_m3_s'] for r in self.rows
             if r['segment'].startswith('W11BH:')}
        self.assertAlmostEqual(b['W11BH:234-270']+b['W11BH:278-270'],.9375)
        # Whole-plant mixed input = clear effluent + RAS, not effluent + IR.
        mixed = sum(r['q_peak_m3_s'] for r in self.rows if r['segment'].startswith('W10T'))
        clear = sum(r['q_peak_m3_s'] for r in self.rows if r['segment'].startswith('W11T'))
        self.assertAlmostEqual(mixed-clear,1.875*.75)

    def test_common_physical_reaches_are_consistent(self):
        seen={}
        for r in self.rows:
            if not r['segment'].startswith('W'):
                continue
            values=tuple(r[k] for k in ('q_peak_m3_s','plan_length_m','diameter_m','local_k'))
            self.assertEqual(seen.setdefault(r['segment'],values),values)

    def test_drop_boundaries_and_anchor(self):
        r=self.result
        self.assertAlmostEqual(r['nodes'][9]['water_peak_el_m']-r['nodes'][9]['floor_el_m'],5)
        self.assertAlmostEqual(sum(s['adopted_drop_m'] for s in r['stages'][:17]),r['drop_to_post_meter_m'])
        self.assertAlmostEqual(r['total_drop_to_boundary_m']-r['drop_to_post_meter_m'],.55)
        self.assertTrue(all(x['lambda030_margin_m']>=-1e-10 for x in self.balance))

    def test_free_weirs_and_meter(self):
        levels=[n['water_peak_el_m'] for n in self.result['nodes']]
        self.assertGreater(levels[4]-h.weir(1.875/4,2)-levels[5],.1)
        self.assertGreater(levels[10]-h.weir(1.875*1.75/8,1.2)-levels[11],.1)
        m=self.result['meter']
        q=.9375; b=1.5; y=m['critical_depth_peak_m']
        self.assertAlmostEqual(q*q/(9.81*b*b*y**3),1)
        self.assertGreater(m['throat_floor_el_m'],m['downstream_peak_el_m'])
        self.assertGreater(self.result['contact']['average_minimum_contact_min'],30)

    def test_pump_energy_is_not_double_counted(self):
        p=self.result['pump']
        required=p['discharge_control_el_m']-p['suction_min_el_m']+p['branch_loss_m']+p['line_loss_m']+p['reserve_m']
        self.assertAlmostEqual(required,p['required_head_m'])
        self.assertGreaterEqual(p['selected_head_m'],required)
        self.assertGreaterEqual(p['motor_selected_kW'],p['shaft_power_with_margin_kW'])
        self.assertGreaterEqual(self.result['ras']['selected_head_m'],max(x['required_m'] for x in self.result['ras']['paths']))


if __name__=='__main__':
    unittest.main()
