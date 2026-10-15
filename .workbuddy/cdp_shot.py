# -*- coding: utf-8 -*-
"""CDP 无头浏览器截图：导航 → 依次执行 JS（点击/输入）→ 截图。

用法：
  python cdp_shot.py --url "http://localhost:5173/#/recognize" --out rec.png \
      --click ".shutter" --wait 2500 --w 520 --h 1600
  python cdp_shot.py --url ... --out x.png --js "document.querySelector('.x').click()" --js "..."
"""
from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import time
import urllib.request

import websocket

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PROFILE = r"D:\PetWiseService\.workbuddy\edge-profile"
PORT = 9222


def wait_devtools(timeout=15):
    for _ in range(timeout * 2):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list", timeout=2) as r:
                targets = json.load(r)
            for t in targets:
                if t.get("type") == "page":
                    return t["webSocketDebuggerUrl"]
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError("devtools 未就绪")


class Cdp:
    def __init__(self, ws_url: str):
        self.ws = websocket.create_connection(ws_url, timeout=30)
        self.mid = 0

    def call(self, method: str, params: dict | None = None):
        self.mid += 1
        self.ws.send(json.dumps({"id": self.mid, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.mid:
                return msg

    def eval(self, expr: str, await_promise: bool = False):
        params = {"expression": expr, "returnByValue": True}
        if await_promise:
            params["awaitPromise"] = True
        r = self.call("Runtime.evaluate", params)
        return r.get("result", {}).get("result", {}).get("value")

    def click_wait(self, sel: str, timeout_ms: int = 8000):
        """页面内轮询等待元素出现并点击（规避渲染时序抖动）。"""
        expr = (
            "new Promise((resolve)=>{"
            f"const t0=Date.now();"
            f"const iv=setInterval(()=>{{"
            f"const el=document.querySelector({json.dumps(sel)});"
            "if(el){clearInterval(iv);el.click();resolve('clicked@'+Date.now());}"
            "else if(Date.now()-t0>" + str(timeout_ms) + "){clearInterval(iv);resolve('timeout');}"
            "},120);})"
        )
        return self.eval(expr, await_promise=True)

    def shot(self, path: str):
        r = self.call("Page.captureScreenshot", {"format": "png"})
        data = base64.b64decode(r["result"]["data"])
        with open(path, "wb") as f:
            f.write(data)
        return len(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--click", action="append", default=[], help="CSS 选择器，点击")
    ap.add_argument("--js", action="append", default=[], help="任意 JS 表达式")
    ap.add_argument("--wait", type=int, default=2500, help="动作后等待毫秒")
    ap.add_argument("--w", type=int, default=520)
    ap.add_argument("--h", type=int, default=1600)
    ap.add_argument("--download", default=None, help="下载目录（允许浏览器下载）")
    a = ap.parse_args()

    proc = subprocess.Popen(
        [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
         f"--remote-debugging-port={PORT}", f"--user-data-dir={PROFILE}",
         "--remote-allow-origins=*",
         f"--window-size={a.w},{a.h}", "--hide-scrollbars", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    try:
        ws_url = wait_devtools()
        cdp = Cdp(ws_url)
        cdp.call("Page.enable")
        if a.download:
            try:
                cdp.call("Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": a.download})
            except Exception:
                pass
            cdp.call("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": a.download})
        cdp.call("Emulation.setDeviceMetricsOverride",
                 {"width": a.w, "height": a.h, "deviceScaleFactor": 2, "mobile": True})
        cdp.call("Page.navigate", {"url": a.url})
        time.sleep(2.5)  # 等 Vue 挂载 + 入场动画
        for sel in a.click:
            ok = cdp.click_wait(sel)
            print(f"click {sel}: {ok}")
            time.sleep(a.wait / 1000)
        for js in a.js:
            print("js ->", cdp.eval(js, await_promise=True))
            time.sleep(a.wait / 1000)
        time.sleep(0.5)
        n = cdp.shot(a.out)
        print(f"saved {a.out} ({n} bytes)")
    finally:
        proc.terminate()


if __name__ == "__main__":
    sys.exit(main())
