# -*- coding: utf-8 -*-
"""
マリオ・ドラクエ・妖怪ウォッチのキャラクター大幅増量スクリプト
並行処理で高画質透過画像をダウンロードし、charactersテーブルに登録します。
"""
import sqlite3
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

DB_PATH = os.path.join(os.path.dirname(__file__), "pokemon_quiz.db")
STATIC_IMG_DIR = os.path.join(os.path.dirname(__file__), "static", "images")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def search_and_download(wiki_api, query, out_path, referer):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 2000:
        return True
    try:
        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': query,
            'srnamespace': 6,
            'format': 'json'
        }
        headers = dict(HEADERS)
        headers['Referer'] = f'https://{referer}/'
        r = requests.get(wiki_api, params=params, headers=headers, timeout=8).json()
        items = r.get('query', {}).get('search', [])
        for it in items[:3]:
            title = it['title']
            if not any(ext in title.lower() for ext in ['.png', '.webp', '.jpg']):
                continue
            p_info = requests.get(wiki_api, params={'action': 'query', 'titles': title, 'prop': 'imageinfo', 'iiprop': 'url', 'format': 'json'}, headers=headers, timeout=8).json()
            pages = p_info.get('query', {}).get('pages', {})
            for _, p in pages.items():
                info = p.get('imageinfo')
                if info and len(info) > 0:
                    iurl = info[0]['url']
                    ir = requests.get(iurl, headers=headers, timeout=12)
                    if ir.status_code == 200 and len(ir.content) > 1000:
                        os.makedirs(os.path.dirname(out_path), exist_ok=True)
                        with open(out_path, 'wb') as f:
                            f.write(ir.content)
                        print(f"  [GET] {os.path.basename(out_path)} ({len(ir.content)} bytes)")
                        return True
    except Exception as e:
        pass
    return False

# =========================================================================
# 拡充キャラクターリスト
# =========================================================================

