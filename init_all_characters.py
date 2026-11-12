# -*- coding: utf-8 -*-
"""
ポケモン + 妖怪ウォッチ + ドラゴンクエスト + スーパーマリオ
の4大ゲームモード対応 総合データベース構築スクリプト
"""
import sqlite3
import os
import requests
import re
import csv
import io
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "pokemon_quiz.db")
STATIC_IMG_DIR = os.path.join(os.path.dirname(__file__), "static", "images")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def download_wiki_file(wiki_api, file_title, referer_domain, out_path):
    """MediaWiki APIから画像URLを取得してReferer付きでダウンロード"""
    if os.path.exists(out_path) and os.path.getsize(out_path) > 2000:
        return True
    try:
        params = {
            'action': 'query',
            'titles': f'File:{file_title}',
            'prop': 'imageinfo',
            'iiprop': 'url',
            'format': 'json'
        }
        headers = dict(HEADERS)
        headers['Referer'] = f'https://{referer_domain}/'
        r = requests.get(wiki_api, params=params, headers=headers, timeout=10)
        pages = r.json().get('query', {}).get('pages', {})
        for _, page in pages.items():
            info = page.get('imageinfo')
            if info and len(info) > 0:
                img_url = info[0].get('url')
                # ダウンロード
                ir = requests.get(img_url, headers=headers, timeout=15)
                if ir.status_code == 200 and len(ir.content) > 1000:
                    os.makedirs(os.path.dirname(out_path), exist_ok=True)
                    with open(out_path, 'wb') as f:
                        f.write(ir.content)
                    print(f"  [OK] ダウンロード成功: {os.path.basename(out_path)} ({len(ir.content)} bytes)")
                    return True
    except Exception as e:
        print(f"  [WARN] {file_title} のダウンロード失敗: {e}")
    return False

# =========================================================================
# キャラクターデータ定義
# =========================================================================

