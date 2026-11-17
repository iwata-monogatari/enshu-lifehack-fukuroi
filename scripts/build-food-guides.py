"""Render the food guides from maintained venue data; no network or third-party packages."""
from pathlib import Path
from html import escape as esc
from urllib.parse import urlencode
import json,re

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'data/food-guide.json').read_text('utf8'))
HOST='https://fukuroi.enshu-lifehack.com'
BASE='/life/play-out/'
HOME=BASE+'food-shopping/'
EGG=BASE+'tamago-fuwafuwa/'
SHOP=BASE+'melon-markets/'
OUT=BASE+'family-outings/'
SOURCES=DATA['sources']

def link(text,url):return '<a href="'+esc(url,quote=True)+'">'+esc(text)+'</a>'
def refs(keys):
 return '<p class="references">出典：'+' ／ '.join(link(SOURCES[k]['label'],SOURCES[k]['url']) for k in keys.split())+'</p>'
def p(text):return '<p>'+text+'</p>'
def section(id,title,body):return '<section class="course" id="'+id+'"><h2>'+title+'</h2>'+body+'</section>'
def note(title,text,keys=''):return '<div class="trip-note"><h3>'+title+'</h3>'+p(text)+(refs(keys) if keys else '')+'</div>'
def directions(address,name,origin='袋井駅 北口',mode='walking'):
 return 'https://www.google.com/maps/dir/?'+urlencode(dict(api=1,origin=origin,destination='袋井市'+address+' '+name,travelmode=mode))
def maplink(address,name):return 'https://www.google.com/maps/search/?'+urlencode(dict(api=1,query='袋井市'+address+' '+name))
def menu():
 return '<nav class="food-nav" aria-label="食べ歩きガイド内">'+link('食べ歩きコース',HOME)+' ／ '+link('たまごふわふわの店',EGG)+' ／ '+link('メロン・特産品・直売所',SHOP)+'</nav>'

def page(path,title,intro,body,script=False):
 template=(ROOT/'tools/guide/index.html').read_text('utf8')
 head=template[:template.index('<main')]
 head=re.sub(r'<title>.*?</title>','<title>'+esc(title)+' | 袋井ライフハック</title>',head)
 head=re.sub(r'<meta name="description" content="[^"]*">','<meta name="description" content="'+esc(intro,quote=True)+'">',head)
 head=head.replace(HOST+'/tools/guide/',HOST+path).replace('/assets/living-tools.css','/assets/outings.css')
 head=head.replace('</head>','<link rel="stylesheet" href="/assets/food-guide.css"></head>')
 footer=template[template.index('<!-- PART:footer:START -->'):]
 crumb=link('ホーム','/')+' › '+link('遊び・外出',BASE)+((' › '+link('食べ歩き・買い物',HOME)) if path!=HOME else '')
 html=head+'<main class="outing food-guide"><div class="wrap"><nav aria-label="パンくず">'+crumb+'</nav><header class="outing-head"><p class="eyebrow">袋井の味を、駅から探そう</p><h1>'+esc(title)+'</h1><p class="lead">'+esc(intro)+'</p></header>'+menu()+body+p('営業時間・メニュー・運行情報の確認日：2026年11月18日。臨時休業や売切れは各店の最新案内をご確認ください。')+'</div></main>'
 if script:html+='<script defer src="/assets/food-finder.js"></script>'
 html+=footer
 dest=ROOT/path.strip('/')/'index.html';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(html.rstrip()+'\n','utf8',newline='\n')

AREAS={'station':'袋井駅から徒歩','oldtown':'宿場町・川井へ歩きを延ばす','bus':'バス＋徒歩（曜日条件あり）','taxi':'タクシーを組み合わせる'}
KINDS={'meal':'料理・食事','sweet':'菓子・アイス・乳製品','melon':'メロンを食べる・買う','market':'農産物直売所','tea':'お茶・お土産'}

