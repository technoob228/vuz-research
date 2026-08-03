#!/usr/bin/env python3
"""Монитор конкурсных списков РЭУ. Данные: abitrating.rea.ru (Supabase REST)."""
import json, urllib.request, sys, os

BASE = "https://abitrating.rea.ru/rest/v1"
KEY = open(os.path.join(os.path.dirname(__file__), "rea.key")).read().strip()
HDR = {"apikey": KEY, "Authorization": "Bearer " + KEY, "Accept": "application/json"}

def get(path, **params):
    q = "&".join(f"{k}={v}" for k, v in params.items())
    req = urllib.request.Request(f"{BASE}/{path}?{q}", headers=HDR)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def get_all(path, page=1000, **params):
    """Постраничная выкачка через Range."""
    out, off = [], 0
    while True:
        q = "&".join(f"{k}={v}" for k, v in params.items())
        req = urllib.request.Request(f"{BASE}/{path}?{q}", headers={**HDR,
              "Range-Unit": "items", "Range": f"{off}-{off+page-1}"})
        with urllib.request.urlopen(req, timeout=120) as r:
            chunk = json.load(r)
        out += chunk
        if len(chunk) < page:
            return out
        off += page

def groups():
    """Справочник конкурсных групп: id -> инфо."""
    g = get_all("all_competitive_group_stats", select="*")
    return {x["competitive_group_id"]: x for x in g}

def by_code(code):
    return get("entrants", unique_code_profile=f"eq.{code}", select="*")

if __name__ == "__main__":
    code = sys.argv[1] if len(sys.argv) > 1 else "2260794"
    G = groups()
    rows = by_code(code)
    print(f"код {code}: {len(rows)} заявок, справочник {len(G)} групп\n")
    items = []
    for r in rows:
        g = G.get(r["competitive_group_id"], {})
        items.append({
            "prog": g.get("speciality_name", "?"),
            "group": g.get("competitive_group_name", "?"),
            "type": g.get("place_type_name", "?"),
            "form": g.get("education_form_name", ""),
            "level": g.get("educational_level_name", ""),
            "seats": g.get("admission_volume"),
            "total": g.get("entrant_count"),
            "pos": r["rating"], "prio": r["priority"], "score": r["sum_mark"],
            "agree": r["agreement"], "contract": r["contract"],
            "date": r["date_of_list"][:16],
        })
    items.sort(key=lambda x: (x["type"], x["prio"] or 99))
    for i in items:
        flag = "СОГЛАСИЕ" if i["agree"] else ("ДОГОВОР" if i["contract"] else "")
        print(f"[{i['type'][:8]:8}] прио {i['prio']:>2} | поз {i['pos']:>5} из {i['total'] or '?':>5} "
              f"| мест {i['seats'] or '?':>4} | балл {i['score']:>3} | {i['prog'][:52]} {flag}")
    print(f"\nдата списка: {items[0]['date'] if items else '?'}")
