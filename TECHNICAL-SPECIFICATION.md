# SPARXSTAR EVENT HORIZON v2.1

## Technical Specification

Starisian Technologies | April 2026

CONFIDENTIAL | PROPRIETARY

================================================================================
## SYSTEM IDENTITY
================================================================================

Product:          SPARXSTAR Event Horizon

Version:          2.1

Repository:       sparxstar-event-horizon

Platform Position: Nginx perimeter layer -- sits between Cloudflare edge and

                  the application stack (system-core / Varnish / WordPress).

Classification:   Detection intelligence core.

Governing Statement: Event Horizon computes threat signals and outputs them.

It does not enforce runtime behaviour. Enforcement is the operator's

responsibility, implemented in the operator's server block using the variables

Event Horizon provides.

================================================================================
## WHAT EVENT HORIZON IS
================================================================================

Event Horizon is an Nginx http-context map library. It receives every inbound

request, evaluates it against a complete threat intelligence ruleset, and

produces two outputs:

  1. $spx_final_decision -- a binary variable (0|1) the operator uses to ghost

     malicious connections before they reach the application.

  2. X-SPX-* and X-SPARXSTAR-* headers -- threat intelligence signals forwarded

     to the upstream PHP application (Helios / Sirus) on every proxied request.

Nothing else is Event Horizon's responsibility. Location blocks, security

response headers, proxy_pass directives, rate limit enforcement, and all other

runtime decisions belong to the operator's server block or platform baseline.

================================================================================
## WHAT EVENT HORIZON IS NOT
================================================================================

Event Horizon does not ship:

  - Security response headers (HSTS, CSP, X-Frame-Options, Permissions-Policy,

    etc.). These are owned by system-core, which is the expected platform

    baseline for all SPARXSTAR deployments. Operators not using system-core

    must provide their own response headers independently.

  - Location blocks. The bot trap (/spx-trap), file extension locks, xmlrpc

    block, health check endpoint, and all other blocking locations are operator

    decisions. Event Horizon documents how to write them; it does not ship them.

  - The firewall gate check. The single line:

      if ($spx_final_decision) { return 444; }

    is a placement instruction, not a file. It appears in the operator example

    documentation. It is not a shipped snippet.

  - Static asset bypass configuration. The operator decides which routes bypass

    threat evaluation and how. Event Horizon provides no stub or placeholder

    for this.

  - An nginx.conf or sites-available configuration. Runtime tuning (buffers,

    timeouts, keepalive, upstream definitions, rate limit enforcement) belongs

    to the operator's deployment adapter or platform baseline.

================================================================================
## THREAT INTELLIGENCE CORE -- 000-spx-horizon-logic.conf
================================================================================

The entire threat intelligence computation lives in one file:

conf.d/000-spx-horizon-logic.conf

This file is the product. It contains:

SECTION 1  Kernel optimisation directives (map_hash_bucket_size,

           reset_timedout_connection, ignore_invalid_headers).

SECTION 2  Real-IP safety guard ($spx_real_ip alias).

SECTION 3  Rate limiting zone definitions (spx_conn, spx_req, spx_wp_login,

           spx_graphql, spx_submission, spx_general). Operators apply these

           zones in their own location blocks.

SECTION 4  Emergency bypass map ($spx_firewall_active). Operators add their

           admin egress IP here to prevent self-lockout.

SECTION 5  Logging filter ($spx_log_trigger), Cloudflare origin gate

           ($spx_from_cloudflare), and country risk amplifier

           ($spx_high_risk_geo, loaded from maps/high-risk-geo.map).

SECTION 6  Threat intelligence maps -- full 8G Firewall v1.5 coverage

           translated from if-block form to http-context map directives:

           $spx_bad_query    -- 17 rule groups covering SQLi, XSS, RCE, path

                                traversal, PHP injection, header injection,

                                encoded attack sequences, dangerous function

                                calls, global variable abuse. (41 map entries)

           $spx_bad_uri      -- 23 rule groups covering path traversal, web

                                shells, sensitive files, backup archives,

                                dangerous file extensions, scanner tool names,

                                admin panel paths, (50 map entries)

           $spx_bad_bot      -- 12 rule groups covering scanners, scrapers,

                                exploit tools, encoded UA payloads, legacy

                                browser fingerprints, 120+ named bad bots.

                                (15 map entries)

           $spx_bad_referer  -- SQL injection and spam/pharma keywords in the

                                HTTP Referer header.

           $spx_bad_method   -- Dangerous HTTP methods (CONNECT, DEBUG, MOVE,

                                TRACE, TRACK). REST methods not blocked.

           $spx_bad_cookie   -- Encoded injection characters in cookie values.

           $spx_empty_ua_is_bad -- Empty User-Agent policy. Blocked by default;

                                operator allowlists monitoring tool IPs here.

SECTION 7  Behavioural maps (SPARXSTAR additions beyond 8G):

           $spx_bad_post, $spx_fake_trackback, $spx_comment_spam,

           $spx_bad_content_disposition, $spx_missing_host.

SECTION 8  Threat aggregation. Three-step model:

           8a. $spx_base_threat -- any non-geo vector fires.

           8b. $spx_geo_amplified -- geo=1 AND base_threat=1.

           8c. $spx_threat_detected -- base OR geo-amplified.

           Geo alone never triggers a block.