def venues(rows):
 kinds=list(dict.fromkeys(r['kind'] for r in rows))
 form='<form id="food-filter" class="food-filter" hidden><div><label for="food-query">店名・食べたいもの</label><input id="food-query" type="search" placeholder="例：メロン、駅、寿司"></div><div><label for="food-kind">目的</label><select id="food-kind"><option value="">すべて</option>'+''.join('<option value="'+k+'">'+KINDS[k]+'</option>' for k in kinds)+'</select></div><div><label for="food-area">移動の組み立て</label><select id="food-area"><option value="">すべて</option>'+''.join('<option value="'+k+'">'+v+'</option>' for k,v in AREAS.items() if any(r['area']==k for r in rows))+'</select></div><button type="reset">条件を解除</button></form>'
 html=form+'<p id="food-count" role="status">'+str(len(rows))+'件</p><p id="food-empty" hidden>条件に合う場所はありません。目的や移動の条件を解除して探し直してください。</p><div class="venue-list">'
 for r in rows:
  html+='<article class="venue" id="'+r['id']+'" data-food data-kind="'+r['kind']+'" data-area="'+r['area']+'"><p class="venue-type">'+KINDS[r['kind']]+' / '+AREAS[r['area']]+'</p><h3>'+esc(r['name'])+'</h3>'+p(r['food'])
  html+='<dl><dt>場所</dt><dd>袋井市'+esc(r['address'])+'</dd><dt>営業時間</dt><dd>'+esc(r['hours'])+'</dd><dt>休み</dt><dd>'+esc(r['closed'])+'</dd></dl>'+note('車なしで行くには',r['trip'])+note('親子で立ち寄る日のメモ',r['note'])
  html+='<div class="venue-actions">'+link('電話 '+r['tel'],'tel:'+r['tel'].replace('-',''))+link('場所を地図で見る',maplink(r['address'],r['name']))
  if r['area'] in ['station','oldtown']:html+=link('袋井駅からの徒歩経路',directions(r['address'],r['name']))
  html+='</div>'+refs(r['sources'])+'</article>'
 return html+'</div>'