# --- 1. スーパーマリオ ---
MARIO_EXPANDED = [
    ("mario", "マリオ", "Mario", "ヒーロー", "配管工", "ヒゲと赤い帽子がトレードマークのスーパースター！", "Super_Mario_Party_Mario.png"),
    ("luigi", "ルイージ", "Luigi", "ヒーロー", "弟", "少し臆病だがジャンプ力は兄以上！オバケが大の苦手な緑の弟。", "Super_Mario_Party_Luigi.png"),
    ("peach", "ピーチ", "Princess Peach", "キノコ王国", "プリンセス", "キノコ王国のお姫様。よくクッパにさらわれるヒロイン。", "Super_Mario_Party_Peach.png"),
    ("bowser", "クッパ", "Bowser", "クッパ軍団", "大魔王", "トゲトゲの甲羅と炎の息を持つ大魔王！マリオ永遠のライバル。", "Super_Mario_Party_Bowser.png"),
    ("yoshi", "ヨッシー", "Yoshi", "相棒", "恐竜", "背中にマリオを乗せて大活躍する長い舌の食いしん坊な恐竜。", "Super_Mario_Party_Yoshi.png"),
    ("toad", "キノピオ", "Toad", "キノコ王国", "お世話役", "頭の赤い水玉キノコが可愛いピーチ姫のお世話役。", "Toad_-_Mario_Party_10.png"),
    ("wario", "ワリオ", "Wario", "ライバル", "怪力", "ニンニクとお金が大好物の下品でパワフルな黄色い男！", "Super_Mario_Party_Wario.png"),
    ("waluigi", "ワルイージ", "Waluigi", "ライバル", "長身", "ルイージをライバル視するずる賢い紫の長身男。", "Waluigi render png"),
    ("daisy", "デイジー", "Princess Daisy", "サラサ・ランド", "プリンセス", "元気いっぱいで明るいサラサ・ランドのお姫様！", "Super_Mario_Party_Daisy.png"),
    ("rosalina", "ロゼッタ", "Rosalina", "宇宙", "星の母", "ほうき星の天文台でチコたちと暮らす謎多き美女。", "Rosalina render png"),
    ("bowser_jr", "クッパJr.", "Bowser Jr.", "クッパ軍団", "御曹司", "クッパの愛息。クラウンに乗って悪巧みをする。", "Bowser Jr render png"),
    ("donkey_kong", "ドンキーコング", "Donkey Kong", "コング", "怪力ゴリラ", "赤いネクタイを締めたジャングルの王者！バナナが大好物。", "Super_Mario_Party_Donkey_Kong.png"),
    ("diddy_kong", "ディディーコング", "Diddy Kong", "コング", "チンパンジー", "赤い帽子とシャツを着たドンキーの軽快な相棒。", "Super_Mario_Party_Diddy_Kong.png"),
    ("goomba", "クリボー", "Goomba", "クッパ軍団", "きのこ", "キノコ王国を裏切ったシイタケのようなザコ敵。踏まれると倒れる。", "Goomba render png"),
    ("koopa_troopa", "ノコノコ", "Koopa Troopa", "クッパ軍団", "カメ", "甲羅を背負ったカメ。踏むと甲羅に閉じこもる。", "Koopa Troopa render png"),
    ("boo", "テレサ", "Boo", "オバケ", "シャイ", "恥ずかしがり屋のおばけ。顔を合わせると手で顔を隠す。", "Boo render png"),
    ("piranha_plant", "パックンフラワー", "Piranha Plant", "クッパ軍団", "食虫植物", "土管から急に顔を出す鋭いキバの危険な植物。", "Piranha_Plant_-_Super_Mario_Party.png"),
    ("bob_omb", "ボムへい", "Bob-omb", "クッパ軍団", "歩く爆弾", "ぜんまい仕掛けで歩き回り、導火線に火がつくと大爆発！", "Bob-omb render png"),
    ("shy_guy", "ヘイホー", "Shy Guy", "クッパ軍団", "仮面", "白いお面をかぶった正体不明の可愛いキャラクター。", "Shy Guy render png"),
    ("kamek", "カメック", "Kamek", "クッパ軍団", "魔法使い", "ホウキに乗って魔法を放つクッパ軍団の知恵袋。", "Kamek render png"),
    ("thwomp", "ドッスン", "Thwomp", "トラップ", "岩石", "天井で待ち構え、近づくとドスンと落下して押しつぶす岩。", "Thwomp render png"),
    ("chain_chomp", "ワンワン", "Chain Chomp", "クッパ軍団", "鉄球", "鎖につながれた凶暴な鉄球。噛みつき攻撃をしてくる。", "Chain Chomp render png"),
    ("bullet_bill", "キラー", "Bullet Bill", "クッパ軍団", "砲弾", "大砲から一直線に飛んでくる目つきの鋭い黒い弾丸。", "Bullet Bill render png"),
    ("toadette", "キノピコ", "Toadette", "キノコ王国", "女の子", "ピンクのツインテールがトレードマークの元気な女の子。", "Toadette_-_Mario_Party_10.png"),
    ("birdo", "キャサリン", "Birdo", "恐竜", "リボン", "頭のピンクのリボンがチャームポイント。口から卵を発射する。", "Birdo render png"),
    ("spiny", "トゲゾー", "Spiny", "クッパ軍団", "トゲカメ", "背中に鋭いトゲが生えており、上から踏むとダメージを受ける。", "Spiny render png"),
    # 追加
    ("dry_bones", "カロン", "Dry Bones", "クッパ軍団", "ガイコツカメ", "骨だけになったノコノコ。踏まれても時間が経つと復活する。", "Dry Bones render png"),
    ("dry_bowser", "ほねクッパ", "Dry Bowser", "クッパ軍団", "不死の大魔王", "溶岩に落ちて骨だけになったクッパの怨念の姿！青い炎を吐く。", "Dry Bowser render png"),
    ("king_boo", "キングテレサ", "King Boo", "オバケ", "オバケの王", "紫の舌と王冠が特徴のテレサの王様。ルイージの宿敵！", "King Boo render png"),
    ("petey_piranha", "ボスパックン", "Petey Piranha", "クッパ軍団", "巨大パックン", "羽が生えて空を飛べる巨大なパックンフラワーのボス。", "Petey Piranha render png"),
    ("king_bob_omb", "ボムキング", "King Bob-omb", "クッパ軍団", "爆弾の王", "立派なヒゲと王冠をつけた巨大なボムへいの王様！投げ飛ばしてくる。", "King Bob-omb render png"),
    ("hammer_bro", "ハンマーブロス", "Hammer Bro", "クッパ軍団", "投擲兵", "ヘルメットをかぶり、大量のハンマーを次々と投げつけてくる難敵。", "Hammer Bro render png"),
    ("wiggler", "ハナチャン", "Wiggler", "森の生き物", "いもむし", "普段はのんびり歩いているが、踏まれると真っ赤になって激怒する！", "Wiggler render png"),
    ("monty_mole", "チョロプー", "Monty Mole", "クッパ軍団", "モグラ", "地面や壁から突然飛び出してきて邪魔をするサングラスのモグラ。", "Monty Mole render png"),
    ("spike", "ガボン", "Spike", "クッパ軍団", "鉄球吐き", "口からトゲトゲのシューリンガンを取り出して投げつけてくる緑の敵。", "Spike render png"),
    ("cheep_cheep", "プクプク", "Cheep Cheep", "水棲", "魚", "水中を泳ぎ、時々海面から大ジャンプしてくる赤い魚。", "Cheep Cheep render png"),
    ("blooper", "ゲッソー", "Blooper", "水棲", "イカ", "水中でピコピコとジグザグに泳ぎ回る白いイカ。スミを吐くことも。", "Blooper render png"),
    ("lakitu", "ジュゲム", "Lakitu", "クッパ軍団", "雲乗り", "笑顔の雲に乗って空からパイポ（トゲゾーの卵）を落としてくる。", "Lakitu render png"),
    ("buzzy_beetle", "メット", "Buzzy Beetle", "クッパ軍団", "頑丈カメ", "硬い青い甲羅を持ち、ファイアボールが効かない防御力の高い敵。", "Buzzy Beetle render png"),
    ("pokey", "サンボ", "Pokey", "砂漠", "サボテン", "黄色いトゲだらけの球体がだるま落としのように重なったサボテン。", "Pokey render png"),
    ("pauline", "ポリーン", "Pauline", "都市", "市長", "初代ドンキーコングで救出された美女。ニュードンク・シティの市長。", "Pauline render png"),
    ("cappy", "キャッピー", "Cappy", "相棒", "帽子", "カブロンの帽子の精霊。投げると敵にキャプチャーして操れる！", "Cappy render png"),
    ("nabbit", "トッテン", "Nabbit", "盗賊", "ウサギ袋", "アイテム袋を背負って逃げ回る泥棒ウサギ。敵に当たっても無敵。", "Nabbit render png"),
    ("larry", "ラリー", "Larry Koopa", "クッパ7人衆", "最年少", "水色のモヒカンが特徴のクッパ7人衆の特攻隊長！", "Larry Koopa render png"),
    ("morton", "モートン", "Morton Koopa Jr.", "クッパ7人衆", "巨漢", "顔に星のタトゥーがある怪力自慢の巨大なクッパ7人衆。", "Morton Koopa Jr render png"),
    ("wendy", "ウェンディ", "Wendy O. Koopa", "クッパ7人衆", "紅一点", "ピンクのリボンとハイヒールを履いたクッパ7人衆のワガママ娘。", "Wendy O Koopa render png"),
    ("iggy", "イギー", "Iggy Koopa", "クッパ7人衆", "マッドサイエンティスト", "緑のパイナップルヘアーとグルグル眼鏡のクッパ7人衆の狂人。", "Iggy Koopa render png"),
    ("roy", "ロイ", "Roy Koopa", "クッパ7人衆", "ピンクサングラス", "ピンクのサングラスと力自慢のガチムチなクッパ7人衆。", "Roy Koopa render png"),
    ("lemmy", "レミー", "Lemmy Koopa", "クッパ7人衆", "玉乗り", "カラフルな玉に乗ってバランスをとるクッパ7人衆のお調子者。", "Lemmy Koopa render png"),
    ("ludwig", "ルドウィッグ", "Ludwig von Koopa", "クッパ7人衆", "リーダー", "青い大ボリュームの髪型を持つクッパ7人衆のリーダー格にして天才作曲家。", "Ludwig von Koopa render png"),
    ("baby_mario", "ベビィマリオ", "Baby Mario", "ヒーロー", "赤ちゃん", "赤ちゃんの頃のマリオ。ヨッシーの背中に乗って大冒険！", "Baby Mario render png"),
    ("baby_luigi", "ベビィルイージ", "Baby Luigi", "ヒーロー", "赤ちゃん", "赤ちゃんの頃のルイージ。泣き虫だが兄思い。", "Baby Luigi render png"),
    ("mecha_koopa", "メカクッパ", "Mecha-Koopa", "クッパ軍団", "ぜんまいロボ", "ぜんまい仕掛けでカタカタ歩くクッパそっくりの小型ロボット。", "Mecha-Koopa render png")
]

