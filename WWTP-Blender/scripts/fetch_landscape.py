"""Fetch public CC0 assets from the official Poly Haven API, retaining originals."""
import concurrent.futures, hashlib, json, shutil, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def get(url):
    with urllib.request.urlopen(url,timeout=90) as r: return r.read()
def asset(aid):
    raw=ROOT/'assets/raw_downloads'/aid; raw.mkdir(parents=True,exist_ok=True)
    meta=json.loads(get('https://api.polyhaven.com/info/'+aid))
    files=json.loads(get('https://api.polyhaven.com/files/'+aid))
    (raw/'metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
    item=files['gltf']['1k']['gltf']; tasks=[(aid+'_1k.gltf',item)]+list(item['include'].items())
    def dl(t):
        name,entry=t; path=raw/name; path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists() or hashlib.md5(path.read_bytes()).hexdigest()!=entry['md5']:
            payload=get(entry['url'])
            assert hashlib.md5(payload).hexdigest()==entry['md5'],name
            path.write_bytes(payload)
        used=ROOT/'assets/vegetation'/aid/name; used.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,used)
        return name
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: print(aid,list(pool.map(dl,tasks)),flush=True)
    print('METADATA',aid,meta.get('authors'),flush=True)
if __name__=='__main__':
    for aid in ('jacaranda_tree','shrub_03'): asset(aid)
