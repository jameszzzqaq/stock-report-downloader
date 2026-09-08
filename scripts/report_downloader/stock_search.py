from __future__ import annotations

import json
import re
from collections.abc import Callable

import requests

from .utils import (
    SearchError,
    StockTarget,
    build_session,
    is_chinese_text,
    names_match,
    normalize_a_code,
    normalize_hk_code,
    request,
    safe_json,
)


CNINFO_SEARCH_URL = "https://www.cninfo.com.cn/new/information/topSearch/query"
HKEX_PARTIAL_URL = "https://www1.hkexnews.hk/search/partial.do"
CNINFO_SEARCH_HEADERS = {
    "Referer": "https://www.cninfo.com.cn/",
    "X-Requested-With": "XMLHttpRequest",
}
HKEX_SEARCH_HEADERS = {
    "Referer": "https://www1.hkexnews.hk/search/titlesearch.xhtml",
    "X-Requested-With": "XMLHttpRequest",
}
SIMPLE_TO_TRADITIONAL_MAP = str.maketrans({
    "业": "業",
    "东": "東",
    "丝": "絲",
    "丽": "麗",
    "乐": "樂",
    "乔": "喬",
    "亚": "亞",
    "产": "產",
    "众": "眾",
    "优": "優",
    "伟": "偉",
    "传": "傳",
    "体": "體",
    "余": "餘",
    "关": "關",
    "兴": "興",
    "兽": "獸",
    "农": "農",
    "凯": "凱",
    "创": "創",
    "刘": "劉",
    "华": "華",
    "协": "協",
    "医": "醫",
    "华": "華",
    "单": "單",
    "厂": "廠",
    "历": "歷",
    "压": "壓",
    "发": "發",
    "台": "臺",
    "叶": "葉",
    "号": "號",
    "后": "後",
    "吴": "吳",
    "启": "啟",
    "国": "國",
    "图": "圖",
    "圣": "聖",
    "场": "場",
    "坚": "堅",
    "报": "報",
    "复": "復",
    "奥": "奧",
    "妇": "婦",
    "孙": "孫",
    "宁": "寧",
    "宝": "寶",
    "实": "實",
    "审": "審",
    "寿": "壽",
    "将": "將",
    "尔": "爾",
    "尧": "堯",
    "层": "層",
    "岚": "嵐",
    "岭": "嶺",
    "币": "幣",
    "庄": "莊",
    "广": "廣",
    "庆": "慶",
    "库": "庫",
    "应": "應",
    "庄": "莊",
    "庙": "廟",
    "废": "廢",
    "张": "張",
    "强": "強",
    "彦": "彥",
    "彻": "徹",
    "德": "德",
    "忆": "憶",
    "怀": "懷",
    "态": "態",
    "总": "總",
    "恒": "恆",
    "悦": "悅",
    "惠": "惠",
    "爱": "愛",
    "户": "戶",
    "执": "執",
    "扩": "擴",
    "扬": "揚",
    "择": "擇",
    "报": "報",
    "担": "擔",
    "拜": "拜",
    "拟": "擬",
    "携": "攜",
    "摄": "攝",
    "收": "收",
    "敌": "敵",
    "数": "數",
    "断": "斷",
    "无": "無",
    "时": "時",
    "晋": "晉",
    "晓": "曉",
    "暂": "暫",
    "术": "術",
    "来": "來",
    "杨": "楊",
    "标": "標",
    "树": "樹",
    "桥": "橋",
    "档": "檔",
    "欧": "歐",
    "欢": "歡",
    "步": "步",
    "汉": "漢",
    "汤": "湯",
    "沪": "滬",
    "洁": "潔",
    "润": "潤",
    "涛": "濤",
    "湾": "灣",
    "点": "點",
    "炼": "煉",
    "热": "熱",
    "爷": "爺",
    "牵": "牽",
    "玛": "瑪",
    "环": "環",
    "电": "電",
    "疗": "療",
    "监": "監",
    "盘": "盤",
    "矿": "礦",
    "礼": "禮",
    "离": "離",
    "稳": "穩",
    "税": "稅",
    "简": "簡",
    "粮": "糧",
    "红": "紅",
    "约": "約",
    "级": "級",
    "纪": "紀",
    "纬": "緯",
    "纳": "納",
    "纵": "縱",
    "纺": "紡",
    "纯": "純",
    "纲": "綱",
    "维": "維",
    "绿": "綠",
    "网": "網",
    "罗": "羅",
    "联": "聯",
    "职": "職",
    "聪": "聰",
    "肠": "腸",
    "胜": "勝",
    "腾": "騰",
    "艺": "藝",
    "药": "藥",
    "萨": "薩",
    "蓝": "藍",
    "补": "補",
    "见": "見",
    "观": "觀",
    "规": "規",
    "觉": "覺",
    "览": "覽",
    "誉": "譽",
    "让": "讓",
    "讯": "訊",
    "证": "證",
    "评": "評",
    "话": "話",
    "诚": "誠",
    "语": "語",
    "课": "課",
    "调": "調",
    "谢": "謝",
    "谱": "譜",
    "财": "財",
    "质": "質",
    "购": "購",
    "资": "資",
    "赛": "賽",
    "赞": "贊",
    "赵": "趙",
    "跃": "躍",
    "车": "車",
    "软": "軟",
    "辉": "輝",
    "运": "運",
    "过": "過",
    "迈": "邁",
    "还": "還",
    "这": "這",
    "进": "進",
    "远": "遠",
    "连": "連",
    "适": "適",
    "选": "選",
    "逊": "遜",
    "递": "遞",
    "逻": "邏",
    "郑": "鄭",
    "里": "裡",
    "钟": "鐘",
    "铁": "鐵",
    "银": "銀",
    "销": "銷",
    "锋": "鋒",
    "锦": "錦",
    "镇": "鎮",
    "长": "長",
    "门": "門",
    "闭": "閉",
    "问": "問",
    "闻": "聞",
    "际": "際",
    "陆": "陸",
    "险": "險",
    "阳": "陽",
    "际": "際",
    "际": "際",
    "难": "難",
    "际": "際",
    "雾": "霧",
    "静": "靜",
    "项": "項",
    "须": "須",
    "顾": "顧",
    "风": "風",
    "飞": "飛",
    "馆": "館",
    "马": "馬",
    "验": "驗",
    "鱼": "魚",
    "鸟": "鳥",
    "麦": "麥",
    "黄": "黃",
    "齐": "齊",
    # ponytail: not OpenCC; add issuer-name pairs when a live HK search misses
    "为": "為",
    "开": "開",
    "会": "會",
    "团": "團",
    "学": "學",
    "经": "經",
    "济": "濟",
    "与": "與",
    "于": "於",
    "现": "現",
    "设": "設",
    "价": "價",
    "区": "區",
    "亿": "億",
    "从": "從",
    "对": "對",
    "个": "個",
    "营": "營",
    "处": "處",
    "备": "備",
    "导": "導",
    "当": "當",
    "录": "錄",
    "愿": "願",
    "虑": "慮",
    "师": "師",
    "带": "帶",
    "帮": "幫",
    "异": "異",
    "归": "歸",
    "头": "頭",
    "内": "內",
    "并": "並",
    "两": "兩",
    "说": "說",
    "给": "給",
    "没": "沒",
    "样": "樣",
    "种": "種",
    "称": "稱",
    "据": "據",
    "条": "條",
})


