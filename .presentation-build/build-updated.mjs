import fs from 'node:fs/promises';
import path from 'node:path';
import JSZip from 'jszip';
import { FileBlob, PresentationFile } from '@oai/artifact-tool';

const sourcePath = 'D:/Downloads/ElNino_Agri_GDP_Final_Project_PPT (1).pptx';
const buildDir = 'C:/Users/hardi/Coding All Programs/pbl agriculture project/.presentation-build';
const candidatePath = path.join(buildDir, 'candidate.pptx');
const source = await JSZip.loadAsync(await fs.readFile(sourcePath));

const slides = {
  1: {
    'Predicting the Impact of El Niño on Agricultural GDP using Panel Data Machine Learning': 'Agricultural GDP Prediction Using Climate and El Niño Data',
  },
  3: {
    'El Niño alters global weather patterns, causing delayed monsoons, lower rainfall, higher temperatures and drought in India.': 'El Niño can affect the Indian monsoon, but its effects vary by place and year.',
    'Indian agriculture depends on the monsoon, so crop output and Agricultural GDP fall when rainfall fails.': 'Rainfall and temperature matter for farming, so we study them alongside an economic target.',
    'Rainfall, temperature, El Niño index and past GDP data exist, but there is no reliable AI system that estimates how a stronger El Niño would change state-wise Agricultural GDP.': 'Can rainfall, temperature and ONI predict the project’s state-year agricultural GDP sample? What happens when we change these inputs?',
    "Farmers' income depends directly on agricultural output.": 'Explore the link between climate indicators and the economic sample.',
    'Governments need early information to plan subsidies, irrigation support and food reserves.': 'Compare a simple baseline with four tree-based ML models.',
    'Accurate prediction enables proactive policy and lower economic losses.': 'Make results easy to explore in a local web app.',
    'Agricultural Gross State Value Added (GSVA) at constant 2011-12 prices, in ₹ Crore. Conventionally called Agricultural GDP.': 'Bundled agricultural GDP sample. Its official source and units are not verified.',
  },
  4: {
    'Research gap:  ': 'Our approach:  ',
    'Climate–Agriculture Studies': 'ENSO and agriculture',
    'ENSO (El Niño–Southern Oscillation) influences rainfall patterns and crop-yield variability across regions.': 'ENSO is linked to rainfall and crop-yield variation in some regions.',
    'Focuses on rainfall and crop yield, not Agricultural GDP.': 'Regional effects differ and need careful testing.',
    'Crop Yield Prediction using ML': 'Crop prediction with ML',
    'ML models use weather and soil features to estimate crop production and improve accuracy.': 'ML can learn patterns from weather and crop data.',
    'Predicts crop yield only; no economic (GDP) estimate.': 'Crop yield and economic output are different targets.',
    'Macroeconomic Impact Studies': 'Climate and the economy',
    'Droughts and weather shocks affect national GDP and agricultural productivity.': 'Weather shocks can be linked to changes in economic output.',
    'National-level analysis, not state-wise Agricultural GDP.': 'National results may not describe every state.',
    'Panel Data Econometrics': 'State-year panel analysis',
    'Combines state-wise and time-series data to study regional trends and support policy analysis.': 'Panel data follows several states across multiple years.',
    'Mostly traditional econometrics, few ML models.': 'Care is needed with time splits and state differences.',
    'no prior work combines panel data, multi-model ML and ENSO scenario simulation to estimate state-wise Agricultural GSVA.': 'This prototype compares climate-based models and lets users explore what-if inputs. It does not establish a new causal effect.',
  },
  5: {
    'Build an AI system that estimates and simulates the impact of El Niño on the Agricultural GDP of Indian states.': 'Build a web prototype that predicts the local agricultural GDP sample from rainfall, temperature and ONI.',
    'Collect NOAA ONI, ERA5 rainfall and temperature, and RBI/MoSPI Agricultural GSVA for 10 states (2009–2023).': 'Prepare NOAA ONI, Open-Meteo weather and a bundled economic sample for 10 states (2009–2023).',
    'Clean and merge into a balanced panel; engineer anomaly and lagged-ENSO features.': 'Join 150 state-year rows and train with three inputs: rainfall, temperature and ONI.',
    'Benchmark five models (OLS, Random Forest, Gradient Boosting, XGBoost, Extra Trees) on a chronological split.': 'Compare five models using earlier years for training and later years for testing.',
    'Simulate El Niño scenarios, from Normal to Strong El Niño and La Niña, for state-wise GSVA.': 'Let users change climate inputs and inspect what-if model estimates.',
    'Deliver a web platform with dashboard, scenario lab, grounded AI search and data exports.': 'Show model scores, scenarios, project search and data exports in a local web app.',
  },
  6: {
    'Oceanic Niño Index (ONI)': 'Oceanic Niño Index (ONI)',
    'NOAA CPC': 'NOAA PSL',
    '3-month running mean SST anomaly, Niño 3.4 (°C)': 'Annual mean of monthly ONI values (°C)',
    'Monthly': 'Annual input',
    'Monsoon precipitation': 'Annual rainfall',
    'Open-Meteo ERA5': 'Open-Meteo archive',
    'Total annual and monsoon rainfall (mm)': 'Daily precipitation summed by year (mm)',
    'Daily, aggregated': 'State centroid',
    'Mean daily air temperature (°C)': 'Mean annual 2-metre air temperature (°C)',
    'Agricultural GSVA': 'Economic target',
    'RBI Handbook / MoSPI': 'Bundled project CSV',
    'Agriculture & allied GSVA, constant 2011-12 prices (₹ Cr)': 'Sample values; source and units unverified',
    'Engineered panel features': 'Three inputs used to train the models',
    'Rainfall anomaly': 'Rainfall',
    'R(i,t) − mean R(i)': 'rainfall_mm',
    "Deviation from the state's 15-year mean.": 'Total annual rainfall at a state centroid.',
    'Temperature anomaly': 'Temperature',
    'T(i,t) − mean T(i)': 'avg_temperature_c',
    'Thermal stress index for each state-year.': 'Average annual air temperature.',
    'Lagged ENSO effect': 'El Niño index',
    'ONI(t−1)': 'oni_index',
    'Captures delayed kharif-to-rabi impact.': 'Annual mean of monthly NOAA ONI.',
  },
  7: {
    'Hosting: Vercel': 'Demo: run locally',
  },
  8: {
    'AI Search': 'Project Search',
    'Grounded search service': 'Keyword search service',
  },
  9: {
    'Econometric baseline': 'Simple baseline',
    'Tests linear climate elasticity; benchmark for non-linear gains': 'Tests whether a straight-line pattern is enough',
    'Bagging ensemble': 'Many decision trees',
    'Reduces variance; captures non-linear interactions': 'Can learn non-linear patterns in the three inputs',
    'Sequential boosting': 'Boosted trees',
    'Fits residual errors step by step across anomaly thresholds': 'Each new tree tries to correct earlier errors',
    'Regularised boosting': 'Boosted trees',
    'L1/L2 regularisation with second-order gradients': 'Compares another widely used boosting method',
    'Extremely randomised trees': 'Randomised trees',
    'Random split points; robust to collinear climate features': 'Uses random splits; best RMSE in this comparison',
    'Random K-fold is avoided because it leaks future shocks into past predictions. The best model has the lowest RMSE and MAE on the held-out years.': 'We use rainfall, temperature and ONI. We selected by test RMSE; a separate final test is future work.',
  },
  10: {
    'MAE (₹ Cr)': 'MAE (units)',
    'RMSE (₹ Cr)': 'RMSE (units)',
    'Selected': 'Role',
    '14.02': '14.00',
    '19.03': '19.09',
    '0.2965': '0.2917',
    '12.9%': '12.8%',
    '₹ Cr RMSE, lowest of five models': 'Sample-unit RMSE, lowest of five',
    'R² on unseen years, highest': 'R² on 2020–2023 test years',
    'MAPE, lowest of five models': 'MAPE, lowest of five models',
  },
  11: {
    'Extra Trees leads on every metric: RMSE 15.68 ₹ Cr, R² 0.52.': 'Extra Trees has the lowest RMSE (15.68) and highest R² (0.5224).',
    'The OLS baseline is second-best (R² 0.41), suggesting much of the climate effect is near-linear.': 'The simple linear baseline also performs reasonably (R² 0.4058).',
    'Boosted models trail on this small panel of 150 observations.': 'The panel has only 150 rows, so scores may change with more data.',
    'R² of about 0.52 means roughly half the variance is explained, so outputs are estimates, not forecasts.': 'R² 0.5224 means the model explains about 52% of variation in these test rows.',
    'Random split points likely help with collinear rainfall and temperature anomalies.': 'The economic target source and units need verification before real use.',
  },
  12: {
    'Five presets (Normal, Weak, Moderate, Strong El Niño, La Niña) with live sliders and ensemble averaging.': 'Five presets change rainfall, temperature and ONI together. The results are what-if estimates.',
    'Grounded AI Search': 'Project Search',
    'Classifies questions as Factual, Historical, Prediction, Scenario or Mixed, and answers with exact metrics and citations (NOAA, IMD, RBI, MoSPI).': 'Routes keyword questions to project facts, data and saved metrics. Check source claims independently.',
    'Per-state climate–economy trajectories, vulnerability indices and historical drought correlations.': 'Shows historical climate and economic sample views for selected states.',
    'One-click CSV and JSON downloads of the cleaned panel and the model benchmark results.': 'Downloads panel data and model scores as CSV or JSON.',
  },
  13: {
    'Early warning for food inflation and drought relief.': 'Discuss possible climate risks in a classroom setting.',
    'Identify states needing support before the impact peaks.': 'Explore how changed rainfall alters model estimates.',
    'Plan procurement and storage ahead of a weak monsoon.': 'Try weak-monsoon examples for discussion.',
    'Target assistance to the most affected regions.': 'Compare illustrative scenarios across state profiles.',
    'Test monsoon-deficit scenarios before the sowing season.': 'Change climate inputs and inspect model output.',
    'Study how climate indicators shape agricultural output.': 'A starting point for work with verified GSVA data.',
    'The platform gives analytical estimates and simulation scenarios to support decisions.': 'This is an educational prototype with an unverified economic sample.',
    'It is not an official government forecast, and it does not claim El Niño is the sole cause of a change in Agricultural GSVA.': 'Its results are model estimates, not official forecasts or causal effects.',
  },
  14: {
    'More climate variables': 'Verify economic data',
    'Add soil moisture, humidity and reservoir levels.': 'Replace the sample target with traceable state GSVA and clear units.',
    'Extend the panel from 10 states to the whole country.': 'Expand beyond 10 states after validating the target.',
    'Predict wheat, cotton, sugarcane and soybean instead of aggregate GSVA.': 'Explore crop outcomes with verified crop data.',
    'Move from state-level to district-level predictions.': 'Add district data when reliable sources exist.',
    'Deep learning & tuning': 'Better validation',
    'Try LSTM and hyperparameter search to improve on R² 0.52.': 'Add state information and keep a final test period untouched.',
    'Live data feeds': 'IMD comparison',
    'Refresh ONI and ERA5 data automatically and retrain on a schedule.': 'Compare IMD rainfall with the current Open-Meteo baseline.',
  },
  15: {
    'Built an end-to-end system: data ingestion, panel preparation, five ML models, scenario simulation and a web platform.': 'Built a local web demo with a data pipeline, five models and what-if scenarios.',
    'Benchmarked models on a strict chronological split (train 2009–2019, test 2020–2023) to avoid temporal leakage.': 'Trained on 2009–2019 and compared models on 2020–2023 (150 rows in all).',
    'Extra Trees performed best: RMSE 15.68 ₹ Cr, MAE 12.19 ₹ Cr, R² 0.5224 on unseen years.': 'Extra Trees scored best here: RMSE 15.68, MAE 12.19 sample units, R² 0.5224.',
    'The Scenario Lab turns model output into what-if estimates that support proactive agricultural policy.': 'Before real use, verify the economic target and test on a separate final period.',
    'LIVE DEMO': 'LOCAL DEMO',
    'pblminiprojecttyaids.vercel.app': 'http://localhost:3000',
  },
  16: {
    '[1] Open-Meteo, "Historical Weather API (ERA5 Reanalysis)." [Online]. Available: https://open-meteo.com/': '[1] Open-Meteo, "Historical Weather API." https://open-meteo.com/en/docs/historical-weather-api',
    '[2] NOAA Climate Prediction Center, "Oceanic Niño Index (ONI) Historical Data." [Online]. Available: https://origin.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php. [Accessed: Aug. 6, 2026].': '[2] NOAA PSL, "Oceanic Niño Index (ONI) Data." https://psl.noaa.gov/data/correlation/oni.data',
    '[3] Ministry of Statistics and Programme Implementation (MoSPI), "State-wise Agricultural GDP Data." [Online]. Available: https://mospi.gov.in/. [Accessed: Aug. 6, 2026].': '[3] Project economic sample: backend/app/data/sources/agricultural_gdp_reference.csv (origin and units unverified).',
    '[4] Reserve Bank of India (RBI), "Handbook of Statistics on Indian States." [Online]. Available: https://www.rbi.org.in/. [Accessed: Aug. 6, 2026].': '[4] IMD Pune, "1° Gridded Rainfall Data" (optional comparison). https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_1_NetCDF.html',
    '[5] India Meteorological Department (IMD), "Rainfall and Temperature Data." [Online]. Available: https://mausam.imd.gov.in/. [Accessed: Aug. 6, 2026].': '[5] Saved model results: data/processed/model_evaluation_report.json (local project file).',
  },
};

