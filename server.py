
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import requests
import json
import uuid
import traceback
from flask import Flask, request, jsonify, redirect

ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "YOUR_TOKEN_HERE")

API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"
BASE_URL_SELF = os.environ.get("BASE_URL_SELF", "https://web-production-2a8d3.up.railway.app")

app = Flask(__name__)
clients = {}

def log_request(endpoint_name):
    try:
        print(f"\n=== {endpoint_name} ===")
        print("Method:", request.method)
        print("Path:", request.path)
        print("Headers:", dict(request.headers))
        try:
            print("JSON:", request.get_json(silent=True))
        except:
            pass
    except Exception as e:
        print("Logging error:", e)

def graph_get(endpoint, params=None):
    params = params or {}
    params["access_token"] = ACCESS_TOKEN
    try:
        r = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=15)
        return r.json()
    except Exception as e:
        return {"error": {"message": str(e)}}

def graph_post(endpoint, data=None):
    data = data or {}
    data["access_token"] = ACCESS_TOKEN
    try:
        r = requests.post(f"{BASE_URL}{endpoint}", data=data, timeout=15)
        return r.json()
    except Exception as e:
        return {"error": {"message": str(e)}}

TOOLS = [
    {"name": "get_ad_accounts", "description": "جلب كل الحسابات الإعلانية", "inputSchema": {"type": "object", "properties": {}}}
]

@app.route("/", methods=["GET"])
def health():
    log_request("health")
    return jsonify({"status": "ok", "server": "meta-ads-mcp"})

@app.route("/.well-known/oauth-authorization-server", methods=["GET"])
def oauth_metadata():
    log_request("oauth_metadata")
    return jsonify({
        "issuer": BASE_URL_SELF,
        "authorization_endpoint": f"{BASE_URL_SELF}/auth",
        "token_endpoint": f"{BASE_URL_SELF}/token",
        "registration_endpoint": f"{BASE_URL_SELF}/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256"]
    })

@app.route("/.well-known/oauth-protected-resource/mcp", methods=["GET"])
def oauth_protected_resource():
    log_request("oauth_protected_resource")
    return jsonify({
        "resource": f"{BASE_URL_SELF}/mcp",
        "authorization_servers": [BASE_URL_SELF],
        "bearer_methods_supported": ["header"]
    })

@app.route("/register", methods=["POST"])
def register():
    try:
        log_request("register")
        body = request.get_json(silent=True) or {}
        client_id = str(uuid.uuid4())
        client_secret = str(uuid.uuid4())

        clients[client_id] = {
            "client_secret": client_secret,
            "redirect_uris": body.get("redirect_uris", [])
        }

        return jsonify({
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": body.get("redirect_uris", []),
            "grant_types": ["authorization_code"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "client_secret_post"
        }), 201
    except Exception:
        print(traceback.format_exc())
        return jsonify({"error": "register_failed"}), 500

@app.route("/auth", methods=["GET"])
def auth():
    try:
        log_request("auth")
        redirect_uri = request.args.get("redirect_uri", "")
        state = request.args.get("state", "")
        code = str(uuid.uuid4())
        return redirect(f"{redirect_uri}?code={code}&state={state}")
    except Exception:
        print(traceback.format_exc())
        return jsonify({"error": "auth_failed"}), 500

@app.route("/token", methods=["POST"])
def token():
    try:
        log_request("token")
        client_id = request.form.get("client_id")
        client_secret = request.form.get("client_secret")

        if client_id and client_id in clients:
            if clients[client_id]["client_secret"] != client_secret:
                return jsonify({"error": "invalid_client"}), 401

        return jsonify({
            "access_token": "meta-ads-token-" + str(uuid.uuid4()),
            "token_type": "bearer",
            "expires_in": 3600
        })
    except Exception:
        print(traceback.format_exc())
        return jsonify({"error": "token_failed"}), 500

@app.route("/mcp", methods=["POST"])
def mcp():
    try:
        log_request("mcp")
        body = request.get_json(silent=True) or {}
        method = body.get("method")
        params = body.get("params", {})
        req_id = body.get("id")

        if method == "initialize":
            return jsonify({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "meta-ads-mcp", "version": "1.1.0"}
                }
            })

        elif method == "tools/list":
            return jsonify({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS}
            })

        return jsonify({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": "Method not found"}
        })

    except Exception:
        print(traceback.format_exc())
        return jsonify({"error": "mcp_crashed"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
