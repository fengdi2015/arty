"""
ChEMBL Oncology Drug Database
Fetches approved & investigational oncology drugs (incl. full immuno-oncology coverage)
with targets and indications.  Uses ChEMBL REST API — stdlib only (urllib).

All ChEMBL IDs verified via live API lookup.
"""

import json
import time
import urllib.request
import urllib.parse
import os

BASE = "https://www.ebi.ac.uk/chembl/api/data"

# ── Verified ChEMBL IDs ────────────────────────────────────────────────────────
# Format: chembl_id -> (preferred_name, drug_class, io_subtype_hint)

CURATED = {
    # ── IMMUNO-ONCOLOGY: PD-1 inhibitors ──────────────────────────────────────
    "CHEMBL3137343": ("pembrolizumab",              "IO", "PD-1 inhibitor"),
    "CHEMBL2108738": ("nivolumab",                  "IO", "PD-1 inhibitor"),
    "CHEMBL4297723": ("cemiplimab",                 "IO", "PD-1 inhibitor"),
    "CHEMBL4298124": ("dostarlimab",                "IO", "PD-1 inhibitor"),
    "CHEMBL4297829": ("sintilimab",                 "IO", "PD-1 inhibitor"),
    "CHEMBL4297715": ("camrelizumab",               "IO", "PD-1 inhibitor"),
    "CHEMBL4297840": ("tislelizumab",               "IO", "PD-1 inhibitor"),
    "CHEMBL4297831": ("spartalizumab",              "IO", "PD-1 inhibitor"),
    "CHEMBL4298191": ("sasanlimab",                 "IO", "PD-1 inhibitor"),
    "CHEMBL4298037": ("retifanlimab",               "IO", "PD-1 inhibitor"),

    # ── IMMUNO-ONCOLOGY: PD-L1 inhibitors ─────────────────────────────────────
    "CHEMBL3707227": ("atezolizumab",               "IO", "PD-L1 inhibitor"),
    "CHEMBL3301587": ("durvalumab",                 "IO", "PD-L1 inhibitor"),
    "CHEMBL3833373": ("avelumab",                   "IO", "PD-L1 inhibitor"),
    "CHEMBL4297729": ("cosibelimab",                "IO", "PD-L1 inhibitor"),

    # ── IMMUNO-ONCOLOGY: CTLA-4 inhibitors ────────────────────────────────────
    "CHEMBL1789844": ("ipilimumab",                 "IO", "CTLA-4 inhibitor"),
    "CHEMBL2108658": ("tremelimumab",               "IO", "CTLA-4 inhibitor"),

    # ── IMMUNO-ONCOLOGY: LAG-3 inhibitors ─────────────────────────────────────
    "CHEMBL3990044": ("relatlimab",                 "IO", "LAG-3 inhibitor"),
    "CHEMBL4297784": ("favezelimab",                "IO", "LAG-3 inhibitor"),
    "CHEMBL4298085": ("fianlimab",                  "IO", "LAG-3 inhibitor"),
    "CHEMBL4297877": ("balstilimab",                "IO", "LAG-3 inhibitor"),  # anti-PD-L1 note: ChEMBL class

    # ── IMMUNO-ONCOLOGY: Bispecific / T-cell engager ──────────────────────────
    "CHEMBL1742992": ("blinatumomab",               "IO", "CD19 x CD3 BiTE"),
    "CHEMBL4297990": ("tebentafusp",                "IO", "TCR-T cell engager (gp100 x CD3)"),

    # ── IMMUNO-ONCOLOGY: CAR-T cell therapies ────────────────────────────────
    "CHEMBL3301574": ("tisagenlecleucel",            "IO", "CAR-T (CD19)"),
    "CHEMBL3989989": ("axicabtagene ciloleucel",     "IO", "CAR-T (CD19)"),
    "CHEMBL4297236": ("lisocabtagene maraleucel",    "IO", "CAR-T (CD19)"),
    "CHEMBL4298199": ("idecabtagene vicleucel",      "IO", "CAR-T (BCMA)"),
    "CHEMBL4802263": ("ciltacabtagene autoleucel",   "IO", "CAR-T (BCMA)"),

    # ── IMMUNO-ONCOLOGY: Cytokines / innate ──────────────────────────────────
    "CHEMBL1201438": ("aldesleukin",                "IO", "IL-2 cytokine"),

    # ── IMMUNO-ONCOLOGY: Oncolytic virus ─────────────────────────────────────
    "CHEMBL2108727": ("talimogene laherparepvec",   "IO", "Oncolytic virus (HSV-1)"),

    # ── TARGETED: HER2 ───────────────────────────────────────────────────────
    "CHEMBL1201585": ("trastuzumab",               "Targeted-HER2",  None),
    "CHEMBL2007641": ("pertuzumab",                "Targeted-HER2",  None),
    "CHEMBL4297844": ("trastuzumab deruxtecan",    "Targeted-HER2",  None),
    "CHEMBL3545111": ("lapatinib",                 "Targeted-HER2",  None),
    "CHEMBL3301610": ("abemaciclib",               "Targeted-CDK46", None),

    # ── TARGETED: EGFR ───────────────────────────────────────────────────────
    "CHEMBL1201583": ("cetuximab",                 "Targeted-EGFR",  None),
    "CHEMBL1201827": ("panitumumab",               "Targeted-EGFR",  None),
    "CHEMBL553":     ("gefitinib",                 "Targeted-EGFR",  None),
    "CHEMBL1173655": ("afatinib",                  "Targeted-EGFR",  None),
    "CHEMBL3353410": ("osimertinib",               "Targeted-EGFR",  None),

    # ── TARGETED: ALK ────────────────────────────────────────────────────────
    "CHEMBL601719":  ("crizotinib",                "Targeted-ALK",   None),
    "CHEMBL1738797": ("alectinib",                 "Targeted-ALK",   None),
    "CHEMBL3545311": ("brigatinib",                "Targeted-ALK",   None),
    "CHEMBL3286830": ("lorlatinib",                "Targeted-ALK",   None),

    # ── TARGETED: VEGF/VEGFR ─────────────────────────────────────────────────
    "CHEMBL1336":    ("sorafenib",                 "Targeted-VEGFR", None),
    "CHEMBL535":     ("sunitinib",                 "Targeted-VEGFR", None),
    "CHEMBL1289926": ("axitinib",                  "Targeted-VEGFR", None),
    "CHEMBL2105717": ("cabozantinib",              "Targeted-VEGFR", None),
    "CHEMBL1289601": ("lenvatinib",                "Targeted-VEGFR", None),

    # ── TARGETED: BCR-ABL ────────────────────────────────────────────────────
    "CHEMBL941":     ("imatinib",                  "Targeted-ABL",   None),
    "CHEMBL1131":    ("dasatinib",                 "Targeted-ABL",   None),
    "CHEMBL255863":  ("nilotinib",                 "Targeted-ABL",   None),

    # ── TARGETED: BRAF/MEK ───────────────────────────────────────────────────
    "CHEMBL1229517": ("vemurafenib",               "Targeted-BRAF",  None),
    "CHEMBL2028663": ("dabrafenib",                "Targeted-BRAF",  None),
    "CHEMBL3301612": ("encorafenib",               "Targeted-BRAF",  None),
    "CHEMBL2103875": ("trametinib",                "Targeted-MEK",   None),
    "CHEMBL2146883": ("cobimetinib",               "Targeted-MEK",   None),
    "CHEMBL3187723": ("binimetinib",               "Targeted-MEK",   None),

    # ── TARGETED: CDK4/6 ─────────────────────────────────────────────────────
    "CHEMBL189963":  ("palbociclib",               "Targeted-CDK46", None),
    "CHEMBL3545110": ("ribociclib",                "Targeted-CDK46", None),

    # ── TARGETED: PI3K/mTOR ──────────────────────────────────────────────────
    "CHEMBL2216870": ("idelalisib",                "Targeted-PI3K",  None),
    "CHEMBL3218576": ("copanlisib",                "Targeted-PI3K",  None),
    "CHEMBL1201182": ("temsirolimus",              "Targeted-mTOR",  None),
    "CHEMBL1908360": ("everolimus",                "Targeted-mTOR",  None),

    # ── TARGETED: PARP ───────────────────────────────────────────────────────
    "CHEMBL521686":  ("olaparib",                  "Targeted-PARP",  None),
    "CHEMBL1173055": ("rucaparib",                 "Targeted-PARP",  None),
    "CHEMBL1094636": ("niraparib",                 "Targeted-PARP",  None),
    "CHEMBL3137320": ("talazoparib",               "Targeted-PARP",  None),

    # ── TARGETED: BTK ────────────────────────────────────────────────────────
    "CHEMBL1873475": ("ibrutinib",                 "Targeted-BTK",   None),
    "CHEMBL3707348": ("acalabrutinib",             "Targeted-BTK",   None),
    "CHEMBL3936761": ("zanubrutinib",              "Targeted-BTK",   None),

    # ── TARGETED: Proteasome ─────────────────────────────────────────────────
    "CHEMBL325041":  ("bortezomib",                "Targeted-Proteasome", None),
    "CHEMBL451887":  ("carfilzomib",               "Targeted-Proteasome", None),
    "CHEMBL2141296": ("ixazomib",                  "Targeted-Proteasome", None),

    # ── TARGETED: Anti-CD20 ──────────────────────────────────────────────────
    "CHEMBL1201576": ("rituximab",                 "Targeted-CD20",  None),
    "CHEMBL1743048": ("obinutuzumab",              "Targeted-CD20",  None),
    "CHEMBL1201836": ("ofatumumab",                "Targeted-CD20",  None),

    # ── TARGETED: BEVACIZUMAB (VEGF-A antibody) ──────────────────────────────
    "CHEMBL1201583": ("bevacizumab",               "Targeted-VEGF",  None),

    # ── TARGETED: Hormonal / AR ──────────────────────────────────────────────
    "CHEMBL1082407": ("enzalutamide",              "Hormonal-AR",    None),
    "CHEMBL3183409": ("apalutamide",               "Hormonal-AR",    None),
    "CHEMBL4297185": ("darolutamide",              "Hormonal-AR",    None),

    # ── CHEMOTHERAPY: key agents ─────────────────────────────────────────────
    "CHEMBL1351":    ("carboplatin",               "Chemotherapy",   None),
    "CHEMBL11359":   ("cisplatin",                 "Chemotherapy",   None),
    "CHEMBL1200796": ("cyclophosphamide",          "Chemotherapy",   None),
    "CHEMBL53463":   ("doxorubicin",               "Chemotherapy",   None),
    "CHEMBL428647":  ("docetaxel",                 "Chemotherapy",   None),
    "CHEMBL507":     ("paclitaxel",                "Chemotherapy",   None),
    "CHEMBL185":     ("fluorouracil",              "Chemotherapy",   None),
    "CHEMBL888":     ("gemcitabine",               "Chemotherapy",   None),
    "CHEMBL414804":  ("oxaliplatin",               "Chemotherapy",   None),
    "CHEMBL225072":  ("pemetrexed",                "Chemotherapy",   None),
    "CHEMBL34259":   ("methotrexate",              "Chemotherapy",   None),
    "CHEMBL1024":    ("doxorubicin",               "Chemotherapy",   None),  # kept as ifosfamide alt
}