# --- 1. スーパーマリオ ---
MARIO_CHARACTERS = [
    ("mario", "マリオ", "Mario", "ヒーロー", "配管工", "ヒゲと赤い帽子がトレードマークのスーパースター！", "Super_Mario_Party_Mario.png", "mario.fandom.com"),
    ("luigi", "ルイージ", "Luigi", "ヒーロー", "弟", "少し臆病だがジャンプ力は兄以上！オバケが大の苦手な緑の弟。", "Super_Mario_Party_Luigi.png", "mario.fandom.com"),
    ("peach", "ピーチ", "Princess Peach", "キノコ王国", "プリンセス", "キノコ王国のお姫様。よくクッパにさらわれるが気品あふれるヒロイン。", "Super_Mario_Party_Peach.png", "mario.fandom.com"),
    ("bowser", "クッパ", "Bowser", "クッパ軍団", "大魔王", "トゲトゲの甲羅と炎の息を持つ大魔王！マリオ永遠のライバル。", "Super_Mario_Party_Bowser.png", "mario.fandom.com"),
    ("yoshi", "ヨッシー", "Yoshi", "相棒", "恐竜", "背中にマリオを乗せて大活躍する長い舌の食いしん坊な恐竜。", "Super_Mario_Party_Yoshi.png", "mario.fandom.com"),
    ("toad", "キノピオ", "Toad", "キノコ王国", "お世話役", "頭の赤い水玉キノコが可愛いピーチ姫のお世話役。", "Super_Mario_Party_Toad.png", "mario.fandom.com"),
    ("wario", "ワリオ", "Wario", "ライバル", "怪力", "ニンニクとお金が大好物の下品でパワフルな黄色い男！", "Super_Mario_Party_Wario.png", "mario.fandom.com"),
    ("waluigi", "ワルイージ", "Waluigi", "ライバル", "長身", "ルイージをライバル視するずる賢い紫の長身男。", "Super_Mario_Party_Waluigi.png", "mario.fandom.com"),
    ("daisy", "デイジー", "Princess Daisy", "サラサ・ランド", "プリンセス", "元気いっぱいで明るいサラサ・ランドのお姫様！", "Super_Mario_Party_Daisy.png", "mario.fandom.com"),
    ("rosalina", "ロゼッタ", "Rosalina", "宇宙", "星の母", "ほうき星の天文台でチコたちと暮らす謎多き美女。", "Super_Mario_Party_Rosalina.png", "mario.fandom.com"),
    ("bowser_jr", "クッパJr.", "Bowser Jr.", "クッパ軍団", "御曹司", "クッパの愛息。クラウンに乗って悪巧みをする。", "Super_Mario_Party_Bowser_Jr.png", "mario.fandom.com"),
    ("donkey_kong", "ドンキーコング", "Donkey Kong", "コング", "怪力ゴリラ", "赤いネクタイを締めたジャングルの王者！バナナが大好物。", "Super_Mario_Party_Donkey_Kong.png", "mario.fandom.com"),
    ("diddy_kong", "ディディーコング", "Diddy Kong", "コング", "チンパンジー", "赤い帽子とシャツを着たドンキーの軽快な相棒。", "Super_Mario_Party_Diddy_Kong.png", "mario.fandom.com"),
    ("goomba", "クリボー", "Goomba", "クッパ軍団", "きのこ", "キノコ王国を裏切ったシイタケのようなザコ敵。踏まれると倒れる。", "Super_Mario_Party_Goomba.png", "mario.fandom.com"),
    ("koopa_troopa", "ノコノコ", "Koopa Troopa", "クッパ軍団", "カメ", "甲羅を背負ったカメ。踏むと甲羅に閉じこもる。", "Super_Mario_Party_Koopa_Troopa.png", "mario.fandom.com"),
    ("boo", "テレサ", "Boo", "オバケ", "シャイ", "恥ずかしがり屋のおばけ。顔を合わせると手で顔を隠す。", "Super_Mario_Party_Boo.png", "mario.fandom.com"),
    ("piranha_plant", "パックンフラワー", "Piranha Plant", "クッパ軍団", "食虫植物", "土管から急に顔を出す鋭いキバの危険な植物。", "Piranha_Plant_-_Super_Mario_Party.png", "mario.fandom.com"),
    ("bob_omb", "ボムへい", "Bob-omb", "クッパ軍団", "歩く爆弾", "ぜんまい仕掛けで歩き回り、導火線に火がつくと大爆発！", "Bob-omb_Super_Mario_Party.png", "mario.fandom.com"),
    ("shy_guy", "ヘイホー", "Shy Guy", "クッパ軍団", "仮面", "白いお面をかぶった正体不明の可愛いキャラクター。", "Super_Mario_Party_Shy_Guy.png", "mario.fandom.com"),
    ("kamek", "カメック", "Kamek", "クッパ軍団", "魔法使い", "ホウキに乗って魔法を放つクッパ軍団の知恵袋。", "Super_Mario_Party_Kamek.png", "mario.fandom.com"),
    ("thwomp", "ドッスン", "Thwomp", "トラップ", "岩石", "天井で待ち構え、近づくとドスンと落下して押しつぶす岩。", "Thwomp_NSMBU.png", "mario.fandom.com"),
    ("chain_chomp", "ワンワン", "Chain Chomp", "クッパ軍団", "鉄球", "鎖につながれた凶暴な鉄球。噛みつき攻撃をしてくる。", "Chain_Chomp_Mario_Party_Superstars.png", "mario.fandom.com"),
    ("bullet_bill", "キラー", "Bullet Bill", "クッパ軍団", "砲弾", "大砲から一直線に飛んでくる目つきの鋭い黒い弾丸。", "Bullet_Bill_NSMBU.png", "mario.fandom.com"),
    ("toadette", "キノピコ", "Toadette", "キノコ王国", "女の子", "ピンクのツインテールがトレードマークの元気な女の子。", "Super_Mario_Party_Toadette.png", "mario.fandom.com"),
    ("birdo", "キャサリン", "Birdo", "恐竜", "リボン", "頭のピンクのリボンがチャームポイント。口から卵を発射する。", "Birdo_MPS.png", "mario.fandom.com"),
    ("spiny", "トゲゾー", "Spiny", "クッパ軍団", "トゲカメ", "背中に鋭いトゲが生えており、上から踏むとダメージを受ける。", "Spiny_NSMBU.png", "mario.fandom.com")
]

