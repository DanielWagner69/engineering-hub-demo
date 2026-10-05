**Version:** 0.8-demo.1 (Framework v0.8)

# Engineering Hub – Production (Demo)

A **Demo Production Hub**: a versioned instance of [Framework Hub v0.8](https://danielwagner69.github.io/engineering-hub/) filled with **entirely fictional** project data for the made-up **Sparrow Light Trainer (Demo)** aircraft.

**Live site:** https://danielwagner69.github.io/engineering-hub-demo/

## Changelog

**v0.8-demo.1 (5 Oct 2026):** closes demo gaps 1–3, 5–7 against Framework v0.8. Production links **Requirement** column; **derived** badge in Major Unit tree; **Bought-in Equipment** as Design Type DT-0014 (with Source); structured **effectivity**; Issue pages show Product Scopes (no Cross-scope badge); fictional **Finish Spec** records (FS-0001–0003) on parts. Gap 4 (authority history/evidence) skipped. See HUB-FEEDBACK.


## Purpose
- Show what a project’s Production Hub looks like on top of the framework
- Exercise production overlays (items, requirements, verifications, issues, authority register)
- Capture framework improvements on the **Framework gaps (feedback)** page while filling real-shaped data

## What is fictional
Every project name, part, requirement, calculation, issue, contact and statistic is invented for demonstration. This is **not** a real programme. Framework taxonomy pages (Systems, Design Types, etc.) are mirrored read-only from Framework Hub v0.8 and keep a “Framework page” origin.

## Contents (demo overlay)
- Project home with mass budget, open issues, verification coverage, baseline BL-2.1, effectivity MSN 001–010
- Points of contact (fictional)
- Production data links on Fuel, Electrical Power and Primary Structure
- Part Instances with home System + supports links (e.g. pipe bracket PI-0001)
- Requirements (Air System › System › Sub-system › Item) linked to items and Verifications
- Project Issues with impact levels and forum bands
- Authority register (some types still in “PLM (demo)”, some moved to Hub)
- Live model schematic (SVG placeholder, not CAD)
- Framework gaps feedback page

## Running locally
Open `index.html`, or `python3 -m http.server 8000` in this folder.

## Checks
```
node tests/check_data.js
# headless crawl + ui_check (see Framework Hub docs)
```

## Relationship to the Framework Hub
Framework Hub remains the master of framework content. This site references Framework Hub v0.8 and does not edit framework pages. Production data is a separate overlay.

Brand colours: primary `#00405E`, accent `#46C1BE`, light `#9EDEDC`.
