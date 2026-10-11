"""Minimal JSON Schema (2020-12 subset) validator, standard library only: type, const,
enum, pattern, required, properties, items, anyOf, allOf, $ref (file and #/$defs),
minimum, maximum. Enough for the Hub schema; no external dependency (plan 2.5)."""
import json, os, re
_T = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "object": dict, "array": list}
class Schemas:
    def __init__(self, root): self.root = root; self.cache = {}
    def load(self, rel, base=""):
        path = os.path.normpath(os.path.join(self.root, os.path.dirname(base), rel))
        if path not in self.cache: self.cache[path] = json.load(open(path))
        return self.cache[path], os.path.relpath(path, self.root)
    def validate(self, inst, schema, base, path="$"):
        errs = []
        if "$ref" in schema:
            ref = schema["$ref"]; f, _, frag = ref.partition("#")
            doc, nb = self.load(f, base) if f else (self.load(base)[0], base)
            sub = doc
            for k in [x for x in frag.split("/") if x]: sub = sub[k]
            errs += self.validate(inst, sub, nb, path)
        for s in schema.get("allOf", []): errs += self.validate(inst, s, base, path)
        if "anyOf" in schema and not any(not self.validate(inst, s, base, path) for s in schema["anyOf"]):
            errs.append("%s: matches none of anyOf" % path)
        t = schema.get("type")
        if t:
            ok = isinstance(inst, _T[t]) and not (t in ("integer", "number") and isinstance(inst, bool))
            if not ok: return errs + ["%s: expected %s" % (path, t)]
        if "const" in schema and inst != schema["const"]: errs.append("%s: expected %r" % (path, schema["const"]))
        if "enum" in schema and inst not in schema["enum"]: errs.append("%s: %r not in %s" % (path, inst, schema["enum"]))
        if "pattern" in schema and isinstance(inst, str) and not re.search(schema["pattern"], inst): errs.append("%s: %r does not match %s" % (path, inst, schema["pattern"]))
        if "minimum" in schema and isinstance(inst, (int, float)) and inst < schema["minimum"]: errs.append("%s: below minimum" % path)
        if "maximum" in schema and isinstance(inst, (int, float)) and inst > schema["maximum"]: errs.append("%s: above maximum" % path)
        if isinstance(inst, dict):
            for r in schema.get("required", []):
                if r not in inst: errs.append("%s: missing %s" % (path, r))
            for k, s in schema.get("properties", {}).items():
                if k in inst and s: errs += self.validate(inst[k], s, base, path + "." + k)
        if isinstance(inst, list) and "items" in schema:
            for i, x in enumerate(inst): errs += self.validate(x, schema["items"], base, "%s[%d]" % (path, i))
        return errs
