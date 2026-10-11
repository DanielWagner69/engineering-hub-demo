# Demo Production Hub v1.0 rebuild: Project D (fictional) gate against the pinned framework bundle.
PY ?= python3
FW := vendor/framework-1.0.0-rc.1
check:
	$(PY) $(FW)/tools/validate.py --framework $(FW)/framework-1.0.0-rc.1.json --schema $(FW)/schema --project data/project-d --repo . --out build/val.json
	$(PY) $(FW)/tools/neg.py --framework $(FW)/framework-1.0.0-rc.1.json --project data/project-d --out build/neg.json
site: check
	$(PY) $(FW)/tools/build_site.py --framework $(FW)/framework-1.0.0-rc.1.json --project data/project-d --out build/site
.PHONY: check site
