"""相關度過濾及分類：標題或描述必須出現蟲害／滅蟲字眼，否則一律剔除。"""


def _hits(text, words):
    t = text.lower()
    return [w for w in words if w.lower() in t]


def pest_hits(text, rules):
    return {cat: n for cat, words in rules["pest_categories"].items() if (n := len(_hits(text, words)))}


def tech_hits(text, rules):
    return _hits(text, rules.get("pest_tech_keywords", []))


def relevance(item, rules):
    title, desc = item["title"], item.get("description", "")
    text = title + " " + desc
    if _hits(text, rules["exclude_keywords"]):
        return 0
    if not (pest_hits(text, rules) or tech_hits(text, rules)):
        return 0
    score = 3 * len(_hits(title, rules["core_keywords"])) + len(_hits(desc, rules["core_keywords"]))
    if _hits(text, rules["districts"]) or "香港" in text or "Hong Kong" in text:
        score += 2
    if item.get("tier") == "official":
        score += 1
    return score


def classify(item, rules):
    text = item["title"] + " " + item.get("description", "")
    excluded = bool(_hits(text, rules["exclude_keywords"]))
    pests = {} if excluded else pest_hits(text, rules)
    cats = [c for c, _ in sorted(pests.items(), key=lambda x: -x[1])]
    if not cats and not excluded and tech_hits(text, rules):
        cats = ["技術及藥劑"]
    if cats:
        cats += [c for c, words in rules["context_categories"].items() if _hits(text, words)]
    item["categories"] = list(dict.fromkeys(cats))
    item["districts"] = _hits(text, rules["districts"])
    high = _hits(text, rules["high_priority_keywords"])
    med = _hits(text, rules["medium_priority_keywords"])
    if high:
        item["priority"], item["priority_reason"] = "高", "、".join(high[:3])
    elif med:
        item["priority"], item["priority_reason"] = "中", "、".join(med[:3])
    else:
        item["priority"], item["priority_reason"] = "低", "一般資訊"
    return item