const notes = {
  1: {
    'Introduce the team and guide. One-line pitch: we built a full-stack ML platform that estimates how El Niño shocks change state-wise Agricultural GDP in India.': 'Introduce the team and guide. This is a local web prototype that compares climate-based predictions for a bundled agricultural GDP sample.',
  },
  3: {
    'GSVA vs GDP: state agricultural accounts are compiled at basic prices (GVA). GDP = GVA + product taxes - product subsidies. In everyday discourse this is called Agricultural GDP, so we use both terms and are explicit about the distinction.': 'The target is a bundled agricultural GDP sample. We have not verified its official source or units, so do not call these values official GSVA or rupee crore.',
  },
  6: {
    'States: Maharashtra, Punjab, Uttar Pradesh, Madhya Pradesh, Rajasthan, Gujarat, Andhra Pradesh, Karnataka, Haryana, West Bengal. 10 states x 15 years = 150 observations, a balanced panel.': 'The training panel contains Andhra Pradesh, Bihar, Gujarat, Karnataka, Kerala, Madhya Pradesh, Maharashtra, Punjab, Rajasthan and Tamil Nadu, with 15 years per state. Anomaly and lag columns exist in preprocessing but are not model inputs.',
  },
  9: {
    'Why not K-fold: in panel data, random folds train on future years and predict past ones, which inflates accuracy. The chronological split mimics real forecasting.': 'A chronological split keeps later years out of training. We selected the winning model on the same test period used to report its score. A stronger study should use a separate validation period and untouched final test.',
  },
  10: {
    'Extra Trees wins on all four metrics. Note the metrics are on the out-of-sample years 2020-2023 only.': 'Extra Trees has the lowest MAE, RMSE and MAPE and highest R² among the five models on 2020–2023 rows. MAE and RMSE are in unverified sample units, not confirmed rupee crore.',
  },
  12: {
    'Suggested: run a live demo here at https://pblminiprojecttyaids.vercel.app and show the Scenario Lab with a Strong El Niño preset for Maharashtra.': 'Run the frontend and backend locally before the presentation. The Vercel address currently returns 404. Show the Scenario Lab as a what-if demo, not a causal forecast.',
  },
};

