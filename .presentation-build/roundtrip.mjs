import { FileBlob, PresentationFile } from '@oai/artifact-tool';
const src = 'D:/Downloads/ElNino_Agri_GDP_Final_Project_PPT (1).pptx';
const out = 'C:/Users/hardi/Coding All Programs/pbl agriculture project/.presentation-build/roundtrip.pptx';
const presentation = await PresentationFile.importPptx(await FileBlob.load(src));
await (await PresentationFile.exportPptx(presentation)).save(out);