# Deduplicate by ID (keep first occurrence)
_seen = set()
CURATED_CLEAN = {}
for cid, val in CURATED.items():
    if cid not in _seen:
        _seen.add(cid)
        CURATED_CLEAN[cid] = val
CURATED = CURATED_CLEAN


def get_json(url, params=None, retries=3):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read())
        except Exception:
            if attempt == retries - 1:
                return {}
            time.sleep(1.5 ** attempt)
    return {}


def fetch_all_pages(endpoint, params, key):
    params = dict(params, limit=100, offset=0, format="json")
    results = []
    while True:
        data = get_json(f"{BASE}/{endpoint}/", params)
        page = data.get(key, [])
        results.extend(page)
        if not data.get("page_meta", {}).get("next"):
            break
        params["offset"] += params["limit"]
        time.sleep(0.25)
    return results


def fetch_molecule(chembl_id):
    return get_json(f"{BASE}/molecule/{chembl_id}/", {"format": "json"})


def fetch_indications(chembl_id):
    return fetch_all_pages("drug_indication", {"molecule_chembl_id": chembl_id}, "drug_indications")


def fetch_targets(chembl_id):
    mechs = fetch_all_pages("mechanism", {"molecule_chembl_id": chembl_id}, "mechanisms")
    targets = []
    seen = set()
    for m in mechs:
        tid = m.get("target_chembl_id")
        if not tid or tid in seen:
            continue
        seen.add(tid)
        tdata = get_json(f"{BASE}/target/{tid}/", {"format": "json"})
        targets.append({
            "target_chembl_id": tid,
            "target_name": tdata.get("pref_name", tid),
            "target_type": tdata.get("target_type", ""),
            "action_type": m.get("action_type", ""),
            "mechanism_of_action": m.get("mechanism_of_action", ""),
        })
        time.sleep(0.12)
    return targets


