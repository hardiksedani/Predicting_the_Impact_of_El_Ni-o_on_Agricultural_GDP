from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from copy import deepcopy as cp
from lxml import etree as E
from PIL import Image
import json,re,html,unicodedata,hashlib

D=Path(__file__).parent
ROOT=D.parent
SRC=Path('D:/Downloads/ieee_paper.docx')
OUT=ROOT/'Machine_Learning_Assessment_IEEE_Full_Report.docx'
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M='http://schemas.openxmlformats.org/officeDocument/2006/math'
NS={'w':W,'m':M,'wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing','a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def q(t):return '{'+W+'}'+t
def setp(e,t,attrs):
 v=e.find(q(t))
 if v is None:v=E.SubElement(e,q(t))
 for k,val in attrs.items():v.set(q(k),str(val))
 return v
def flatindent(pp):
 e=pp.find(q('ind'))
 if e is not None:pp.remove(e)
 setp(pp,'ind',{'left':0,'right':0,'firstLine':0})

with ZipFile(SRC) as z:parts={n:z.read(n) for n in z.namelist()}
root=E.fromstring(parts['word/document.xml']);body=root.find(q('body'))
ps=list(body.findall(q('p')));ts=list(body.findall(q('tbl')))
sections=[cp(x) for x in root.findall('.//w:sectPr',NS)]
for c in list(body):body.remove(c)
sources=json.loads((D/'verified_references.json').read_text(encoding='utf-8'))
order=[]
def cites(t):
 def f(m):
  keys=m.group(1).split(',');nums=[]
  for k in keys:
   assert k in sources,k
   if k not in order:order.append(k)
   nums.append(order.index(k)+1)
  return ', '.join(f'[{i}]' for i in nums)
 return re.sub(r'\{([a-z0-9,]+)\}',f,t)

def para(i,text,keep=None):
 p=cp(ps[i]);p.attrib.clear()
 pp=p.find(q('pPr'));rp=p.find('w:r/w:rPr',NS)
 if rp is None:rp=pp.find(q('rPr')) if pp is not None else None
 rp=cp(rp) if rp is not None else E.Element(q('rPr'))
 for ch in list(p):
  if ch.tag!=q('pPr'):p.remove(ch)
 if pp is None:pp=E.SubElement(p,q('pPr'))
 for s in pp.findall(q('sectPr')):pp.remove(s)
 if keep is not None:setp(pp,'keepNext',{'val':int(keep)})
 for j,part in enumerate(text.split('\n')):
  r=E.SubElement(p,q('r'));r.append(cp(rp))
  if j:E.SubElement(r,q('br'))
  t=E.SubElement(r,q('t'));t.set('{http://www.w3.org/XML/1998/namespace}space','preserve');t.text=part
 return p
def put(i,t,keep=None):
 p=para(i,cites(t),keep);body.append(p);return p

def authors(i,name,email):
 p=para(i,'');pp=p.find(q('pPr'))
 for r in p.findall(q('r')):p.remove(r)
 if i==4:
  rr=E.SubElement(p,q('r'));E.SubElement(rr,q('br')).set(q('type'),'column')
 lines=[name,'Dept. of Artificial Intelligence and Data Science','K. J. Somaiya Institute of Technology','Mumbai, India',email] if name else ['']
 for j,t in enumerate(lines):
  r=E.SubElement(p,q('r'));rp=E.SubElement(r,q('rPr'));setp(rp,'rFonts',{'ascii':'Times New Roman','hAnsi':'Times New Roman'});setp(rp,'sz',{'val':22});setp(rp,'i',{'val':int(j in [1,2])})
  if j:E.SubElement(r,q('br'))
  E.SubElement(r,q('t')).text=t
 return p

def table(n,caption,headers,rows,widths):
 cap=para(78,f'TABLE {n}\n{caption.upper()}',True)
 pp=cap.find(q('pPr'))
 for v in pp.findall(q('numPr')):pp.remove(v)
 setp(pp,'ind',{'left':0,'right':0,'firstLine':0});setp(pp,'jc',{'val':'center'})
 body.append(cap)
 proto=ts[0];tb=E.Element(q('tbl'));tb.append(cp(proto.find(q('tblPr'))))
 setp(tb.find(q('tblPr')),'tblW',{'w':4866,'type':'dxa'})
 grid=E.SubElement(tb,q('tblGrid'))
 for w in widths:E.SubElement(grid,q('gridCol')).set(q('w'),str(w))
 rr=proto.findall(q('tr'));cells=[rr[0].find(q('tc')),rr[1].find(q('tc'))]
 for i,row in enumerate([headers]+rows):
  tr=E.SubElement(tb,q('tr'));trpr=E.SubElement(tr,q('trPr'));setp(trpr,'cantSplit',{'val':1})
  if i==0:setp(trpr,'tblHeader',{'val':1})
  for j,txt in enumerate(row):
   tc=E.SubElement(tr,q('tc'));pr=cp(cells[int(i>0)].find(q('tcPr')));tc.append(pr);setp(pr,'tcW',{'w':widths[j],'type':'dxa'})
   for v in pr.findall(q('gridSpan')):pr.remove(v)
   pp0=cells[int(i>0)].find(q('p'))
   p=cp(pp0);p.attrib.clear()
   for v in list(p):
    if v.tag!=q('pPr'):p.remove(v)
   pp=p.find(q('pPr'));setp(pp,'keepNext',{'val':int(i<len(rows))});setp(pp,'keepLines',{'val':1})
   setp(pp,'jc',{'val':'left' if j==0 else 'center'})
   rp=cp(pp0.find('w:r/w:rPr',NS))
   r=E.SubElement(p,q('r'));r.append(rp);t=E.SubElement(r,q('t'));t.text=str(txt);tc.append(p)
  tb.append(tr)
 body.append(tb)

T={
1:('I','Variables and source alignment',['Variable','Source and construction','Unit'],[
 ['Rainfall','IMD daily 0.25° grid; FY sum','mm'],['Temperature','IMD daily 1° grid; FY mean','°C'],['ONI','NOAA; 10 complete seasons per FY','°C'],['Crop GSVA','RBI/NSO Table 30; 2011–12 prices','INR crore'],['State','28 one-hot indicators','Binary']], [1020,3000,846]),
2:('II','Saved model configurations',['Model','Principal settings'],[
 ['OLS','Intercept; 31 input columns'],['Random Forest','150 trees; depth 10; split 3; leaf 2; bootstrap'],['Extra Trees','150 trees; depth 10; split 3; leaf 2; no bootstrap'],['Gradient Boosting','150 stages; depth 4; rate 0.08; subsample 0.85'],['XGBoost','150 trees; depth 4; rate 0.08; row/column sampling 0.85']], [1350,3516]),
3:('III','Model errors on 105 held-out rows',['Model','MAE¹','RMSE¹','R²','MAPE %'],[
 ['OLS','10,049.97','17,410.41','0.8783','33.51'],['Random Forest','12,556.09','21,343.40','0.8172','60.82'],['Gradient Boosting','11,023.36','18,086.89','0.8687','62.83'],['XGBoost','11,267.99','18,752.05','0.8589','70.74'],['Extra Trees','12,105.21','18,388.83','0.8643','71.66']], [1370,970,970,756,800]),
4:('IV','Training-only historical benchmarks',['Predictor','MAE¹','RMSE¹','R²'],[
 ['State mean','9,911.99','17,552.79','0.8763'],['Last value','5,343.19','10,890.73','0.9524'],['OLS comparison','10,049.97','17,410.41','0.8783']], [1656,1070,1070,1070]),
5:('V','Annual held-out performance of OLS',['FY','n','MAE¹','RMSE¹','R²'],[
 ['2021–22','28','7,034.36','13,072.53','0.9237'],['2022–23','28','9,439.80','15,284.48','0.9022'],['2023–24','27','10,863.91','17,953.27','0.8686'],['2024–25','22','13,665.68','23,158.59','0.8130']], [1070,400,1150,1150,1096]),
6:('VI','Linear-model climate permutation diagnostic',['Permuted input','Mean ΔRMSE¹','Procedure'],[
 ['Rainfall','+2.07','Within state'],['Temperature','+14.52','Within state'],['ONI','−13.50','Shared test year']], [1550,1316,2000])}
figcaps={1:'Data preparation, chronological evaluation, and application workflow.',2:'Complete observations by financial year. The final four years form the holdout.',3:'RMSE comparison including training-only baselines. Last value denotes fixed persistence from FY 2020–21.',4:'Observed and predicted crop GSVA for the linear model. The diagonal represents exact prediction.',5:'Annual RMSE for OLS and fixed persistence on the same available observations.',6:'Mean change in linear-model RMSE after separate climate permutations. Small magnitudes limit substantive interpretation.'}
figprotos={1:33,2:81,3:84,4:91,5:97,6:108}
rels=E.fromstring(parts['word/_rels/document.xml.rels'])
relmap={r.get('Id'):r.get('Target') for r in rels}
changedmedia=[]
def figure(n):
 p=cp(ps[figprotos[n]]);p.attrib.clear();pp=p.find(q('pPr'));setp(pp,'keepNext',{'val':1});setp(pp,'keepLines',{'val':1})
 setp(pp,'ind',{'left':0,'right':0,'firstLine':0});setp(pp,'jc',{'val':'center'})
 # Drop cached page-position markers, retain the source inline drawing.
 for e in p.findall('.//w:lastRenderedPageBreak',NS):e.getparent().remove(e)
 im=D/f'fig{n}.png';iw,ih=Image.open(im).size;cx=3017520;cy=round(cx*ih/iw)
 for e in p.findall('.//wp:extent',NS)+p.findall('.//a:xfrm/a:ext',NS):e.set('cx',str(cx));e.set('cy',str(cy))
 for e in p.findall('.//wp:docPr',NS):e.set('descr',figcaps[n]);e.set('name',f'Figure {n}');e.set('id',str(n))
 rid=p.find('.//a:blip',NS).get('{'+NS['r']+'}embed');target='word/'+relmap[rid];parts[target]=im.read_bytes();changedmedia.append(target)
 body.append(p);cap=para(34,f'Fig. {n}. {figcaps[n]}',False)
 for e in cap.findall('w:pPr/w:numPr',NS):e.getparent().remove(e)
 flatindent(cap.find(q('pPr')));body.append(cap)

eqtexts={1:'Rₛᵧ = Σ Pₛd ,   Tₛᵧ = (1 / |D|) Σ (Tmaxₛd + Tminₛd) / 2',2:'ŷₛᵧ = αₛ + βR Rₛᵧ + βT Tₛᵧ + βO ONIᵧ',3:'ŷmeanₛᵧ = μₛ ,              ŷlastₛᵧ = yₛ,₂₀₂₀',4:'MAE = Σ |yᵢ − ŷᵢ| / n ;   RMSE = √[Σ (yᵢ − ŷᵢ)² / n]',5:'ΔRMSEⱼ = meanᵦ[RMSE(y, f(Xpermⱼᵦ))] − RMSE(y, f(X))',6:'Δŷ = f(x*) − f(x) ,       Δ% = 100 Δŷ / f(x)'}
def equation(n):
 p=para(37,'');pp=p.find(q('pPr'))
 for e in list(p):
  if e.tag!=q('pPr'):p.remove(e)
 for e in pp.findall(q('numPr')):pp.remove(e)
 setp(pp,'ind',{'left':0,'right':0,'firstLine':0});setp(pp,'jc',{'val':'center'});setp(pp,'spacing',{'before':50,'after':90,'line':240,'lineRule':'auto'});setp(pp,'keepNext',{'val':0})
 # Editable native Office Math, sized to the template's equation style.
 om=E.SubElement(p,'{'+M+'}oMath');r=E.SubElement(om,'{'+M+'}r');rp=E.SubElement(r,q('rPr'));setp(rp,'rFonts',{'ascii':'Cambria Math','hAnsi':'Cambria Math'});setp(rp,'sz',{'val':16});E.SubElement(r,'{'+M+'}t').text=eqtexts[n]+f'    ({n})'
 body.append(p)

lines=(D/'paper.txt').read_text(encoding='utf-8').splitlines()
for line in lines:
 if not line.strip():continue
 if line.startswith('@title '):
  put(0,line[7:]);br=para(1,'');br.find(q('pPr')).append(cp(sections[0]));body.append(br)
  for i,name,email in [(2,'Prof. Pankaj Deshmukh','pankaj@somaiya.edu'),(3,'Altair Patel','altair.patel@somaiya.edu'),(4,'Hardik Sedani','hardik.sedani@somaiya.edu'),(5,'','')]:
   p=authors(i,name,email)
   if i==5:p.find(q('pPr')).append(cp(sections[1]))
   body.append(p)
 elif line.startswith('@abstract '):put(6,line[10:])
 elif line.startswith('@keywords '):put(7,line[10:])
 elif line.startswith('## '):put(35,line[3:],True)
 elif line.startswith('# '):put(8,line[2:],True)
 elif line.startswith('@ack '):put(117,line[5:],True)
 elif line.startswith('@fig'):figure(int(line[4:]))
 elif line.startswith('@table'):
  n=int(line[6:]);table(*T[n])
  if n in [3,4,5,6]:
   p=para(34,'¹ Monetary errors are in INR crore.' if n!=6 else '¹ INR crore; 20 repeats; baseline RMSE = 17,410.41.',False)
   for e in p.findall('w:pPr/w:numPr',NS):e.getparent().remove(e)
   flatindent(p.find(q('pPr')));body.append(p)
 elif line.startswith('@eq'):equation(int(line[3:]))
 else:put(9,line)

assert len(order)==48,(len(order),set(sources)-set(order))
put(119,'References',True)
def clean(s):return unicodedata.normalize('NFC',html.unescape(re.sub('<[^>]+>','',s))).replace('\r',' ').replace('\n',' ').strip().rstrip('.*')
def author(a):
 if 'family' not in a:return a.get('name','')
 given=a.get('given','');ini=' '.join(x[0]+'.' for x in re.findall(r'[^\W\d_]+',given,re.UNICODE))
 return (ini+' '+a['family']).strip()
bib=[]
for key in order:
 v=sources[key];aa=[author(a) for a in (v.get('author') or [])]
 au=', '.join(aa[:-1])+', and '+aa[-1] if 2<len(aa)<=6 else ' and '.join(aa) if len(aa)<=2 else aa[0]+' et al.'
 if not au:au='OECD and European Commission'
 title=clean(v['title'][0]);journal=clean((v.get('container-title') or [''])[0]);year=v['published']['date-parts'][0][0]
 if key=='chakraborty2016':year=2016
 if key=='rice2012':year=2012
 if key=='xgb2016':title='XGBoost: A scalable tree boosting system'
 text=f'{au}, “{title},” '
 if True:
  text+=journal
  if v.get('volume'):text+=f', vol. {v["volume"]}'
  if v.get('issue'):text+=f', no. {v["issue"]}'
  if v.get('page'):
   label='Art. no.' if re.fullmatch(r'\d{5,}',v['page']) else 'pp.'
   text+=f', {label} {v["page"].replace("-","–")}'
  elif v.get('article-number') and key!='ashok2007':text+=f', Art. no. {v["article-number"]}'
  text+=f', {year}, doi: {v["DOI"]}.'
 bib.append(text);p=put(120,text,False);setp(p.find(q('pPr')),'keepLines',{'val':1})
last=body[-1];last.find(q('pPr')).append(cp(sections[2]));body.append(cp(sections[3]))

# Unique paragraph IDs are not carried over from cloned template components.
for p in root.findall('.//w:p',NS):
 for a in list(p.attrib):
  if a.endswith('paraId') or a.endswith('textId'):del p.attrib[a]
parts['word/document.xml']=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
core=E.fromstring(parts['docProps/core.xml'])
for tag,value in [('title',lines[0][7:]),('creator','Pankaj Deshmukh; Altair Patel; Hardik Sedani')]:
 e=core.find('{http://purl.org/dc/elements/1.1/}'+tag)
 if e is not None:e.text=value
parts['docProps/core.xml']=E.tostring(core,xml_declaration=True,encoding='UTF-8',standalone=True)
with ZipFile(OUT,'w',ZIP_DEFLATED) as z:
 for n,b in parts.items():z.writestr(n,b)
with ZipFile(SRC) as z:
 changed=[n for n in z.namelist() if z.read(n)!=parts[n]]
allowed=['word/document.xml','docProps/core.xml']+changedmedia
assert set(changed)<=set(allowed),changed
def structure(e):return (e.tag,dict(e.attrib),e.text.strip() if e.text else '',[structure(c) for c in e])
assert [structure(x) for x in root.findall('.//w:sectPr',NS)]==[structure(x) for x in sections]
(D/'bibliography.json').write_text(json.dumps(dict(zip(order,bib)),indent=2,ensure_ascii=False),encoding='utf-8')
(D/'build-audit.json').write_text(json.dumps({'references':len(order),'body_words':len(' '.join(lines).split()),'changed_parts':changed,'preserved_parts':len(parts)-len(changed),'sections':len(sections),'figures':6,'tables':6,'output':str(OUT)},indent=2),encoding='utf-8')
print(json.loads((D/'build-audit.json').read_text()))
