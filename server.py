#!/usr/bin/env python3
import sys
import os
import json
import urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import concurrent.futures

# Add zap-infrastructure scripts directory to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../zap-infrastructure/scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import stress_test_engine

class DocsStressTestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_POST(self):
        if self.path.startswith("/api/run-stress-test"):
            self._handle_run_stress_test()
        else:
            self.send_error(404, "Endpoint not found")

    def _handle_run_stress_test(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
        
        parsed_body = {}
        if body_bytes:
            try:
                parsed_body = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                pass

        # Extract CCU (default = 1)
        ccu = int(parsed_body.get("ccu") or 1)
        ccu = max(1, min(100, ccu))

        stats = stress_test_engine.StatsCollector()
        all_logs = []
        all_orders = []

        def run_worker(worker_idx):
            phone_idx = 600 + (worker_idx % 101)
            phone = f"0356465{phone_idx:03d}"
            session = stress_test_engine.ZapUserSession(
                base_url="https://uat-api.zap.vn",
                brand_id="e8cb2035-8d7d-4959-8776-6c2706a8c5ec",
                stats=stats
            )
            success = session.run_user_flow(phone=phone, password="Theluong1503@", dialing_code="+84", worker_idx=worker_idx)
            return session.request_logs

        # Execute parallel worker flows against live UAT API
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(ccu, 20)) as executor:
            futures = [executor.submit(run_worker, i) for i in range(ccu)]
            for f in concurrent.futures.as_completed(futures):
                try:
                    logs = f.result()
                    all_logs.extend(logs)
                except Exception as e:
                    print(f"Worker execution error: {e}")

        # Format orders
        for idx, ord_rec in enumerate(stats.created_orders):
            qty = (idx % 10) + 1
            all_orders.append({
                "phone": ord_rec.phone,
                "order_code": ord_rec.order_code,
                "order_number": ord_rec.order_number,
                "order_id": ord_rec.order_id,
                "quantity": qty,
                "total_amount": ord_rec.total_amount,
                "status": ord_rec.status,
                "details": {
                    "id": ord_rec.order_id,
                    "order_code": ord_rec.order_code,
                    "order_number": ord_rec.order_number,
                    "customer_phone": ord_rec.phone,
                    "quantity": qty,
                    "total_amount": ord_rec.total_amount,
                    "status": ord_rec.status,
                    "created_at": "Real API Live Response"
                }
            })

        # Calculate percentiles
        all_durations = sorted([r["latency"] for r in all_logs]) if all_logs else [0]
        p50 = all_durations[int(len(all_durations) * 0.50)] if all_durations else 0
        p95 = all_durations[int(len(all_durations) * 0.95)] if all_durations else 0

        res_payload = {
            "success": True,
            "ccu": ccu,
            "total_requests": len(all_logs),
            "orders": all_orders,
            "requests": sorted(all_logs, key=lambda x: x["id"]),
            "stats": {
                "p50": round(p50, 2),
                "p95": round(p95, 2),
                "pass_count": len([r for r in all_logs if 200 <= r["status"] < 300]),
                "fail_count": len([r for r in all_logs if r["status"] >= 300 or r["status"] == 0])
            }
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(res_payload).encode("utf-8"))

def run_server(port=8080):
    server_address = ("", port)
    httpd = ThreadingHTTPServer(server_address, DocsStressTestHandler)
    print(f"🚀 ZAP System Design Server with Live API Stress Test Engine running at http://localhost:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