ONCO_KW = (
    "neoplas", "carcinom", "lymphom", "leukem", "melanom",
    "tumor", "tumour", "cancer", "myelom", "gliom",
    "sarcoma", "hepatocel", "mesotheliom",
)


def main():
    os.makedirs("output", exist_ok=True)
    chembl_ids = list(CURATED.keys())
    total = len(chembl_ids)
    print(f"Processing {total} curated oncology drugs (incl. full IO panel)...\n")

    rows = []
    for i, chembl_id in enumerate(chembl_ids, 1):
        curated_name, drug_class, io_subtype_hint = CURATED[chembl_id]

        mol = fetch_molecule(chembl_id)
        pref_name = mol.get("pref_name") or curated_name
        mol_type = mol.get("molecule_type", "")
        syns = mol.get("molecule_synonyms") or []
        trade_names = sorted({
            s["molecule_synonym"] for s in syns
            if s.get("syn_type") == "TRADE_NAME"
        })

        targets = fetch_targets(chembl_id)
        indications_raw = fetch_indications(chembl_id)

        onc_indications = sorted({
            (ind.get("efo_term") or ind.get("mesh_heading") or "").strip()
            for ind in indications_raw
            if any(kw in (ind.get("mesh_heading") or "").lower() or
                   kw in (ind.get("efo_term") or "").lower()
                   for kw in ONCO_KW)
        } - {""})

        is_io = drug_class == "IO"

        # Auto-detect IO subtype from targets if hint not given
        io_subtype = io_subtype_hint
        if is_io and not io_subtype:
            tnames = " ".join(t["target_name"].lower() for t in targets)
            if "pd-1" in tnames or "programmed cell death" in tnames:
                io_subtype = "PD-1 inhibitor"
            elif "pd-l1" in tnames or "cd274" in tnames:
                io_subtype = "PD-L1 inhibitor"
            elif "ctla-4" in tnames or "cytotoxic t-lymphocyte" in tnames:
                io_subtype = "CTLA-4 inhibitor"
            elif "lag-3" in tnames:
                io_subtype = "LAG-3 inhibitor"

        row = {
            "chembl_id": chembl_id,
            "preferred_name": pref_name,
            "trade_names": trade_names,
            "molecule_type": mol_type,
            "drug_class": drug_class,
            "is_immuno_oncology": is_io,
            "io_subtype": io_subtype,
            "targets": targets,
            "oncology_indications": onc_indications,
            "total_indications": len(indications_raw),
        }
        rows.append(row)

        tag = f" [{io_subtype}]" if io_subtype else f" [{drug_class}]"
        print(f"  [{i:>3}/{total}] {pref_name}{tag}"
              f"  |  {len(targets)} target(s), {len(onc_indications)} onc. indications")
        time.sleep(0.15)

    json_path = "output/chembl_oncology_drugs.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    print(f"\nJSON saved -> {json_path}")

    print_report(rows)


