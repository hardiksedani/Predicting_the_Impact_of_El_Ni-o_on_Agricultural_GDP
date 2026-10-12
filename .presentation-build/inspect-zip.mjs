import fs from 'node:fs/promises';
import JSZip from 'jszip';
const ppt = await JSZip.loadAsync(await fs.readFile('D:/Downloads/ElNino_Agri_GDP_Final_Project_PPT (1).pptx'));
const chart = await ppt.file('ppt/charts/chart1.xml').async('string');
console.log('CHART', chart);
const workbook = await JSZip.loadAsync(await ppt.file('ppt/embeddings/Microsoft_Excel_Worksheet1.xlsx').async('nodebuffer'));
for (const name of Object.keys(workbook.files)) {
  if (!workbook.files[name].dir && (name.startsWith('xl/worksheets/') || name === 'xl/sharedStrings.xml')) {
    console.log(name, await workbook.file(name).async('string'));
  }
}