def infer_market(query: str, forced_market: str | None = None) -> str:
    if forced_market in {"a", "hk"}:
        return forced_market
    normalized = query.strip().upper()
    if normalized.endswith(".HK"):
        return "hk"
    if normalized.isdigit():
        if len(normalized) == 6:
            return "a"
        if len(normalized) <= 5:
            return "hk"
    if is_chinese_text(query):
        return "a"
    raise SearchError("无法自动识别市场，请使用 --market 指定 a 或 hk。")


def resolve_stock(
    query: str,
    market: str | None = None,
    *,
    session: requests.Session | None = None,
) -> StockTarget:
    active_session = session or build_session()
    normalized = query.strip()
    inferred_market = infer_market(normalized, market)

    if inferred_market == "a" and normalized.isdigit():
        code = normalize_a_code(normalized)
        return StockTarget(
            query=query,
            code=code,
            market="a",
            exchange="sse" if code.startswith(("6", "9")) else "szse",
        )

    if inferred_market == "hk" and re.fullmatch(r"\d{1,5}(\.HK)?", normalized.upper()):
        code = normalize_hk_code(normalized)
        return StockTarget(query=query, code=code, market="hk", stock_id=code)

    if market == "a":
        result = search_cninfo_by_name(normalized, active_session)
        if result:
            return result
        raise SearchError(f"未找到 A 股股票: {query}")

    if market == "hk":
        result = search_hk_by_name(normalized, active_session)
        if result:
            return result
        raise SearchError(f"未找到港股股票: {query}")

    for searcher in (search_cninfo_by_name, search_hk_by_name):
        result = searcher(normalized, active_session)
        if result:
            return result
    raise SearchError(f"未找到股票: {query}")