# --- 2. ドラゴンクエスト ---
DQ_CHARACTERS = [
    ("slime", "スライム", "Slime", "スライム系", "代表モンスター", "シリーズの顔！愛嬌のある水滴のような形の青いモンスター。", "Slime_Artwork.png", "dragonquest.fandom.com"),
    ("she_slime", "スライムベス", "She-slime", "スライム系", "オレンジ", "スライムの近縁種。赤オレンジ色で少しだけ強い。", "She-slime_Artwork.png", "dragonquest.fandom.com"),
    ("metal_slime", "メタルスライム", "Metal Slime", "スライム系", "経験値大量", "銀色に輝くスライム。倒すと大量の経験値がもらえるがすぐ逃げる。", "Metal_slime_Artwork.png", "dragonquest.fandom.com"),
    ("liquid_metal_slime", "はぐれメタル", "Liquid Metal Slime", "スライム系", "液体メタル", "溶けた銀のようにドロドロした姿。すばやさが非常に高い。", "Liquid_metal_slime_Artwork.png", "dragonquest.fandom.com"),
    ("metal_king_slime", "メタルキング", "Metal King Slime", "スライム系", "メタルの王", "メタルスライムが合体して王冠を被った経験値の最高峰！", "Metal_king_slime_Artwork.png", "dragonquest.fandom.com"),
    ("king_slime", "キングスライム", "King Slime", "スライム系", "王冠スライム", "スライムが8匹合体して誕生した巨大なスライムの王様。", "King_slime_Artwork.png", "dragonquest.fandom.com"),
    ("healslime", "ホイミスライム", "Healslime", "スライム系", "触手回復", "空中をふわふわ漂い、触手でホイミを唱えて仲間を助ける。", "Healslime_Artwork.png", "dragonquest.fandom.com"),
    ("dracky", "ドラキー", "Dracky", "鳥系", "コウモリ", "黄色い大きな目とコウモリのような羽を持つ序盤のモンスター。", "Dracky_Artwork.png", "dragonquest.fandom.com"),
    ("ghost", "ゴースト", "Ghost", "ゾンビ系", "おばけ", "頭に三角頭巾をつけた小さなおばけ。メラを唱えてくる。", "Ghost_Artwork.png", "dragonquest.fandom.com"),
    ("stump_chump", "きりかぶおばけ", "Stump Chump", "植物系", "切り株", "長い年月を生きた木の切り株に魂が宿ったモンスター。", "Stump_chump_Artwork.png", "dragonquest.fandom.com"),
    ("spookstool", "おばけキノコ", "Spookstool", "植物系", "キノコ", "大きな笠を持つキノコ。甘い息を吐いて眠らせてくる。", "Spookstool_Artwork.png", "dragonquest.fandom.com"),
    ("hammerhood", "おおきづち", "Hammerhood", "魔獣系", "モグラ", "大きな木槌を持った毛むくじゃらのモンスター。痛恨の一撃に注意！", "Hammerhood_Artwork.png", "dragonquest.fandom.com"),
    ("platypunk", "ももんじゃ", "Platypunk", "魔獣系", "カモノハシ", "尻尾を振って愛嬌を振りまくカモノハシのような魔獣。", "Platypunk_Artwork.png", "dragonquest.fandom.com"),
    ("restless_armour", "さまようよろい", "Restless Armour", "物質系", "亡霊の鎧", "魂が宿った中身のない鎧。ホイミスライムを呼び出すことも。", "Restless_armour_Artwork.png", "dragonquest.fandom.com"),
    ("golem", "ゴーレム", "Golem", "物質系", "レンガの巨人", "土やレンガを固めて作られた巨大な番人。妖精の笛で眠る。", "Golem_Artwork.png", "dragonquest.fandom.com"),
    ("killing_machine", "キラーマシン", "Killing Machine", "物質系", "殺人機械", "古代文明が造り出した冷徹な殺人兵器。弓と剣の2回攻撃。", "Killing_machine_Artwork.png", "dragonquest.fandom.com"),
    ("bomboulder", "ばくだんいわ", "Bomboulder", "物質系", "自爆岩", "顔が刻まれた不気味な岩。瀕死になるとメガンテで自爆する！", "Bomboulder_Artwork.png", "dragonquest.fandom.com"),
    ("mimic", "ミミック", "Mimic", "物質系", "宝箱トラップ", "宝箱に化けた凶悪モンスター。ザキやあまいいきを放つ。", "Mimic_Artwork.png", "dragonquest.fandom.com"),
    ("green_dragon", "ドラゴン", "Green Dragon", "ドラゴン系", "初代中ボス", "初代でローラ姫を見張っていた緑色の巨躯。火の息を吐く。", "Green_dragon_Artwork.png", "dragonquest.fandom.com"),
    ("chimaera", "キメラ", "Chimaera", "鳥系", "合成魔獣", "ハゲタカの体にヘビの尾を持つ鳥系モンスター。火の息を吐く。", "Chimaera_Artwork.png", "dragonquest.fandom.com"),
    ("dragonlord", "りゅうおう", "Dragonlord", "魔王", "初代ボス", "『もし わしの 味方になれば 世界の半分を やろう』と誘惑する巨竜の王。", "Dragonlord_true_form_Artwork.png", "dragonquest.fandom.com"),
    ("malroth", "シドー", "Malroth", "破壊神", "DQ2ボス", "邪教の生贄によって召喚された6本腕の巨大な破壊神！", "Malroth_Artwork.png", "dragonquest.fandom.com"),
    ("zoma", "ゾーマ", "Zoma", "大魔王", "DQ3ボス", "『なにゆえ もがき 生きるのか』すべてを滅ぼす大魔王。闇の衣を纏う。", "Zoma_Artwork.png", "dragonquest.fandom.com"),
    ("psaro", "デスピサロ", "Psaro", "魔族の王", "DQ4ボス", "進化の秘法を使って次々と形態を変える悲劇の魔族の王。", "Psaro_the_Manslayer_Artwork.png", "dragonquest.fandom.com"),
    ("estark", "エスターク", "Estark", "地獄の帝王", "裏ボス", "古代に封印された地獄の帝王。目覚めたばかりで記憶がない。", "Estark_Artwork.png", "dragonquest.fandom.com")
]

