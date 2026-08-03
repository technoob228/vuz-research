#!/usr/bin/env python3
"""Симуляция зачисления: кто из стоящих выше реально претендует на место.

Логика: у каждого конкурента смотрим все его заявки. Если у него есть заявка
с БОЛЕЕ ВЫСОКИМ приоритетом (меньший номер), где он проходит по позиции в
пределах числа мест, — он уйдёт туда, и здесь место освободит.
"""
import sys, json
from collections import defaultdict
from rea_fetch import get_all, groups, get

def analyze(group_id, my_code, key_field="rating"):
    G = groups()
    g = G[group_id]
    seats = g["admission_volume"]
    rows = get_all("entrants", competitive_group_id=f"eq.{group_id}", select="*")
    rows.sort(key=lambda r: r[key_field])
    me = next((r for r in rows if r["unique_code_profile"] == my_code), None)
    my_pos = me["rating"] if me else None

    above = [r for r in rows if r["rating"] < (my_pos or 10**9)]
    codes = [r["unique_code_profile"] for r in above]

    # тянем все заявки конкурентов пачками
    profiles = defaultdict(list)
    B = 150
    for i in range(0, len(codes), B):
        chunk = codes[i:i+B]
        lst = ",".join(chunk)
        data = get("entrants", unique_code_profile=f"in.({lst})", select="unique_code_profile,competitive_group_id,rating,priority,agreement,contract")
        for d in data:
            profiles[d["unique_code_profile"]].append(d)

    leaving = staying = unknown = 0
    for r in above:
        code = r["unique_code_profile"]
        my_prio = r["priority"]
        apps = profiles.get(code, [])
        better = [a for a in apps
                  if a["priority"] and my_prio and a["priority"] < my_prio]
        # проходит ли он где-то выше по приоритету
        goes_elsewhere = False
        for a in better:
            gg = G.get(a["competitive_group_id"])
            if gg and gg["admission_volume"] and a["rating"] <= gg["admission_volume"]:
                goes_elsewhere = True
                break
        if goes_elsewhere: leaving += 1
        elif better: unknown += 1
        else: staying += 1

    return {
        "group": g["competitive_group_name"], "seats": seats,
        "total": len(rows), "my_pos": my_pos, "my_score": me["sum_mark"] if me else None,
        "above": len(above), "leaving": leaving, "staying": staying, "unknown": unknown,
        "effective_pos": staying + 1,
        "verdict": "ПРОХОДИТ" if staying + 1 <= seats else "не проходит",
        "margin": seats - (staying + 1),
    }

if __name__ == "__main__":
    gid = sys.argv[1]; code = sys.argv[2] if len(sys.argv) > 2 else "2260794"
    r = analyze(gid, code)
    print(json.dumps(r, ensure_ascii=False, indent=2))
