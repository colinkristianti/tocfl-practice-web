"""Rebuild public learning assets in GitHub from checksum-verified official sources.

No access to Google Sheets, student records, credentials, or private Drive needed.
"""
import pathlib,json,hashlib,urllib.request,re,subprocess
from concurrent.futures import ThreadPoolExecutor
R=pathlib.Path(__file__).resolve().parent
manifest=json.loads((R/'manifest.json').read_text())
(R/'raw').mkdir(exist_ok=True)
def fetch(f):
 p=R/'raw'/f['name']
 if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256']:return
 req=urllib.request.Request(f['official_url'],headers={'User-Agent':'XinYa-TOCFL-source-verification/1.0'})
 with urllib.request.urlopen(req,timeout=180) as response,open(p.with_suffix(p.suffix+'.part'),'wb') as out:
  while data:=response.read(1024*1024):out.write(data)
 temp=p.with_suffix(p.suffix+'.part')
 assert temp.stat().st_size==f['size'],(f['name'],'source size mismatch')
 assert hashlib.sha256(temp.read_bytes()).hexdigest()==f['sha256'],(f['name'],'source edition changed')
 temp.replace(p)
 print('Verified official source:',f['name'],flush=True)
with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(fetch,manifest))
import pdfplumber
index={};answers={}
for p in sorted((R/'raw').glob('*.pdf')):
 with pdfplumber.open(p) as doc:
  if '_questions_' in p.name:
   pages=[]
   for i,page in enumerate(doc.pages):
    words=page.extract_words();pages.append({'page':i+1,'numbers':[w['text'] for w in words if re.fullmatch(r'\d{1,2}\.',w['text']) and w['x0']<350],'text':page.extract_text() or '', 'words':words,'width':page.width,'height':page.height})
   index[p.name]=pages
  elif 'answer keys' in p.name:
   pairs=re.findall(r'\b(\d{1,2})\s+([A-F])\b','\n'.join(p.extract_text() or '' for p in doc.pages))
   assert len(pairs)==50,(p.name,'answer count');answers[p.name]=pairs
(R/'pdf-index.json').write_text(json.dumps(index,ensure_ascii=False))
(R/'answers.json').write_text(json.dumps(answers))
for p in sorted((R/'raw').glob('*.rar')):
 dest=R/'audio'/p.stem;dest.mkdir(parents=True,exist_ok=True)
 # Old RARs contain incorrectly encoded instruction filenames. Scored tracks
 # use ASCII filenames and are asserted in build-audio.py; ignore those extras.
 subprocess.run(['bsdtar','-xf',str(p),'-C',str(dest)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run(['python3',str(R/'build.py')],check=True)
subprocess.run(['python3',str(R/'build-audio.py')],check=True)
images=sorted((R/'assets').rglob('*.webp'));clips=sorted((R/'assets').rglob('*.mp3'))
assert len(images)==800 and len(clips)==400,(len(images),len(clips))
asset_manifest={'questions':800,'audio_clips':400,'source_files':[{k:f[k] for k in ['name','official_url','sha256','size']} for f in manifest],'assets':[{'path':'assets/official/'+str(p.relative_to(R/'assets')),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in images+clips]}
(R/'assets'/'volumes2-5-manifest.json').write_text(json.dumps(asset_manifest,ensure_ascii=False,indent=2))
print('PASS: 48 exact official sources, 800 rendered items, 400 decoded audio clips.')