def search_cninfo_by_name(name: str, session: requests.Session) -> StockTarget | None:
    response = request(
        session,
        "POST",
        CNINFO_SEARCH_URL,
        params={"keyWord": name, "maxNum": 20},
        headers=CNINFO_SEARCH_HEADERS,
    )
    payload = safe_json(response)
    candidates = _iter_cninfo_candidates(payload)
    matched = _best_named_item(
        name,
        candidates,
        lambda item: str(item.get("zwjc") or item.get("secName") or "").strip(),
        lambda item: str(item.get("code") or item.get("secCode") or "").strip(),
    )
    if matched is None:
        return None
    return _build_a_target(name, matched)


def search_hk_by_name(name: str, session: requests.Session) -> StockTarget | None:
    for candidate_name in _hk_name_candidates(name):
        result = _search_hk_by_single_name(candidate_name, session)
        if result:
            result.query = name
            return result
    return None


def _search_hk_by_single_name(name: str, session: requests.Session) -> StockTarget | None:
    response = request(
        session,
        "GET",
        HKEX_PARTIAL_URL,
        params={
            "lang": "ZH",
            "type": "A",
            "name": name,
            "market": "SEHK",
            "callback": "callback",
        },
        headers=HKEX_SEARCH_HEADERS,
    )
    match = re.search(r"callback\((.*)\)\s*;?\s*$", response.text, re.S)
    if not match:
        return None
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise SearchError("HKEX 返回了无法解析的证券搜索结果。") from exc
    stock_info = payload.get("stockInfo", [])
    items = [item for item in stock_info if isinstance(item, dict)]
    matched = _best_named_item(
        name,
        items,
        lambda item: str(item.get("name") or "").strip(),
        lambda item: str(item.get("code") or "").strip(),
    )
    if matched is None:
        return None
    stock_code = str(matched.get("code") or "").strip()
    return StockTarget(
        query=name,
        code=normalize_hk_code(stock_code),
        market="hk",
        name=str(matched.get("name") or "").strip(),
        stock_id=str(matched.get("stockId") or "").strip(),
        extra={"raw": matched},
    )


def _hk_name_candidates(name: str) -> list[str]:
    candidates = [name]
    converted = name.translate(SIMPLE_TO_TRADITIONAL_MAP)
    if converted != name:
        candidates.append(converted)
    return candidates


def _best_named_item(
    query: str,
    items: list[dict],
    name_of: Callable[[dict], str],
    code_of: Callable[[dict], str],
) -> dict | None:
    partial: dict | None = None
    for item in items:
        item_name = name_of(item)
        item_code = code_of(item)
        if not item_code:
            continue
        if query == item_name or query == item_code:
            return item
        if partial is None and names_match(query, item_name):
            partial = item
    return partial


def _build_a_target(query: str, candidate: dict) -> StockTarget:
    sec_name = str(candidate.get("zwjc") or candidate.get("secName") or "").strip()
    sec_code = str(candidate.get("code") or candidate.get("secCode") or "").strip()
    code = normalize_a_code(sec_code)
    return StockTarget(
        query=query,
        code=code,
        market="a",
        name=sec_name,
        exchange="sse" if code.startswith(("6", "9")) else "szse",
        org_id=str(candidate.get("orgId") or candidate.get("orgid") or "").strip(),
        stock_id=str(candidate.get("stockCode") or "").strip(),
        extra={"raw": candidate},
    )


def _iter_cninfo_candidates(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("classifiedAnnouncements", "stockList", "result", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []
