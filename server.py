import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import json
import logging
import secrets
from flask import Flask, request, jsonify, redirect
from datetime import datetime, timedelta

# =============================================
# LOGGING
# =============================================
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

ACCESS_TOKEN = "EAF2KBRxntS4BRlNiNPDxSVzt5Nrec7KTBI0ies9TsocLQ1IcgV5m7QpDoapIIZB25pHPDZCyBVZAPmN1bCR6lAi2X8xM6vIvdPAlznLZAgmB82l75UWTRKfKqPZBal7z5ZCQzRs3esLDMHQ511QNcdfx5veDdkk58QuMUCp55ZCdKGPVxlbZCZBFl4w76soS3rQZDZD"

API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"
BASE_URL_SERVER = "https://web-production-2a8d3.up.railway.app"

app = Flask(__name__)

# =============================================
# IN-MEMORY STORES
# =============================================
registered_clients = {}   # client_id -> client_data
auth_codes = {}           # code -> {client_id, redirect_uri, expires}
access_tokens = {}        # token -> {client_id, expires}


# =============================================
# GRAPH API HELPERS
# =============================================
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


# =============================================
# TOOLS
# =============================================
TOOLS = [
    {"name": "get_ad_accounts", "description": "جلب كل الحسابات الإعلانية", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "get_campaigns", "description": "جلب الحملات", "inputSchema": {"type": "object", "properties": {"account_id": {"type": "string"}}, "required": ["account_id"]}},
    {"name": "get_account_insights", "description": "إحصائيات الحساب", "inputSchema": {"type": "object", "properties": {"account_id": {"type": "string"}, "date_preset": {"type": "string"}}, "required": ["account_id"]}},
    {"name": "get_campaign_insights", "description": "إحصائيات كامبين", "inputSchema": {"type": "object", "properties": {"campaign_id": {"type": "string"}, "date_preset": {"type": "string"}}, "required": ["campaign_id"]}},
    {"name": "get_adsets", "description": "Ad sets لكامبين", "inputSchema": {"type": "object", "properties": {"campaign_id": {"type": "string"}}, "required": ["campaign_id"]}},
    {"name": "get_adset_insights", "description": "إحصائيات ad set", "inputSchema": {"type": "object", "properties": {"adset_id": {"type": "string"}, "date_preset": {"type": "string"}}, "required": ["adset_id"]}},
    {"name": "get_ads", "description": "الإعلانات جوه ad set", "inputSchema": {"type": "object", "properties": {"adset_id": {"type": "string"}}, "required": ["adset_id"]}},
    {"name": "get_ad_insights", "description": "إحصائيات إعلان", "inputSchema": {"type": "object", "properties": {"ad_id": {"type": "string"}, "date_preset": {"type": "string"}}, "required": ["ad_id"]}},
    {"name": "update_campaign_status", "description": "تشغيل/إيقاف كامبين", "inputSchema": {"type": "object", "properties": {"campaign_id": {"type": "string"}, "status": {"type": "string"}}, "required": ["campaign_id", "status"]}},
    {"name": "update_adset_status", "description": "تشغيل/إيقاف ad set", "inputSchema": {"type": "object", "properties": {"adset_id": {"type": "string"}, "status": {"type": "string"}}, "required": ["adset_id", "status"]}},
    {"name": "update_ad_status", "description": "تشغيل/إيقاف إعلان", "inputSchema": {"type": "object", "properties": {"ad_id": {"type": "string"}, "status": {"type": "string"}}, "required": ["ad_id", "status"]}},
    {"name": "update_adset_budget", "description": "تعديل بودجت ad set", "inputSchema": {"type": "object", "properties": {"adset_id": {"type": "string"}, "daily_budget": {"type": "string"}}, "required": ["adset_id", "daily_budget"]}},
    {"name": "update_campaign_budget", "description": "تعديل بودجت كامبين", "inputSchema": {"type": "object", "properties": {"campaign_id": {"type": "string"}, "daily_budget": {"type": "string"}}, "required": ["campaign_id", "daily_budget"]}},
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


# =============================================
# OAUTH ENDPOINTS
# =============================================

@app.route("/.well-known/oauth-authorization-server", methods=["GET"])
def oauth_metadata():
    logger.info("GET /.well-known/oauth-authorization-server")
    metadata = {
        "issuer": BASE_URL_SERVER,
        "authorization_endpoint": f"{BASE_URL_SERVER}/auth",
        "token_endpoint": f"{BASE_URL_SERVER}/token",
        "registration_endpoint": f"{BASE_URL_SERVER}/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "none"],
        "code_challenge_methods_supported": ["S256", "plain"]
    }
    logger.info(f"Returning metadata: {json.dumps(metadata)}")
    return jsonify(metadata)


@app.route("/register", methods=["POST"])
def register():
    body = request.get_json(silent=True) or {}
    logger.info(f"POST /register - incoming: {json.dumps(body)}")

    client_id = secrets.token_urlsafe(16)
    client_secret = secrets.token_urlsafe(32)

    client_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uris": body.get("redirect_uris", []),
        "grant_types": body.get("grant_types", ["authorization_code"]),
        "response_types": body.get("response_types", ["code"]),
        "client_name": body.get("client_name", "Claude"),
        "registered_at": datetime.utcnow().isoformat()
    }

    registered_clients[client_id] = client_data
    logger.info(f"Registered client_id={client_id}, redirect_uris={client_data['redirect_uris']}")

    return jsonify(client_data), 201