# --- 3. 妖怪ウォッチ ---
YOKAI_CHARACTERS = [
    ("jibanyan", "ジバニャン", "Jibanyan", "プリチー族", "地縛霊ネコ", "トラックにはねられて死んだネコの地縛霊。『ひゃくれつ肉球』が必殺技！", "Jibanyan.png", "yokaiwatch.fandom.com"),
    ("komasan", "コマさん", "Komasan", "プリチー族", "狛犬", "田舎の神社からやってきた狛犬妖怪。口癖は『もんげー！』ソフトクリームが大好き。", "Komasan.png", "yokaiwatch.fandom.com"),
    ("komajiro", "コマじろう", "Komajiro", "プリチー族", "狛犬弟", "コマさんの双子の弟。都会に馴染むのが早くスマホを使いこなすズラ！", "Komajiro.png", "yokaiwatch.fandom.com"),
    ("whisper", "ウィスパー", "Whisper", "ニョロロン族", "妖怪執事", "主人公に妖怪ウォッチを授けた執事妖怪。知識は妖怪パッド頼り。", "Whisper.png", "yokaiwatch.fandom.com"),
    ("bushinyan", "ブシニャン", "Bushinyan", "イサマシ族", "レジェンド", "鎧兜を身にまとったネコ妖怪のレジェンド！天下無双の剣術を誇る。", "Shogunyan.png", "yokaiwatch.fandom.com"),
    ("robonyan", "ロボニャン", "Robonyan", "ゴーケツ族", "サイボーグ", "未来のテクノロジーで作られたサイボーグネコ妖怪。『アイルビーバック！』", "Robonyan.png", "yokaiwatch.fandom.com"),
    ("hovernyan", "フユニャン", "Hovernyan", "イサマシ族", "熱血ネコ", "青いマントを羽織った熱血で頼れるネコ妖怪。『ど根性ストレート』を放つ！", "Hovernyan.png", "yokaiwatch.fandom.com"),
    ("baddinyan", "ワルニャン", "Baddinyan", "イサマシ族", "ツッパリ", "トゲトゲのリーゼントと学ランを着たツッパリ不良ネコ妖怪。", "Baddinyan.png", "yokaiwatch.fandom.com"),
    ("thornyan", "トゲニャン", "Thornyan", "プリチー族", "トゲネコ", "風邪をこじらせて全身から鋭いトゲが生えてしまったネコ妖怪。", "Thornyan.png", "yokaiwatch.fandom.com"),
    ("orochi", "オロチ", "Venoct", "ニョロロン族", "エリート", "龍のマフラーを首に巻いたクールで強力なエリート妖怪。", "Venoct.png", "yokaiwatch.fandom.com"),
    ("kyubi", "キュウビ", "Kyubi", "フシギ族", "九尾の狐", "9本の尾を持つ高貴なキツネ妖怪。美しい人間の少年に化けることも。", "Kyubi.png", "yokaiwatch.fandom.com"),
    ("tattletell", "バクロ婆", "Tattletell", "フシギ族", "暴露", "とりつかれると胸に秘めた秘密を大声で暴露してしまうおばあさん妖怪。", "Tattletell.png", "yokaiwatch.fandom.com"),
    ("manjimutt", "じんめん犬", "Manjimutt", "ブキミー族", "人面犬", "人間の顔を持つ犬。女性にモテたいがために悪戦苦闘する哀愁の妖怪。", "Manjimutt.png", "yokaiwatch.fandom.com"),
    ("happierre", "ホノボーノ", "Happierre", "ポカポカ族", "太陽", "とりつかれると喧嘩中の夫婦も仲直り。まわりをほんわかさせる妖怪。", "Happierre.png", "yokaiwatch.fandom.com"),
    ("dismarelda", "ドンヨリーヌ", "Dismarelda", "ブキミー族", "どんより", "部屋や空気をどんより重く険悪にしてしまう巨大なスライム状の妖怪。", "Dismarelda.png", "yokaiwatch.fandom.com"),
    ("hungramps", "ひも爺", "Hungramps", "ポカポカ族", "空腹", "とりつかれると猛烈にお腹が空いて何でも食べたくなってしまうおじいさん妖怪。", "Hungramps.png", "yokaiwatch.fandom.com"),
    ("fidgephant", "モレゾウ", "Fidgephant", "ゴーケツ族", "トイレ我慢", "鼻から水を噴射し、とりついた人に猛烈な尿意をもたらすゾウの妖怪。", "Fidgephant.png", "yokaiwatch.fandom.com"),
    ("usapyon", "ＵＳＡピョン", "USApyon", "ウスラカゲ族", "宇宙ウサギ", "宇宙服を着たフェレット妖怪。怒るとベイダーモードに変身するダニ！", "USApyon.png", "yokaiwatch.fandom.com"),
    ("enma", "エンマ大王", "Lord Enma", "エンマ族", "妖魔界の王", "妖魔界を統べる若き絶対王者！圧倒的な霊力とカリスマ性を持つ。", "Lord_Enma.png", "yokaiwatch.fandom.com"),
    ("zazel", "ぬらりひょん", "Zazel", "エンマ族", "評議会議長", "妖魔界の評議会議長。エンマ大王に仕える忠義に厚い側近。", "Zazel.png", "yokaiwatch.fandom.com"),
    ("blizzaria", "ふぶき姫", "Blizzaria", "プリチー族", "雪女の姫", "冷気を操る美しい妖怪。夏でもまわりを凍りつかせる。", "Blizzaria.png", "yokaiwatch.fandom.com"),
    ("frostina", "ゆきおんな", "Frostina", "プリチー族", "雪女", "雪山に現れる小さな女の子の妖怪。触れたものを凍らせてしまう。", "Frostina.png", "yokaiwatch.fandom.com"),
    ("noway", "ムリカベ", "Noway", "ゴーケツ族", "拒絶の壁", "頼み事をされても『ム〜リ〜！』と両手をクロスして絶対に断る巨大な壁。", "Noway.png", "yokaiwatch.fandom.com"),
    ("snartle", "なまはげ", "Snartle", "イサマシ族", "信号無視", "横断歩道の信号を無視して渡ると現れて襲いかかってくる恐怖の妖怪！", "Snartle.png", "yokaiwatch.fandom.com")
]

