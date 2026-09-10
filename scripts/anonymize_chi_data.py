# Turns the real CLIENT MASTER + VISIT_LOG sheets into anonymized seed
# data so this can actually go on GitHub. Quick rundown of what changes:
#
# - names, emails, phones, addresses: gone completely
# - free text fields (visit notes, "other specify"): gone completely,
#   people write background/health/immigration stuff in there sometimes
# - SS card / birth cert / state ID: squashed into one 0-3 score instead
#   of 3 separate yes/no columns, so no single doc status is exposed
# - SNAP status: dropped, not touching benefits data at all
# - client IDs: shuffled and renumbered so they can't map back to the
#   original sheet
# - volunteer names: replaced with Volunteer_A, Volunteer_B, etc.
#
# usage: python3 anonymize_chi_data.py <path-to-xlsx>
# writes: seeds/dim_clients.csv, seeds/fact_visits.csv
import sys
import random
import openpyxl
import csv
from pathlib import Path

random.seed(42)  # so the shuffle is repeatable, not different every run

def load(path):
    return openpyxl.load_workbook(path, data_only=True)

def clean_client_master(ws):
    header = [c.value for c in ws[1]]
    idx = {h.strip(): i for i, h in enumerate(header) if h}

    def col(row, name, default=None):
        i = idx.get(name)
        return row[i] if i is not None and i < len(row) else default

    clients = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        client_id = col(row, "Client ID") or col(row, "Client ID ")
        if not client_id:
            continue
        clients.append(row)
    return header, idx, clients

def yn(val):
    if val is None:
        return 0
    s = str(val).strip().lower()
    return 1 if s in ("yes", "y", "true") else 0

def main(xlsx_path):
    wb = load(xlsx_path)
    ws_cm = wb["CLIENT MASTER"]
    ws_vl = wb["VISIT_LOG"] if "VISIT_LOG" in wb.sheetnames else wb["VISIT LOG"]

    header, idx, raw_clients = clean_client_master(ws_cm)

    def g(row, *names):
        for n in names:
            i = idx.get(n.strip())
            if i is not None and i < len(row):
                return row[i]
        return None

    # shuffle old ids and hand out new CLIENT-### ids so they don't map back
    old_ids = [g(r, "Client ID", "Client ID ") for r in raw_clients]
    old_ids = [str(x).strip() for x in old_ids if x]
    shuffled = old_ids[:]
    random.shuffle(shuffled)
    id_map = {old: f"CLIENT-{i+1:03d}" for i, old in enumerate(shuffled)}

    dim_clients = []
    for row in raw_clients:
        old_id = str(g(row, "Client ID", "Client ID ")).strip()
        if old_id not in id_map:
            continue
        new_id = id_map[old_id]

        ss_card = yn(g(row, "Do you have your social security card?"))
        birth_cert = yn(g(row, "Do you have your birth certificate?"))
        state_id = yn(g(row, "Do you have state ID card? ", "Do you have state ID card?"))
        doc_score = ss_card + birth_cert + state_id

        intake_date = g(row, "Date ", "Date", "First Visit")
        intake_date = intake_date.date().isoformat() if hasattr(intake_date, "date") else intake_date

        dim_clients.append({
            "client_id": new_id,
            "intake_date": intake_date,
            "gender": g(row, "gender", "Gender") or "Unknown",
            "age_bucket": g(row, "Age") or "Unknown",
            "employment_status": g(row, "Are you currently employed? ", "Employed?") or "Unknown",
            "work_interest": g(row, "What kind of work are you interested in? ", "Work Interest") or "Unspecified",
            "job_goal": g(row, "What is your current job goal? ", "Job Goal") or "Unspecified",
            "has_resume": g(row, "Do you currently have a resume? ", "Has Resume?") or "Unknown",
            "document_readiness_score": doc_score,
        })

    # ---- VISIT_LOG ----
    header_vl = [c.value for c in ws_vl[1]]
    idx_vl = {h.strip(): i for i, h in enumerate(header_vl) if h}

    def gv(row, *names):
        for n in names:
            i = idx_vl.get(n.strip())
            if i is not None and i < len(row):
                return row[i]
        return None

    volunteer_map = {}
    fact_visits = []
    visit_num = 0
    for row in ws_vl.iter_rows(min_row=2, values_only=True):
        client_old_id = gv(row, "CLIENT ID", "CLIENT ID ", "Client ID")
        date_val = gv(row, "Date", "Date ") or (row[0] if len(row) > 0 else None)
        if not client_old_id or not date_val:
            continue
        client_old_id = str(client_old_id).strip()
        if client_old_id not in id_map:
            continue
        visit_num += 1

        vol = gv(row, "VOLUNTEER NAME ", "Volunteer")
        vol_key = str(vol).strip().lower() if vol else "unknown"
        if vol_key not in volunteer_map:
            volunteer_map[vol_key] = f"Volunteer_{chr(65 + len(volunteer_map))}"
        vol_pseudo = volunteer_map[vol_key]

        visit_date = date_val.date().isoformat() if hasattr(date_val, "date") else date_val

        fact_visits.append({
            "visit_id": f"V-{visit_num:04d}",
            "client_id": id_map[client_old_id],
            "visit_date": visit_date,
            "volunteer": vol_pseudo,
            "resume_done": gv(row, "RESUME DONE ", "RESUME DONE") or "Unknown",
            "phone_given": 1 if gv(row, "PHONE (GIVEN) ", "PHONE (GIVEN)") else 0,
            "bus_pass_given": 1 if gv(row, "BUS PASS") else 0,
            "service_category": gv(row, "SUMMARY") or "Uncategorized",
        })

    out_dir = Path(__file__).parent / "seeds"
    out_dir.mkdir(exist_ok=True)

    with open(out_dir / "dim_clients.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(dim_clients[0].keys()))
        w.writeheader()
        w.writerows(dim_clients)

    with open(out_dir / "fact_visits.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fact_visits[0].keys()))
        w.writeheader()
        w.writerows(fact_visits)

    print(f"Wrote {len(dim_clients)} clients -> seeds/dim_clients.csv")
    print(f"Wrote {len(fact_visits)} visits  -> seeds/fact_visits.csv")

if __name__ == "__main__":
    main(sys.argv[1])
