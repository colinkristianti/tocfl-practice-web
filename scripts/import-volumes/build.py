"""Audited edition-specific conversion of supplied official volumes 2–5.

Original question artwork is rendered, not rewritten. Source PDFs stay in Drive.
Question headings are distinguished from example/preview headings by choices.
Shared reading contexts and audio passages are included in each affected item.
"""
import pathlib,json,re,sys,subprocess,hashlib
import pdfplumber,pypdfium2 as pdfium
from PIL import Image,ImageChops
from concurrent.futures import ThreadPoolExecutor
R=pathlib.Path(__file__).resolve().parent
INDEX=json.loads((R/'pdf-index.json').read_text())
ANS=json.loads((R/'answers.json').read_text())
MAN=json.loads((R/'manifest.json').read_text())
NUMBER=re.compile(r'^(\d{1,2})\.$')
ROMAN=re.compile(r'^[（(][一二三四五六七八九十]+[）)]$')
CHOICE=re.compile(r'^[（(]\s*[A-F]\s*[）)]$')
OFFICIAL='https://tocfl.edu.tw/tocfl/index.php/exam/test/page/1'
ROWS=[];AUDIT=[]

def kind(b,v,s,n):
 if s=='listening':
  if b=='B':return 'type_dialogue' if n<=(31 if v==4 else 30) else 'type_monologue'
  ends={2:[25,40,45],3:[10,25,40],4:[10,25,40],5:[10,28,40]}[v]
  return ['type_picture_answer','type_single_dialogue','type_multi_dialogue','type_dialogue'][sum(n>x for x in ends)]
 if b=='B':return 'type_cloze' if n<={2:15,3:18,4:17,5:18}[v] else 'type_passage'
 ends=[15,30,35 if v in [3,4] else 40,45]
 return ['type_sentence','type_picture_description','type_cloze','type_paragraph','type_passage'][sum(n>x for x in ends)]

def trim(im):
 im=im.convert('RGB');box=ImageChops.difference(im,Image.new('RGB',im.size,'white')).getbbox()
 assert box,'Blank crop'
 return im.crop((max(0,box[0]-12),max(0,box[1]-12),min(im.width,box[2]+12),min(im.height,box[3]+12)))
def compose(parts):
 parts=[trim(p) for p in parts];w=max(p.width for p in parts)
 im=Image.new('RGB',(w+24,sum(p.height for p in parts)+24*(len(parts)+1)),'white');y=24
 for p in parts:im.paste(p,(12,y));y+=p.height+24
 return im

