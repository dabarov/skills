#!/usr/bin/env node
// Render original blue, black, and white CTA motion as straight-alpha ProRes 4444.
// Install this skill's locked dependencies with npm ci before rendering.
const fs = require('node:fs');
const path = require('node:path');
const { spawn, spawnSync } = require('node:child_process');
const { once } = require('node:events');
let sharp;
try { sharp = require('sharp'); }
catch {
  console.error('Missing sharp. Run npm ci --prefix ' + JSON.stringify(path.resolve(__dirname, '..')));
  process.exit(1);
}
const ffmpegCheck = spawnSync('ffmpeg', ['-version'], { stdio: 'ignore' });
if (ffmpegCheck.error || ffmpegCheck.status !== 0) {
  console.error('FFmpeg is unavailable. Install FFmpeg and add it to PATH before rendering engagement graphics.');
  process.exit(1);
}

const argv = process.argv.slice(2);
function option(name, fallback) {
  const i = argv.indexOf(name);
  if (i < 0) return fallback;
  if (!argv[i + 1] || argv[i + 1].startsWith('--')) throw new Error(`Missing value for ${name}`);
  return argv[i + 1];
}
const tap = argv.includes('--tap');
const output = path.resolve(option('--output', path.join(__dirname, '../generated/engagement', tap ? 'tap' : '')));
const platformFilter = option('--platform', 'all');
const actionFilter = option('--action', 'all');
const customComment = option('--comment', 'Comment');
const overwrite = argv.includes('--overwrite');
const platforms = ['instagram', 'tiktok', 'youtube'].filter(p => platformFilter === 'all' || p === platformFilter);
const actions = ['like', 'comment', 'follow', 'sequence'].filter(a => actionFilter === 'all' || a === actionFilter);
if (!platforms.length || !actions.length) throw new Error('Unknown --platform or --action');
if (customComment.length > 16) throw new Error('Keep --comment to 16 characters or fewer for a compact prompt.');
fs.mkdirSync(output, { recursive: true });
const FPS = 30, WIDTH = 320, HEIGHT = tap ? 176 : 112;
const clamp = x => Math.max(0, Math.min(1, x));
const out = x => 1 - Math.pow(1 - clamp(x), 3);
// Normalized critically damped step: no overshoot and no decorative bouncing.
const spring = x => { const u=clamp(x); return (1-(1+8*u)*Math.exp(-8*u))/(1-9*Math.exp(-8)); };
const escape = s => s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
const labelWidths = new Map();
const copy = (platform, action) => ({
  like: 'Like',
  comment: customComment,
  follow: platform === 'youtube' ? 'Subscribe' : 'Follow',
}[action]);
const activeCopy = (platform, action) => ({
  like: 'Liked', comment: 'Commented', follow: platform === 'youtube' ? 'Subscribed' : 'Following',
}[action]);
const mixColor = (a,b,p) => '#' + [0,2,4].map(i=>Math.round(parseInt(a.slice(i,i+2),16)*(1-p)+parseInt(b.slice(i,i+2),16)*p).toString(16).padStart(2,'0')).join('');

function activeIcon(action, platform) {
  if(action==='follow') return '<path d="m4 12 5 5L20 6"/>';
  if(action==='comment') return `${icon(action,platform)}<g fill="#FFFFFF" stroke="none"><circle cx="7" cy="11" r="1.1"/><circle cx="12" cy="11" r="1.1"/><circle cx="17" cy="11" r="1.1"/></g>`;
  return icon(action,platform);
}

function cursorAt(u, targetX) {
  if(u<.48 || u>=1.60) return '';
  const arrive=spring((u-.48)/.38);
  const leave=1-spring(1-clamp((u-1.26)/.32));
  const opacity=Math.min(out((u-.48)/.17),1-out((u-1.30)/.29));
  const press=u<1.0 ? out((u-.9)/.1) : 1-spring((u-1.0)/.18);
  // The arrow tip lands near the lower edge, leaving the label readable.
  const x=targetX+18*(1-arrive)+12*leave;
  const y=69+25*(1-arrive)+19*leave+2*press;
  return `<g opacity="${opacity}" transform="translate(${x} ${y}) scale(${1-.07*press})">
    <path d="M0 0V28L7.4 20.5L13.2 33L18.1 30.6L12.4 18.3H23Z" fill="#061B31" stroke="#FFFFFF" stroke-width="1.8" stroke-linejoin="round" filter="url(#cursorShadow)"/>
  </g>`;
}