SECTION 9  Final decision matrix ($spx_final_decision). Combines

           $spx_firewall_active and $spx_threat_detected into a single

           binary. Operator usage: if ($spx_final_decision) { return 444; }

SECTION 10 Cloudflare Worker trust infrastructure. Shared secret verification

           ($spy_worker_secret_ok), combined trust gate ($spy_is_trusted_worker),

           and conditional X-SPARXSTAR-* header forwarding maps.

SECTION 11 Threat signal propagation. Reason flag maps ($spx_rflag_*) and

           risk score map ($spx_risk_score, 0-100 numeric tier).

================================================================================
OUTPUT LAYER -- snippets/spx-dynamic-proxy-headers.conf
================================================================================

This snippet is included inside every location block that proxies to a dynamic

upstream. It sets:

  X-Worker-Origin-Secret   -- stripped (never forwarded to upstream)

  X-SPARXSTAR-User         -- forwarded only when $spx_is_trusted_worker = 1

  X-SPARXSTAR-Session      -- forwarded only when $spx_is_trusted_worker = 1

  X-SPARXSTAR-Roles        -- forwarded only when $spx_is_trusted_worker = 1

  X-SPARXSTAR-Issued       -- forwarded only when $spx_is_trusted_worker = 1

  X-SPARXSTAR-Expires      -- forwarded only when $spx_is_trusted_worker = 1

  X-SPARXSTAR-Site         -- forwarded only when $spx_is_trusted_worker = 1

  X-SPARXSTAR-AuthLevel    -- forwarded only when $spx_is_trusted_worker = 1

  Standard proxy headers (Host, X-Real-IP, X-Forwarded-For, X-Forwarded-Proto,

  X-Forwarded-Port, X-Request-ID, Connection)

  X-SPX-Threat    -- 0|1 binary threat flag

  X-SPX-Risk      -- 0-100 numeric triage score

  X-SPX-Geo-Risk  -- 0|1 high-risk country flag

  X-SPX-Bot       -- 0|1 bad bot flag

  X-SPX-Reason    -- pipe-delimited active signal tokens

All X-SPX-* values are server-computed. proxy_set_header overwrites any

client-supplied value, making spoofing impossible from outside Nginx.

This snippet is not included in static asset bypass locations.

================================================================================
SUPPORTING FILES
================================================================================

conf.d/spx-cloudflare-trust.conf

  set_real_ip_from directives for all Cloudflare IP ranges. Auto-generated

  by scripts/update_cloudflare.py. Must be kept in sync with the

  geo $realip_remote_addr $spx_from_cloudflare block in Section 5a of

  000-spx-horizon-logic.conf -- both lists must contain identical CIDR ranges.

maps/high-risk-geo.map

  Include fragment loaded inside the $spx_high_risk_geo map block. Contains

  ISO 3166-1 alpha-2 country codes. Operators edit this file to customise

  the geo amplifier list. Geo codes act as risk amplifiers only -- they

  never trigger a block without another concurrent threat signal.

scripts/update_cloudflare.py

  Refreshes spx-cloudflare-trust.conf from the Cloudflare IP API with atomic

  write and nginx -t guard before apply.

scripts/update_bots.py

  Refreshes the $spx_bad_bot map entries in 000-spx-horizon-logic.conf.

secrets/worker-secret.conf

  Not committed. Created manually by the operator. Contains one line:

  "your-shared-secret-value" 1;

  Nginx will not start if this file is absent.

================================================================================
OPERATOR DOCUMENTATION -- docs/operator-example-server-block.conf
================================================================================

This file documents how an operator wires Event Horizon into their server

block. It is not shipped code. It contains:

  - How to include 000-spx-horizon-logic.conf (via conf.d/*.conf in nginx.conf)

  - How to include spx-dynamic-proxy-headers.conf per proxied location

  - How to apply the firewall gate: if ($spx_final_decision) { return 444; }

  - How to apply rate limiting zones in location blocks

  - How to implement a bot trap location using $spx_firewall_active

  - How to implement file extension blocking location blocks

  - How to implement a health check endpoint exempt from UA checks

  - A note that security response headers are provided by system-core and

    are not Event Horizon's responsibility

================================================================================

REPOSITORY STIRUCTURE

================================================================================

sparxstar-event-horizon/
|-- conf.d/
|   |-- 000-spx-horizon-logic.conf       Core. Maps, zones, aggregation,
|   |                                     worker trust, risk scoring.
|   |-- spx-cloudflare-trust.conf        RealIP trust list.
|-- maps/
|   |-- high-risk-geo.map                Geo amplifier include fragment.
|-- snippets/
|   |-- spx-dynamic-proxy-headers.conf   X-SPX-* and X-SPARXSTAR-* output.
|-- docs/
|   |-- operator-example-server-block.conf  Operator reference. Not code.
|-- scripts/
|   |-- update_cloudflare.py
|   |-- update_bots.py
|-- tests/
|   |-- test_firewall.py
|-- secrets/
    |-- worker-secret.conf               Not committed. Operator-created.

================================================================================
BOUNDARY RUME
================================================================================

If a file contains proxy_pass, return, add_header, a location block, or a

limit_req enforcement directive, it is operator runtime code and does not

belong in Event Horizon. Event Horizon ships maps and proxy headers. The

operator ships everything else.

================================================================================

Version: 2.1 | Starisian Technologies | April 2026

CONFIDENTIAL | PROPRIETARY | All Rights Reserved
