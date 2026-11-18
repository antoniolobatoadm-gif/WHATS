// uso: node shoot.js arquivo.glb saida_prefixo [w h] ; views via env VIEWS="nome:az:el:zoom:tx:ty;..."
const {chromium} = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const root = __dirname;
const srv = http.createServer((q, s) => {
  const p = path.join(root, decodeURIComponent(q.url.split('?')[0]));
  if (!fs.existsSync(p)) { s.writeHead(404); return s.end(); }
  const ext = path.extname(p);
  s.writeHead(200, {'Content-Type': ext=='.js'?'text/javascript':ext=='.html'?'text/html':'application/octet-stream'});
  fs.createReadStream(p).pipe(s);
}).listen(0, async () => {
  const port = srv.address().port;
  const [glb, outp, w='700', h='1000'] = process.argv.slice(2);
  fs.copyFileSync(glb, path.join(root, 'cur.glb'));
  const views = (process.env.VIEWS || 'frente:0:0:1:0:0;perfil:90:0:1:0:0;tres_quartos:28:12:1:0:0').split(';');
  const b = await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const pg = await b.newPage({viewport:{width:+w, height:+h}});
  for (const v of views) {
    const [n, az, el, zoom, tx, ty] = v.split(':');
    await pg.goto(`http://127.0.0.1:${port}/index.html?f=cur.glb&w=${w}&h=${h}&az=${az}&el=${el}&zoom=${zoom}&tx=${tx}&ty=${ty}`);
    await pg.waitForFunction(() => document.title === 'done', null, {timeout: 600000});
    await pg.screenshot({path: `${outp}_${n}.png`});
    console.log('ok', n);
  }
  await b.close(); srv.close();
});
