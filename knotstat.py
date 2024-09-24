#!/usr/bin/env python3

import re
import sys
import json
import subprocess

CMD_TIMEOUT = 5 # seconds

def knotc(cmd):
  try:
    proc = subprocess.run(
      f"knotc {cmd}".split(), timeout=CMD_TIMEOUT,
      stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
  except FileNotFoundError: raise Exception("knotc not found")
  result = proc.stdout.decode("utf-8")
  return result

def convert_state_time(time):
  if time == "pending" or time == "running":
    return 0
  elif time == "not scheduled":
    return None
  else:
    match = re.match(r"([+-])((\d+)D)?((\d+)h)?((\d+)m)?((\d+)s)?", time)
    seconds = -1 if match.group(1) == "-" else 1
    if match.group(3):
      seconds = seconds + 86400 * int(match.group(3))
    if match.group(5):
      seconds = seconds + 3600 * int(match.group(5))
    if match.group(7):
      seconds = seconds + 60 * int(match.group(7))
    if match.group(9):
      seconds = seconds + int(match.group(9))
    return seconds

def knot_status():
  data = dict()
  return knotc("status").strip().lower()

def knot_zones():
  zones = dict()
  output = knotc("zone-status")
  for line in output.splitlines():
    res = re.search(r"^\[(.*)\.\]\s.*role:\s+(\w+)\s*",line)
    zones[res.group(1)] = res.group(2)
  return zones

def knot_zone_stats(zone):
  data = {"domain": zone}
  output = knotc(f"zone-status {zone}")
  output = output.replace(f"[{zone}.] ", "")
  error_pattern = f"error: "
  if output.startswith(error_pattern):
    if "(no such zone found)" in output:
      print(f"error: zone '{zone}' not found in knot")
      exit(1)
    raise Exception(f"error:"+output.replace(error_pattern,""))
  for metric in output.split("|"):
    m = metric.split(":")
    mk = m[0].strip().replace(".","-")
    mv = m[1].strip()
    if mk in ["expiration", "refresh"]:
      mv = convert_state_time(mv)
    data[mk] = mv
  # ---
  output = knotc(f"zone-stats {zone}")
  for line in output.splitlines():
    res = re.search(r"^\[.*\.\]\s(.*)\s+=\s+(.*)$",line)
    mk = res.group(1).strip().replace("mod-stats.","").replace(".","-")
    mv = res.group(2).strip()
    if mv.isnumeric():
      if re.search(r"\d+\.\d+", mv): mv = float(mv)
      else: mv = int(mv)
    res = re.search(r"([\w-]+)\[(\w+)\]", mk)
    if res:
      if res.group(1) not in data: data[res.group(1)] = dict()
      data[res.group(1)][res.group(2)] = mv
    else: data[mk] = mv
    # ---
  output = knotc(f"zone-read {zone} @ SOA")
  res = output.split()
  data["soa"] = dict()
  data["soa"]["ttl"] = int(res[2])
  data["soa"]["refresh"] = int(res[7])
  data["soa"]["retry"] = int(res[8])
  data["soa"]["expire"] = int(res[9])
  data["soa"]["min-ttl"] = int(res[10])

  return data

def resolve(result):
  print(json.dumps(result,sort_keys=True))
  exit(0)

def help():
  print("knotstats.py {cmd}:")
  print(" status  - get knot status")
  print(" zones  - get zones list")
  print(" stats {zone}  - get zone stats")
  exit(0)

def main():
  if len(sys.argv) < 2: help()
  cmd = sys.argv[1]
  if cmd == "status":
    print(knot_status())
    exit(0)
  elif cmd == "zones":
    resolve(knot_zones())
  elif cmd == "zone":
    if len(sys.argv) != 3:
      print("error: empty zone param")
      exit(1)
    resolve(knot_zone_stats(sys.argv[2]))
  else:
    print(f"error: unknown command {cmd}")
    exit(1)

if __name__ == "__main__":
  main()
