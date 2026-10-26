# Combined registration evidence revision

This is tool preparation only. It does not create a ready target, package,
registration output, native acceptance, browser acceptance or MAIN change.

`toolchain/` is a separate copy of the original packaging tools. The packager,
decoder, finite bridge and common finite engine retain their original bytes.
Only the registration source-layout compatibility patch and supplemental
evidence gate change. The original tool freeze and the author's separately
frozen compatibility proposal remain untouched.

For an eventual authorized run, use the packager, decoder and registrar from
this same `toolchain/` directory. The existing registrar binds the actual
packaging helper's absolute path relative to itself, so mixing an old package
run with the new registrar is intentionally rejected.

The library target must provide `actual.geometry_supplements`, with exactly:

- `bounded_revision_preservation`
- `horizontal_pane_seating`
- `colonnade_cap_clearance`

Each value is an absolute `source`, positive `bytes` and SHA256 descriptor of
the actual proof file. No top-level registration-request fields are added.
Other building types cannot smuggle in an unrecognized supplemental suite.

Each proof has a distinct schema and true field. Current raw, independent
structure, source freeze, geometry and calibration bindings are checked.
Revision preservation covers the exact authorized 265 changed and 2,988
unchanged raw parts. All 788 pane/frame seats require finite positive horizontal
area and matching actual interval endpoints. All six column caps require their
entire top footprint under the surface, positive vertical clearance and a real
deck joint. A generic structure PASS cannot substitute for any of these.

After the existing actual decoder and per-role finite checks pass, the new gate
requires every dependent pane, frame, column, deck and walking-surface part in
raw/web/LOD/authored-LOD to retain exact oriented positions and actual loaded
materials. Decoder normals remain subject to their separate 0.05-degree
policy. The transfer record is copied explicitly into the registration summary
and model metadata. The 265/2,988 revision counts remain historical raw counts;
they are not falsely asserted for an authored LOD that omits approved tile seams.

All native, root visual, source/near-neighbor, navigation, nine-section
prebrowser and source-delivery gates remain in force. The tool never sets
browser acceptance. Supplemental reports and their checker files must be
included in the separate tool/input locks, and public delivery should keep the
proof descriptors and explicit transfer records.

`tests/test_supplement_guards.py` exercises actual existing raw-proof contract
validation plus deliberately malformed proof inputs. Its delivery fixtures
are synthetic contract controls, deleted afterward; they are not actual
decoded-asset evidence and are never used as a registration request.
