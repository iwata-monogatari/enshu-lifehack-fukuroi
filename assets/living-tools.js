const tool = document.querySelector('[data-tool]');
const kind = tool.dataset.tool;
const byId = (id) => document.getElementById(id);
const yen = (n) => n.toLocaleString('ja-JP') + '円';
const normalize = (str) => str.normalize('NFKC').toLowerCase().replace(/\s/g, '')
  .replace(/[ァ-ヶ]/g, c => String.fromCharCode(c.charCodeAt(0) - 96))
  .replace(/([一二三四五六七八九])丁目/g, (_, n) => ('一二三四五六七八九'.indexOf(n) + 1) + '丁目');
function el(tag, text) {
  const node = document.createElement(tag);
  node.textContent = text;
  return node;
}
function link(label, url) {
  const a = el('a', label);
  a.href = url;
  return a;
}
function dayLabel(day) {
  return new Intl.DateTimeFormat('ja-JP', {timeZone:'UTC', month:'long', day:'numeric', weekday:'short'}).format(day);
}
function pickup(pattern, date) {
  if (!date || date < '2026-04-01' || date > '2027-03-31') return '公式表の対象期間内の日付を選んでください。';
  const start = new Date(date + 'T00:00:00Z');
  const found = [];
  for (let n = 0; n < 14 && found.length < 2; n++) {
    const day = new Date(start.getTime() + n * 86400000);
    const iso = day.toISOString().slice(0, 10);
    if (iso > '2027-03-31') break;
    if (iso >= '2026-12-31' && iso <= '2027-01-03') continue;
    if (pattern.includes('日月火水木金土'[day.getUTCDay()])) found.push(dayLabel(day));
  }
  return found.length ? '収集予定　' + found.join('、') : 'この年度の表に残りの収集日はありません。';
}
function todayInJapan() {
  const parts = new Intl.DateTimeFormat('en', {year:'numeric', month:'2-digit', day:'2-digit', timeZone:'Asia/Tokyo'}).formatToParts(new Date());
  const piece = (type) => parts.find(p => p.type === type).value;
  return [piece('year'),piece('month'),piece('day')].join('-');
}
async function directory() {
  const response = await fetch('/assets/tool-data/' + kind + '.json');
  if (!response.ok) throw new Error('data');
  const rows = await response.json();
  const query = byId('query');
  const age = byId('age');
  const available = byId('available');
  const date = byId('date');
  if (date) date.value = todayInJapan();
  const list = byId('results');
  const more = byId('more');
  let limit = 12;
  function render() {
    const terms = query.value.trim().split(/\s+/).filter(Boolean).map(normalize);
    const matched = rows.filter(row => {
      if (kind === 'nursery' && available.checked && !/[○△]/.test(row[Number(age.value)+1])) return false;
      const haystack = normalize(kind === 'schools' ? row[0]+' '+row[1]+' '+row[2] : ['questions','care'].includes(kind) ? row.slice(0,2).join(' ') : row[0]);
      return terms.every(t => haystack.includes(t));
    });
    list.replaceChildren();
    for (const row of matched.slice(0, limit)) {
      const card = el('li','');
      const heading = el('h3',row[0]);
      card.append(heading);
      if (kind === 'waste') {
        for (const [material, group] of row[2]) card.append(el('p',(material ? material + '　' : '') + group));
        if (row[3]) card.append(el('p',row[3]));
        card.append(link('出し方・例外を原表で確認（冊子' + (row[1]+18) + 'ページ）',tool.dataset.pdf+'#page='+row[1]));
      } else if (kind === 'collection') {
        card.append(el('p',row[1]+'曜日　朝8時30分まで'),el('strong',pickup(row[1],date.value)));
      } else if (kind === 'schools') {
        card.append(el('p',row[1]));
        if (row[3]) card.append(el('p','進学先の区域を確認　'+row[3]));
      } else if (kind === 'nursery') {
        const mark = row[Number(age.value)+1];
        const legend = {'○':'空き4人以上','△':'空き1～3人','×':'空きなし','斜線':'原表は斜線'};
        card.append(el('p',age.value+'歳クラス　'+mark+'　'+(legend[mark.slice(-1)] || legend[mark] || '')));
      } else if (kind === 'questions') {
        heading.replaceChildren(link(row[0],row[2]));
        card.append(el('p',row[1]));
      } else if (kind === 'care') {
        card.append(el('p','担当　'+row[1]),el('p',row[2]+' ／ '+row[4]),link(row[3],'tel:'+row[3]));
      }
      list.append(card);
    }
    byId('count').textContent = matched.length ? matched.length+'件中 '+Math.min(limit,matched.length)+'件を表示' : '該当する項目がありません。入力を短くするか、下の公式資料を確認してください。';
    more.hidden = matched.length <= limit;
  }
  for (const input of [query,age,available,date].filter(Boolean)) input.addEventListener('input',() => { limit=12; render(); });
  more.addEventListener('click',() => {limit+=36;render();});
  render();
}
function calculate() {
  const form = byId('calculator');
  const result = byId('amount');
  function render() {
    const type = byId('supply')?.value;
    if (kind === 'water') {
      byId('volume').disabled = type === 'well';
      byId('diameter').disabled = type === 'well';
    }
    if (!form.checkValidity()) {
      result.textContent='人数・使用量は入力欄の範囲内の整数で入力してください。';
      return;
    }
    if (kind === 'allowance') {
      let older = Number(byId('older').value);
      let total=0;
      const detail=[];
      for (const [id,rate,label] of [['school',10000,'3歳～高校生年代'],['young',15000,'3歳未満']]) {
        const count=Number(byId(id).value);
        const regular=Math.min(count,Math.max(2-older,0));
        total+=regular*rate+(count-regular)*30000;
        if (count) detail.push(label+' '+count+'人（うち第3子以降 '+(count-regular)+'人）');
        older+=count;
      }
      result.replaceChildren(el('strong','月額の目安　'+yen(total)),el('p',detail.join('、') || '支給対象となる年齢の入力は0人です。'));
      return;
    }
    const size=Number(byId('diameter').value);
    const volume=Number(byId('volume').value);
    const basic={13:2519,20:4191,25:5038,30:7689,40:16346,50:29205,75:84249,100:179377};
    function fee(m, base, included, rate1, rate2) {
      const first=Math.max(0,Math.min(50,m)-included);
      const second=Math.max(0,Math.min(100,m)-50);
      return base+Math.floor((first*rate1+second*rate2+Math.max(0,m-100)*2057)/10);
    }
    const sewageVolume=type==='well'?60:volume+(type==='mixed'?30:0);
    const water=type==='well'?0:fee(volume,basic[size],size<=20?16:0,1815,1936);
    const sewer=type==='water'?0:fee(sewageVolume,2200,16,1529,1947);
    result.replaceChildren(el('strong','2か月の目安　'+yen(water+sewer)),
      el('p','上水道 '+yen(water)+' ／ 公共下水道 '+yen(sewer)+(type==='water'?'':'（認定水量 '+sewageVolume+'m³）')));
  }
  form.addEventListener('submit',e=>e.preventDefault());
  form.addEventListener('input',render);
  render();
}
function checklist() {
  const selector=byId('event');
  const panels=[...tool.querySelectorAll('[data-event]')];
  const stored=id=>'fukuroi-life.v1.'+id;
  const boxes=[...tool.querySelectorAll('input[type=checkbox]')];
  for (const box of boxes) {
    try {box.checked=localStorage.getItem(stored(box.id))==='1';} catch {}
    box.addEventListener('change',()=>{
      try {
        if (box.checked) localStorage.setItem(stored(box.id),'1');
        else localStorage.removeItem(stored(box.id));
      } catch {byId('storage').textContent='このブラウザでは、チェックはページを閉じるまで有効です。';}
      render();
    });
  }
  function render() {
    for (const panel of panels) panel.hidden=panel.dataset.event!==selector.value;
    const current=panels.find(p=>!p.hidden);
    byId('progress').textContent=current.querySelectorAll(':checked').length+' / '+current.querySelectorAll('input').length+' 項目を確認';
  }
  const initial=location.hash.slice(1);
  if (panels.some(p=>p.dataset.event===initial)) selector.value=initial;
  selector.addEventListener('change',()=>{history.replaceState(null,'','#'+selector.value);render();});
  byId('clear').addEventListener('click',()=>{
    for(const box of boxes.filter(b=>!b.closest('[data-event]').hidden)) {
      box.checked=false;
      try {localStorage.removeItem(stored(box.id));} catch {}
    }
    render();
  });
  byId('print').addEventListener('click',()=>window.print());
  render();
}
function migration() {
  const paths={
    employment:'対象として掲載された求人、または指定の人材事業による就業かを確認します。',
    remote:'自分の意思で移住し、移住元の業務を移住先で週20時間以上続ける条件と証明書を確認します。',
    ties:'過去の居住・通学・勤務・寄附・親族の条件のいずれかと、移住後の就業・創業・事業承継等の両方を確認します。',
    startup:'県の起業支援金の交付決定から1年以内か、交付決定書を確認します。',
    unknown:'就業、テレワーク、関係人口、起業のどの区分に当たるか、市のブランド戦略係へ確認してください。'
  };
  const render=()=>{
    const origin=byId('origin').value;
    const residence=byId('residence').value;
    const route=byId('route').value;
    const messages=[];
    if (origin==='no' || origin==='unsure') messages.push('移住元の居住・通勤歴と、通学期間の算入可否を確認してください。');
    if (residence==='no' || residence==='unsure') messages.push('転入日からの申請期限と、継続居住の要件を確認してください。');
    if (origin==='yes' && residence==='yes') messages.push('移住元・移住先の基本条件に該当するとの入力です。');
    if (route) messages.push(paths[route]);
    byId('migration-result').textContent=messages.join(' ') || '条件を選ぶと、次に確認する事項が表示されます。';
  };
  for(const id of ['origin','residence','route']) byId(id).addEventListener('input',render);
}
if (['water','allowance'].includes(kind)) calculate();
else if (kind==='support') migration();
else if (kind==='checklist') checklist();
else if (byId('results')) directory().catch(()=>{byId('count').textContent='一覧を読み込めませんでした。下の公式資料からも確認できます。';});