function unescapeXml(s) {
  return s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, '&');
}
function escapeXml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&apos;');
}
function updateText(xml, changes, name) {
  const seen = new Set();
  const updated = xml.replace(/(<a:t(?:\s[^>]*)?>)([\s\S]*?)(<\/a:t>)/g, (full, open, content, close) => {
    const old = unescapeXml(content);
    if (!Object.prototype.hasOwnProperty.call(changes, old)) return full;
    seen.add(old);
    return `${open}${escapeXml(changes[old])}${close}`;
  });
  const missing = Object.keys(changes).filter(k => !seen.has(k));
  if (missing.length) throw new Error(`${name}: missing text nodes: ${missing.join(' || ')}`);
  return updated;
}
function replaceOnce(s, oldText, newText, name) {
  const at = s.indexOf(oldText);
  if (at < 0 || s.indexOf(oldText, at + 1) >= 0) throw new Error(`${name}: expected one occurrence of ${oldText}`);
  return s.slice(0, at) + newText + s.slice(at + oldText.length);
}

for (const [num, changes] of Object.entries(slides)) {
  const filename = `ppt/slides/slide${num}.xml`;
  const before = await source.file(filename).async('string');
  source.file(filename, updateText(before, changes, filename));
}
for (const [num, changes] of Object.entries(notes)) {
  const filename = `ppt/notesSlides/notesSlide${num}.xml`;
  const before = await source.file(filename).async('string');
  source.file(filename, updateText(before, changes, filename));
}