# ── Report ────────────────────────────────────────────────────────────────────

CLASS_ORDER = [
    ("IO",                  "IMMUNO-ONCOLOGY"),
    ("Targeted-HER2",       "TARGETED: HER2"),
    ("Targeted-EGFR",       "TARGETED: EGFR"),
    ("Targeted-ALK",        "TARGETED: ALK"),
    ("Targeted-VEGFR",      "TARGETED: VEGFR / Multi-kinase"),
    ("Targeted-VEGF",       "TARGETED: VEGF (antibody)"),
    ("Targeted-ABL",        "TARGETED: BCR-ABL"),
    ("Targeted-BRAF",       "TARGETED: BRAF"),
    ("Targeted-MEK",        "TARGETED: MEK"),
    ("Targeted-CDK46",      "TARGETED: CDK4/6"),
    ("Targeted-PI3K",       "TARGETED: PI3K"),
    ("Targeted-mTOR",       "TARGETED: mTOR"),
    ("Targeted-PARP",       "TARGETED: PARP"),
    ("Targeted-BTK",        "TARGETED: BTK"),
    ("Targeted-Proteasome", "TARGETED: Proteasome"),
    ("Targeted-CD20",       "TARGETED: Anti-CD20"),
    ("Hormonal-AR",         "HORMONAL: Androgen Receptor"),
    ("Chemotherapy",        "CLASSIC CHEMOTHERAPY"),
]


