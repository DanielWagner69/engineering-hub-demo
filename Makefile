# Demo Production Hub v1.0-demo rebuild: Project D (fictional) gate and site against the pinned framework bundle.
PY ?= python3
FWV := 1.0.0-rc.2
FW := vendor/framework-$(FWV)
ARGS := --framework $(FW)/framework-$(FWV).json --schema $(FW)/schema --project data/project-d
check:            ## schema, carried WE4 checks, per-FDPS checks, purity, example assertions; then negative tests
	$(PY) $(FW)/tools/validate.py $(ARGS) --repo . --out build/val.json
	$(PY) $(FW)/tools/neg.py --framework $(FW)/framework-$(FWV).json --project data/project-d --out build/neg.json
site: check       ## generate the Demo into docs/ (served by GitHub Pages from main:/docs)
	$(PY) $(FW)/tools/build_demo.py $(ARGS) --repo . --old data/v08_demo_ids.json --out docs
site-check:       ## generate into build/site and fail if docs/ is out of date
	$(PY) $(FW)/tools/build_demo.py $(ARGS) --repo . --old data/v08_demo_ids.json --out build/site
	diff -r -q build/site docs
.PHONY: check site site-check
