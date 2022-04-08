#!/usr/bin/env python3

# Messy build script to compile the templates.
# Unreadable, but that's just how hastily slapped together python be.

import os
import jinja2
import yaml
import urllib.request, json
import subprocess

# Load input data & jinja
env = jinja2.Environment(loader=jinja2.FileSystemLoader('./templates'))
with open('data.yml') as f:
    data = yaml.safe_load(f)

# Get repositories
with urllib.request.urlopen('https://git.angm.xyz/api/v1/repos/search?uid=1') as url:
    data['git'] = json.loads(url.read().decode())['data']
with urllib.request.urlopen('https://git.angm.xyz/api/v1/repos/search?uid=8') as url:
    data['git'] += json.loads(url.read().decode())['data']

# Populate repo data
data['sloc'] = {}
data['sloc_pct'] = {}
data['total_sloc'] = 0
for repo in data['git']:
    with subprocess.Popen(["git", "clone", repo["clone_url"]], cwd="repos") as proc:
        pass
    with subprocess.Popen(["scc", "-f", "json"], cwd="repos/" + repo["name"], stdout=subprocess.PIPE) as proc:
        lang_list = json.loads(proc.stdout.read().decode("utf-8"))
    with subprocess.Popen(["du", "-sh"], cwd="repos/" + repo["name"], stdout=subprocess.PIPE) as proc:
        repo['size'] = proc.stdout.read().decode("utf-8").split('\t', 1)[0]

    langs = {}
    total = 0
    for dic in lang_list:
        lang = dic["Name"]
        if lang in data['ignored_langs']:
            continue
        if lang in data['is_shell']:
            lang = "Shell"

        if lang not in langs:
            langs[lang] = 0
        langs[lang] += dic["Lines"]
        if lang not in data['sloc']:
            data['sloc'][lang] = 0
        data['sloc'][lang] += langs[lang]

        total += langs[lang]

    data['total_sloc'] += total
    repo['total_src'] = total
    repo['langs'] = dict(sorted(langs.items(), reverse=True, key=lambda item: item[1]))
    for lang in repo['langs']:
        repo['langs'][lang] /= total
        repo['langs'][lang] = round(repo['langs'][lang] * 100, 1)

for entry in data['sloc']:
    data['sloc_pct'][entry] = round(data['sloc'][entry] / data['total_sloc'] * 100, 1)

data['git'].sort(reverse=True, key=lambda repo: repo['total_src'])
data['sloc'] = dict(sorted(data['sloc'].items(), reverse=True, key=lambda l: l[1]))

# Get template with given name
def tem(name):
    return env.get_template(f'{name}.html')

# Write a rendered template to the given path.
def write(dat, location):
    with open(f'{location}.html', 'w') as f:
        f.write(dat)

write(tem('index').render(data=data), 'index')
write(tem('projects').render(data=data), 'projects')
write(tem('services').render(data=data), 'services')
write(tem('stats').render(data=data), 'stats')