# --- 2. ドラゴンクエスト ---
DQ_EXPANDED = [
    ("slime", "スライム", "Slime", "スライム系", "代表モンスター", "シリーズの顔！愛嬌のある水滴のような形の青いモンスター。", "Slime_Artwork.png"),
    ("she_slime", "スライムベス", "She-slime", "スライム系", "オレンジ", "スライムの近縁種。赤オレンジ色で少しだけ強い。", "She-slime_Artwork.png"),
    ("metal_slime", "メタルスライム", "Metal Slime", "スライム系", "経験値大量", "銀色に輝くスライム。倒すと大量の経験値がもらえるがすぐ逃げる。", "Liquid Metal Slime Artwork.png"),
    ("liquid_metal_slime", "はぐれメタル", "Liquid Metal Slime", "スライム系", "液体メタル", "溶けた銀のようにドロドロした姿。すばやさが非常に高い。", "Liquid Metal Slime Artwork.png"),
    ("metal_king_slime", "メタルキング", "Metal King Slime", "スライム系", "メタルの王", "メタルスライムが合体して王冠を被った経験値の最高峰！", "Metal King Slime Artwork.png"),
    ("king_slime", "キングスライム", "King Slime", "スライム系", "王冠スライム", "スライムが8匹合体して誕生した巨大なスライムの王様。", "King Slime Artwork.png"),
    ("healslime", "ホイミスライム", "Healslime", "スライム系", "触手回復", "空中をふわふわ漂い、触手でホイミを唱えて仲間を助ける。", "Healslime_Artwork.png"),
    ("dracky", "ドラキー", "Dracky", "鳥系", "コウモリ", "黄色い大きな目とコウモリのような羽を持つ序盤のモンスター。", "Dracky_Artwork.png"),
    ("ghost", "ゴースト", "Ghost", "ゾンビ系", "おばけ", "頭に三角頭巾をつけた小さなおばけ。メラを唱えてくる。", "Ghost_Artwork.png"),
    ("stump_chump", "きりかぶおばけ", "Stump Chump", "植物系", "切り株", "長い年月を生きた木の切り株に魂が宿ったモンスター。", "DQT - Stump Chump.png"),
    ("spookstool", "おばけキノコ", "Spookstool", "植物系", "キノコ", "大きな笠を持つキノコ。甘い息を吐いて眠らせてくる。", "Spookstool Artwork.png"),
    ("hammerhood", "おおきづち", "Hammerhood", "魔獣系", "モグラ", "大きな木槌を持った毛むくじゃらのモンスター。痛恨の一撃に注意！", "Hammerhood_Artwork.png"),
    ("platypunk", "ももんじゃ", "Platypunk", "魔獣系", "カモノハシ", "尻尾を振って愛嬌を振りまくカモノハシのような魔獣。", "Platypunk Artwork.png"),
    ("restless_armour", "さまようよろい", "Restless Armour", "物質系", "亡霊の鎧", "魂が宿った中身のない鎧。ホイミスライムを呼び出すことも。", "DQ8-067-Restless armour.png"),
    ("golem", "ゴーレム", "Golem", "物質系", "レンガの巨人", "土やレンガを固めて作られた巨大な番人。妖精の笛で眠る。", "Golem_Artwork.png"),
    ("killing_machine", "キラーマシン", "Killing Machine", "物質系", "殺人機械", "古代文明が造り出した冷徹な殺人兵器。弓と剣の2回攻撃。", "Killing Machine Artwork.png"),
    ("bomboulder", "ばくだんいわ", "Bomboulder", "物質系", "自爆岩", "顔が刻まれた不気味な岩。瀕死になるとメガンテで自爆する！", "Rockbomb Artwork.png"),
    ("mimic", "ミミック", "Mimic", "物質系", "宝箱トラップ", "宝箱に化けた凶悪モンスター。ザキやあまいいきを放つ。", "Mimic_Artwork.png"),
    ("green_dragon", "ドラゴン", "Green Dragon", "ドラゴン系", "初代中ボス", "初代でローラ姫を見張っていた緑色の巨躯。火の息を吐く。", "Green Dragon Artwork.png"),
    ("chimaera", "キメラ", "Chimaera", "鳥系", "合成魔獣", "ハゲタカの体にヘビの尾を持つ鳥系モンスター。火の息を吐く。", "Chimaera_Artwork.png"),
    ("dragonlord", "りゅうおう", "Dragonlord", "魔王", "初代ボス", "『もし わしの 味方になれば 世界の半分を やろう』と誘惑する巨竜の王。", "Dragonlord 2nd Forme Artwork.png"),
    ("malroth", "シドー", "Malroth", "破壊神", "DQ2ボス", "邪教の生贄によって召喚された6本腕の巨大な破壊神！", "Malroth_Artwork.png"),
    ("zoma", "ゾーマ", "Zoma", "大魔王", "DQ3ボス", "『なにゆえ もがき 生きるのか』すべてを滅ぼす大魔王。闇の衣を纏う。", "Zoma_Artwork.png"),
    ("psaro", "デスピサロ", "Psaro", "魔族の王", "DQ4ボス", "進化の秘法を使って次々と形態を変える悲劇の魔族の王。", "Psaro Upscaled Artwork.png"),
    ("estark", "エスターク", "Estark", "地獄の帝王", "裏ボス", "古代に封印された地獄の帝王。目覚めたばかりで記憶がない。", "Estark Rivals art.jpg"),
    # 追加
    ("slime_knight", "スライムナイト", "Slime Knight", "スライム系", "騎士とスライム", "緑のスライムの上に小さな騎士がまたがった大人気モンスター！", "Slime knight Artwork.png"),
    ("slime_tower", "スライムタワー", "Slime Tower", "スライム系", "3段スライム", "緑、オレンジ、青の3匹のスライムが縦に積まれたタワー！", "Slime tower Artwork.png"),
    ("bubble_slime", "バブルスライム", "Bubble Slime", "スライム系", "毒泡スライム", "緑色の泡立つスライム。攻撃に毒を持っており序盤の脅威。", "Bubble slime Artwork.png"),
    ("golden_slime", "ゴールデンスライム", "Golden Slime", "スライム系", "黄金の王", "金ピカに輝く四角いスライム。倒すと超大量のゴールドが手に入る！", "Golden slime Artwork.png"),
    ("drackyma", "ドラキーマ", "Drackmage", "鳥系", "上位コウモリ", "赤紫色のドラキーの上位種。ラリホーやイオを唱えてくる。", "Drackmage Artwork.png"),
    ("great_sabrecat", "キラーパンサー", "Great Sabrecat", "魔獣系", "巨大サーベルタイガー", "牙の長い巨大なトラ型モンスター。DQ5では心強い仲間に！", "Great sabrecat Artwork.png"),
    ("great_sabrecub", "ベビーパンサー", "Great Sabrecub", "魔獣系", "子トラ", "キラーパンサーの子供。子猫のようにじゃれついてきて可愛い。", "Great sabrecub Artwork.png"),
    ("gigantes", "ギガンテス", "Gigantes", "悪魔系", "一つ目巨人", "青い巨体と巨大な棍棒を持つ一つ目の巨人。痛恨の一撃を連発！", "Gigantes Artwork.png"),
    ("cyclops", "サイクロプス", "Cyclops", "悪魔系", "一つ目", "ギガンテスの下位種。黄色い棍棒を持って暴れまわる。", "Cyclops Artwork.png"),
    ("atlas", "アトラス", "Atlas", "悪魔系", "巨神", "ロンダルキアの洞窟を守るハーゴン軍の巨人ボス。", "Atlas Artwork.png"),
    ("bazuzu", "バズズ", "Bazuzu", "悪魔系", "猿型悪魔", "ハーゴン軍の幹部。ザラキやメガンテを使ってくる危険な魔物。", "Bazuzu Artwork.png"),
    ("belial", "ベリアル", "Belial", "悪魔系", "狐型悪魔", "ハーゴン直属の側近。イオナズンを連発してくる強敵。", "Belial Artwork.png"),
    ("troll", "トロール", "Troll", "怪人系", "肥満巨人", "緑色の太った巨人。棍棒を振り回すが時々転ぶ愛嬌もある。", "Troll Artwork.png"),
    ("boss_troll", "ボストロール", "Boss Troll", "怪人系", "サマンオサ偽王", "サマンオサの国王に化けて暴政を行っていた大柄なトロール。", "Boss troll Artwork.png"),
    ("robbino_ood", "カンダタ", "Robbin' 'Ood", "怪人系", "義賊・盗賊", "覆面マスクとパンツ一丁の盗賊の親分！『許してくれよ！な！』", "Robbin' 'Ood Artwork.png"),
    ("orochi_dq", "やまたのおろち", "Orochi", "ドラゴン系", "八つ首の竜", "ジパングの村を恐怖に陥れていた5つの首を持つ大蛇の魔物。", "Orochi Artwork.png"),
    ("king_leo", "キングレオ", "King Leo", "魔獣系", "4本腕の獅子", "4本の腕とライオンの顔を持つ魔獣。進化の秘法の実験体。", "King Leo Artwork.png"),
    ("archdemon", "アークデーモン", "Archdemon", "悪魔系", "大悪魔", "巨大な角とフォークを持つ大悪魔。イオナズンを唱える。", "Archdemon Artwork.png"),
    ("minidemon", "ベビーサタン", "Minidemon", "悪魔系", "子悪魔", "子供の悪魔。イオナズンを唱えようとするがMPが足りない！", "Minidemon Artwork.png"),
    ("cannibox", "ひとくいばこ", "Cannibox", "物質系", "罠の小箱", "ミミックより小柄だが序盤で出会うと痛恨の一撃で即全滅する。", "Cannibox Artwork.png"),
    ("pandoras_box", "パンドラボックス", "Pandora's Box", "物質系", "最凶トラップ", "宝箱系モンスターの最強種。完全2回行動でザラキや痛恨を放つ。", "Pandora's box Artwork.png"),
    ("nimzo", "ミルドラース", "Grandmaster Nimzo", "魔王", "DQ5ボス", "魔界の神になろうとした邪悪な魔王。老人の姿から真の巨体へ変身する。", "Grandmaster Nimzo Artwork.png"),
    ("mortamor", "デスタムーア", "Mortamor", "大魔王", "DQ6ボス", "夢と現実を支配する幻の大魔王。最終形態はおぞましい顔と両手！", "Mortamor Artwork.png"),
    ("nokturnus", "ダークドレアム", "Nokturnus", "破壊神", "DQ6裏ボス", "大魔王デスタムーアを軽々と一蹴する破壊と殺戮の絶対神。", "Nokturnus Artwork.png"),
    ("dhoulmagus", "ドルマゲス", "Dhoulmagus", "道化師/魔人", "DQ8中ボス", "『悲しいなぁ…』封印の杖を奪い狂気にとりつかれた道化師。", "Dhoulmagus Artwork.png"),
    ("rhapthorne", "ラプソーン", "Rhapthorne", "暗黒神", "DQ8ボス", "杖に封印されていた暗黒神。巨大な丸い球体の姿で降臨する。", "Rhapthorne Artwork.png")
]