function icon(action, platform) {
  // Original outline paths; the optional tap treatment provides illustrated feedback.
  if (action === 'like' && platform === 'youtube') return '<path d="M8 11v10H4V11Zm0 0 5-8c2 0 3 1 2 5h5c2 0 2 2 1 5l-2 7H8"/>';
  if (action === 'like') return '<path d="M12 21 3.8 13.2C-2 7.5 5.5.2 12 6.1 18.5.2 26 7.5 20.2 13.2Z"/>';
  if (action === 'comment') return '<path d="M5 3h14a3 3 0 0 1 3 3v10a3 3 0 0 1-3 3h-8l-6 4v-4a3 3 0 0 1-3-3V6a3 3 0 0 1 3-3Z"/>';
  if (platform === 'youtube') return '<rect x="1" y="4" width="22" height="16" rx="5"/><path d="m10 8 7 4-7 4Z"/>';
  return '<path d="M12 4v16M4 12h16"/>';
}

function svgAt(t, platform, requested, duration) {
  const entry = spring(t / .32);
  const exit = 1-spring(1-clamp((t - (duration - .2333333333)) / .2));
  const alpha = Math.min(entry, 1 - exit);
  const dy = 6 * (1 - entry) + 6 * exit;
  const beats = requested === 'sequence' ? ['like', 'comment', 'follow'] : [requested];
  const index=Math.min(beats.length-1,Math.floor(t/2.8));
  const beatIndex=requested==='sequence'?index:0;
  const local=requested==='sequence'?t-beatIndex*2.8:t;
  const action=beats[beatIndex];
  const press=tap?(local<1 ? out((local-.9)/.1) : 1-spring((local-1)/.2)):0;
  const active=tap?spring((local-.9)/.22):0;
  const between=beats.length>1 && beatIndex<beats.length-1 ? 1-out((local-2.61)/.19):1;
  const material=active*between;
  const bodyScale = (1-.035*(1-entry)-.035*exit)*(1-.045*press);
  let content = '';
  const widths = beats.map(action => 94+labelWidths.get(copy(platform,action)));
  const selectedWidths=beats.map(action=>tap?94+labelWidths.get(activeCopy(platform,action)):94+labelWidths.get(copy(platform,action)));
  const stateWidth=(i,u)=>widths[i]+(selectedWidths[i]-widths[i])*spring((u-.9)/.28);
  let width=tap?stateWidth(0,t):widths[0];
  for (let i=1;i<beats.length;i++) {
    const p=spring((t-(i*2.8-.13))/.36);
    if(t>=i*2.8-.13) width=selectedWidths[i-1]+(widths[i]-selectedWidths[i-1])*p;
    if(tap && t>=i*2.8+.23) width=stateWidth(i,t-i*2.8);
  }
  beats.forEach((action, i) => {
    const start = requested === 'sequence' ? i * 2.8 : 0;
    const end = requested === 'sequence' ? (i + 1) * 2.8 : duration;
    let a = 1, y = 0;
    if (i > 0) { const p = spring((t - start) / .2); a *= p; y += 3 * (1-p); }
    if (i < beats.length-1) { const p = Math.pow(clamp((t-(end-.17))/.17), 2); a *= 1-p; y -= 3*p; }
    if (t < start || t >= end || a < .001) return;
    const scale = .94+.06*spring((t-start)/.24);
    const u=t-start;
    const feedback=tap?spring((u-.9)/.18):0;
    const changesLabel=tap;
    const oldText=changesLabel?1-out((u-.9)/.11):1;
    const newText=changesLabel?out((u-1.0)/.16):0;
    const text=(label,opacity,offset)=>`<text x="84" y="${58+offset}" opacity="${opacity}" dominant-baseline="middle" font-family="SF Pro Text, Helvetica Neue, Arial, sans-serif" font-size="34" font-weight="600" letter-spacing="0" fill="#061B31">${escape(label)}</text>`;
    content += `<g opacity="${a}" transform="translate(0 ${y})">
      ${text(copy(platform,action),oldText,-2*(1-oldText))}
      ${changesLabel?text(activeCopy(platform,action),newText,2*(1-newText)):''}
      <g transform="translate(56 56) scale(${scale}) translate(-16 -16) scale(1.3333)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <g fill="none" stroke="#061B31" opacity="${1-feedback}">${icon(action,platform)}</g>
        ${tap?`<g fill="${action==='follow'?'none':'#005BB8'}" stroke="#005BB8" opacity="${feedback}">${activeIcon(action,platform)}</g>`:''}
      </g>
    </g>`;
  });
  // Keep the pill centered through label changes and press feedback.
  // The cursor stays at its contact point while the active label changes width.
  const targetX=Math.min(WIDTH-48,WIDTH/2+widths[beatIndex]/2-30);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="320" height="${HEIGHT}" viewBox="0 0 320 ${HEIGHT}">
    <defs><filter id="s" x="-20%" y="-30%" width="140%" height="180%"><feDropShadow dx="0" dy="3" stdDeviation="3" flood-color="#061B31" flood-opacity=".1"/></filter><filter id="cursorShadow" x="-25%" y="-20%" width="160%" height="160%"><feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#061B31" flood-opacity=".18"/></filter><linearGradient id="rim" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF" stop-opacity="${.2+.18*entry}"/><stop offset=".55" stop-color="#FFFFFF" stop-opacity=".12"/><stop offset="1" stop-color="#061B31" stop-opacity=".08"/></linearGradient></defs>
    <g opacity="${alpha}" transform="translate(${WIDTH/2} ${56+dy}) scale(${bodyScale}) translate(${-16-width/2} -56)">
      <rect x="16" y="18" width="${width}" height="76" rx="38" fill="${mixColor('F5F5F7','E8F3FF',material)}" fill-opacity="${.64+.14*material-.035*press}" filter="url(#s)"/>
      <rect x="16.5" y="18.5" width="${width-1}" height="75" rx="37.5" fill="none" stroke="url(#rim)"/>
      ${content}
    </g>
    ${tap?`<g opacity="${alpha}">${cursorAt(local,targetX)}</g>`:''}
  </svg>`;
}

async function render(platform, action) {
  const duration = action === 'sequence' ? 8.4 : 3.2;
  const target = path.join(output, `${platform}-${action}.mov`);
  if (fs.existsSync(target) && !overwrite) throw new Error(`Exists: ${target}; pass --overwrite for derivatives`);
  const ff = spawn('ffmpeg', ['-hide_banner','-loglevel','error', overwrite ? '-y':'-n',
    '-f','rawvideo','-pixel_format','rgba','-video_size',`${WIDTH}x${HEIGHT}`,'-framerate',String(FPS),'-i','pipe:0',
    '-an','-c:v','prores_ks','-profile:v','4','-pix_fmt','yuva444p10le','-alpha_bits','16',
    '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-vendor','apl0', target], {stdio:['pipe','ignore','inherit']});
  const complete = once(ff,'close');
  for (let n=0; n<Math.round(FPS*duration); n++) {
    const svg = svgAt(n/FPS, platform, action, duration);
    const bytes = await sharp(Buffer.from(svg), {density:144}).resize(WIDTH,HEIGHT).ensureAlpha().raw().toBuffer();
    if (!ff.stdin.write(bytes)) await once(ff.stdin,'drain');
    if (n===(tap?27:30) || (tap&&n===54)) {
      const suffix=n===54?'-active':'';
      fs.writeFileSync(path.join(output, `${platform}-${action}${suffix}.svg`), svg);
      await sharp(bytes,{raw:{width:WIDTH,height:HEIGHT,channels:4}}).png().toFile(path.join(output,`${platform}-${action}${suffix}.png`));
    }
  }
  ff.stdin.end();
  const [code] = await complete;
  if (code !== 0) throw new Error(`ffmpeg failed: ${code}`);
  console.log(`${target} (${duration}s)`);
  const beatActions=action==='sequence'?['like','comment','follow']:[action];
  return { platform, action, style:tap?'tap':'quiet', duration, width:WIDTH, height:HEIGHT, fps:FPS, horizontalAlignment:'center', materialOpacity:.64, mascot:false, visibleWidths:beatActions.map(a=>94+labelWidths.get(copy(platform,a))), file:path.basename(target), copy:beatActions.map(a=>copy(platform,a)), ...(tap?{activeCopy:beatActions.map(a=>activeCopy(platform,a)),tapTime:.9,pointer:'arrow'}:{} ) };
}
(async () => {
  if (!customComment.trim()) throw new Error('Comment text must not be empty.');
  for(const label of new Set(['Like',customComment,'Follow','Subscribe',...(tap?['Liked','Commented','Following','Subscribed']:[])])){
    const measured = await sharp(Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="100"><text x="0" y="65" font-family="SF Pro Text, Helvetica Neue, Arial, sans-serif" font-size="34" font-weight="600" letter-spacing="0">${escape(label)}</text></svg>`)).trim().png().toBuffer({resolveWithObject:true});
    if (measured.info.width > 194) throw new Error('Label is too wide; use a shorter question such as "Your take?".');
    labelWidths.set(label,measured.info.width);
  }
  const manifest = [];
  for (const platform of platforms) for (const action of actions) manifest.push(await render(platform,action));
  const manifestPath = path.join(output,'manifest.json');
  const previous = fs.existsSync(manifestPath) ? JSON.parse(fs.readFileSync(manifestPath,'utf8')).assets || [] : [];
  const merged = previous.filter(old => !manifest.some(next => old.file === next.file)).concat(manifest);
  fs.writeFileSync(manifestPath,JSON.stringify({version:tap?6:3,alpha:'straight',silent:true,renderer:'Original compact translucent vector motion; FFmpeg ProRes 4444',assets:merged},null,2)+'\n');
})().catch(e=>{console.error(e.message);process.exitCode=1;});
