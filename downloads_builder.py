import glob
import json
import os
import urllib.request


def clean_str(s):
  s = s.strip()
  for c in ['"', "'"]:
    if s.startswith(c) and s.endswith(c) and len(s) >= 2:
      s = s[1:-1]
  return s.strip()


# Mapping assets to ID
asset_to_id = {}
for toml_path in glob.glob("launcher-data/mods/*.toml"):
  try:
    mod_id = ""
    download_url = ""
    with open(toml_path, "r", encoding="utf-8") as f:
      for line in f:
        line = line.strip()
        if line.startswith("id"):
          eq = line.find("=")
          if eq > 0:
            mod_id = clean_str(line[eq + 1 :])
        elif line.startswith("downloadUrl") or line.startswith("download"):
          eq = line.find("=")
          if eq > 0:
            download_url = clean_str(line[eq + 1 :])
    if download_url and mod_id:
      asset_name = download_url.split("/")[-1].lower()
      asset_to_id[asset_name] = mod_id
    elif mod_id:
      fn = os.path.basename(toml_path).replace(".toml", ".zip").lower()
      asset_to_id[fn] = mod_id
  except Exception as e:
    print(f"Error reading {toml_path}: {e}")

# Fetching downloads!
req = urllib.request.Request(
    "https://api.github.com/repos/lw-kizii/_/releases",
    headers={
        "User-Agent": "Downloads-Builder",
        "Accept": "application/vnd.github+json",
    },
)
token = os.environ.get("GITHUB_TOKEN")
if token:
  req.add_header("Authorization", f"token {token}")

lines = ["# Mods (sorted by downloads!)"]
try:
  with urllib.request.urlopen(req) as resp:
    releases = json.loads(resp.read().decode("utf-8"))
    for rel in releases:
      for asset in rel.get("assets", []):
        name = asset.get("name", "")
        count = asset.get("download_count", 0)
        if name:
          asset_key = name.lower()
          mod_id = asset_to_id.get(asset_key)
          if not mod_id:
            mod_id = (
                asset_key[:-4] if asset_key.endswith(".zip") else asset_key
            )
          lines.append(f"{mod_id}={count}")
except Exception as e:
  print(f"Error fetching releases: {e}")

os.makedirs("launcher-data", exist_ok=True)
with open("launcher-data/downloads.txt", "w", encoding="utf-8") as f:
  f.write("\n".join(lines) + "\n")

print("Successfully updated launcher-data/downloads.txt")