# --- 3. 妖怪ウォッチ ---
YOKAI_EXPANDED = [
    ("jibanyan", "ジバニャン", "Jibanyan", "プリチー族", "地縛霊ネコ", "トラックにはねられて死んだネコの地縛霊。『ひゃくれつ肉球』が必殺技！", "Jibanyan.png"),
    ("komasan", "コマさん", "Komasan", "プリチー族", "狛犬", "田舎の神社からやってきた狛犬妖怪。口癖は『もんげー！』ソフトクリームが大好き。", "Komasan.png"),
    ("komajiro", "コマじろう", "Komajiro", "プリチー族", "狛犬弟", "コマさんの双子の弟。都会に馴染むのが早くスマホを使いこなすズラ！", "Komajiro.png"),
    ("whisper", "ウィスパー", "Whisper", "ニョロロン族", "妖怪執事", "主人公に妖怪ウォッチを授けた執事妖怪。知識は妖怪パッド頼り。", "Whisper.png"),
    ("bushinyan", "ブシニャン", "Bushinyan", "イサマシ族", "レジェンド", "鎧兜を身にまとったネコ妖怪のレジェンド！天下無双の剣術を誇る。", "Shogunyan.png"),
    ("robonyan", "ロボニャン", "Robonyan", "ゴーケツ族", "サイボーグ", "未来のテクノロジーで作られたサイボーグネコ妖怪。『アイルビーバック！』", "Robonyan.png"),
    ("hovernyan", "フユニャン", "Hovernyan", "イサマシ族", "熱血ネコ", "青いマントを羽織った熱血で頼れるネコ妖怪。『ど根性ストレート』を放つ！", "Hovernyan.png"),
    ("baddinyan", "ワルニャン", "Baddinyan", "イサマシ族", "ツッパリ", "トゲトゲのリーゼントと学ランを着たツッパリ不良ネコ妖怪。", "Baddinyan.png"),
    ("thornyan", "トゲニャン", "Thornyan", "プリチー族", "トゲネコ", "風邪をこじらせて全身から鋭いトゲが生えてしまったネコ妖怪。", "Thornyan.png"),
    ("orochi", "オロチ", "Venoct", "ニョロロン族", "エリート", "龍のマフラーを首に巻いたクールで強力なエリート妖怪。", "Venoct.png"),
    ("kyubi", "キュウビ", "Kyubi", "フシギ族", "九尾の狐", "9本の尾を持つ高貴なキツネ妖怪。美しい人間の少年に化けることも。", "Kyubi.png"),
    ("tattletell", "バクロ婆", "Tattletell", "フシギ族", "暴露", "とりつかれると胸に秘めた秘密を大声で暴露してしまうおばあさん妖怪。", "Tattletell.png"),
    ("manjimutt", "じんめん犬", "Manjimutt", "ブキミー族", "人面犬", "人間の顔を持つ犬。女性にモテたいがために悪戦苦闘する哀愁の妖怪。", "Manjimutt.png"),
    ("happierre", "ホノボーノ", "Happierre", "ポカポカ族", "太陽", "とりつかれると喧嘩中の夫婦も仲直り。まわりをほんわかさせる妖怪。", "Happierre.png"),
    ("dismarelda", "ドンヨリーヌ", "Dismarelda", "ブキミー族", "どんより", "部屋や空気をどんより重く険悪にしてしまう巨大なスライム状の妖怪。", "Dismarelda.png"),
    ("hungramps", "ひも爺", "Hungramps", "ポカポカ族", "空腹", "とりつかれると猛烈にお腹が空いて何でも食べたくなってしまうおじいさん妖怪。", "Hungramps.png"),
    ("fidgephant", "モレゾウ", "Fidgephant", "ゴーケツ族", "トイレ我慢", "鼻から水を噴射し、とりついた人に猛烈な尿意をもたらすゾウの妖怪。", "Fidgephant.png"),
    ("usapyon", "ＵＳＡピョン", "USApyon", "ウスラカゲ族", "宇宙ウサギ", "宇宙服を着たフェレット妖怪。怒るとベイダーモードに変身するダニ！", "USApyon.png"),
    ("enma", "エンマ大王", "Lord Enma", "エンマ族", "妖魔界の王", "妖魔界を統べる若き絶対王者！圧倒的な霊力とカリスマ性を持つ。", "Lord_Enma.png"),
    ("zazel", "ぬらりひょん", "Zazel", "エンマ族", "評議会議長", "妖魔界の評議会議長。エンマ大王に仕える忠義に厚い側近。", "Zazel.png"),
    ("blizzaria", "ふぶき姫", "Blizzaria", "プリチー族", "雪女の姫", "冷気を操る美しい妖怪。夏でもまわりを凍りつかせる。", "Blizzaria.png"),
    ("frostina", "ゆきおんな", "Frostina", "プリチー族", "雪女", "雪山に現れる小さな女の子の妖怪。触れたものを凍らせてしまう。", "Frostina.png"),
    ("noway", "ムリカベ", "Noway", "ゴーケツ族", "拒絶の壁", "頼み事をされても『ム〜リ〜！』と両手をクロスして絶対に断る巨大な壁。", "Noway.png"),
    ("snartle", "なまはげ", "Snartle", "イサマシ族", "信号無視", "横断歩道の信号を無視して渡ると現れて襲いかかってくる恐怖の妖怪！", "Snartle.png"),
    # 追加
    ("darknyan", "ダークニャン", "Darknyan", "ブキミー族", "漆黒のマント", "暗闇に潜み悪を裁く黒いマントのネコ妖怪。『ダークニャイト爪』！", "Darknyan png"),
    ("sailornyan", "セーラーニャン", "Sailornyan", "プリチー族", "セーラー服", "水色のセーラー服と大きなリボンが可愛い海を愛するネコ妖怪。", "Sailornyan png"),
    ("goldenyan", "ゴルニャン", "Goldenyan", "ゴーケツ族", "黄金ロボ", "純金で作られた最高級のロボニャン。ゴールド波動を放つ。", "Goldenyan png"),
    ("dandoodle", "イケメン犬", "Dandoodle", "ブキミー族", "レジェンド", "人面犬のレジェンド！どんな女性も一瞬でメロメロにする超イケメン。", "Dandoodle png"),
    ("elder_bloom", "花さか爺", "Elder Bloom", "ポカポカ族", "レジェンド", "枯れ木に花を咲かせる心優しいレジェンド妖怪。桜吹雪を巻き起こす。", "Elder Bloom png"),
    ("komashura", "しゅらコマ", "Komashura", "フシギ族", "レジェンド", "全身が紅蓮の炎に包まれたコマさんの先祖にして最強の阿修羅妖怪。", "Komashura png"),
    ("spoil_erina", "ネタバレリーナ", "Spoil-erina", "プリチー族", "レジェンド", "映画や漫画の結末をバレリーナのように踊りながら大声でネタバレする！", "Spoil-erina png"),
    ("poofessor", "うんちく魔", "Poofessor", "ウスラカゲ族", "レジェンド", "頭にうんちくの詰まった巨大な巻きグソを乗せた博識なクマのレジェンド。", "Poofessor png"),
    ("slurpent", "やまタン", "Slurpent", "ニョロロン族", "レジェンド", "8枚の舌を持つ巨大な大蛇のレジェンド妖怪。あらゆる言葉を話す。", "Slurpent png"),
    ("gilgaros", "山吹鬼", "Gilgaros", "ゴーケツ族", "最凶レジェンド", "山吹色の巨体と巨大な金棒を持つ封印されし最強の鬼妖怪。", "Gilgaros png"),
    ("gargaros", "赤鬼", "Gargaros", "ゴーケツ族", "鬼時間ボス", "鬼時間に現れる赤い巨大な鬼。見つかると棍棒を持って追いかけてくる！", "Gargaros png"),
    ("ogralus", "青鬼", "Ogralus", "ゴーケツ族", "青い巨鬼", "赤鬼よりさらに強力な青い鬼。圧倒的な力で踏み潰してくる。", "Ogralus png"),
    ("orcanos", "黒鬼", "Orcanos", "ゴーケツ族", "漆黒の鬼", "黒い鋼鉄の体を持つ鬼たちの頂点。一切の妥協のない強さを誇る。", "Orcanos png"),
    ("toadal_dude", "土蜘蛛", "Toadal Dude", "ブキミー族", "元祖軍大将", "平釜平原の戦いで元祖軍を率いる誇り高き大将妖怪。蜘蛛糸を操る。", "Toadal Dude png"),
    ("arachnus", "大ガマ", "Arachnus", "ポカポカ族", "本家軍大将", "本家軍を率いるカエルの大将妖怪。土蜘蛛とは永遠のライバル！", "Arachnus png"),
    ("illuminoct", "ヒカリオロチ", "Illuminoct", "イサマシ族", "光の龍", "黄金のオーラを放つ神聖なオロチの姿。悪を光の刃で滅ぼす。", "Illuminoct png"),
    ("shadow_venoct", "影オロチ", "Shadow Venoct", "ニョロロン族", "影の暗殺者", "闇に紛れて任務をこなすオロチの影の姿。気配を完全に消す。", "Shadow Venoct png"),
    ("dark_kyubi", "ヤミキュウビ", "Dark Kyubi", "ウスラカゲ族", "闇の九尾", "漆黒の毛並みを持つキュウビの裏の姿。闇の業火を操る。", "Dark Kyubi png"),
    ("damona", "百鬼姫", "Damona", "プリチー族", "闇の姫君", "ふぶき姫のカラーバリエーション。漆黒の着物を着た高貴な姫。", "Damona png"),
    ("slimamander", "ミツマタノヅチ", "Slimamander", "ニョロロン族", "3つ首ボス", "3本の長い首を持つ巨大ボス妖怪。真ん中の目玉が弱点！", "Slimamander png"),
    ("sv_snaggerjag", "つられたろう丸", "SV Snaggerjag", "ニョロロン族", "巨大ナマズ", "ひょうたん池の主。一本釣りでルアーを投げて子分を呼び寄せる。", "SV Snaggerjag png"),
    ("sproink", "のぼせトンマン", "Sproink", "ブキミー族", "銭湯ボス", "温泉で長風呂してのぼせ上がった巨大なブタ妖怪。ヘソに弱点がある。", "Sproink png"),
    ("wobblewok", "どんどろ", "Wobblewok", "ウスラカゲ族", "お釜の邪神", "巨大な釜に封印されていた太古の邪悪な妖怪。目玉の色で耐性が変わる。", "Wobblewok png"),
    ("mckraken", "イカカモネ議長", "McKraken", "ニョロロン族", "妖魔界の反逆者", "妖魔界の乗っ取りを企てた白いイカのボス妖怪。最終形態は巨大化！", "McKraken png"),
    ("dame_dedtime", "トキヲ・ウバウネ", "Dame Dedtime", "怪魔", "時間の支配者", "人間の時間を奪い尽くそうとする巨大な魔女。ケマモト村を襲撃した。", "Dame Dedtime png"),
    ("master_nyada", "マスターニャーダ", "Master Nyada", "フシギ族", "ホースの使い手", "伝説のフォース（ホース）を極めた小さな老人ネコ妖怪。無敵の強さ。", "Master Nyada png"),
    ("meganyan", "デカニャン", "Meganyan", "イサマシ族", "巨大ネコ", "体が風船のように巨大化して身動きが取れなくなったフユニャンの姿。", "Meganyan png")
]

