#!/usr/bin/env python3
"""Combine all niche JSON files into a single dataset."""

import json
import os

niches_dir = "/Users/yahya/shopify_list/niches/"
all_apps = []

for fname in sorted(os.listdir(niches_dir)):
    if fname.endswith(".json"):
        path = os.path.join(niches_dir, fname)
        with open(path) as f:
            data = json.load(f)
        niche = data["niche"]
        for app in data["top_apps"]:
            app["niche"] = niche
        all_apps.extend(data["top_apps"])

output = {"total_apps": len(all_apps), "niches": {}, "all_apps": all_apps}

# Group by niche
for app in all_apps:
    niche = app.pop("niche")
    if niche not in output["niches"]:
        output["niches"][niche] = []
    output["niches"][niche].append(app)

# Write combined file
out_path = "/Users/yahya/shopify_list/combined_all_apps.json"
with open(out_path, "w") as f:
    json.dump(output, f, indent=2)

print(f"Total apps: {len(all_apps)}")
print(f"Niche count: {len(output['niches'])}")
for niche, apps in sorted(output["niches"].items()):
    print(f"  {niche}: {len(apps)} apps")