@app.route("/auth", methods=["GET"])
def auth():
    client_id = request.args.get("client_id", "")
    redirect_uri = request.args.get("redirect_uri", "")
    state = request.args.get("state", "")
    code_challenge = request.args.get("code_challenge", "")
    code_challenge_method = request.args.get("code_challenge_method", "")

    logger.info(f"GET /auth - client_id={client_id} redirect_uri={redirect_uri} state={state} code_challenge={code_challenge}")

    if not redirect_uri:
        logger.error("Missing redirect_uri")
        return jsonify({"error": "missing redirect_uri"}), 400

    code = secrets.token_urlsafe(32)
    auth_codes[code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "expires": datetime.utcnow() + timedelta(minutes=10)
    }

    logger.info(f"Generated auth_code={code} for client_id={client_id}")

    return f"""
    <html>
    <head><style>
        body {{ font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f0f2f5; }}
        .box {{ background: white; padding: 40px; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); text-align: center; max-width: 400px; }}
        h2 {{ color: #1877f2; }}
        .btn {{ padding: 12px 30px; font-size: 16px; background: #1877f2; color: white; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; margin-top: 20px; }}
    </style></head>
    <body>
    <div class="box">
        <h2>Meta Ads MCP</h2>
        <p>Claude يطلب الاتصال بحساباتك الإعلانية</p>
        <a href="{redirect_uri}?code={code}&state={state}" class="btn">Authorize</a>
    </div>
    </body></html>
    """


@app.route("/token", methods=["POST"])
def token():
    body = request.get_json(silent=True) or request.form.to_dict()
    logger.info(f"POST /token - incoming: {json.dumps(body)}")

    grant_type = body.get("grant_type")
    code = body.get("code")
    redirect_uri = body.get("redirect_uri")
    client_id = body.get("client_id")

    if grant_type != "authorization_code":
        logger.error(f"Unsupported grant_type: {grant_type}")
        return jsonify({"error": "unsupported_grant_type"}), 400

    if code not in auth_codes:
        logger.error(f"Invalid code: {code}")
        return jsonify({"error": "invalid_grant", "error_description": "code not found"}), 400

    stored = auth_codes[code]

    if datetime.utcnow() > stored["expires"]:
        logger.error(f"Expired code: {code}")
        del auth_codes[code]
        return jsonify({"error": "invalid_grant", "error_description": "code expired"}), 400

    if stored["redirect_uri"] != redirect_uri:
        logger.error(f"Redirect URI mismatch: expected={stored['redirect_uri']} got={redirect_uri}")
        return jsonify({"error": "invalid_grant", "error_description": "redirect_uri mismatch"}), 400

    del auth_codes[code]

    token_value = secrets.token_urlsafe(32)
    access_tokens[token_value] = {
        "client_id": client_id,
        "expires": datetime.utcnow() + timedelta(days=30)
    }

    logger.info(f"Issued token for client_id={client_id}")

    return jsonify({
        "access_token": token_value,
        "token_type": "bearer",
        "expires_in": 2592000
    })


# =============================================
# MCP ENDPOINT
# =============================================

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "server": "meta-ads-mcp", "clients": len(registered_clients)})


@app.route("/mcp", methods=["POST"])
def mcp():
    body = request.get_json()
    method = body.get("method")
    params = body.get("params", {})
    req_id = body.get("id")

    logger.info(f"POST /mcp method={method}")

    if method == "initialize":
        return jsonify({"jsonrpc": "2.0", "id": req_id, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "meta-ads-mcp", "version": "2.0.0"}
        }})
    elif method == "tools/list":
        return jsonify({"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}})
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        logger.info(f"tools/call name={tool_name} args={arguments}")
        result = handle_tool(tool_name, arguments)
        return jsonify({"jsonrpc": "2.0", "id": req_id, "result": {
            "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
        }})
    else:
        return jsonify({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