def run():
    print("============================================================")
    print("キャラクター大幅拡張開始 (並行ダウンロード & DB更新)")
    print("============================================================")

    # 1. 画像ダウンロードタスクの作成
    download_tasks = []

    for item in MARIO_EXPANDED:
        ident, name_ja, name_en, attr1, genus, flavor, q = item
        out = os.path.join(STATIC_IMG_DIR, "mario", f"{ident}.png")
        download_tasks.append(("https://www.mariowiki.com/api.php", q, out, "www.mariowiki.com"))

    for item in DQ_EXPANDED:
        ident, name_ja, name_en, attr1, genus, flavor, q = item
        out = os.path.join(STATIC_IMG_DIR, "dq", f"{ident}.png")
        download_tasks.append(("https://dragonquest.fandom.com/api.php", q, out, "dragonquest.fandom.com"))

    for item in YOKAI_EXPANDED:
        ident, name_ja, name_en, attr1, genus, flavor, q = item
        out = os.path.join(STATIC_IMG_DIR, "yokai", f"{ident}.png")
        download_tasks.append(("https://yokaiwatch.fandom.com/api.php", q, out, "yokaiwatch.fandom.com"))

    print(f"ダウンロード対象数: {len(download_tasks)} 件。並行処理で取得中...")

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(search_and_download, api, q, path, ref) for api, q, path, ref in download_tasks]
        for f in as_completed(futures):
            f.result()

    print("\n画像取得完了！ データベースを更新します...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # マリオ登録
    for item in MARIO_EXPANDED:
        ident, name_ja, name_en, attr1, genus, flavor, _ = item
        out_rel = f"/images/mario/{ident}.png"
        out_abs = os.path.join(STATIC_IMG_DIR, "mario", f"{ident}.png")
        if not os.path.exists(out_abs):
            continue  # 画像がないものはスキップ
        aliases = f"{name_ja},{name_en.lower()}"
        cursor.execute("SELECT id FROM characters WHERE category = 'mario' AND identifier = ?", (ident,))
        row = cursor.fetchone()
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

    # ドラクエ登録
    for item in DQ_EXPANDED:
        ident, name_ja, name_en, attr1, genus, flavor, _ = item
        out_rel = f"/images/dq/{ident}.png"
        out_abs = os.path.join(STATIC_IMG_DIR, "dq", f"{ident}.png")
        if not os.path.exists(out_abs):
            continue
        aliases = f"{name_ja},{name_en.lower()}"
        cursor.execute("SELECT id FROM characters WHERE category = 'dq' AND identifier = ?", (ident,))
        row = cursor.fetchone()
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

    # 妖怪ウォッチ登録
    for item in YOKAI_EXPANDED:
        ident, name_ja, name_en, attr1, genus, flavor, _ = item
        out_rel = f"/images/yokai/{ident}.png"
        out_abs = os.path.join(STATIC_IMG_DIR, "yokai", f"{ident}.png")
        if not os.path.exists(out_abs):
            continue
        aliases = f"{name_ja},{name_en.lower()}"
        cursor.execute("SELECT id FROM characters WHERE category = 'yokai' AND identifier = ?", (ident,))
        row = cursor.fetchone()
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

    print("\n============================================================")
    print("新キャラクター登録集計:")
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
    run()
