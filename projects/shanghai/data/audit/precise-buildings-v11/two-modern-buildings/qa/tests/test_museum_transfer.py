#!/usr/bin/env python3
"""Synthetic binding controls only; never produces a model acceptance record."""
import copy
import unittest
from modern_model_gate import check_museum_supplement_transfer as check


def fixture():
    desc = lambda name: {'source': '/synthetic-control/' + name, 'bytes': 1, 'sha256': '0' * 64}
    proofs = {k: desc(k) for k in ('bounded_revision_preservation', 'repair_envelope', 'finite_area_pane_seating', 'all_opaque_slot_rays')}
    package = {'assets': {role: dict(desc(role), file=role) for role in ('raw', 'web', 'lod')}}
    request = {'source_freeze': desc('freeze'), 'decoded_report': desc('decoded')}
    target = {'id': 'jiading-shanghai-auto-museum', 'lod_policy': {'mode': 'compression-only'},
              'actual': {'geometry_supplements': proofs, 'source_structure_report': desc('structure'), 'authored_lod': None}}
    decoded = {'passed': True, 'authored_lod': None, 'finite_actual_decoded_report': desc('suite')}
    suite = {'schema': 'modern-actual-decoded-finite-suite-v11', 'passed': True, 'building_id': target['id'],
             'raw_sha256': package['assets']['raw']['sha256'], 'roles': {
                role: {'passed': True, 'current_asset': package['assets'][role],
                       'finite_report': desc(role + '-finite'), 'array_manifest': desc(role + '-arrays')}
                for role in ('raw', 'web', 'lod')}}
    transfer = {'schema': 'modern-museum-supplement-delivery-transfer-v11', 'raw_proofs': proofs,
                'source_raw': package['assets']['raw'], 'source_freeze': request['source_freeze'],
                'source_structure_report': target['actual']['source_structure_report'],
                'actual_decoded_package_report': request['decoded_report'],
                'actual_decoded_finite_suite': decoded['finite_actual_decoded_report'],
                'bounded_revision_proof_bound_as_raw_history': True, 'finite_area_pane_seating_preserved': True,
                'repair_envelope_and_slot_clearance_preserved': True, 'all_current_parts_preserved': True,
                'native_accepted': False, 'browser_accepted': False, 'roles': {
                    role: {'current_asset': package['assets'][role],
                           'actual_decoded_finite_report': suite['roles'][role]['finite_report'],
                           'actual_decoded_array_manifest': suite['roles'][role]['array_manifest'],
                           'required_retained_part_count': 12378, 'exact_oriented_positions_preserved': True,
                           'actual_loaded_materials_preserved': True, 'normal_policy_degrees': .05,
                           'omitted_source_part_keys': [], 'raw_supplement_proofs': proofs}
                    for role in ('raw', 'web', 'lod')}}
    return [transfer, copy.deepcopy(transfer), request, target, package, decoded, suite]


class MuseumTransferControls(unittest.TestCase):
    def reject(self, edit):
        args = fixture(); edit(args); args[1] = copy.deepcopy(args[0])
        with self.assertRaises(ValueError): check(*args)

    def test_exact_synthetic_contract(self): check(*fixture())

    def test_summary_and_metadata_disagreement_rejected(self):
        args = fixture(); args[1]['all_current_parts_preserved'] = False
        with self.assertRaises(ValueError): check(*args)

    def test_missing_or_extra_raw_proof_rejected(self):
        self.reject(lambda a: a[0]['raw_proofs'].pop('all_opaque_slot_rays'))
        self.reject(lambda a: a[0]['raw_proofs'].update(extra={'source': 'private'}))

    def test_target_cannot_bind_different_raw_proof(self):
        self.reject(lambda a: a[3]['actual'].update(geometry_supplements={}))

    def test_required_geometry_flags_false_or_nonbool_rejected(self):
        for key in ('bounded_revision_proof_bound_as_raw_history', 'finite_area_pane_seating_preserved',
                    'repair_envelope_and_slot_clearance_preserved', 'all_current_parts_preserved'):
            for value in (False, 1, None):
                with self.subTest(key=key, value=value): self.reject(lambda a: a[0].update({key: value}))

    def test_museum_authored_lod_or_grouped_protocol_rejected(self):
        self.reject(lambda a: a[3]['lod_policy'].update(mode='authored-subtraction'))
        self.reject(lambda a: a[5].update(authored_lod={'unexpected': True}))
        self.reject(lambda a: a[6].update(schema='invented-grouped-suite'))

    def test_missing_or_extra_delivery_role_rejected(self):
        self.reject(lambda a: a[0]['roles'].pop('lod'))
        self.reject(lambda a: a[6]['roles'].update(authored_lod=a[6]['roles']['raw']))

    def test_actual_role_proof_identity_drift_rejected(self):
        self.reject(lambda a: a[0]['roles']['web'].update(actual_decoded_finite_report={'wrong': True}))
        self.reject(lambda a: a[0]['roles']['web'].update(actual_decoded_array_manifest={'wrong': True}))
        self.reject(lambda a: a[0]['roles']['web'].update(current_asset={'wrong': True}))

    def test_missing_parts_omissions_materials_normals_rejected(self):
        for key, value in [('required_retained_part_count', 12377), ('required_retained_part_count', True),
                           ('omitted_source_part_keys', ['lost']), ('exact_oriented_positions_preserved', False),
                           ('actual_loaded_materials_preserved', False), ('normal_policy_degrees', .06)]:
            with self.subTest(key=key): self.reject(lambda a: a[0]['roles']['lod'].update({key: value}))

    def test_transfer_cannot_assert_visual_acceptance(self):
        for key in ('native_accepted', 'browser_accepted'):
            with self.subTest(key=key): self.reject(lambda a: a[0].update({key: True}))

    def test_failed_actual_suite_or_role_rejected(self):
        self.reject(lambda a: a[6].update(passed=False))
        self.reject(lambda a: a[6]['roles']['web'].update(passed=False))


if __name__ == '__main__': unittest.main(verbosity=2)