for v in range(2,6):
 for b in ['A','B']:
  for s in ['listening','reading']:
   f=f'{s}_questions_{b}_vol_{v}.pdf';pages=INDEX[f];raw=R/'raw'/f
   source=next(m for m in MAN if m['name']==f);doc=pdfium.PdfDocument(str(raw));rendered={};maps={};candidates=[]
   for pi,p in enumerate(pages):
    if pi<3 or ('說明：' in p['text'][:220] and '例題' in p['text']):continue
    words=p['words']
    for w in words:
     m=NUMBER.fullmatch(w['text'])
     if not m or not 1<=int(m[1])<=50 or w['x0']>=350:continue
     # Actual item headings must be followed by choices before another item.
     nexttops=[q['top'] for q in words if NUMBER.fullmatch(q['text']) and q['top']>w['top']+5 and abs(q['x0']-w['x0'])<35]
     bottom=min(nexttops) if nexttops else p['height']-30
     nearby=[q for q in words if CHOICE.fullmatch(q['text']) and q['top']>=w['top']-3 and q['top']<bottom and q['x0']>=w['x0']-5 and q['x0']<w['x0']+190]
     # PDF extraction sometimes joins an option marker with its text.
     nearby += [q for q in words if re.match(r'^[（(]A[）)]',q['text']) and w['top']-3<=q['top']<bottom and w['x0']-5<=q['x0']<w['x0']+190]
     if s=='listening' and b=='A' and kind(b,v,s,int(m[1]))=='type_picture_answer':nearby=[w]
     if s=='reading' and b=='A' and 16<=int(m[1])<=30:nearby=[w]
     nearby += [q for q in words if re.match(r'^A[）)]',q['text']) and w['top']-3<=q['top']<bottom]
     if nearby:candidates.append((int(m[1]),pi,w))
   for n,pi,w in candidates:
    assert n not in maps,(f,'duplicate actual question',n,maps.get(n),pi)
    maps[n]=(pi,w)
   if (b,s)==('A','reading'):
    start=36 if v in [3,4] else 41
    pi=15 if v in [3,4] else 17
    for n in range(start,46):maps[n]=(pi,None)
   assert sorted(maps)==list(range(1,51)),(f,'missing',sorted(set(range(1,51))-set(maps)))
   def crop(pi,x0,y0,x1,y1):
    p=pages[pi];y0=max(0,y0);y1=min(p['height']-28,y1)
    assert y1>y0,(f,pi,x0,y0,x1,y1)
    if pi not in rendered:rendered[pi]=doc[pi].render(scale=2.2).to_pil().convert('RGB')
    im=rendered[pi];sx=im.width/p['width'];sy=im.height/p['height']
    return im.crop((int(x0*sx),int(y0*sy),int(x1*sx),int(y1*sy)))
   pairs=ANS[f'{s}_answer keys_{b}_vol_{v}.pdf'];assert len(pairs)==50
   for n in range(1,51):
    pi,w=maps[n];p=pages[pi];words=p['words'];k=kind(b,v,s,n);parts=[];boxes=[]
    pageq=sorted([(nn,ww) for nn,(pp,ww) in maps.items() if pp==pi and ww],key=lambda x:(x[1]['top'],x[1]['x0']))
    def add(pp,x0,y0,x1,y1):parts.append(crop(pp,x0,y0,x1,y1));boxes.append([pp+1,x0,y0,x1,y1])
    if k=='type_paragraph':
     if v in [3,4]:add(pi,40,45 if n<41 else 390,565,390 if n<41 else p['height']-28)
     else:add(pi,40,45,565,p['height']-28)
    elif s=='reading' and b=='B' and k=='type_cloze':
     first=min(ww['top'] for _,ww in pageq);add(pi,40,45,565,first-8)
     split=p['width']/2;x0=60 if w['x0']<split-10 else split-5;x1=split-5 if w['x0']<split-10 else 550
     later=[ww['top'] for _,ww in pageq if ww['top']>w['top']+5 and abs(ww['x0']-w['x0'])<35]
     add(pi,x0,w['top']-5,x1,min(later)-8 if later else p['height']-28)
    elif s=='reading' and (k in ['type_cloze','type_passage']):
     rom=[ww for ww in words if ROMAN.fullmatch(ww['text']) and ww['top']<w['top']]
     # A section with two passages on a page resets its context at the Roman label.
     section=max((ww['top'] for ww in rom),default=45)
     group=[ww for _,ww in pageq if ww['top']>=section-2];first=min(ww['top'] for ww in group)
     if first-section>35:add(pi,40,section-5,565,first-8)
     elif pi>3:
      prev=pages[pi-1]
      assert not any(pp==pi-1 for pp,ww in maps.values()) or b=='A',(f,n,'shared context needs manual review')
      add(pi-1,40,45,565,p['height']-28)
     later=[ww['top'] for _,ww in pageq if ww['top']>w['top']+5]
     later += [ww['top'] for ww in words if ROMAN.fullmatch(ww['text']) and ww['top']>w['top']+5]
     add(pi,40,w['top']-5,565,min(later)-8 if later else p['height']-28)
    else:
     later=[ww['top'] for _,ww in pageq if ww['top']>w['top']+5]
     # Do not append a later listening preview to the final actual item on a page.
     later += [ww['top'] for ww in words if (ww['text'].startswith('下面是') or ww['text'].startswith('請聽')) and ww['top']>w['top']+8]
     add(pi,40,w['top']-6,565,min(later)-8 if later else p['height']-28)
    im=compose(parts);dest=R/'assets'/f'vol{v}';dest.mkdir(parents=True,exist_ok=True);name=f'{b}-v{v}-{s}-{n:03d}.webp'
    im.save(dest/name,'WEBP',quality=92,method=6)
    count=6 if k=='type_paragraph' else 3 if b=='A' and k not in ['type_dialogue','type_passage'] else 4
    printed,answer=pairs[n-1];answer=ord(answer)-65;assert 0<=answer<count,(f,n,answer,count)
    assert int(printed)==n or (s,b,n,v) in [('listening','A',34,2),('listening','A',34,3),('listening','A',34,4)]
    base=f'https://colinkristianti.github.io/tocfl-practice-web/assets/official/vol{v}/'
    ROWS.append([f'official-{b}-{v}-{s}-{n:03d}',b,v,s,n,k,'','',json.dumps(['']*count),answer,base+f'{b}-v{v}-audio-{n:03d}.mp3' if s=='listening' else '',source['official_url'],False,base+name,'','','待撰寫'])
    AUDIT.append({'id':ROWS[-1][0],'source_pdf':f,'drive_url':source.get('drive_url',source['official_url']),'source_sha256':source['sha256'],'answer':chr(answer+65),'printed_answer_number':int(printed),'type':k,'pdf_regions':boxes,'image':name,'image_sha256':hashlib.sha256((dest/name).read_bytes()).hexdigest(),'image_size':list(im.size)})
   print('Verified',b,v,s,len(maps),flush=True)
   doc.close()
(R/'questions.json').write_text(json.dumps({'headers':['question_id','band','volume','skill','number','type','passage','prompt','options_json','answer_index','audio_url','source_url','is_demo','image_url','explanation_zh','explanation_th','explanation_status'],'rows':ROWS},ensure_ascii=False,indent=2))
(R/'audit.json').write_text(json.dumps(AUDIT,ensure_ascii=False,indent=2))
print('Verified 800 questions and answer mappings.')
