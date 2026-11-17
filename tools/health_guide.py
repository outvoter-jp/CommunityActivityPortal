"""特集ページ「からだと地域活動」の本文

build_site.py から呼ばれる。考え方の文章はここに書き、つなぎ先は contacts.json、
並べる催しは themes.json（健康づくり）から作る。
医療判断はしない（診断・治療・個別の運動処方は書かない）方針で文章を書くこと。
"""
import html

e = html.escape

STAGES = [
    ("prevent", "予防", "日々の準備で、ケガと不調を減らす",
     "<p>いちばん効果が大きく、すぐ始められるのは、運動の前のウォームアップを毎回同じ流れでやることです。"
     "小さい関節から始め、座る・寝る、立つ、歩く・走る、方向転換やジャンプ、と順に負荷を上げていきます"
     "（<a href=\"https://www.jfa.jp/medical/column09.html\" target=\"_blank\" rel=\"noopener\">JFAメディカル通信</a>）。</p>"
     "<ol><li>足指・足首・肩周りをほぐす（座ってでもよい）</li><li>体幹と片脚バランス</li>"
     "<li>ゆっくりしたジョギングと、動きながらのストレッチ</li><li>ステップ、方向転換、軽いジャンプ</li>"
     "<li>ボールや道具を使った動きに移る</li></ol>"
     "<p>寝不足、前日の飲酒、風邪気味、どこかが痛む日は「今日は休む」「短い時間だけ出る」が当たり前、"
     "という空気をつくることも予防です。人数合わせの無理が、大人のケガのよくある入口です。</p>"),
    ("emergency", "もしもの対処", "起きたときは、応急とつなぎだけ",
     "<p>その場でできるのは、応急の手当てと、どこにつなぐかの判断だけです。「大丈夫だろう」と仲間内で決めないことが大切です。</p>"
     "<ul><li><b>意識がない・呼吸がおかしい・胸が痛い・頭を強く打った</b>：すぐ119番。必要ならAED。迷ったら呼ぶ。</li>"
     "<li><b>救急車か受診か迷う</b>：#7119（埼玉県救急電話相談・24時間）か、埼玉県AI救急相談へ。</li>"
     "<li><b>ねんざ・打撲・肉離れの疑い</b>：運動をやめ、冷やす・圧迫する・高くする。後日、医療機関へ。</li></ul>"
     "<p>活動の場所ごとにAEDの置き場所を確かめておくこと、何人かが消防の救命講習を受けておくことも備えになります。</p>"),
    ("return", "復帰", "道筋を、元気なうちに描いておく",
     "<p>これまで普通にできていた人ほど、できなくなった自分を想像しにくく、ケガや不調の後に戻る道筋を描けないまま離れてしまいがちです。"
     "復帰は階段のように少しずつ。どの段で何日かけるかは人とケガによって違うので、医師や理学療法士と相談して決めます。</p>"
     "<ol><li>日常生活が痛みなく送れる</li><li>歩く・軽く走るなど、一人でできる運動</li>"
     "<li>道具を使った個人練習（人と接触しない）</li><li>グループの活動に一部参加（時間短め）</li>"
     "<li>活動に全部参加</li><li>試合や本番に出る（時間を少しずつ増やす）</li></ol>"
     "<p>痛みや腫れが戻ったら、ひとつ前の段に戻ります。また、出る時間を短くする、役割を変える、"
     "走らない・接触しない遊び方にするなど、<b>形を変えて戻るのも立派な復帰</b>です。</p>"),
    ("belong", "休んでいる間の居場所", "プレーしなくても、仲間のまま",
     "<p>休んでいる間に仲間との接点が切れると、体が治っても戻りにくくなります。"
     "予約や連絡などの運営、記録や応援、地域行事の手伝い、情報集めなど、体に負担の少ない役割をふだんから開いておくと、"
     "休む期間も自然に関われます。</p>"
     "<p>元気なうちに、自分用の「もしものメモ」（かかりつけ、家族の連絡先、休んでいる間にやってみたい役割、"
     "自分にとっての復帰の形）を書いておくのもおすすめです。健康の情報は本人が持ち、団体では集めないようにしましょう。</p>"),
]


