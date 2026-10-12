import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const workspaceDir = 'C:/Users/hardi/Coding All Programs/pbl agriculture project';
const SKILL_DIR = 'C:/Users/hardi/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations';
const candidatePath = path.join(workspaceDir, '.presentation-build/candidate.pptx');
const finalPath = path.join(workspaceDir, 'presentation/ElNino_Agri_GDP_Project_Updated_2026-09-29.pptx');
const stagingDir = path.join(workspaceDir, '.presentation-build/finalization');
await fs.mkdir(stagingDir, { recursive: true });
await fs.mkdir(path.dirname(finalPath), { recursive: true });
const { finalizePresentation } = await import(pathToFileURL(path.join(SKILL_DIR, 'container_tools/artifact_tool_utils.mjs')).href);
const result = await finalizePresentation({
  workspaceDir,
  candidatePath,
  finalPath,
  explicitTotalSlideCount: 16,
  sourceTemplatePath: 'D:/Downloads/ElNino_Agri_GDP_Final_Project_PPT (1).pptx',
  requiredNativeTableOwnerSlides: [2, 4, 6, 9, 10],
  requiredNativeChartOwnerSlides: [11],
  pythonExecutable: 'C:/Users/hardi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
  integrityValidatorPath: path.join(SKILL_DIR, 'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath: path.join(SKILL_DIR, 'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs: [
    '--expected-slide-size-emu', '9144000,5143500',
    '--validate-bullet-geometry',
    '--validate-heading-fit',
    ...[2, 4, 6, 9, 10].flatMap(n => ['--require-native-table-slide', String(n)]),
  ],
  fontPolicy: {
    basis: 'reference',
    families: ['Times New Roman', 'Courier New'],
    referencePath: 'D:/Downloads/ElNino_Agri_GDP_Final_Project_PPT (1).pptx',
    referenceSha256: 'e46582f2653be80c04d760ee4afa09f4a3b4d9b86924dabf995201295a1cce4c',
  },
  verifyArtifactToolImport: true,
  receiptPath: path.join(stagingDir, 'updated.validation.json'),
});
console.log(JSON.stringify(result, null, 2));
