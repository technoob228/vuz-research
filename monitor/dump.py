#!/usr/bin/env python3
"""Полная выгрузка списков РЭУ в локальный JSON."""
import json, time, urllib.request, os
BASE="https://abitrating.rea.ru/rest/v1"
KEY=open(os.path.join(os.path.dirname(__file__),"rea.key")).read().strip()
HDR={"apikey":KEY,"Authorization":"Bearer "+KEY}

def page(path, off, size, select="*"):
    req=urllib.request.Request(f"{BASE}/{path}?select={select}",
        headers={**HDR,"Range-Unit":"items","Range":f"{off}-{off+size-1}"})
    with urllib.request.urlopen(req,timeout=120) as r: return json.load(r)

def dump(path, size=5000, select="*"):
    out=[]; off=0
    while True:
        c=page(path,off,size,select)
        out+=c
        print(f"  {path}: {len(out)}",end="\r",flush=True)
        if len(c)<size: break
        off+=size; time.sleep(0.2)
    print()
    return out

if __name__=="__main__":
    g=dump("all_competitive_group_stats")
    json.dump(g,open("groups.json","w"),ensure_ascii=False)
    e=dump("entrants",select="unique_code_profile,competitive_group_id,rating,priority,sum_mark,agreement,contract,application_status,without_tests")
    json.dump(e,open("entrants.json","w"),ensure_ascii=False)
    print(f"готово: {len(g)} групп, {len(e)} записей")
