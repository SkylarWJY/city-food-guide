// One-time: lift the NYC-100 master HTML's inline data into a clean guide.json.
// Usage: node scripts/_nyc_to_json.js <master.html> <out.json>
const fs = require('fs');
const src = process.argv[2] || "/Users/jiayiwang/Desktop/2026/自媒体/吃饭/纽约美食100-pro.html";
const out = process.argv[3] || "examples/nyc-100.json";
const html = fs.readFileSync(src, 'utf8');

function grab(re, label) {
  const m = html.match(re);
  if (!m) throw new Error("could not extract " + label);
  return eval('(' + m[1] + ')');           // the captured group is a JS literal
}

const data     = grab(/const data = (\[[\s\S]*?\n\]);/, 'data');
const imgMap   = grab(/const imgMap = (\{[\s\S]*?\n\});/, 'imgMap');
const extraImg = grab(/const extraImg = (\{[\s\S]*?\n\});/, 'extraImg');
const featured = grab(/const featured=(\[[\s\S]*?\]);/, 'featured');
const typeEn   = grab(/const typeEn=(\{[\s\S]*?\n\});/, 'typeEn');
const groupZh  = grab(/const groupZh=(\[[\s\S]*?\]);/, 'groupZh');
const groupEn  = grab(/const groupEn=(\{[\s\S]*?\});/, 'groupEn');
const GEO      = grab(/const GEO = (\{[\s\S]*?\});/, 'GEO');

const featRank = {};
featured.forEach((name, i) => featRank[name] = i);

const venues = data.map(d => {
  const v = { name: d.name, type: d.type, group: d.group, addr: d.addr };
  if (typeEn[d.type]) v.type_en = typeEn[d.type];
  if (imgMap[d.name]) v.img = imgMap[d.name];
  if (extraImg[d.name]) v.extra_imgs = extraImg[d.name];
  if (featRank[d.name] !== undefined) v.featured_rank = featRank[d.name];
  if (GEO[d.name]) { v.lat = GEO[d.name][0]; v.lng = GEO[d.name][1]; }
  if (d.view) v.view = d.view;
  return v;
});

const config = {
  site_title: "Skylar's NYC 100 · 纽约好吃榜",
  brand_wordmark: "<em>Skylar's</em> NYC 100",
  brand_sub: "· 纽约好吃榜",
  site_url: "https://skylar-nyc-100.netlify.app/",
  og_image: "https://skylar-nyc-100.netlify.app/og.png",
  site_display_url: "skylar-nyc-100.netlify.app",
  share_link: "https://skylar-nyc-100.netlify.app",
  beehiiv_form_id: "460499a5-dbab-4eab-9fcc-8bc9edcdf3b2",
  ig_url: "https://instagram.com/skylarwjy",
  ig_handle: "@skylarwjy",
  xhs_url: "https://xhslink.com/m/8QM3DnmS1H9",
  xhs_handle: "@Skylar创业版",
  mymaps_url: "https://www.google.com/maps/d/viewer?mid=14g-pKJngHBuC5DfcF_-f3geqFZmXOQg",
  pdf_url: "Skylar-NYC-100.pdf",
  caption_brand_zh: "Skylar 私藏纽约好吃榜",
  caption_brand_en: "Skylar's NYC 100",
  groups: groupZh.map(zh => ({ zh, en: groupEn[zh] || zh }))
};

fs.writeFileSync(out, JSON.stringify({ config, venues }, null, 2), 'utf8');
const mapped = venues.filter(v => v.lat != null).length;
console.log(`wrote ${out}: ${venues.length} venues (${mapped} mapped, ${featured.length} featured)`);
