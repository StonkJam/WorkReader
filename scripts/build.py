#!/usr/bin/env python3
"""Make the portable HTML, embedding the latest public snapshot and capture code."""
import json
from urllib.parse import quote
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def safe_json(value):
    return json.dumps(value,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
def main():
    template=(ROOT/'reader.template.html').read_text()
    logo=(ROOT/'assets/outlook.svg').read_text()
    favicon='data:image/svg+xml,'+quote(logo,safe='')
    template=template.replace('__OUTLOOK_LOGO_HEADER__',logo.replace('outlook-tile','outlook-tile-header')).replace('__OUTLOOK_LOGO_RAIL__',logo.replace('outlook-tile','outlook-tile-rail')).replace('__OUTLOOK_FAVICON__',favicon)
    snapshot=json.loads((ROOT/'data/deals.json').read_text())
    cfg=json.loads((ROOT/'config.json').read_text())
    template=template.replace('__OUTLOOK_STYLE__',(ROOT/'styles/outlook.css').read_text()).replace('__RAINDROP_CLIENT__',(ROOT/'scripts/raindrop-client.js').read_text()).replace('__COVER_CLIENT__',(ROOT/'scripts/cover-view.js').read_text())
    for marker,name in [('__SNAPSHOT_CLIENT__','snapshot-client.js'),('__MESSAGE_ACTIONS__','message-actions.js'),('__JETSTAR_FORMAT__','jetstar-format.js'),('__UI_SCALE__','ui-scale.js'),('__SOURCES_CLIENT__','source-settings.js'),('__VIDEO_CLIENT__','video-client.js')]:
        template=template.replace(marker,(ROOT/'scripts'/name).read_text())
    template=template.replace('__SOURCE_CATEGORIES__',safe_json(json.loads((ROOT/'assets/source-categories.json').read_text())))
    result=template.replace('__SNAPSHOT__',safe_json(snapshot)).replace('__CONFIG__',safe_json(cfg)).replace('__EXTRACTOR__',safe_json((ROOT/'scripts/extract-page.js').read_text()))
    (ROOT/'WorkReader.html').write_text(result)
    (ROOT/'index.html').write_text(result)
    print('Built WorkReader.html and index.html')
if __name__=='__main__':main()
