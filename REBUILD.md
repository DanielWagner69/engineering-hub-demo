# Demo Production Hub v1.0 rebuild (branch `rebuild`)

All data here is fictional: Project D, Sparrow Light Trainer. The live v0.8-demo.1 site on `main` is unchanged and tagged `v0.8-demo.1` for rollback.

| Phase | State |
| --- | --- |
| 0 Preparation | Done: `v0.8-demo.1` tag, `rebuild` branch, scaffold |
| 1 Data layer and gate | Done: Worked Example v4 records migrated, pinned framework bundle, gate and negative tests, CI validation |
| 2 to 5 | Not started (FD-D-0000009 is still the partly modelled context FDPS; it is built out in Phase 3) |

## Layout

- `vendor/framework-1.0.0-rc.2/`: the pinned framework release bundle (registers, Design Considerations, framework records), its schema and gate tools, copied from DanielWagner69/engineering-hub (see PIN.json for commit and content hash).
- `data/project-d/`: Project D records split by data type (235 records), `register_entries.json` (the project's access marking only; all other register entries come from the bundle), `project.json` (meta and the fictional people directory), `config.json` (values the generic checks need, and Worked Example expectations).
- `data/project-d/tests/`: `neg_cases.py` (43 negative tests carried from Worked Example v4 plus 19 new ones), `example_assertions.py` and `expected_info_we4.json` (inference outputs must equal those of Worked Example v4).
- `data/tailoring/`: Tailoring Records TR-D-0000001 (Annex A lists, interface lists) and TR-D-0000002 (Low Observability not applicable).
- `tools/migrate_we4.py`: the one-off migration script (Worked Example v4 to this layout, with the R-15 and R-18 deltas).

## Running the gate

```
make check     # gate (schema, 82 carried checks, rebuild checks, purity, example assertions) and negative tests
make site      # Phase 0 scaffold site into build/site (not published)
```

## Phase 3 (done)

Pinned to framework 1.0.0-rc.2. FD-D-0000009 (frames 14 to 15A) promoted to a full structural FDPS by `tools/build_fd9.py` (frames 15 and 15A, Structures team and Centre Structure Sub-team pages, two Requirements, four Verifications, five Compliance Statements, reviews A to C with snapshots and agreements, checklist responses, ACT-D-0000106, rev A released with four baselines). Per-FDPS checks run over every FDPS; 11 new negative tests on the structural FDPS. The Demo site is generated into `docs/` (`make site`) and served from `main:/docs`: project home, FDPS pages, production data on tree pages, record registers (detail inside the register; no Part Instance pages), coverage, release gate and flag reports, tailoring and framework feedback (R-16, R-19). v0.8-demo links redirect through `assets/aliases.js`. Rollback: tag `v0.8-demo.1` and Pages back to `main:/`.
