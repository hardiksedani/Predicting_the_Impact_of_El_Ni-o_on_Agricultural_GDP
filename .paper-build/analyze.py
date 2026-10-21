import hashlib,json,sqlite3,sys
from pathlib import Path
import numpy as np,pandas as pd,joblib
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.services.ml import model_features,_linear_climate_permutation_on_test
con=sqlite3.connect((ROOT/'data/pbl_database.sqlite').as_uri()+'?mode=ro',uri=True)
metrics=json.loads(con.execute("SELECT data FROM documents WHERE collection='model_metrics' AND doc_id='current'").fetchone()[0]);con.close()
panel=ROOT/'data/processed/official_panel.csv'
assert hashlib.sha256(panel.read_bytes()).hexdigest()==metrics['panel_sha256']
df=pd.read_csv(panel)
train=df[df.year.isin(metrics['train_years'])].copy()
test=df[df.year.isin(metrics['test_years'])].copy()
X=model_features(test,metrics['training_states'])
def measure(y,p):
 return {'n':len(y),'mae':float(mean_absolute_error(y,p)),'rmse':float(np.sqrt(mean_squared_error(y,p))),'r2':float(r2_score(y,p)),'mape':float(np.mean(np.abs((np.asarray(y)-np.asarray(p))/np.asarray(y)))*100)}
models={}
for name in metrics['models']:
 path=ROOT/'data/models/official'/metrics['run_id']/(name+'.joblib')
 assert hashlib.sha256(path.read_bytes()).hexdigest()==metrics['artifact_sha256'][name]
 model=joblib.load(path);models[name]=model
 test[name]=model.predict(X)
 m=measure(test.agricultural_gdp_cr,test[name])
 assert abs(m['rmse']-metrics['models'][name]['rmse'])<.011
test['state_mean']=test.state.map(train.groupby('state').agricultural_gdp_cr.mean())
test['state_last']=test.state.map(train.sort_values('year').groupby('state').tail(1).set_index('state').agricultural_gdp_cr)
baselines={name:measure(test.agricultural_gdp_cr,test[name]) for name in ['state_mean','state_last']}
annual={str(year):measure(g.agricultural_gdp_cr,g.linear_regression) for year,g in test.groupby('year')}
states={state:measure(g.agricultural_gdp_cr,g.linear_regression) for state,g in test.groupby('state')}
permutation=_linear_climate_permutation_on_test(models['linear_regression'],test,metrics['training_states'])
out={'metrics':metrics,'baselines':baselines,'annual':annual,'states':states,'permutation':permutation,'counts':{str(k):int(v) for k,v in df.groupby('year').size().items()},'summary':df[['rainfall_mm','avg_temperature_c','oni_index','agricultural_gdp_cr']].describe().to_dict()}
(ROOT/'.paper-build/analysis.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
test.to_csv(ROOT/'.paper-build/heldout_predictions.csv',index=False)
print(json.dumps({'baselines':baselines,'annual':annual,'permutation':permutation},indent=2))
