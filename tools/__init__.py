# coding=utf-8
import os
import shutil

PATHS = [
    os.path.join(os.path.dirname(os.__file__), "../../etc/splitter/"),
    "/usr/local/etc/splitter/",
    "/usr/etc/splitter/",
    "/etc/splitter/",
]

for path in PATHS:
    if os.path.exists(path):
        EP_SPLITTER_PATH = path
        break

CACHE_PATH = os.path.join(EP_SPLITTER_PATH, "cache")
REPO_PATH = os.path.join(EP_SPLITTER_PATH, "repo")
SDF_DIR_PREFIX = os.path.join(EP_SPLITTER_PATH, "data")
SDF_DIR_FORMAT = "{}/{}/slices"

if os.path.exists(CACHE_PATH):
    shutil.rmtree(CACHE_PATH)

if os.path.exists(REPO_PATH):
    shutil.rmtree(REPO_PATH)