def contact_card(c):
    phone = ""
    if c.get("phone"):
        phone = f'<a class="tel" href="tel:{e(c["phone"].replace("-", "").replace("#", "%23"))}">{e(c["phone"])}</a>'
        if c.get("phone_alt"):
            phone += f'（つながらないとき <a class="tel" href="tel:{e(c["phone_alt"].replace("-", ""))}">{e(c["phone_alt"])}</a>）'
    rows = [("こんな時", e(c.get("when", ""))), ("電話", phone), ("受付", e(c.get("hours", ""))), ("費用", e(c.get("cost", ""))),
            ("所在地", e(c.get("address", ""))), ("担当地区", e(c.get("area", "")))]
    facts = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows if v)
    note = f'<p class="lead">{e(c["note"])}</p>' if c.get("note") else ""
    return (f'<li class="item" id="{e(c["id"])}"><div class="meta"><span class="status info">{e(c.get("kind", ""))}</span>'
            f'<span>{e(c.get("region", ""))}</span><span>{e("・".join(c.get("stages", [])))}</span></div>'
            f'<h3><a href="{e(c["url"])}" target="_blank" rel="noopener">{e(c["name"])}</a></h3>'
            f'<dl class="facts">{facts}</dl>{note}'
            f'<p class="lead">確認日 {e(c.get("checked_at", ""))}・<a href="{e(c["source_url"])}" target="_blank" rel="noopener">出典</a></p></li>')


def body(contacts, theme_cards):
    toc = "".join(f'<a href="#{slug}">{e(name)}</a>' for slug, name, _, _ in STAGES)
    stages = "".join(f'<section id="{slug}"><h2>{e(name)}：{e(sub)}</h2>{text}</section>' for slug, name, sub, text in STAGES)
    groups = []
    for region in ("埼玉県", "川口市", "蕨市"):
        rows = [c for c in contacts if c.get("region") == region]
        if rows:
            groups.append(f'<h3 class="group">{e(region)}</h3><ul class="items">{"".join(contact_card(c) for c in rows)}</ul>')
    events = (f'<ul class="items">{theme_cards}</ul>' if theme_cards
              else '<p class="lead">いま掲載中の健康づくりの情報はありません。</p>')
    return (f'<article><h1 class="item-title">からだと地域活動</h1>'
            '<p>体に不安があると、地域の活動にも前向きになりにくいものです。ケガや不調を「予防」し、'
            '起きたときに「対処」し、形を変えてでも「復帰」する。その間も「居場所」を保つ。'
            'この4つの考え方と、困ったときの相談先をまとめました。</p>'
            '<p class="filter">このページは考え方の紹介です。診断や治療、個別の運動の指示はしません。'
            '体のことは、医師・理学療法士などの専門家や、下の相談先に相談してください。</p>'
            f'<nav class="sections" aria-label="目次">{toc}<a href="#contacts">相談先</a><a href="#events">健康づくりの催し</a></nav>'
            f'{stages}'
            f'<section id="contacts"><h2>相談先（つなぎ先）</h2>'
            '<p class="lead">電話番号は確認日時点のものです。最新の情報は各出典でご確認ください。'
            '地域包括支援センターは住所で担当が決まります。</p>'
            f'{"".join(groups)}</section>'
            f'<section id="events"><h2>健康づくりの催し・講座</h2>{events}</section>'
            '<p class="note">機械で読む場合は <a href="api/v1/contacts.json"><code>api/v1/contacts.json</code></a>（相談先）と '
            '<a href="api/v1/themes/health.json"><code>api/v1/themes/health.json</code></a>（健康づくりの情報）。</p></article>')
