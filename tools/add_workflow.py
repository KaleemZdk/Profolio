"""Add (or update) an interactive n8n workflow diagram in your portfolio.

    python3 tools/add_workflow.py index.html my-workflow.json KEY "Title shown in the viewer" ["One-line summary"]

- KEY must match data-flow="KEY" on the project card (see the PROJECT CARD TEMPLATE in index.html).
- Running it again with the same KEY replaces the old diagram.
- Only node names, types, notes and connections are read — never credentials, IDs or parameters.

Tips for a great diagram (do these in n8n before exporting, via ⋯ menu → Download):
- Rename nodes to plain English ("Save lead", not "Append row in sheet").
- Add a note to each node (node ⚙ Settings → Notes). The note becomes the description people see
  when they click that step.
- Optional: a labels file (same name + .labels.json) can override label / sub / desc per node name.
"""
import json, os, re, sys
from collections import defaultdict

KIND = {
    "webhook": "webhook", "respondToWebhook": "respond", "set": "set", "agent": "agent",
    "code": "code", "if": "if", "switch": "if", "filter": "if", "googleSheets": "sheets", "twilio": "twilio",
    "httpRequest": "http", "scheduleTrigger": "schedule", "manualTrigger": "manual", "googleDrive": "drive",
    "merge": "merge", "splitInBatches": "loop", "gmail": "mail", "chainLlm": "agent", "emailSend": "mail",
}
PRETTY = {
    "webhook": "Webhook", "respondToWebhook": "Respond to Webhook", "set": "Set", "agent": "AI Agent",
    "code": "Code", "if": "IF", "switch": "Switch", "filter": "Filter", "googleSheets": "Google Sheets",
    "twilio": "Twilio", "httpRequest": "HTTP Request", "scheduleTrigger": "Schedule", "manualTrigger": "Manual trigger",
    "googleDrive": "Google Drive", "merge": "Merge", "splitInBatches": "Loop", "gmail": "Gmail", "chainLlm": "LLM chain",
    "memoryBufferWindow": "Memory", "lmChatGoogleGemini": "Gemini", "lmChatOpenAi": "OpenAI", "lmChatGroq": "Groq",
}
TRIGGERS = {"webhook", "schedule", "manual"}

def kind_of(t):
    short = t.split(".")[-1]
    if short.startswith("lmChat") or short.startswith("lm"): return "model"
    if short.startswith("memory"): return "memory"
    return KIND.get(short, "generic")

COL, ROW = 232, 112
NODE_W, NODE_H = 190, 64
STAGE_TITLE, STAGE_GAP = 44, 84

def _layout(names, edges, order):
    """Layered left-to-right layout for one group of nodes. Returns {name: (x, y)} (unnormalised)."""
    preds, succ = defaultdict(list), defaultdict(list)
    for s, oi, t in edges:
        if s in names and t in names: preds[t].append((s, oi)); succ[s].append((oi, t))
    layer = {}
    def L(n, seen=()):
        if n in layer: return layer[n]
        if n in seen or not preds[n]: layer[n] = 0; return 0
        layer[n] = max(L(p, seen + (n,)) for p, _ in preds[n]) + 1
        return layer[n]
    for n in names: L(n)
    y, by_layer = {}, defaultdict(list)
    for n in names: by_layer[layer[n]].append(n)
    for li in sorted(by_layer):
        want = {}
        for n in by_layer[li]:
            if not preds[n]:
                want[n] = 0.0; continue
            vals = []
            for p, oi in preds[n]:
                kids = [t for o, t in sorted(succ[p], key=lambda e: (e[0], order.index(e[1])))]
                vals.append(y.get(p, 0) + (kids.index(n) - (len(kids) - 1) / 2) * ROW)
            want[n] = sum(vals) / len(vals)
        lst = sorted(by_layer[li], key=lambda n: (want[n], order.index(n)))
        prev = None
        for n in lst:
            v = want[n] if prev is None else max(want[n], prev + ROW)
            y[n] = prev = v
        shift = (sum(want[n] for n in lst) - sum(y[n] for n in lst)) / len(lst)
        for n in lst: y[n] += shift
    # extra room after steps with 3+ outputs (e.g. a Switch) so their branch labels stay readable
    outs = defaultdict(set)
    for s_, oi, t in edges:
        if s_ in names and t in names: outs[s_].add(oi)
    wide = {layer[n] for n in names if len(outs[n]) > 2}
    return {n: (layer[n] * COL + 90 * sum(1 for l in wide if l < layer[n]), y[n]) for n in names}

