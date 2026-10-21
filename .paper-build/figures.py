import json,csv,math
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor,Color,black,white
import pypdfium2 as pdfium

OUT=Path(__file__).parent
A=json.loads((OUT/'analysis.json').read_text())
rows=list(csv.DictReader((OUT/'heldout_predictions.csv').open()))
blue=HexColor('#24547A'); teal=HexColor('#147568'); gray=HexColor('#6E7780'); pale=HexColor('#E8EEF3')
W=340
def start(n,h):
 c=canvas.Canvas(str(OUT/f'fig{n}.pdf'),pagesize=(W,h));c.setTitle(f'Figure {n}');return c
def text(c,x,y,t,size=9,font='Times-Roman',align='left',color=black):
 c.setFillColor(color);c.setFont(font,size)
 {'left':c.drawString,'center':c.drawCentredString,'right':c.drawRightString}[align](x,y,str(t))
def line(c,x1,y1,x2,y2,color=gray,width=.5):
 c.setStrokeColor(color);c.setLineWidth(width);c.line(x1,y1,x2,y2)
def finish(c,n):
 c.save();d=pdfium.PdfDocument(str(OUT/f'fig{n}.pdf'));d[0].render(scale=3).to_pil().save(OUT/f'fig{n}.png');d.close()

c=start(1,275)
boxes=[('Official inputs','IMD rainfall and temperature | ONI | RBI crop GSVA'),('Financial year harmonization','April to March | common 2011-12 price base'),('Panel and quality checks','28 states | 385 complete rows | 7 missing targets'),('Chronological evaluation','280 training rows | 105 held-out rows'),('Five regressors and two baselines','OLS | RF | GB | XGB | ET | mean | last observation'),('Application and scientific review','Dashboard | predictions | scenarios | diagnostics')]
for i,(a,b) in enumerate(boxes):
 y=238-i*43;c.setFillColor(pale);c.setStrokeColor(blue);c.setLineWidth(.7);c.roundRect(8,y,324,31,3,stroke=1,fill=1)
 text(c,170,y+19,a,10,'Times-Bold','center',blue);text(c,170,y+6,b,8.5,align='center')
 if i<5:
  line(c,170,y,170,y-10,blue,1);c.setFillColor(blue);p=c.beginPath();p.moveTo(167,y-7);p.lineTo(170,y-11);p.lineTo(173,y-7);p.close();c.drawPath(p,fill=1,stroke=0)
finish(c,1)

c=start(2,175)
left,bottom,pw,ph=32,32,294,121
for v in [0,7,14,21,28]:
 y=bottom+ph*v/28;line(c,left,y,left+pw,y,HexColor('#DDDDDD'));text(c,left-5,y-3,v,8,align='right')
for i,(year,n) in enumerate(A['counts'].items()):
 x=left+i*21+3;c.setFillColor(blue if int(year)<=2020 else teal);c.rect(x,bottom,14,ph*n/28,fill=1,stroke=0)
 text(c,x+7,20,year[-2:],8,align='center')
text(c,32,164,'Complete state-year observations',9,'Times-Bold')
text(c,133,4,'Financial year starting in 20xx',9,align='center')
text(c,251,164,'Train',8,color=blue);text(c,293,164,'Test',8,color=teal)
finish(c,2)

c=start(3,187)
names=['Last value','OLS','State mean','GB','ET','XGB','RF']
values=[A['baselines']['state_last']['rmse'],17410.41,A['baselines']['state_mean']['rmse'],18086.89,18388.83,18752.05,21343.40]
for i,(name,val) in enumerate(zip(names,values)):
 y=150-i*20;text(c,65,y+4,name,9,align='right');c.setFillColor(teal if i==0 else blue if i==1 else gray);c.rect(72,y,220*val/23000,12,fill=1,stroke=0);text(c,75+220*val/23000,y+3,f'{val:,.0f}',8)
for t in [0,10000,20000]:text(c,72+220*t/23000,12,str(t//1000),8,align='center')
text(c,185,0,'Test RMSE (thousand INR crore)',9,align='center');text(c,72,174,'Lower is better',9,'Times-Bold')
finish(c,3)

c=start(4,210)
x0,y0,pw,ph=44,35,271,156
for v in [0,50,100,150,200]:
 x=x0+pw*v/220;y=y0+ph*v/220
 line(c,x,y0,x,y0+ph,HexColor('#EEEEEE'));line(c,x0,y,x0+pw,y,HexColor('#EEEEEE'))
 text(c,x,y0-12,v,8,align='center');text(c,x0-7,y-3,v,8,align='right')
line(c,x0,y0,x0+pw,y0+ph,gray,.8)
for r in rows:
 x=x0+pw*float(r['agricultural_gdp_cr'])/220000;y=y0+ph*float(r['linear_regression'])/220000
 c.setFillColor(blue);c.circle(x,y,1.8,fill=1,stroke=0)
text(c,175,11,'Observed crop GSVA (thousand INR crore)',9,align='center')
c.saveState();c.translate(10,113);c.rotate(90);text(c,0,0,'OLS predicted GSVA (thousand INR crore)',9,align='center');c.restoreState()
text(c,49,198,'105 held-out state-years',9,'Times-Bold');finish(c,4)

c=start(5,172)
x0,y0,pw,ph=38,32,286,110
for v in [0,10,20,30]:
 y=y0+ph*v/30;line(c,x0,y,x0+pw,y,HexColor('#DDDDDD'));text(c,x0-5,y-3,v,8,align='right')
series=[]
for name,col in [('OLS',blue),('Last value',teal)]:
 pts=[]
 for i,y in enumerate(range(2021,2025)):
  rr=[r for r in rows if int(r['year'])==y];k='linear_regression' if name=='OLS' else 'state_last';v=math.sqrt(sum((float(r[k])-float(r['agricultural_gdp_cr']))**2 for r in rr)/len(rr))/1000
  x=x0+20+i*82;yp=y0+ph*v/30;pts.append((x,yp));c.setFillColor(col);c.circle(x,yp,2.6,fill=1,stroke=0)
 for p,q in zip(pts,pts[1:]):line(c,*p,*q,col,1.2)
for i,y in enumerate(range(2021,2025)):text(c,x0+20+i*82,19,f'{y}-{str(y+1)[-2:]}',8,align='center')
text(c,38,157,'RMSE (thousand INR crore)',9,'Times-Bold');text(c,241,157,'OLS',9,color=blue);text(c,279,157,'Last value',9,color=teal)
text(c,180,3,'Held-out financial year',9,align='center');finish(c,5)

c=start(6,144)
xzero=196;sc=5.7
for v in [-15,-10,-5,0,5,10,15,20]:
 x=xzero+v*sc;line(c,x,27,x,126,HexColor('#DDDDDD'));text(c,x,15,v,8,align='center')
for i,(lab,v) in enumerate([('Rainfall',2.07),('Temperature',14.52),('ONI',-13.50)]):
 y=105-i*32;text(c,89,y+3,lab,9,align='right');c.setFillColor(teal if v<0 else blue);c.rect(min(xzero,xzero+v*sc),y,abs(v)*sc,14,fill=1,stroke=0);text(c,xzero+v*sc+(4 if v>=0 else -4),y+3,f'{v:+.2f}',9,align='left' if v>=0 else 'right')
line(c,xzero,27,xzero,126,black,.8);text(c,170,1,'Change in RMSE after permutation (INR crore)',9,align='center');text(c,96,133,'OLS | 20 repeats | shared-year ONI',9,'Times-Bold');finish(c,6)
print('Six scientific figures rendered')