routes=[
 ('station','まずは駅の北側で、名物ランチと直売所','徒歩中心・小さな子と短く回る日',
  '袋井駅北口 → 観光案内所 → とれたて食楽部 → 駅前の昼食 → 絵本や屋内遊び → 駅前でお土産',
  note('10時ごろから買い物、11時台に昼食','北口正面の観光案内所で地図を受け取り、山名町の'+link('とれたて食楽部',SHOP+'#toretate')+'へ。直売所は9:00開店。駅前へ戻り、'+link('とりや茶屋',EGG+'#tori')+'・'+link('山梨屋寿司店',EGG+'#yamana')+'・'+link('美食亭 遥',EGG+'#haru')+'から昼食を一店選びます。午前の買い物を短くすれば、たまごふわふわの調理を待つ時間にも余裕を取れます。','info toretour tori yamana haru')+
  note('子どもの休憩をはさむ','昼食後は'+link('袋井図書館とカンガルーのぽっけの利用案内',OUT+'#station')+'へ。ぽっけには授乳室・ベビーベッドがあり、午後の利用時間は13:00～17:30。第2・第4水曜などの休館日があります。食事先のトイレ設備と同一視せず、移動して利用する場所として予定に入れます。','baby library')+
  note('帰りの買い物は駅前で',''+link('ふるさと銘菓いとう',EGG+'#ito')+'の半熟チーズケーキや、観光案内所のふくろい茶を候補に。ケーキは持ち歩ける時間を聞いてから購入。火曜はとれたて食楽部、木曜はいとうが定休です。各店の休みに合わせて買い物先を入れ替えましょう。','eggnews produce')),
 ('shuku','旧東海道へ歩いて、カフェのたまごふわふわ','歩ける子と、宿場町をゆっくり巡る日',
  '袋井駅北口 → 旧東海道 → まめはな・どまん中茶屋周辺 → 駅へ戻る',
  note('昼の散策と夜の食事を分けて選ぶ',''+link('お花とカフェ まめはな',EGG+'#mamehana')+'でたまごふわふわを食べる場合は、料理の提供時刻と予約を電話で確認。'+link('居酒屋 どまん中',EGG+'#domannaka')+'は通常17:30開店です。昼に立ち寄れると見込まず、日中の利用は事前に相談します。川井方面まで歩くなら'+link('Good Day Cafe',EGG+'#goodday')+'のケーキも候補です。','eggnews')+
  note('歩く距離は寄り道分も含める',''+link('袋井宿の散策ガイド',OUT+'#shuku')+'で街道の位置と休憩場所を確認。駅前のランチだけのコースより歩く距離が増えます。幼児連れは一店を目的地にして折り返すなど、短く組み替えましょう。')),
 ('melon','平日の循環バスでクラウンメロンを味わう','堀越のメロー静岡へ・土日祝は配車を使う',
  '袋井駅北口2番 → 北部循環線52右回り → 県営住宅入口 → 徒歩でメロー静岡 → 51左回りで駅へ',
  note('半玉を食べるか、ジュースで一息つくか',''+link('メロー静岡 袋井本店',SHOP+'#mero')+'では、種を取った半玉を店内で食べられます。ソフトクリームやジュースにも店内飲食スペースの案内があります。丸ごと購入すると荷物が増えるため、先に店内で味わい、贈答品は発送も含めて店に相談する組み立てが便利です。','mero merocutdetail merojuicedetail merosoftdetail')+
  note('平日の往復例を先に決める','市の北部循環線時刻表では、52右回りは袋井駅北口10:05発 → 県営住宅入口10:16着。帰りの51左回りは県営住宅入口12:24発 → 袋井駅北口12:35着です。停留所から店舗までの徒歩と待ち時間もこの間に確保します。'+link('停留所から店舗への徒歩経路',directions('堀越3丁目5-1','メロー静岡 袋井本店','袋井市 県営住宅入口 バス停'))+'を出発前に開き、帰りは51左回りの乗車位置を確認してください。','north')+
  note('休日は同じバスが走らない','フーちゃん号は平日のみ、1乗車200円。未就学児は無料で引率者の同乗が必要です。大人の往復バス代は400円で、飲食代は別。土日祝と12月29日～1月3日は運休です。休日にメロンを目的にするなら往復のタクシーを予約し、電車の時間も伝えます。','bus')+
  note('隣の御膳は予約条件に注意','袋井観光センターの「袋井どまんなか御膳」は団体限定・要予約。家族が当日注文できる昼食としては予定に入れず、'+link('駅前の食事処',EGG+'#tori')+'などと組み合わせます。','eggnews')),
 ('north','可睡齋のアイス、月見の里の野菜と遊び場','北へ向かう路線バスで行き先を選ぶ',
  '袋井駅北口1番 → 可睡齋入口 または 山梨方面 → おやつ・買い物 → 袋井駅北口',
  note('お寺とアイスの日','可睡齋入口から歩いて門前の'+link('じぇらーとげんき',EGG+'#genki')+'へ。たまごふわふわアイス盆は、温かい卵料理と別の創作メニューです。店の現行案内は10:00～17:00、水・木曜定休（祝日は営業）。'+link('遠州三山の徒歩・設備案内',OUT+'#temples')+'も合わせて確認できます。','genki eggnews busouting')+
  note('野菜と公園を楽しむ日','山梨方面では'+link('新鮮市 月見の里ひろば',SHOP+'#tsukimi')+'と'+link('月見の里公園・学遊館',OUT+'#tsukimi')+'を組み合わせられます。市場は16:00閉店・水曜休み、学遊館は木曜休館が基本です。学遊館には授乳・おむつ替えの案内があります。市場と学遊館は別の敷地なので、停留所を含めた歩く区間も確認しましょう。','tsukimarket tsuki tsukifaq')+
  note('二か所を詰め込まず、帰り便を選んでおく','秋葉バスには土曜・日祝の時刻表もあります。往路と復路で標柱・方面が異なるので、停留所別の時刻表で袋井駅方面を選択。幼児連れで可睡齋と月見の里の両方へ回る場合は、次のバスまでの待ち時間を含めて判断します。','timetable bustime busnow')),
 ('south','土曜の浅羽で、直売所と図書館へ','黒大豆の味噌・季節の野菜を買う日',
  '袋井駅南口 → 秋葉中遠線 → 浅羽支所入口 → あさば新鮮市 → 図書館・資料館 → 駅へ',
  note('市場は日曜休み、土曜の午前が組みやすい',''+link('あさば新鮮市',SHOP+'#asaba')+'は9:00～15:00、日曜休み。'+link('浅羽の図書館・資料館・復元機関車コース',OUT+'#asaba')+'に組み込むなら、土曜に買い物を先に済ませる案があります。黒大豆の味噌など常温で持ち歩けるかは表示を確認し、生鮮品を買う日は保冷袋を用意します。','asaba museumroute')+
  note('どんどこあさばは別の立ち寄り先',''+link('おかって市場',SHOP+'#dondo')+'は浅岡地区。秋葉中遠線の浅岡方面と徒歩で行く候補で、浅羽支所の前にある店ではありません。公式には市場9:00～17:00、併設レストランは休業の案内。市場での買い物と別の昼食場所を組み合わせましょう。','dondo south')+
  note('駅では南口に出る','浅羽方面は袋井駅南口の乗車です。休日は秋葉中遠線の土日祝ダイヤを使用し、平日だけの市のメローバスと取り違えないようにします。帰りの浅羽支所入口や浅岡から袋井駅南口への便を先に確認します。','timetable bustime south')),
 ('taxi','だんご・茶室・農場カフェを目的地にする','駅からタクシーを組み合わせる小旅行',
  '袋井駅・愛野駅 → 予約したタクシー → 目的地で食事や買い物 → 迎車で駅へ',
  note('法多山でお茶付きのだんご休憩',''+link('法多山の厄除だんご',SHOP+'#dango')+'は店内飲食と土産販売を選べます。愛野駅からの徒歩は30～40分で歩道のない箇所があるため、幼児連れは配車を組み合わせる案も。愛野駅にタクシーは常駐していません。門前から茶屋までも歩くので、'+link('参道・境内の設備',OUT+'#temples')+'を確認します。','dango hattabus')+
  note('土日の茶室と、南部のメロンカフェ',''+link('茶ピア',SHOP+'#chapia')+'は袋井駅からタクシー約10分。茶室は土日営業、直売所は火曜定休です。'+link('fruit cafe NiJi',SHOP+'#niji')+'も通常は土日祝営業。二つを必ず回る行程ではなく、茶室で過ごすか、農場のメロンスイーツを味わうかで目的地を選びましょう。','chapiafac nijtour')+
  note('牧場スイーツは季節と場所を確認',''+link('Motaの店',SHOP+'#mota')+'は市北部、'+link('デンマーク牧場のグリーングラス',SHOP+'#denmark')+'は南部にあります。グリーングラスの売店は土日祝営業で12月～3月休業。冬の行程では売店の利用を見込まないようにします。','mota denmilk')+
  note('帰りも同時に手配する','配車時に目的地、帰りの希望時刻、子どもの人数、ベビーカーの有無を伝えます。法多山公式が案内する連絡先は、交通タクシー '+link('0538-42-2251','tel:0538422251')+'、袋井タクシー '+link('0538-42-2131','tel:0538422131')+'。市の登録制デマンドタクシーは対象地区住民向けの制度なので、観光の配車は一般のタクシーへ相談します。','hattabus taxi')),
]

