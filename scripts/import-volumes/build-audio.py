"""Source-track mapping: archive filenames + official scripts, not question number alone."""
import pathlib,sys,re,json,subprocess,hashlib
from concurrent.futures import ThreadPoolExecutor
R=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent/'deps'));import imageio_ffmpeg
FF=imageio_ffmpeg.get_ffmpeg_exe()
JOBS=[];AUDIT=[]
for v in range(2,6):
 for b in ['A','B']:
  files={p.name:p for p in (R/'audio'/f'listening_audio_{b}_vol_{v}').rglob('*.mp3')}
  mapping={}
  if b=='A':
   for name,p in files.items():
    m=re.fullmatch(r'[1-4]-(\d{2})\.mp3',name)
    if m:mapping[int(m[1])]=[p]
  elif v==2:
   starts=sorted(int(re.fullmatch(r'[12]-(\d{2})-0\.mp3',f)[1]) for f in files if re.fullmatch(r'[12]-\d{2}-0\.mp3',f))
   for n in range(1,51):
    s=1 if n<=30 else 2
    group=max((g for g in starts if g<=n and (g<=30)==(n<=30)),default=None)
    mapping[n]=[files[f'{s}-{group:02d}-0.mp3'],files[f'{s}-{n:02d}{"-1" if group==n else ""}.mp3']] if group else [files[f'{s}-{n:02d}.mp3']]
  else:
   # (first question, last question, shared track, first question track).
   if v==3:
    single={**{n:f'1-{n:02d}.mp3' for n in range(1,20)},31:'2-36.mp3',32:'2-37.mp3'}
    groups=[(20,21,20,21),(22,23,23,24),(24,25,26,27),(26,27,29,30),(28,30,32,33),(33,34,38,39),(35,36,41,42),(37,38,44,45),(39,40,47,48),(41,42,50,51),(43,44,53,54),(45,47,56,57),(48,50,60,61)]
    fmt=lambda t:'1-' if t<=35 else '2-'
    fn=lambda t:f'{fmt(t)}{t:02d}.mp3'
   elif v==4:
    single={**{n:f'{n+2:03d}.mp3' for n in range(1,18)},**{n:f'{n+9:03d}.mp3' for n in range(32,36)}}
    groups=[(18,19,20,21),(20,21,23,24),(22,23,26,27),(24,25,29,30),(26,28,32,33),(29,31,36,37),(36,37,45,46),(38,39,48,49),(40,41,51,52),(42,43,54,55),(44,45,57,58),(46,47,60,61),(48,50,63,64)]
    fn=lambda t:f'{t:03d}.mp3'
   else:
    single={n:f'{n+2:03d}.mp3' for n in range(1,14)}
    groups=[(14,15,16,17),(16,17,19,20),(18,19,22,23),(20,21,25,26),(22,23,28,29),(24,25,31,32),(26,27,34,35),(28,30,37,38),(31,32,42,43),(33,34,45,46),(35,36,48,49),(37,38,51,52),(39,40,54,55),(41,42,57,58),(43,44,60,61),(45,47,63,64),(48,50,67,68)]
    fn=lambda t:f'{t:03d}.mp3'
   for n,name in single.items():mapping[n]=[files[name]]
   for first,last,shared,q in groups:
    for n in range(first,last+1):mapping[n]=[files[fn(shared)],files[fn(q+n-first)]]
  assert sorted(mapping)==list(range(1,51)),(b,v,sorted(mapping))
  for n,sources in mapping.items():JOBS.append((b,v,n,sources))
def convert(job):
 b,v,n,sources=job;dest=R/'assets'/f'vol{v}'/f'{b}-v{v}-audio-{n:03d}.mp3';dest.parent.mkdir(parents=True,exist_ok=True)
 args=[FF,'-v','error','-y']
 for f in sources:args+=['-i',str(f)]
 if len(sources)>1:args+=['-filter_complex','[0:a][1:a]concat=n=2:v=0:a=1[out]','-map','[out]']
 args+=['-ac','1','-ar','44100','-codec:a','libmp3lame','-b:a','64k',str(dest)]
 subprocess.run(args,check=True)
 subprocess.run([FF,'-v','error','-i',str(dest),'-f','null','-'],check=True,stdout=subprocess.DEVNULL)
 assert dest.stat().st_size>1000
 return {'id':f'official-{b}-{v}-listening-{n:03d}','file':f'vol{v}/{dest.name}','sources':[str(f.relative_to(R)) for f in sources],'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bytes':dest.stat().st_size}
with ThreadPoolExecutor(max_workers=4) as pool:
 for i,result in enumerate(pool.map(convert,JOBS),1):
  AUDIT.append(result)
  if i%50==0:print('Decoded and validated',i,'clips',flush=True)
(R/'audio-audit.json').write_text(json.dumps(AUDIT,ensure_ascii=False,indent=2))
print('All 400 clips playable; bytes:',sum(a['bytes'] for a in AUDIT))