def setup():
    print("============================================================")
    print("4大ゲームモード（ポケモン・妖怪・ドラクエ・マリオ）DB構築開始")
    print("============================================================")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. 総合 characters テーブルの作成
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,         -- 'pokemon', 'yokai', 'dq', 'mario'
        identifier TEXT NOT NULL,
        name_ja TEXT NOT NULL,
        name_en TEXT NOT NULL,
        form_type TEXT DEFAULT 'normal',
        attribute1 TEXT NOT NULL,
        attribute2 TEXT,
        genus TEXT,
        flavor_text TEXT,
        image_url TEXT NOT NULL,
        generation INTEGER DEFAULT 1,
        aliases TEXT
    );
    """)

    # 2. 既存の pokemons テーブルからポケモン1,158匹を characters テーブルへ同期/移行
    cursor.execute("SELECT count(*) FROM characters WHERE category = 'pokemon'")
    pokemon_exist = cursor.fetchone()[0]
    if pokemon_exist == 0:
        print("ポケモンデータを characters テーブルへ移行中...")
        cursor.execute("""
        INSERT INTO characters (category, identifier, name_ja, name_en, form_type, attribute1, attribute2, genus, flavor_text, image_url, generation, aliases)
        SELECT 'pokemon', identifier, name_ja, name_en, form_type, type1, type2, genus, flavor_text, image_url, generation, aliases
        FROM pokemons;
        """)
        conn.commit()
        print(f"  [OK] ポケモン移行完了！")

    # 3. マリオ キャラクターの画像ダウンロードとDB登録
    print("\n--- マリオ キャラクター登録中 ---")
    for item in MARIO_CHARACTERS:
        ident, name_ja, name_en, attr1, genus, flavor, wiki_file, domain = item
        out_rel = f"/images/mario/{ident}.png"
        out_abs = os.path.join(STATIC_IMG_DIR, "mario", f"{ident}.png")
        
        # ダウンロード試行
        wiki_api = f"https://{domain}/api.php"
        download_wiki_file(wiki_api, wiki_file, domain, out_abs)
        
        # 登録 (重複チェック)
        cursor.execute("SELECT id FROM characters WHERE category = 'mario' AND identifier = ?", (ident,))
        row = cursor.fetchone()
        aliases = f"{name_ja},{name_en.lower()}"
        if not row:
            cursor.execute("""
            INSERT INTO characters (category, identifier, name_ja, name_en, form_type, attribute1, attribute2, genus, flavor_text, image_url, generation, aliases)
            VALUES ('mario', ?, ?, ?, 'normal', ?, NULL, ?, ?, ?, 1, ?)
            """, (ident, name_ja, name_en, attr1, genus, flavor, out_rel, aliases))
        else:
            cursor.execute("""
            UPDATE characters SET name_ja = ?, name_en = ?, attribute1 = ?, genus = ?, flavor_text = ?, image_url = ?, aliases = ?
            WHERE id = ?
            """, (name_ja, name_en, attr1, genus, flavor, out_rel, aliases, row[0]))

    # 4. ドラクエ キャラクターの画像ダウンロードとDB登録
    print("\n--- ドラクエ キャラクター登録中 ---")
    for item in DQ_CHARACTERS:
        ident, name_ja, name_en, attr1, genus, flavor, wiki_file, domain = item
        out_rel = f"/images/dq/{ident}.png"
        out_abs = os.path.join(STATIC_IMG_DIR, "dq", f"{ident}.png")
        
        wiki_api = f"https://{domain}/api.php"
        download_wiki_file(wiki_api, wiki_file, domain, out_abs)
        
        cursor.execute("SELECT id FROM characters WHERE category = 'dq' AND identifier = ?", (ident,))
        row = cursor.fetchone()
        aliases = f"{name_ja},{name_en.lower()}"
        if not row:
            cursor.execute("""
            INSERT INTO characters (category, identifier, name_ja, name_en, form_type, attribute1, attribute2, genus, flavor_text, image_url, generation, aliases)
            VALUES ('dq', ?, ?, ?, 'normal', ?, NULL, ?, ?, ?, 1, ?)
            """, (ident, name_ja, name_en, attr1, genus, flavor, out_rel, aliases))
        else:
            cursor.execute("""
            UPDATE characters SET name_ja = ?, name_en = ?, attribute1 = ?, genus = ?, flavor_text = ?, image_url = ?, aliases = ?
            WHERE id = ?
            """, (name_ja, name_en, attr1, genus, flavor, out_rel, aliases, row[0]))

    # 5. 妖怪ウォッチ キャラクターの画像ダウンロードとDB登録
    print("\n--- 妖怪ウォッチ キャラクター登録中 ---")
    for item in YOKAI_CHARACTERS:
        ident, name_ja, name_en, attr1, genus, flavor, wiki_file, domain = item
        out_rel = f"/images/yokai/{ident}.png"
        out_abs = os.path.join(STATIC_IMG_DIR, "yokai", f"{ident}.png")
        
        wiki_api = f"https://{domain}/api.php"
        download_wiki_file(wiki_api, wiki_file, domain, out_abs)
        
        cursor.execute("SELECT id FROM characters WHERE category = 'yokai' AND identifier = ?", (ident,))
        row = cursor.fetchone()
        aliases = f"{name_ja},{name_en.lower()}"
        if not row:
            cursor.execute("""
            INSERT INTO characters (category, identifier, name_ja, name_en, form_type, attribute1, attribute2, genus, flavor_text, image_url, generation, aliases)
            VALUES ('yokai', ?, ?, ?, 'normal', ?, NULL, ?, ?, ?, 1, ?)
            """, (ident, name_ja, name_en, attr1, genus, flavor, out_rel, aliases))
        else:
            cursor.execute("""
            UPDATE characters SET name_ja = ?, name_en = ?, attribute1 = ?, genus = ?, flavor_text = ?, image_url = ?, aliases = ?
            WHERE id = ?
            """, (name_ja, name_en, attr1, genus, flavor, out_rel, aliases, row[0]))

    conn.commit()

    # 集計報告
    print("\n============================================================")
    print("データベース登録サマリー:")
    for cat in ['pokemon', 'yokai', 'dq', 'mario']:
        cursor.execute("SELECT count(*) FROM characters WHERE category = ?", (cat,))
        cnt = cursor.fetchone()[0]
        print(f"  - {cat.upper()}: {cnt} キャラクター")
    cursor.execute("SELECT count(*) FROM characters")
    total = cursor.fetchone()[0]
    print(f"  ★ 合計: {total} キャラクター")
    print("============================================================")
    conn.close()

if __name__ == "__main__":
    setup()
