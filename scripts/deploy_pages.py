#!/usr/bin/env python3
"""Deploy dist/ to Cloudflare Pages via the verified Direct Upload flow.

Usage: python3 scripts/deploy_pages.py [--project NAME] [--branch BRANCH]

Steps:
  1. GET  /client/v4/accounts                                   -> account id
  2. POST /client/v4/accounts/{acct}/pages/projects             -> create project (skip if exists)
  3. GET  .../pages/projects/{name}/upload-token               -> short-lived JWT
  4. POST https://api.cloudflare.com/client/v4/pages/assets/upload
         JSON array [{key, value(base64), metadata:{contentType}, base64:true}]
         with Authorization: Bearer <jwt>
  5. POST .../pages/projects/{name}/deployments  (multipart form:
         manifest={"/path": key}, branch=<branch>) with account-token auth

Manifest keys are the file's site path with a leading slash, e.g.
"/index.html", "/check-off/index.html", "/assets/css/style.css".
Asset key = first 32 chars of sha256 hex of the file content.

Credentials are injected at request time via dynamic_credentials (surrogate);
nothing is printed or written to disk.
"""
import base64
import hashlib
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
API = "https://api.cloudflare.com/client/v4"
CRED = "custom.cloudflare"
HOSTS = ("api.cloudflare.com",)

PROJECT = "national-park-passport"
BRANCH = "main"
for i, a in enumerate(sys.argv):
    if a == "--project" and i + 1 < len(sys.argv):
        PROJECT = sys.argv[i + 1]
    if a == "--branch" and i + 1 < len(sys.argv):
        BRANCH = sys.argv[i + 1]

BATCH = 10  # files per assets-upload request


def cf(method, path, body=None, headers=None, raw_body=None):
    """Call the Cloudflare API with the stored account credential."""
    url = API + path if path.startswith("/") else path
    data = None
    if raw_body is not None:
        data = raw_body
    elif body is not None:
        data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("User-Agent", "muse-cloudflare-skill")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    if body is not None and not (headers or {}).get("Content-Type"):
        req.add_header("Content-Type", "application/json")
    add_surrogate_to_request(req, CRED, allowed_hosts=HOSTS)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return read_json_response(resp)
    except urllib.error.HTTPError as exc:
        try:
            err = json.loads(exc.read().decode("utf-8", errors="replace"))
        except Exception:
            err = {"http_status": exc.code}
        raise RuntimeError(f"CF {method} {path} -> HTTP {exc.code}: {json.dumps(err)[:500]}")


def collect_files():
    files = []
    for dirpath, _, filenames in os.walk(DIST):
        for f in sorted(filenames):
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, DIST).replace(os.sep, "/")
            files.append((rel, full))
    return files


def content_type(rel):
    mime, _ = mimetypes.guess_type(rel)
    if rel.endswith(".js"):
        return "application/javascript"
    if rel.endswith(".xml"):
        return "application/xml"
    return mime or "application/octet-stream"


def main():
    if not os.path.isdir(DIST):
        sys.exit("dist/ not found — run python3 build.py first")

    # 1. account id
    accts = cf("GET", "/accounts")
    results = accts.get("result") or []
    if not results:
        sys.exit("no Cloudflare accounts found for this credential")
    acct = results[0]["id"]
    print(f"account: {results[0].get('name')} ({acct[:8]}...)")

    # 2. project (create or reuse)
    try:
        proj = cf("GET", f"/accounts/{acct}/pages/projects/{PROJECT}")
        print(f"project '{PROJECT}' exists")
    except RuntimeError as e:
        if "8092" in str(e) or "not found" in str(e).lower() or "404" in str(e):
            proj = cf("POST", f"/accounts/{acct}/pages/projects",
                      {"name": PROJECT, "production_branch": BRANCH})
            print(f"project '{PROJECT}' created")
        else:
            raise
    # tolerate already-exists race on create path
    subdomain = (proj.get("result") or {}).get("subdomain") or f"{PROJECT}.pages.dev"

    # 3. upload token (JWT, ~5 min validity)
    tok = cf("GET", f"/accounts/{acct}/pages/projects/{PROJECT}/upload-token")
    jwt = tok["result"]["jwt"]
    print("upload token acquired")

    # 4. upload assets in batches
    files = collect_files()
    print(f"uploading {len(files)} files ...")
    manifest = {}
    batch = []
    def flush(batch):
        payload = [
            {"key": key, "value": b64, "metadata": {"contentType": ct}, "base64": True}
            for key, b64, ct in batch
        ]
        req = urllib.request.Request(
            API + "/pages/assets/upload",
            data=json.dumps(payload).encode(), method="POST")
        req.add_header("User-Agent", "muse-cloudflare-skill")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", "Bearer " + jwt)
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                out = read_json_response(resp)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:800]
            raise RuntimeError(f"assets upload -> HTTP {exc.code}: {body}")
        # response: {"result": {"jwt": ..., "buckets": [[hash,...], ...]}}
        return out

    pending = []  # (site_path, key)
    for rel, full in files:
        with open(full, "rb") as fh:
            raw = fh.read()
        key = hashlib.sha256(raw).hexdigest()[:32]
        site_path = "/" + rel
        manifest[site_path] = key
        batch.append((key, base64.b64encode(raw).decode(), content_type(rel)))
        pending.append(site_path)
        if len(batch) >= BATCH:
            flush(batch)
            print(f"  ... {len(pending)}/{len(files)}")
            batch = []
    if batch:
        flush(batch)
    print(f"  ... {len(pending)}/{len(files)} assets uploaded")

    # 5. create deployment (multipart form, account-token auth)
    boundary = "----nppdeploy" + hashlib.sha256(os.urandom(16)).hexdigest()[:16]
    def part(name, value, ctype="text/plain"):
        return (f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n'
                f"Content-Type: {ctype}\r\n\r\n{value}\r\n").encode()
    body = part("manifest", json.dumps(manifest), "application/json")
    body += part("branch", BRANCH)
    body += f"--{boundary}--\r\n".encode()
    dep = cf("POST", f"/accounts/{acct}/pages/projects/{PROJECT}/deployments",
             headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
             raw_body=body)
    result = dep.get("result") or {}
    url = result.get("url")
    print(f"deployment created: id={result.get('id')}")
    print(f"preview URL: {url}")
    print(f"production URL (after promote): https://{subdomain}/")
    print("verify with: curl -sI " + (url or f"https://{subdomain}/"))


if __name__ == "__main__":
    main()
