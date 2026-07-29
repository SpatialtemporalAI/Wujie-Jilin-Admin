const fs = require('node:fs');
const path = require('node:path');
const mammoth = require('mammoth');

const docxPath = 'src/assets/files/机器人管理系统用户手册 .docx';
const outDir = 'public/manual-images';
fs.mkdirSync(outDir, { recursive: true });

let imgIndex = 0;

mammoth
  .convertToMarkdown(
    { path: docxPath },
    {
      convertImage: mammoth.images.imgElement(function (image) {
        return image.read('base64').then(function (imageBuffer) {
          imgIndex++;
          const ext = image.contentType.split('/')[1] || 'png';
          const filename = `image-${imgIndex}.${ext}`;
          fs.writeFileSync(path.join(outDir, filename), imageBuffer, 'base64');
          return { src: `manual-images/${filename}` };
        });
      })
    }
  )
  .then(result => {
    fs.writeFileSync('src/assets/files/机器人管理系统用户手册.md', result.value);
    console.log('done, images:', imgIndex);
  })
  .catch(err => {
    console.error(err);
    process.exit(1);
  });