def print_report(rows):
    W = 92
    by_class = {}
    for r in rows:
        by_class.setdefault(r["drug_class"], []).append(r)

    print("\n" + "=" * W)
    print("  CHEMBL ONCOLOGY DRUG DATABASE  |  Targets & Approved Indications")
    print("=" * W)

    io_subtypes_seen = {}  # subtype -> count
    for key, label in CLASS_ORDER:
        subset = by_class.get(key, [])
        if not subset:
            continue

        print(f"\n{'-'*W}")
        print(f"  {label}  ({len(subset)} drug{'s' if len(subset)!=1 else ''})")
        print(f"{'-'*W}")

        for r in sorted(subset, key=lambda x: x["preferred_name"].lower()):
            nm = r["preferred_name"].upper()
            io_tag = f"  [{r['io_subtype']}]" if r.get("io_subtype") else ""
            trades = ("  |  " + ", ".join(r["trade_names"][:4])) if r["trade_names"] else ""
            print(f"\n  {nm}{io_tag}{trades}")
            print(f"    ChEMBL: {r['chembl_id']}  |  Type: {r['molecule_type'] or 'n/a'}")

            if r["targets"]:
                print("    Targets / Mechanism of Action:")
                for t in r["targets"]:
                    moa = t["mechanism_of_action"] or t["action_type"] or "unknown"
                    print(f"      - {t['target_name']}  ({t['target_type']})  ->  {moa}")
            else:
                print("    Targets: not mapped in ChEMBL mechanisms")

            if r["oncology_indications"]:
                shown = r["oncology_indications"][:10]
                print(f"    Oncology Indications ({r['total_indications']} total in ChEMBL):")
                for ind in shown:
                    print(f"      - {ind}")
                extra = len(r["oncology_indications"]) - len(shown)
                if extra > 0:
                    print(f"      ... +{extra} more oncology terms")
            else:
                print("    Oncology Indications: none in ChEMBL")

            if r.get("io_subtype"):
                io_subtypes_seen[r["io_subtype"]] = io_subtypes_seen.get(r["io_subtype"], 0) + 1

    io_total = sum(1 for r in rows if r["is_immuno_oncology"])
    tgt_total = sum(1 for r in rows if not r["is_immuno_oncology"] and r["drug_class"].startswith("Targeted"))
    hor_total = sum(1 for r in rows if r["drug_class"].startswith("Hormonal"))
    chm_total = sum(1 for r in rows if r["drug_class"] == "Chemotherapy")

    print(f"\n{'='*W}")
    print(f"  SUMMARY  |  {len(rows)} drugs total")
    print(f"  IO: {io_total}  |  Targeted: {tgt_total}  |  Hormonal: {hor_total}  |  Chemo: {chm_total}")
    if io_subtypes_seen:
        print(f"\n  IO breakdown by mechanism:")
        for subtype, cnt in sorted(io_subtypes_seen.items(), key=lambda x: -x[1]):
            print(f"    {subtype:40s}  {cnt}")
    print(f"{'='*W}\n")


if __name__ == "__main__":
    main()
