import fs from 'node:fs/promises';
import path from 'node:path';
import { FileBlob, PresentationFile } from '@oai/artifact-tool';

const source = 'D:/Downloads/ElNino_Agri_GDP_Final_Project_PPT (1).pptx';
const output = 'C:/Users/hardi/Coding All Programs/pbl agriculture project/.presentation-build/source';
await fs.mkdir(output, { recursive: true });
const presentation = await PresentationFile.importPptx(await FileBlob.load(source));
const snapshot = await presentation.inspect({ kind: 'slide,textbox,shape,image,table,chart,layout,notes', maxChars: 200000 });
await fs.writeFile(path.join(output, 'inspection.ndjson'), snapshot.ndjson);
await fs.writeFile(path.join(output, 'summary.json'), JSON.stringify({ slides: presentation.slides.items.length, masters: presentation.masters.items.length, layouts: presentation.layouts.items.length }, null, 2));
for (let i = 0; i < presentation.slides.items.length; i++) {
  const slide = presentation.slides.getItem(i);
  const png = await slide.export({ format: 'png', scale: 1 });
  await fs.writeFile(path.join(output, `slide-${String(i + 1).padStart(2, '0')}.png`), new Uint8Array(await png.arrayBuffer()));
}