// Update the existing editable chart's labels and cache. Its native workbook is kept in sync.
let chart = await source.file('ppt/charts/chart1.xml').async('string');
chart = replaceOnce(chart, 'Out-of-sample error, 2020–2023 (₹ Crore)', 'Out-of-sample error, 2020–2023 (sample units)', 'chart title');
chart = replaceOnce(chart, 'MAE (₹ Cr)', 'MAE (units)', 'chart legend');
chart = replaceOnce(chart, 'RMSE (₹ Cr)', 'RMSE (units)', 'chart legend');
chart = replaceOnce(chart, '<c:pt idx="3"><c:v>14.02</c:v></c:pt>', '<c:pt idx="3"><c:v>14.00</c:v></c:pt>', 'chart MAE');
chart = replaceOnce(chart, '<c:pt idx="3"><c:v>19.03</c:v></c:pt>', '<c:pt idx="3"><c:v>19.09</c:v></c:pt>', 'chart RMSE');
source.file('ppt/charts/chart1.xml', chart);

const workbookName = 'ppt/embeddings/Microsoft_Excel_Worksheet1.xlsx';
const workbook = await JSZip.loadAsync(await source.file(workbookName).async('nodebuffer'));
let shared = await workbook.file('xl/sharedStrings.xml').async('string');
shared = replaceOnce(shared, 'MAE (₹ Cr)', 'MAE (units)', 'workbook header');
shared = replaceOnce(shared, 'RMSE (₹ Cr)', 'RMSE (units)', 'workbook header');
workbook.file('xl/sharedStrings.xml', shared);
let worksheet = await workbook.file('xl/worksheets/sheet1.xml').async('string');
worksheet = replaceOnce(worksheet, '<c r="B5"><v>14.02</v></c>', '<c r="B5"><v>14.00</v></c>', 'workbook MAE');
worksheet = replaceOnce(worksheet, '<c r="C5"><v>19.03</v></c>', '<c r="C5"><v>19.09</v></c>', 'workbook RMSE');
workbook.file('xl/worksheets/sheet1.xml', worksheet);
source.file(workbookName, await workbook.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE' }));

let rels = await source.file('ppt/slides/_rels/slide15.xml.rels').async('string');
rels = replaceOnce(rels, 'https://pblminiprojecttyaids.vercel.app', 'http://localhost:3000', 'local demo hyperlink');
source.file('ppt/slides/_rels/slide15.xml.rels', rels);

// The supplied deck has 15 stale master content-type declarations for files it
// does not contain. Drop only those broken declarations; visual parts stay intact.
let contentTypes = await source.file('[Content_Types].xml').async('string');
let staleMasterDeclarations = 0;
contentTypes = contentTypes.replace(/<Override\b[^>]*PartName="\/(ppt\/slideMasters\/slideMaster\d+\.xml)"[^>]*\/>/g, (tag, target) => {
  if (source.file(target)) return tag;
  staleMasterDeclarations++;
  return '';
});
if (staleMasterDeclarations !== 15) throw new Error(`Unexpected stale master count: ${staleMasterDeclarations}`);
source.file('[Content_Types].xml', contentTypes);

await fs.writeFile(candidatePath, await source.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE' }));
const imported = await PresentationFile.importPptx(await FileBlob.load(candidatePath));
if (imported.slides.items.length !== 16) throw new Error('Slide count changed');
const previewDir = path.join(buildDir, 'updated');
await fs.mkdir(previewDir, { recursive: true });
for (let i = 0; i < imported.slides.items.length; i++) {
  const png = await imported.slides.getItem(i).export({ format: 'png', scale: 1 });
  await fs.writeFile(path.join(previewDir, `slide-${String(i + 1).padStart(2, '0')}.png`), new Uint8Array(await png.arrayBuffer()));
}
console.log(candidatePath);