nav='<section class="choose" id="choose"><h2>今日の移動に合うコースを選ぶ</h2><ul>'
for id,title,short,_,_ in routes:nav+='<li><a href="#'+id+'"><strong>'+title+'</strong><span>'+short+'</span></a></li>'
nav+='</ul>'+p('コースは公式の営業時間・交通案内をもとにした編集上の提案です。徒歩経路は地図で確認できます。子どもの歩く速さや休憩時間に合わせ、一店を目的にする短い回り方にもできます。')+'</section>'
body=nav
for id,title,_,journey,content in routes:body+=section(id,title,p(esc(journey)).replace('<p>','<p class="journey">',1)+content+link('コース選びに戻る ↑','#choose'))
body+=section('with-kids','子連れで食べ歩く日の組み立て',note('昼の食事は一店を決めてから','予約の電話では「たまごふわふわを食べたい」「大人と子どもの人数・年齢」「到着時刻」を先に伝えると相談しやすくなります。予約の要否、子ども用いす、ベビーカーの置き場、取り分けや食べられる量を確認してください。店ごとの乳幼児設備は、公表が確認できたものだけ紹介しています。')+note('食べる時間と持ち帰る時間を分ける','熱い料理は店内で落ち着いて食べ、冷蔵が必要なケーキや乳製品は買い物の最後に。保冷剤、保冷袋、消費期限は商品表示や店の説明を確認します。お茶や常温の加工品は電車の荷物に収めやすい候補です。')+note('雨の日は駅周辺に縮める','駅前でランチとお土産を選び、屋内の'+link('図書館・子育て支援センター',OUT+'#station')+'へ。晴れていて歩きたい日は'+link('公園検索',BASE+'park-finder/')+'から寄り道を選べます。市場やカフェを、授乳室が必ずある場所としては案内していません。'))
body+=section('more','袋井の味をもう少し知る',note('名物料理と特産品を選び分ける','たまごふわふわは、卵とだしを使う江戸時代の料理を再現したもの。店ごとに具材や仕立てが異なります。クラウンメロン、ふくろい茶、米、いちごなどの農産物は市の紹介から生産地の特徴を調べられます。お土産には産地表示と保存方法も確認しましょう。','egg produce')+note('おはたき肉巻きを見かけたら','うるち米の餅「おはたき」に豚肉を巻いて焼く、浅羽地域から生まれた食べ物です。観光協会はイベント出店を紹介しています。掲載される浅羽町商工会の住所・営業時間は問い合わせ先のものなので、常設の飲食店として向かわず、販売予定を確認して楽しみましょう。','ohataki'))
page(HOME,'袋井の食べ歩き・買い物ガイド｜子連れ・車なしで巡る','たまごふわふわの昼食、クラウンメロンのおやつ、直売所のお土産。袋井駅から歩く日、バスに乗る日、タクシーを組み合わせる日で、食べる場所と帰り方を一緒に選べます。',body)

