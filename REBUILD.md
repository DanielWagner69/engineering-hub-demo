# Demo Production Hub v1.0 rebuild (branch `rebuild`)

All data here is fictional: Project D, Sparrow Light Trainer. The live v0.8-demo.1 site on `main` is unchanged and tagged `v0.8-demo.1` for rollback.

| Phase | State |
| --- | --- |
| 0 Preparation | Done: `v0.8-demo.1` tag, `rebuild` branch, scaffold |
| 1 Data layer and gate | Done: Worked Example v4 records migrated, pinned framework bundle, gate and negative tests, CI validation |
| 2 to 5 | Not started (FD-D-0000009 is still the partly modelled context FDPS; it is built out in Phase 3) |

## Layout

- `vendor/framework-1.0.0-rc.1/`: the pinned framework release bundle (registers, Design Considerations, framework records), its schema and gate tools, copied from DanielWagner69/engineering-hub (see PIN.json for commit and content hash).
- `data/project-d/`: Project D records split by data type (235 records), `register_entries.json` (the project's access marking only; all other register entries come from the bundle), `project.json` (meta and the fictional people directory), `config.json` (values the generic checks need, and Worked Example expectations).
- `data/project-d/tests/`: `neg_cases.py` (43 negative tests carried from Worked Example v4 plus 19 new ones), `example_assertions.py` and `expected_info_we4.json` (inference outputs must equal those of Worked Example v4).
- `data/tailoring/`: Tailoring Records TR-D-0000001 (Annex A lists, interface lists) and TR-D-0000002 (Low Observability not applicable).
- `tools/migrate_we4.py`: the one-off migration script (Worked Example v4 to this layout, with the R-15 and R-18 deltas).

## Running the gate

```
make check     # gate (schema, 82 carried checks, rebuild checks, purity, example assertions) and negative tests
make site      # Phase 0 scaffold site into build/site (not published)
```
