#!/usr/bin/env python3
"""Итеративная симуляция зачисления (deferred acceptance).

Каждый абитуриент занимает место только на самом приоритетном конкурсе,
где проходит. Освободившиеся места достаются следующим — и так по кругу,
пока картина не стабилизируется. Бюджет и контракт считаются раздельно.
"""
import json, sys
from collections import defaultdict

G = {g["competitive_group_id"]: g for g in json.load(open("groups.json"))}
E = json.load(open("entrants.json"))

def run(place_type, level="Бакалавриат", verbose=False):
    gids = {k for k, g in G.items()
            if g.get("place_type_name") == place_type
            and g.get("educational_level_name") == level}
    rows = [r for r in E if r["competitive_group_id"] in gids and r["rating"]]
    # заявки по людям
    apps = defaultdict(list)
    for r in rows:
        apps[r["unique_code_profile"]].append(r)
    for c in apps:
        apps[c].sort(key=lambda r: r["priority"] or 99)
    # списки по группам, отсортированные по позиции
    bygroup = defaultdict(list)
    for r in rows:
        bygroup[r["competitive_group_id"]].append(r)
    for g in bygroup:
        bygroup[g].sort(key=lambda r: r["rating"])

    assigned = {}          # код -> competitive_group_id
    for it in range(40):
        # для каждой группы отбираем топ по местам среди тех,
        # кто не устроен лучше (по своему приоритету)
        newass = {}
        for gid, lst in bygroup.items():
            seats = G[gid].get("admission_volume") or 0
            if not seats: continue
            taken = 0
            for r in lst:
                code = r["unique_code_profile"]
                cur = assigned.get(code)
                if cur and cur != gid:
                    # уже устроен: сравниваем приоритеты
                    cur_prio = next((a["priority"] for a in apps[code]
                                     if a["competitive_group_id"] == cur), 99) or 99
                    if cur_prio <= (r["priority"] or 99):
                        continue          # там лучше или столько же — сюда не идёт
                newass.setdefault(code, []).append((r["priority"] or 99, gid))
                taken += 1
                if taken >= seats: break
        # каждый выбирает лучший из предложенных
        upd = {c: min(v)[1] for c, v in newass.items()}
        if upd == assigned:
            break
        assigned = upd
    return assigned, bygroup, apps

def report(code, place_type):
    assigned, bygroup, apps = run(place_type)
    mine = apps.get(code, [])
    if not mine:
        print(f"нет заявок ({place_type})"); return
    print(f"\n=== {place_type} ===")
    got = assigned.get(code)
    for a in mine:
        g = G[a["competitive_group_id"]]
        seats = g.get("admission_volume") or 0
        lst = bygroup[a["competitive_group_id"]]
        # сколько выше по списку реально остаётся здесь после каскада
        above_stay = sum(1 for r in lst if r["rating"] < a["rating"]
                         and assigned.get(r["unique_code_profile"]) == a["competitive_group_id"])
        eff = above_stay + 1
        mark = "  ✓ ЗАЧИСЛЕН" if got == a["competitive_group_id"] else ""
        name = g["competitive_group_name"].split(",")[0]
        print(f"прио {a['priority']:>2} | поз {a['rating']:>4}/{len(lst):<4} мест {seats:>4} "
              f"| после каскада ≈{eff:>4} | балл {a['sum_mark']:>3} | {name[:46]}{mark}")
    if got:
        print(f"\nИТОГ: проходит на «{G[got]['competitive_group_name'].split(',')[0]}»")
    else:
        print("\nИТОГ: не проходит никуда по текущим данным")

if __name__ == "__main__":
    code = sys.argv[1] if len(sys.argv) > 1 else "2260794"
    for pt in ("Контракт", "Общий конкурс"):
        report(code, pt)
