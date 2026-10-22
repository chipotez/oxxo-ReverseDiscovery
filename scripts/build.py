"""Dependency-free static compilation. All editorial values are HTML-escaped."""
from pathlib import Path
from html import escape
import json
import shutil
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist'

def text(value):
    return escape(str(value), quote=True)

def icon(name):
    if not re.fullmatch(r'[a-z0-9-]+', name):
        raise ValueError('Invalid icon name')
    svg = (ROOT / 'src/assets/icons' / (name + '.svg')).read_text()
    svg = svg.replace('stroke-width="2"', 'stroke-width="1.75"')
    return svg.replace('<svg ', '<svg aria-hidden="true" focusable="false" ', 1)

def link(label, target, cls=''):
    return f'<a class="{text(cls)}" href="#{text(target)}">{text(label)}</a>'

def card(item, kind):
    topics = ''.join(f'<li>{text(topic)}</li>' for topic in item['topics'])
    return f'''<article class="competency-card">
      <div class="card-top"><span class="icon-tile">{icon(item['icon'])}</span><span class="level">{text(item['level'])}</span></div>
      <p class="card-kind">{text(kind)}</p><h3>{text(item['title'])}</h3><p>{text(item['description'])}</p>
      <details><summary>Ver enfoque {icon('arrow-up-right')}</summary><div class="detail-body"><p>Aspectos que explora esta competencia:</p><ul>{topics}</ul></div></details>
    </article>'''

def catalog(groups):
    tabs = ''.join(f'<button type="button" id="tab-{text(g["id"])}" data-tab="{text(g["id"])}" aria-controls="panel-{text(g["id"])}">{text(g["label"])}</button>' for g in groups)
    panels = ''.join(f'<section id="panel-{text(g["id"])}" class="catalog-panel" aria-labelledby="tab-{text(g["id"])}"><h3 class="panel-heading">{text(g["label"])}</h3><div class="card-grid">'+''.join(card(item,g['kind']) for item in g['items'])+'</div></section>' for g in groups)
    return f'<div class="tabs" aria-label="Tipos de competencias">{tabs}</div>{panels}'

def build():
    data = json.loads((ROOT / 'src/content/es.json').read_text())
    assert len({g['id'] for g in data['catalog']}) == len(data['catalog'])
    replacements = {
        'NAVIGATION': ''.join(link(label, target) for label,target in data['navigation']),
        'CATALOG': catalog(data['catalog']),
        'TECHNOLOGIES': ''.join(f'<li class="technology"><span class="tech-icon">{icon(i)}</span><div><h3>{text(n)}</h3><p>{text(d)}</p></div></li>' for n,i,d in data['technologies']),
    }
    template = (ROOT / 'src/index.html').read_text()
    for name,value in replacements.items():
        template = template.replace('{{'+name+'}}', value)
    template = re.sub(r'\{\{icon:([a-z0-9-]+)\}\}', lambda m: icon(m.group(1)), template)
    if '{{' in template:
        raise ValueError('Unresolved template expression')
    OUT.mkdir(exist_ok=True)
    (OUT/'index.html').write_text(template)
    shutil.copytree(ROOT/'src/assets', OUT/'assets', dirs_exist_ok=True)
    shutil.copyfile(ROOT/'docs/tabler-LICENSE.txt', OUT/'assets/tabler-LICENSE.txt')
    (OUT/'healthz').write_text('ok\n')
    print('Built dist/index.html and local assets')

if __name__ == '__main__':
    build()
