import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import json
from flask import Flask, request, jsonify

ACCESS_TOKEN = "EAF2KBRxntS4BRlNiNPDxSVzt5Nrec7KTBI0ies9TsocLQ1IcgV5m7QpDoapIIZB25pHPDZCyBVZAPmN1bCR6lAi2X8xM6vIvdPAlznLZAgmB82l75UWTRKfKqPZBal7z5ZCQzRs3esLDMHQ511QNcdfx5veDdkk58QuMUCp55ZCdKGPVxlbZCZBFl4w76soS3rQZDZD"

API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

app = Flask(__name__)


def graph_get(endpoint, params={}):
    params["access_token"] = ACCESS_TOKEN
    try:
        r = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=15)
        return r.json()
    except Exception as e:
        return {"error": {"message": str(e)}}


def graph_post(endpoint, data={}):
    data["access_token"] = ACCESS_TOKEN
    try:
        r = requests.post(f"{BASE_URL}{endpoint}", data=data, timeout=15)
        return r.json()
    except Exception as e:
        return {"error": {"message": str(e)}}


TOOLS = [
    {"name": "get_ad_accounts", "description": "جلب كل الحسابات الإعلانية", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "get_campaigns", "description": "جلب الحملات", "inputSchema": {"type": "object", "properties": {"account_id": {"type": "string"}}, "required": ["account_id"]}},
    {"name": "get_account_insights", "description": "إحصائيات الحساب", "inputSchema": {"type": "object", "properties": {"account_id": {"type": "string"}, "date_preset": {"type": "string"}}, "required": ["account_id"]}},
    {"name": "get_campaign_insights", "description": "إحصائيات كامبين", "inputSchema": {"type": "object", "properties": {"campaign_id": {"type": "string"}, "date_preset": {"type": "string"}}, "required": ["campaign_id"]}},
    {"name": "get_adsets", "description": "Ad sets لكامبين", "inputSchema": {"type": "object", "properties": {"campaign_id": {"type": "string"}}, "required": ["campaign_id"]}},
    {"name": "get_adset_insights", "description": "إحصائيات ad set", "inputSchema": {"type": "object", "properties": {"adset_id": {"type": "string"}, "date_preset": {"type": "string"}}, "required": ["adset_id"]}},
    {"name": "get_ads", "description": "الإعلانات جوه ad set", "inputSchema": {"type": "object", "properties": {"adset_id": {"type": "string"}}, "required": ["adset_id"]}},
    {"name": "get_ad_insights", "description": "إحصائيات إعلان", "inputSchema": {"type": "object", "properties": {"ad_id": {"type": "string"}, "date_preset": {"type": "string"}}, "required": ["ad_id"]}},
    {"name": "update_campaign_status", "description": "تشغيل/إيقاف كامبين", "inputSchema": {"type": "object", "properties": {"campaign_id": {"type": "string"}, "status": {"type": "string", "enum": ["ACTIVE", "PAUSED"]}}, "required": ["campaign_id", "status"]}},
    {"name": "update_adset_status", "description": "تشغيل/إيقاف ad set", "inputSchema": {"type": "object", "properties": {"adset_id": {"type": "string"}, "status": {"type": "string", "enum": ["ACTIVE", "PAUSED"]}}, "required": ["adset_id", "status"]}},
    {"name": "update_ad_status", "description": "تشغيل/إيقاف إعلان", "inputSchema": {"type": "object", "properties": {"ad_id": {"type": "string"}, "status": {"type": "string", "enum": ["ACTIVE", "PAUSED"]}}, "required": ["ad_id", "status"]}},
    {"name": "update_adset_budget", "description": "تعديل بودجت ad set (بالقروش، 10000 = 100 جنيه)", "inputSchema": {"type": "object", "properties": {"adset_id": {"type": "string"}, "daily_budget": {"type": "string"}}, "required": ["adset_id", "daily_budget"]}},
    {"name": "update_campaign_budget", "description": "تعديل بودجت كامبين CBO", "inputSchema": {"type": "object", "properties": {"campaign_id": {"type": "string"}, "daily_budget": {"type": "string"}}, "required": ["campaign_id", "daily_budget"]}},
    {"name": "copy_campaign", "description": "نسخ كامبين", "inputSchema": {"type": "object", "properties": {"campaign_id": {"type": "string"}, "account_id": {"type": "string"}}, "required": ["campaign_id", "account_id"]}},
    {"name": "copy_adset", "description": "نسخ ad set", "inputSchema": {"type": "object", "properties": {"adset_id": {"type": "string"}, "campaign_id": {"type": "string"}}, "required": ["adset_id", "campaign_id"]}},
    {"name": "get_pixels", "description": "Pixels الحساب", "inputSchema": {"type": "object", "properties": {"account_id": {"type": "string"}}, "required": ["account_id"]}},
    {"name": "get_pixel_stats", "description": "إحصائيات pixel", "inputSchema": {"type": "object", "properties": {"pixel_id": {"type": "string"}, "date_preset": {"type": "string"}}, "required": ["pixel_id"]}},
    {"name": "get_pixel_events", "description": "أحداث الـ pixel", "inputSchema": {"type": "object", "properties": {"pixel_id": {"type": "string"}, "date_preset": {"type": "string"}}, "required": ["pixel_id"]}},
    {"name": "get_signal_source_insights", "description": "EMQ وجودة الإشارة", "inputSchema": {"type": "object", "properties": {"pixel_id": {"type": "string"}}, "required": ["pixel_id"]}},
    {"name": "get_domains_and_aem", "description": "Domains وAEM", "inputSchema": {"type": "object", "properties": {"account_id": {"type": "string"}, "business_id": {"type": "string"}}, "required": ["account_id"]}},
]


