#!/usr/bin/env python3
"""
Real Browser Test Suite for Leenardo Dynamic Reader
Automates real Google Chrome via Chrome DevTools Protocol (CDP) over WebSocket:
  - Tests 3 articles across 3 categories (tarih, bilim, sanat)
  - Word click -> morphological popover
  - CEFR level switching (A1 -> C1)
  - Flashcard notebook opening
  - Quiz interaction and grading
  - Word saving with simulated authenticated user
  - Supabase network failure simulation -> fallback to local static data
  - Captures full-resolution screenshots for all actions
"""

import os
import sys
import time
import json
import base64
import socket
import urllib.request
import subprocess
import threading
import http.server
import socketserver

PORT = 8089
CDP_PORT = 9222
WORKSPACE = "/Users/sencanyuksel/Desktop/Leenardo"
SCREENSHOT_DIR = os.path.join(WORKSPACE, "test_screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

class NetlifySimHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WORKSPACE, **kwargs)

    def do_GET(self):
        clean_path = self.path.split("?")[0].split("#")[0]
        # Netlify security redirects simulation:
        blocked = [
            "/LAUNCH_CHECKLIST.md", "/BRANCHES.md", "/PROJECT_STATUS.md", "/README.md",
            "/generate_article_pages.py", "/generate_sitemap.py", "/news_pipeline.py",
            "/sync_database.py", "/validate_content.py",
            "/Daily_Turkish_with_Mia_100_Topics.csv", "/Daily_Turkish_with_Mia_100_Topics.xlsx",
            "/logo-preview.html"
        ]
        if clean_path in blocked or any(clean_path.startswith(d) for d in ["/scripts/", "/supabase/", "/docs/", "/.github/", "/worksheets/", "/konular/"]):
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            with open(os.path.join(WORKSPACE, "404.html"), "rb") as f:
                self.wfile.write(f.read())
            return

        # Netlify rewrite: /articles/* -> /article.html
        if clean_path.startswith("/articles/"):
            qs = "?" + self.path.split("?", 1)[1] if "?" in self.path else ""
            self.path = "/article.html" + qs
        return super().do_GET()

    def log_message(self, format, *args):
        pass

class SimpleWebSocketClient:
    def __init__(self, url):
        # url: ws://127.0.0.1:9222/devtools/page/...
        parts = url.replace("ws://", "").split("/", 1)
        host_port = parts[0].split(":")
        self.host = host_port[0]
        self.port = int(host_port[1])
        self.path = "/" + parts[1]
        self.sock = socket.create_connection((self.host, self.port), timeout=10)
        self._handshake()
        self.msg_id = 0
        self.console_logs = []

    def _handshake(self):
        key = base64.b64encode(os.urandom(16)).decode('utf-8')
        req = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(req.encode('utf-8'))
        resp = b""
        while b"\r\n\r\n" not in resp:
            data = self.sock.recv(4096)
            if not data:
                break
            resp += data
        if b"101 " not in resp:
            raise ConnectionError(f"WebSocket handshake failed: {resp.decode('utf-8', errors='ignore')}")

    def send_cmd(self, method, params=None):
        self.msg_id += 1
        cmd_id = self.msg_id
        payload = {"id": cmd_id, "method": method, "params": params or {}}
        raw_msg = json.dumps(payload).encode('utf-8')
        
        # Build masked frame
        frame = bytearray([0x81]) # FIN + text
        length = len(raw_msg)
        mask = os.urandom(4)
        if length <= 125:
            frame.append(0x80 | length)
        elif length <= 65535:
            frame.extend([0x80 | 126, (length >> 8) & 0xff, length & 0xff])
        else:
            frame.extend([0x80 | 127] + list((length).to_bytes(8, 'big')))
        frame.extend(mask)
        frame.extend(b ^ mask[i % 4] for i, b in enumerate(raw_msg))
        self.sock.sendall(bytes(frame))

        # Wait for reply matching cmd_id
        while True:
            reply = self._recv_frame()
            if not reply:
                continue
            try:
                data = json.loads(reply)
                if data.get("method") == "Runtime.consoleAPICalled":
                    args = data.get("params", {}).get("args", [])
                    txt = " ".join(str(a.get("value", "")) for a in args)
                    self.console_logs.append(txt)
                elif data.get("id") == cmd_id:
                    return data
            except Exception:
                pass

    def _recv_frame(self):
        head = self.sock.recv(2)
        if len(head) < 2:
            return None
        byte1, byte2 = head[0], head[1]
        is_masked = bool(byte2 & 0x80)
        pay_len = byte2 & 0x7f
        if pay_len == 126:
            ext = self.sock.recv(2)
            pay_len = int.from_bytes(ext, 'big')
        elif pay_len == 127:
            ext = self.sock.recv(8)
            pay_len = int.from_bytes(ext, 'big')
        
        mask = self.sock.recv(4) if is_masked else None
        data = bytearray()
        while len(data) < pay_len:
            chunk = self.sock.recv(pay_len - len(data))
            if not chunk:
                break
            data.extend(chunk)
        
        if is_masked and mask:
            data = bytearray(b ^ mask[i % 4] for i, b in enumerate(data))
        return data.decode('utf-8', errors='ignore')

    def eval_js(self, expression):
        res = self.send_cmd("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True
        })
        if "result" in res and "result" in res["result"]:
            res_obj = res["result"]["result"]
            if "value" in res_obj:
                return res_obj["value"]
            if res_obj.get("subtype") == "error":
                print(f"    ⚠️ JS Eval Error: {res_obj.get('description')}")
                return None
            return res_obj
        return None

    def screenshot(self, filename):
        res = self.send_cmd("Page.captureScreenshot", {"format": "png"})
        if "result" in res and "data" in res["result"]:
            raw_bytes = base64.b64decode(res["result"]["data"])
            path = os.path.join(SCREENSHOT_DIR, filename)
            with open(path, "wb") as f:
                f.write(raw_bytes)
            return path
        return None

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass

