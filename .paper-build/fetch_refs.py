import concurrent.futures, json, re, urllib.request, urllib.parse,sys,time
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

SEEDS = '''kumar2004|10.1002/joc.1081
rasmusson1983|10.1175/1520-0493(1983)111<0517:TRBEEP>2.0.CO;2
kumar1999|10.1126/science.284.5423.2156
kumar2006|10.1126/science.1131152
gadgil2003|10.1146/annurev.earth.31.100901.141251
ashok2001|10.1029/2001GL013294
saji1999|10.1038/43854
ashok2007|10.1029/2006JC003798
index2021|10.1088/1748-9326/abe9ed
pai2014|10.54302/mausam.v65i1.851
srivastava2009|10.1002/asl.232
mishra2010|10.1016/j.jhydrol.2010.07.012
wilhelmi2002|10.1023/A:1013388814894
udmale2014|10.1016/j.ijdrr.2014.09.011
swami2021|10.1016/j.ecolind.2020.107206
chakraborty2016|10.1080/19475705.2014.897656
saha2021|10.1080/19475705.2020.1861114
balaganesh2020|10.1016/j.ecolind.2020.106197
murthy2015|10.1016/j.ijdrr.2015.01.004
sharma2019|10.1088/2515-7620/ab24ed
nair2022|10.1007/s12517-022-09623-0
cutter2003|10.1111/1540-6237.8402002
abson2012|10.1016/j.apgeog.2012.08.004
adger2006|10.1016/j.gloenvcha.2006.02.006
fussel2007|10.1016/j.gloenvcha.2006.05.002
handbook2008|10.1787/9789264043466-en
jolliffe2016|10.1098/rsta.2015.0202
lobell2011|10.1126/science.1204531
schlenker2009|10.1073/pnas.0906865106
wheat2012|10.1038/nclimate1356
rice2012|10.1007/s10584-011-0208-4
dell2014|10.1257/jel.52.3.740
rf2001|10.1023/A:1010933404324
et2006|10.1007/s10994-006-6226-1
gb2001|10.1214/aos/1013203451
xgb2016|10.1145/2939672.2939785
bergmeir2012|10.1016/j.ins.2011.12.028
roberts2017|10.1111/ecog.02881
varma2006|10.1186/1471-2105-7-91
hyndman2006|10.1016/j.ijforecast.2006.03.001
willmott2005|10.3354/cr030079
chai2014|10.5194/gmd-7-1247-2014
strobl2007|10.1186/1471-2105-8-25
altmann2010|10.1093/bioinformatics/btq134
shmueli2010|10.1214/10-STS330
rudin2019|10.1038/s42256-019-0048-x
cropml2020|10.1016/j.compag.2020.105709
agml2018|10.3390/s18082674'''

OUT = Path(__file__).parent / 'verified_references.json'
existing=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}

def fetch(seed):
    key,doi=seed.split('|')
    if key in existing and 'title' in existing[key]:return key,existing[key]
    try:
        time.sleep(1.2)
        url='https://api.crossref.org/works/'+urllib.parse.quote(doi,safe='')
        req=urllib.request.Request(url,headers={'User-Agent':'AcademicReportReferenceCheck/1.0'})
        with urllib.request.urlopen(req,timeout=45) as r:m=json.load(r)['message']
        return key,{k:m.get(k) for k in ['DOI','title','author','container-title','volume','issue','page','article-number','published','abstract','URL','publisher']}
    except Exception as e:return key,{'error':str(e),'DOI':doi}

with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
    results=dict(pool.map(fetch,SEEDS.splitlines()))
OUT.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
for key,m in results.items():print(key,m.get('title',m.get('error')))
print('Verified',sum('title' in m for m in results.values()),'of',len(results))