def handle_tool(name, arguments):
    if name == "get_ad_accounts":
        return graph_get("/me/adaccounts", {"fields": "id,name,account_status,currency,balance"})
    elif name == "get_campaigns":
        return graph_get(f"/{arguments['account_id']}/campaigns", {"fields": "id,name,status,objective,daily_budget,lifetime_budget"})
    elif name == "get_account_insights":
        return graph_get(f"/{arguments['account_id']}/insights", {"fields": "impressions,clicks,spend,ctr,cpc,reach", "date_preset": arguments.get("date_preset", "last_7d")})
    elif name == "get_campaign_insights":
        return graph_get(f"/{arguments['campaign_id']}/insights", {"fields": "campaign_name,impressions,clicks,spend,ctr,cpc,reach,actions,cost_per_action_type,frequency", "date_preset": arguments.get("date_preset", "last_7d")})
    elif name == "get_adsets":
        return graph_get(f"/{arguments['campaign_id']}/adsets", {"fields": "id,name,status,daily_budget,lifetime_budget,bid_strategy,optimization_goal,billing_event,targeting"})
    elif name == "get_adset_insights":
        return graph_get(f"/{arguments['adset_id']}/insights", {"fields": "adset_name,impressions,clicks,spend,ctr,cpc,reach,actions,cost_per_action_type,frequency", "date_preset": arguments.get("date_preset", "last_7d")})
    elif name == "get_ads":
        return graph_get(f"/{arguments['adset_id']}/ads", {"fields": "id,name,status,creative{title,body,image_url}"})
    elif name == "get_ad_insights":
        return graph_get(f"/{arguments['ad_id']}/insights", {"fields": "ad_name,impressions,clicks,spend,ctr,cpc,reach,actions,cost_per_action_type,frequency", "date_preset": arguments.get("date_preset", "last_7d")})
    elif name == "update_campaign_status":
        return graph_post(f"/{arguments['campaign_id']}", {"status": arguments["status"]})
    elif name == "update_adset_status":
        return graph_post(f"/{arguments['adset_id']}", {"status": arguments["status"]})
    elif name == "update_ad_status":
        return graph_post(f"/{arguments['ad_id']}", {"status": arguments["status"]})
    elif name == "update_adset_budget":
        return graph_post(f"/{arguments['adset_id']}", {"daily_budget": arguments["daily_budget"]})
    elif name == "update_campaign_budget":
        return graph_post(f"/{arguments['campaign_id']}", {"daily_budget": arguments["daily_budget"]})
    elif name == "copy_campaign":
        return graph_post(f"/{arguments['campaign_id']}/copies", {"account_id": arguments["account_id"]})
    elif name == "copy_adset":
        return graph_post(f"/{arguments['adset_id']}/copies", {"campaign_id": arguments["campaign_id"]})
    elif name == "get_pixels":
        data = graph_get(f"/{arguments['account_id']}/adspixels", {"fields": "id,name,creation_time,last_fired_time,is_unavailable,owner_business"})
        if "data" in data:
            for px in data["data"]:
                px["status"] = "unavailable" if px.get("is_unavailable") else "active"
        return data
    elif name == "get_pixel_stats":
        pixel_id = arguments["pixel_id"]
        pixel_info = graph_get(f"/{pixel_id}", {"fields": "id,name,creation_time,last_fired_time,is_unavailable,match_rate_approx"})
        stats = graph_get(f"/{pixel_id}/stats", {"aggregation": "event"})
        return {"pixel_info": pixel_info, "stats": stats}
    elif name == "get_pixel_events":
        pixel_id = arguments["pixel_id"]
        event_results = {}
        for event in ["PageView", "ViewContent", "AddToCart", "InitiateCheckout", "Purchase"]:
            event_results[event] = graph_get(f"/{pixel_id}/stats", {"aggregation": "event", "event": event})
        return {"event_breakdown": event_results}
    elif name == "get_signal_source_insights":
        pixel_id = arguments["pixel_id"]
        diagnostics = graph_get(f"/{pixel_id}", {"fields": "id,name,last_fired_time,is_unavailable,match_rate_approx"})
        return {"pixel_diagnostics": diagnostics}
    elif name == "get_domains_and_aem":
        account_id = arguments["account_id"]
        business_id = arguments.get("business_id")
        pixels_data = graph_get(f"/{account_id}/adspixels", {"fields": "id,name"})
        pixel_aem = []
        if "data" in pixels_data:
            for px in pixels_data["data"]:
                pid = px["id"]
                aem_config = graph_get(f"/{pid}/aem_conversion_filter", {"fields": "pixel_id,domains,event_configurations"})
                pixel_aem.append({"pixel_id": pid, "pixel_name": px.get("name"), "aem_config": aem_config})
        domain_data = graph_get(f"/{business_id}/owned_domains", {"fields": "id,domain,verification_status"}) if business_id else {"note": "Provide business_id"}
        return {"pixels_and_aem": pixel_aem, "domain_verification": domain_data}
    return {"error": f"Tool not found: {name}"}


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "server": "meta-ads-mcp"})


@app.route("/mcp", methods=["POST"])
def mcp():
    body = request.get_json()
    method = body.get("method")
    params = body.get("params", {})
    req_id = body.get("id")

    if method == "initialize":
        return jsonify({"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "meta-ads-mcp", "version": "1.0.0"}}})
    elif method == "tools/list":
        return jsonify({"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}})
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        result = handle_tool(tool_name, arguments)
        return jsonify({"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}})
    else:
        return jsonify({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