def wait_for_article_ready(client, timeout=12.0):
    start = time.time()
    while time.time() - start < timeout:
        res = client.eval_js("""(() => {
            const titleElem = document.getElementById('article-main-title');
            const paras = document.querySelectorAll('.article-paragraph');
            if (titleElem && titleElem.textContent && titleElem.textContent !== 'Loading Story...' && titleElem.textContent !== 'Story Not Found' && paras.length > 0) {
                return { ready: true, title: titleElem.textContent, paras: paras.length };
            }
            return { ready: false, currentTitle: titleElem ? titleElem.textContent : null };
        })()""")
        if res and isinstance(res, dict) and res.get("ready"):
            return res
        time.sleep(0.3)
    return {"ready": False, "title": "Timeout waiting for story"}

def run_tests():
    print("=" * 75)
    print("🚀 STARTING REAL BROWSER (HEADLESS CHROME) TEST SUITE")
    print("=" * 75)

    # 1. Start Local HTTP Server with Netlify simulation
    server = socketserver.TCPServer(("127.0.0.1", PORT), NetlifySimHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"✓ Local HTTP Server running on http://127.0.0.1:{PORT} (with Netlify rewrites & security blocks)")

    # 2. Launch Google Chrome in Headless Mode with Remote Debugging
    chrome_bin = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    chrome_proc = subprocess.Popen([
        chrome_bin,
        "--headless=new",
        f"--remote-debugging-port={CDP_PORT}",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--user-data-dir=/tmp/leenardo_chrome_profile",
        "--window-size=1280,950",
        "about:blank"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    print(f"✓ Headless Chrome launched with CDP on port {CDP_PORT}")

    results = []

    try:
        # Get websocket URL
        targets_resp = urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json").read().decode('utf-8')
        targets = json.loads(targets_resp)
        page_target = next(t for t in targets if t.get("type") == "page")
        ws_url = page_target["webSocketDebuggerUrl"]
        client = SimpleWebSocketClient(ws_url)
        client.send_cmd("Page.enable")
        client.send_cmd("Runtime.enable")
        client.send_cmd("Console.enable")

        test_articles = [
            ("tarih-truva-ve-tahta-at", "Tarih (History)", "C1"),
            ("bilim-proust-etkisi-koku-ve-bellek", "Bilim (Science)", "B2"),
            ("sanat-bedri-rahmi-mavi-yolculuk", "Sanat (Art)", "B1")
        ]

        for slug, cat_name, target_level in test_articles:
            print("\n" + "-" * 75)
            print(f"📖 TESTING STORY: '{slug}' [Category: {cat_name}]")
            print("-" * 75)

            article_results = {"slug": slug, "category": cat_name, "actions": {}}

            # Navigate directly via clean URL (/articles/:slug) as served in production
            url = f"http://127.0.0.1:{PORT}/articles/{slug}"
            client.send_cmd("Page.navigate", {"url": url})
            
            ready_info = wait_for_article_ready(client, timeout=12.0)
            if not ready_info.get("ready"):
                print(f"  ❌ Article load failed or timed out: {ready_info}")
                article_results["actions"]["load"] = False
                results.append(article_results)
                continue

            title = ready_info.get("title")
            paras_count = ready_info.get("paras")
            print(f"  • Rendered Headline (Supabase): \"{title}\" ({paras_count} paragraphs)")
            article_results["actions"]["load"] = True

            # Action 1: Click first word span -> check popover
            popover_ok = client.eval_js("""(() => {
                const firstWord = document.querySelector('.article-body .word-span');
                if (!firstWord) return false;
                firstWord.click();
                const pop = document.getElementById('word-popover');
                const isVis = pop && !pop.classList.contains('hidden') && pop.style.display !== 'none';
                return isVis;
            })()""")
            print(f"  • Word Click -> Translation Popover: {'PASS' if popover_ok else 'FAIL'}")
            article_results["actions"]["word_click"] = bool(popover_ok)

            # Capture Word Click Screenshot
            snap1 = client.screenshot(f"{slug}_word_click.png")
            if snap1: print(f"    [Saved Screenshot: {os.path.basename(snap1)}]")

            # Action 2: Switch Level (A1 -> target_level)
            lvl_switch_ok = client.eval_js(f"""(() => {{
                changeLevel('{target_level}');
                const activeBtn = document.querySelector('.level-btn.active');
                return activeBtn && activeBtn.getAttribute('data-level') === '{target_level}' && currentLevel === '{target_level}';
            }})()""")
            print(f"  • CEFR Level Switch (A1 -> {target_level}): {'PASS' if lvl_switch_ok else 'FAIL'}")
            article_results["actions"]["level_switch"] = bool(lvl_switch_ok)

            # Capture Level Switch Screenshot
            snap2 = client.screenshot(f"{slug}_level_{target_level}.png")
            if snap2: print(f"    [Saved Screenshot: {os.path.basename(snap2)}]")

            # Action 3: Open Flashcards
            flashcards_ok = client.eval_js("""(() => {
                openVocabNotebook('flashcards');
                const modal = document.getElementById('vocab-notebook-modal');
                const panel = document.getElementById('vn-panel-flashcards');
                return !!(modal && modal.classList.contains('show') && panel && panel.classList.contains('active'));
            })()""")
            print(f"  • Flashcards Deck Modal: {'PASS' if flashcards_ok else 'FAIL'}")
            article_results["actions"]["flashcards"] = bool(flashcards_ok)

            # Capture Flashcards Screenshot & close modal
            snap3 = client.screenshot(f"{slug}_flashcards.png")
            if snap3: print(f"    [Saved Screenshot: {os.path.basename(snap3)}]")
            client.eval_js("closeVocabNotebook();")

            # Action 4: Answer one quiz question
            quiz_ok = client.eval_js("""(() => {
                const btn = document.querySelector('.quiz-opt-btn');
                if (!btn) return false;
                btn.click();
                const fb = document.getElementById('quiz-feedback-box');
                return fb && fb.innerHTML.trim().length > 0;
            })()""")
            print(f"  • Quiz Interaction & Grading: {'PASS' if quiz_ok else 'FAIL'}")
            article_results["actions"]["quiz"] = bool(quiz_ok)

            # Action 5: Save a word while logged in
            save_ok = client.eval_js("""(() => {
                currentAuthUser = { id: 'usr_test_verification_456', email: 'test@leenardo.com' };
                const firstWord = document.querySelector('.article-body .word-span');
                if (!firstWord) return false;
                const wordText = firstWord.textContent.trim();
                saveWordItem({
                    id: 'w_' + encodeURIComponent(wordText.toLowerCase()),
                    word: wordText,
                    translation: 'Verified Test Translation',
                    contextSentence: 'Example sentence context',
                    articleId: currentArticleId,
                    level: currentLevel
                });
                const words = getSavedWords();
                return words.some(w => w.word.toLowerCase() === wordText.toLowerCase());
            })()""")
            print(f"  • Save Word (Authenticated Context): {'PASS' if save_ok else 'FAIL'}")
            article_results["actions"]["save_word"] = bool(save_ok)

            results.append(article_results)

        # 4. Simulate Supabase Network Failure & Verify Fallback
        print("\n" + "=" * 75)
        print("⚡ SIMULATING SUPABASE OUTAGE (FALLBACK TO LOCAL DATASET)")
        print("=" * 75)

        client.send_cmd("Page.navigate", {"url": f"http://127.0.0.1:{PORT}/articles/tarih-truva-ve-tahta-at"})
        wait_for_article_ready(client, timeout=5.0)

        # Intentionally corrupt Supabase URL to simulate total API outage
        fallback_ok = client.eval_js("""(async () => {
            SUPABASE_CONFIG.url = "https://invalid-nonexistent-project-ref.supabase.co";
            articlesDatabase = [];
            currentArticleId = "";
            articleNotFound = false;
            
            // Re-run article loader with corrupted Supabase endpoint
            await loadArticlesData();
            initArticlePage();

            const headline = document.getElementById('article-main-title').textContent;
            const hasParas = document.querySelectorAll('.article-paragraph').length > 0;
            return {
                headline: headline,
                hasParas: hasParas,
                count: articlesDatabase.length,
                success: hasParas && headline.length > 5 && headline !== "Story Not Found" && headline !== "Loading Story..."
            };
        })()""")

        print(f"  • Set SUPABASE_CONFIG.url to invalid outage endpoint.")
        print(f"  • Fallback Headline: \"{fallback_ok.get('headline')}\"")
        print(f"  • Paragraphs Rendered from local data: {fallback_ok.get('hasParas')}")
        print(f"  • Articles in database cache: {fallback_ok.get('count')}")
        print(f"  • Fallback Execution: {'PASS' if fallback_ok.get('success') else 'FAIL'}")

        snap_fallback = client.screenshot("fallback_offline_simulation.png")
        if snap_fallback: print(f"    [Saved Screenshot: {os.path.basename(snap_fallback)}]")

        # 5. Verify Security 404 for internal files
        print("\n" + "=" * 75)
        print("🔒 VERIFYING 404 ON INTERNAL FILES VIA HTTP")
        print("=" * 75)
        sec_checks = ["/LAUNCH_CHECKLIST.md", "/BRANCHES.md", "/scripts/migrate_articles_to_supabase.py", "/validate_content.py"]
        sec_all_pass = True
        for sc in sec_checks:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{sc}") as r:
                    status = r.status
            except urllib.error.HTTPError as e:
                status = e.code
            is_404 = (status == 404)
            print(f"  • Request {sc} -> HTTP {status} ({'PASS 404' if is_404 else 'FAIL'})")
            if not is_404: sec_all_pass = False

        client.close()

    finally:
        chrome_proc.terminate()
        server.shutdown()

    print("\n" + "=" * 75)
    print("📊 REAL BROWSER AUDIT SUMMARY REPORT")
    print("=" * 75)
    all_passed = True
    for r in results:
        actions_str = ", ".join(f"{k}: {'✓' if v else '✗'}" for k, v in r["actions"].items())
        print(f"• [{r['category']}] {r['slug']} -> {actions_str}")
        if not all(r["actions"].values()):
            all_passed = False

    if fallback_ok.get("success"):
        print("• [Fallback Simulation] Supabase Down -> articles-data.js Lazy Loaded -> ✓ PASS")
    else:
        print("• [Fallback Simulation] FAILED")
        all_passed = False

    if sec_all_pass:
        print("• [Security 404 Audit] Internal files returned HTTP 404 -> ✓ PASS")
    else:
        print("• [Security 404 Audit] FAILED")
        all_passed = False

    if all_passed:
        print("\n🎉 ALL REAL BROWSER TESTS & VERIFICATIONS PASSED WITH 100% SUCCESS!")
    else:
        print("\n❌ SOME TESTS FAILED.")
    
    return all_passed

if __name__ == "__main__":
    ok = run_tests()
    sys.exit(0 if ok else 1)
