# Walkthrough: Complete Enterprise Documentation Portal

Expanded the documentation portal with 3 essential enterprise system guides:

## 🚀 Live Localhost Server
👉 **[http://localhost:8090](http://localhost:8090)**

---

## 📚 Complete Documentation Sections Available

1. **Ecosystem Topology Diagram**: Interactive 4-column SVG topology with native auto-rotating arrowheads, zoom controls, and fullscreen view.
2. **End-to-End Security Architecture (`view-security`)**:
   - Layer 0: SSL/TLS Certificate Pinning on FE Clients.
   - Layer 1: OAuth2 Bearer Access Token Verification.
   - Layer 2: Hardware-bound RSA 2048-bit Digital Signatures & Nonce Replay Attack Defense.
3. **Redis Lua High-Concurrency Engine (`view-cart`)**:
   - Single-threaded atomic cart mutations (`cart_mutate.lua`).
   - Sliding Window Rate Limiter (`rate_limiter.lua`).
   - Idempotency Lock Release (`release_lock.lua`).
4. **Event-Driven Pub/Sub Topic Catalog (`view-events`)**:
   - `order.created.event`, `payment.success.event`, `user.registered.event`.
5. **PostgreSQL Standalone ERD Schemas (`view-database`)**:
   - Table structure breakdown for `identity_db`, `commerce_db`, `payment_db`, and `notification_db`.
6. **Payment IPN Webhook Verification (`view-webhook`)**:
   - HMAC-SHA256 checksum verification & IP whitelisting for Payoo, VietQR (BIDV/NAPAS), MoMo & Stripe callbacks.
7. **API Endpoint Catalog (`view-api`)**:
   - Complete 350 endpoints parsed from Java Controllers with method badges, search bar, and cURL generator.