body=section('choose','温かい料理と、甘いアレンジを選び分ける',p('観光協会が2026年11月5日に公開した「味わいマップ」の提供店を比較できます。だしと卵の料理を食べたい日は「料理・食事」、アイスやケーキなら「菓子・アイス」を選んでください。提供時間や予約条件は店ごとに異なります。')+refs('eggnews egg')+p(link('駅前でランチとお土産を組み合わせる',HOME+'#station')+' ／ '+link('旧東海道へ歩くコース',HOME+'#shuku')))
body+=section('restaurants','たまごふわふわを楽しめる店',venues(DATA['eggshops']))
body+=section('faq','予約前によくある疑問',note('料理なら、どの店でも同じ材料？','基本は卵とだしですが、具材は店ごとに違います。和の湯はとらふぐ入り、遥はすっぽん入りの案内があります。食べられない食材がある場合は、卵だけと思い込まず、だしや具も店に確認してください。','eggnews yawa')+note('昼に予約なしで必ず食べられる？','通常営業の食事処でも売切れや仕込みの都合があります。とくに目当ての一品がある日は電話で提供と予約の要否を確認。袋井観光センターの御膳は団体限定・要予約、どまん中は通常夜営業です。','eggnews')+note('ケーキを買ってすぐ電車に乗りたい','袋井駅北口近くのいとうが候補。木曜休みです。保冷できる時間を店頭で聞いてから購入し、駅へ戻るルートを確認しましょう。','eggnews'))
page(EGG,'袋井宿たまごふわふわ｜提供店・予約・駅からの行き方','駅前で温かいたまごふわふわを食べる、お寺の門前でアイスを味わう、ケーキを持ち帰る。公式の提供店案内をもとに、食べたいものと移動方法で店を選べます。',body,True)

body=section('choose','食べるメロン、贈るメロン、日々の買い物',p('クラウンメロンを店内で食べるならメロー静岡、農場カフェのスイーツならNiJi。駅から歩く買い物はとれたて食楽部と観光案内所、バスの寄り道は月見の里や浅羽の市場が候補です。農場カフェのメロンは、すべてをクラウンメロンの銘柄として扱っていません。')+p(link('平日のメロン往復バス例',HOME+'#melon')+' ／ '+link('土曜の浅羽市場コース',HOME+'#south')+' ／ '+link('駅前のたまごふわふわ・ケーキ',EGG)))
body+=section('shops','メロン・お茶・直売所・甘味を探す',venues(DATA['markets']))
body+=section('gifts','持ち帰るものから、お土産を選ぶ',note('クラウンメロンを丸ごと贈る','市は温室メロンを主要農産物として紹介し、クラウンメロンを扱う店の一覧を掲載しています。専門店では、食べる予定日と持ち運び・発送の希望を伝えて、熟度や価格を相談しましょう。店内の半玉と通販送料込みの商品は価格が別なので、店頭用の価格を確認してください。','produce merocutdetail')+note('お茶・米・味噌なら','軽く持ち帰るなら観光案内所のお茶、銘柄を見比べるなら茶ピアが候補。袋井は米も作る地域で、直売所の米や野菜は産地・品種を売場で選べます。浅羽の黒大豆味噌や月見の里の加工品は、保存方法と袋の大きさも見て決めましょう。','info chapiafac produce asaba tsukimarket')+note('営業情報の基準','市の農産物ページは2022年更新のため、地域の特産品と取扱候補を把握する資料として使用し、時間は運営者などの現行案内を優先しました。どんどこあさばのレストラン休業、茶ピアの茶室の土日営業、観光案内所の2026年4月の時間変更を反映しています。','produce dondo chapiafac info'))
page(SHOP,'袋井のクラウンメロン・特産品・直売所ガイド','クラウンメロンをその場で味わう店、ふくろい茶を選べる売場、野菜や加工品の直売所を比較。営業時間と休み、駅からの移動、親子で立ち寄る日のポイントをまとめました。',body,True)
print('Rendered 3 food guides from data/food-guide.json')
