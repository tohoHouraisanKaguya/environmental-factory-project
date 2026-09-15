import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
const [directory, dependencyDirectory] = process.argv.slice(2);
const require = createRequire(path.join(path.resolve(dependencyDirectory), 'package.json'));
const sharp = require('sharp');
for (const name of (await fs.readdir(directory)).filter(x=>x.endsWith('.svg'))) {
  await sharp(path.join(directory,name)).flatten({background:'#ffffff'})
    .resize(1600,800,{fit:'fill'}).png().toFile(path.join(directory,name.replace(/\.svg$/,'.png')));
}
process.stdout.write('12幅图件已渲染\n');