def convert(wf, ov):
    nodes = {n["name"]: n for n in wf["nodes"] if n["type"] != "n8n-nodes-base.stickyNote"}
    order = list(nodes)
    main_edges, ai_edges = [], []
    for src, kinds in wf.get("connections", {}).items():
        for k, outs in kinds.items():
            for oi, targets in enumerate(outs):
                for t in targets or []:
                    if src not in nodes or t["node"] not in nodes: continue
                    (main_edges.append((src, oi, t["node"])) if k == "main" else ai_edges.append((src, t["node"], k)))
    sub_nodes = {s for s, _, _ in ai_edges}
    main_nodes = [n for n in nodes if n not in sub_nodes]
    has_pred = {t for _, _, t in main_edges}
    by_parent = defaultdict(list)
    for s, t, k in ai_edges: by_parent[t].append(s)

    # Optional stages: "__stages__": [{"title": "...", "nodes": [...]}, ...] in the labels file
    stage_defs = [dict(st) for st in ov.get("__stages__", [])]
    in_stage = {n: i for i, st in enumerate(stage_defs) for n in st["nodes"] if n in nodes}
    rest = [n for n in main_nodes if n not in in_stage]
    if not stage_defs: stage_defs = [{"title": "", "nodes": rest}]; in_stage = {n: 0 for n in rest}
    elif rest: stage_defs.append({"title": "Other steps", "nodes": rest}); in_stage.update({n: len(stage_defs) - 1 for n in rest})
    for parent, subs in by_parent.items():  # AI sub-nodes live in their parent's stage
        for s_ in subs: in_stage[s_] = in_stage.get(parent, 0)

    pos, stages_out, top = {}, [], 0.0
    for si, st in enumerate(stage_defs):
        names = [n for n in main_nodes if in_stage.get(n) == si]
        if not names: continue
        lay = _layout(names, main_edges, order)
        for parent, subs in by_parent.items():
            if parent in lay:
                px, py = lay[parent]
                for i, s_ in enumerate(subs):
                    lay[s_] = (px + (i - (len(subs) - 1) / 2) * 150 + 10, py + ROW * 1.25)
        miny = min(v[1] for v in lay.values()); maxy = max(v[1] for v in lay.values())
        title_h = STAGE_TITLE if st.get("title") else 0
        for n, (x_, y_) in lay.items(): pos[n] = (x_, y_ - miny + top + title_h)
        stages_out.append({"title": st.get("title", ""), "y": round(top + 40), "index": si})
        st["top"] = top
        top = top + title_h + (maxy - miny) + NODE_H + STAGE_GAP
    for n in nodes:  # anything unconnected
        if n not in pos: pos[n] = (0, top)
    minx = min(v[0] for v in pos.values())
    out_nodes = []
    for name, n in nodes.items():
        k = ov.get(name, {}).get("kind") or kind_of(n["type"]); o = ov.get(name, {}); short = n["type"].split(".")[-1]
        outs = max([oi for s, oi, _ in main_edges if s == name] + [0]) + 1
        if k == "if" or n.get("onError") == "continueErrorOutput": outs = max(outs, 2)
        out_nodes.append({
            "id": name, "label": o.get("label", name), "sub": o.get("sub", PRETTY.get(short, short)),
            "desc": o.get("desc", (n.get("notes") or "").strip()), "kind": k,
            "trigger": kind_of(n["type"]) in TRIGGERS and name not in has_pred, "isSub": name in sub_nodes,
            "x": round(pos[name][0] - minx + 40), "y": round(pos[name][1] + 40), "outputs": outs,
        })
    byid = {n["id"]: n for n in out_nodes}
    W = max(n["x"] for n in out_nodes) + NODE_W + 110
    H = max(n["y"] for n in out_nodes) + NODE_H + 60
    def label(src, oi):
        lbls = ov.get(src, {}).get("outLabels")
        if lbls and oi < len(lbls): return lbls[oi]
        t = nodes[src]["type"].split(".")[-1]
        if t in ("if", "filter"): return "true" if oi == 0 else "false"
        if nodes[src].get("onError") == "continueErrorOutput": return "success" if oi == 0 else "error"
        return ""
    edges = []
    for s_, oi, t in main_edges:
        e = {"from": s_, "to": t, "out": oi, "label": label(s_, oi)}
        a, b = in_stage.get(s_, 0), in_stage.get(t, 0)
        if a != b:
            via = round(stage_defs[b]["top"] + 40 - STAGE_GAP / 2)
            e["route"] = {"via": via, "xr": (W - 40) if b > a + 1 else None}
        edges.append(e)
    edges += [{"from": s_, "to": t, "ai": True, "label": k.replace("ai_", "").replace("languageModel", "model")} for s_, t, k in ai_edges]
    data = {"name": wf.get("name", ""), "w": W, "h": H, "nodes": out_nodes, "edges": edges}
    if any(st["title"] for st in stages_out): data["stages"] = [{"title": st["title"], "y": st["y"]} for st in stages_out if st["title"]]
    return data

def main():
    if len(sys.argv) < 5:
        print(__doc__); sys.exit(1)
    page, wf_path, key, title = sys.argv[1:5]
    summary = sys.argv[5] if len(sys.argv) > 5 else ""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key): sys.exit("KEY must be letters/numbers/underscore, e.g. classroom")
    wf = json.load(open(wf_path, encoding="utf-8"))
    labels_path = os.path.splitext(wf_path)[0] + ".labels.json"
    ov = json.load(open(labels_path, encoding="utf-8")) if os.path.exists(labels_path) else {}
    data = convert(wf, ov); data["title"] = title; data["summary"] = summary
    html = open(page, encoding="utf-8").read()
    start = html.index("const FLOWS = {"); end = html.index("\n  };", start)
    entries = dict(re.findall(r"^\s{4}([A-Za-z_][A-Za-z0-9_]*): (\{.*\}),?$", html[start:end], flags=re.M))
    entries[key] = json.dumps(data, ensure_ascii=False)
    block = "const FLOWS = {\n" + ",\n".join(f"    {k}: {v}" for k, v in entries.items())
    html = html[:start] + block + html[end:]
    open(page, "w", encoding="utf-8").write(html)
    n = len(data["nodes"])
    print(f"Added workflow '{key}' ({n} nodes). Make sure a card has: data-flow=\"{key}\" — see the PROJECT CARD TEMPLATE in {page}.")

if __name__ == "__main__":
    main()
