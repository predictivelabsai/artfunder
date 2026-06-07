/* Kanvas.ai -- chat client (SSE streaming, 3-pane interactions). */

(() => {
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => Array.from(document.querySelectorAll(sel));

    let currentSessionId = getSidFromURL();
    let currentAgentSlug = null;
    let streaming = false;

    const AGENT_PROMPTS = readJsonScript("agent-prompts-data") || {};
    const AGENT_NAMES = readJsonScript("agent-names-data") || {};

    function readJsonScript(id) {
        const el = document.getElementById(id);
        if (!el) return null;
        try { return JSON.parse(el.textContent); }
        catch (e) { return null; }
    }

    function getSidFromURL() {
        const p = new URLSearchParams(window.location.search);
        return p.get("sid") || "";
    }
    function setSid(sid) {
        currentSessionId = sid;
        const u = new URL(window.location);
        u.searchParams.set("sid", sid);
        history.replaceState(null, "", u);
    }

    function addBubble(role, text, agentSlug) {
        const wrap = document.createElement("div");
        wrap.className = `msg msg-${role}`;
        if (role === "assistant" && agentSlug) {
            const hdr = document.createElement("div");
            hdr.className = "msg-agent";
            const nice = AGENT_NAMES[agentSlug] || agentSlug;
            hdr.innerHTML = `<span class="msg-agent-icon">*</span><span class="msg-agent-label">${nice}</span>`;
            wrap.appendChild(hdr);
        }
        const bubble = document.createElement("div");
        bubble.className = "msg-bubble";
        bubble.textContent = text;
        wrap.appendChild(bubble);
        $("#messages").appendChild(wrap);
        scrollMessagesBottom();
        return bubble;
    }

function scrollMessagesBottom() {
        const m = $("#messages");
        if (m) m.scrollTop = m.scrollHeight;
    }

    function stripSQL(text) {
        text = text.replace(/```sql[\s\S]*?```/gi, '');
        text = text.replace(/\bSQL used:.*$/gim, '');
        const lines = text.split('\n');
        const out = [];
        let inSQL = false;
        for (const line of lines) {
            const trimmed = line.trim();
            if (!inSQL && /^(SELECT|WITH)\b/i.test(trimmed)) { inSQL = true; continue; }
            if (inSQL) {
                if (/^(FROM|JOIN|WHERE|GROUP|ORDER|HAVING|LIMIT|AND|OR|ON|LEFT|RIGHT|INNER|OUTER|CASE|WHEN|AS|UNION|INSERT|UPDATE|DELETE)\b/i.test(trimmed)
                    || /^[)(\s,]/.test(trimmed) || trimmed === '' || /;\s*$/.test(trimmed)) {
                    continue;
                }
                inSQL = false;
            }
            out.push(line);
        }
        return out.join('\n').replace(/\n{3,}/g, '\n\n').trim();
    }

    function renderMarkdownLite(text) {
        text = stripSQL(text);
        if (window.marked) return marked.parse(text);
        return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/\n/g, "<br>");
    }

    function tableToCSV(table) {
        const rows = [];
        table.querySelectorAll("tr").forEach(tr => {
            const cells = [];
            tr.querySelectorAll("th, td").forEach(td => {
                cells.push('"' + td.textContent.trim().replace(/"/g, '""') + '"');
            });
            rows.push(cells.join(","));
        });
        return rows.join("\n");
    }

    function enhanceTables(container) {
        if (!container) return;
        container.querySelectorAll("table").forEach(table => {
            if (table.dataset.enhanced) return;
            table.dataset.enhanced = "1";
            const toolbar = document.createElement("div");
            toolbar.className = "table-toolbar";
            const copyBtn = document.createElement("button");
            copyBtn.textContent = "Copy CSV";
            copyBtn.className = "table-action-btn";
            copyBtn.onclick = () => {
                navigator.clipboard.writeText(tableToCSV(table)).then(() => {
                    copyBtn.textContent = "Copied!";
                    setTimeout(() => { copyBtn.textContent = "Copy CSV"; }, 1500);
                });
            };
            const dlBtn = document.createElement("button");
            dlBtn.textContent = "Download CSV";
            dlBtn.className = "table-action-btn";
            dlBtn.onclick = () => {
                const blob = new Blob([tableToCSV(table)], { type: "text/csv" });
                const a = document.createElement("a");
                a.href = URL.createObjectURL(blob);
                a.download = "kanvas-data.csv";
                a.click();
                URL.revokeObjectURL(a.href);
            };
            toolbar.appendChild(copyBtn);
            toolbar.appendChild(dlBtn);
            table.parentNode.insertBefore(toolbar, table);
        });
    }

    // ── Thinking indicator ────────────────────────────────────
    const TOOL_LABELS = {
        art_market_query: ["Querying art market data", "Analyzing auction records", "Processing market statistics"],
        search_auction_lots: ["Searching auction lots", "Scanning auction records"],
        artist_auction_history: ["Looking up artist history", "Retrieving auction data"],
        art_market_chart: ["Building visualization", "Generating chart"],
        treemap_chart: ["Building market treemap", "Mapping artist sales"],
        price_trend_chart: ["Analyzing price trends", "Charting market data"],
        web_search: ["Searching the web", "Finding market insights"],
        game_master: ["The art world unfolds", "Game master is thinking"],
    };
    const GENERIC_LABELS = ["Thinking", "Analyzing", "Processing", "Working on it"];

    let thinker = null;
    function showThinking(bubble) {
        if (!bubble) return;
        thinker = {
            started: Date.now(),
            tool: null,
            labelIdx: 0,
            el: document.createElement("div"),
            timerId: null,
            rotateId: null,
        };
        thinker.el.className = "thinking-indicator";
        thinker.el.innerHTML = `<span class="dot"></span><span class="label">Thinking... <span class="secs">0s</span></span>`;
        bubble.parentElement.insertBefore(thinker.el, bubble);
        thinker.timerId = setInterval(updateThinking, 500);
    }
    function updateThinking() {
        if (!thinker) return;
        const secs = Math.floor((Date.now() - thinker.started) / 1000);
        const labels = thinker.tool ? (TOOL_LABELS[thinker.tool] || GENERIC_LABELS) : GENERIC_LABELS;
        const idx = Math.floor(secs / 3) % labels.length;
        const text = labels[idx];
        thinker.el.querySelector(".label").innerHTML = `${text}... <span class="secs">${secs}s</span>`;
    }
    function setThinkingTool(name) {
        if (!thinker) return;
        thinker.tool = name;
        updateThinking();
    }
    function hideThinking() {
        if (!thinker) return;
        clearInterval(thinker.timerId);
        if (thinker.el && thinker.el.parentElement) thinker.el.parentElement.removeChild(thinker.el);
        thinker = null;
    }

    // ── Sample cards ──────────────────────────────────────────
    const ART_GURU_CHARS = [
        { icon: "\u{1F3A8}", label: "Famous Artist", value: "famous_artist", desc: "5,000 gold · 3 knowledge" },
        { icon: "\u{1F525}", label: "Emerging Artist", value: "emerging_artist", desc: "3,000 gold · 2 knowledge" },
        { icon: "\u{1F3DB}", label: "Gallerist", value: "gallerist", desc: "8,000 gold · 4 knowledge" },
        { icon: "\u{1F3DB}️", label: "Museum Curator", value: "museum_curator", desc: "4,000 gold · 5 knowledge" },
        { icon: "\u{1F4B0}", label: "Billionaire Collector", value: "billionaire_collector", desc: "15,000 gold · 1 knowledge" },
        { icon: "\u{1F50D}", label: "Regular Collector", value: "regular_collector", desc: "6,000 gold · 3 knowledge" },
    ];

    window.updateSampleCards = (slug) => {
        const row = $("#sample-cards-row");
        if (!row) return;

        const isGame = slug === "art_guru" || window.location.pathname.includes("art-guru");
        if (isGame) {
            row.innerHTML = "";
            ART_GURU_CHARS.forEach(ch => {
                const b = document.createElement("button");
                b.className = "sample-card";
                b.title = ch.label;
                b.innerHTML = `<span class="sample-card-text"><span style="font-size:1.2em">${ch.icon}</span> <strong>${ch.label}</strong><br><span style="font-size:0.8em;color:#888">${ch.desc}</span></span>`;
                b.onclick = () => { fillChat(ch.value); sendMessage(null); };
                row.appendChild(b);
            });
            return;
        }

        let prompts = (slug && AGENT_PROMPTS[slug]) || [];
        if (!prompts.length) {
            prompts = [
                "artist: Konrad Magi",
                "market: top selling Estonian artists",
                "advise: EUR 50,000 budget for Baltic art",
                "value: Adamson-Eric tempera, 40x50cm",
                "auction: recent sales at Allee Galerii",
                "compare: Konrad Magi vs Ants Laikmaa",
            ];
        }
        row.innerHTML = "";
        prompts.slice(0, 6).forEach(p => {
            const b = document.createElement("button");
            b.className = "sample-card";
            b.title = p;
            const span = document.createElement("span");
            span.className = "sample-card-text";
            span.textContent = p;
            b.appendChild(span);
            b.onclick = () => { fillChat(p); sendMessage(null); };
            row.appendChild(b);
        });
    };

    window.onInputChange = (ta) => {};

    // Init sample cards on load
    if ($("#sample-cards-row")) updateSampleCards(null);

    // Handle prefill from navigation (e.g. agent click from Art Index)
    const prefill = new URLSearchParams(window.location.search).get("prefill");
    if (prefill) {
        requestAnimationFrame(() => {
            const ta = $("#chat-input");
            if (ta) { ta.value = prefill; ta.focus(); autoResize(ta); }
        });
    }

    // ── SSE send ──────────────────────────────────────────────
    async function sendMessage(evt) {
        if (evt) evt.preventDefault();
        if (streaming) return;
        const ta = $("#chat-input");
        if (!ta) return;
        const msg = ta.value.trim();
        if (!msg) return;

        streaming = true;
        const sendBtn = $("#send-btn");
        if (sendBtn) sendBtn.disabled = true;

        const wh = $("#welcome-hero");
        if (wh) wh.style.display = "none";

        addBubble("user", msg);
        ta.value = "";
        ta.style.height = "";

        const body = new URLSearchParams({ msg, sid: currentSessionId || "" });
        const chatEndpoint = window.location.pathname.includes("art-guru") ? "/app/art-guru/chat" : "/app/chat";
        const resp = await fetch(chatEndpoint, { method: "POST", body });
        if (!resp.ok) {
            addBubble("assistant", "Error: " + resp.status);
            streaming = false;
            if (sendBtn) sendBtn.disabled = false;
            return;
        }

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let bubble = null;
        let accumulated = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });

            let idx;
            while ((idx = buffer.indexOf("\n\n")) !== -1) {
                const raw = buffer.slice(0, idx);
                buffer = buffer.slice(idx + 2);
                handleEvent(raw, (type, payload) => {
                    if (type === "agent_route") {
                        const nice = payload.agent || AGENT_NAMES[payload.slug] || payload.slug;
                        const label = $("#current-agent-label");
                        if (label) label.textContent = nice;
                        currentAgentSlug = payload.slug;
                        updateSampleCards(payload.slug);
                        bubble = addBubble("assistant", "", payload.slug);
                        bubble.classList.add("streaming");
                        showThinking(bubble);
                    } else if (type === "token") {
                        if (!bubble) bubble = addBubble("assistant", "", "");
                        if (accumulated === "") hideThinking();
                        accumulated += payload.text;
                        bubble.innerHTML = renderMarkdownLite(accumulated);
                        scrollMessagesBottom();
                    } else if (type === "tool_start") {
                        if (!thinker && bubble) showThinking(bubble);
                        setThinkingTool(payload.name);
                    } else if (type === "tool_end") {
                        // noop
                    } else if (type === "artifact_show") {
                        showArtifact(payload);
                    } else if (type === "error") {
                        hideThinking();
                        if (!bubble) bubble = addBubble("assistant", "", "");
                        bubble.textContent = "Error: " + (payload.message || "unknown");
                    } else if (type === "choices") {
                        if (bubble) {
                            const btns = document.createElement("div");
                            btns.className = "choice-buttons";
                            (payload.options || []).forEach(opt => {
                                const b = document.createElement("button");
                                b.className = "choice-btn";
                                b.innerHTML = opt.icon ? `<span class="choice-icon">${opt.icon}</span> ${opt.label}` : opt.label;
                                b.onclick = () => {
                                    btns.querySelectorAll(".choice-btn").forEach(x => x.disabled = true);
                                    b.classList.add("choice-selected");
                                    fillChat(opt.value || opt.label);
                                    sendMessage(null);
                                };
                                btns.appendChild(b);
                            });
                            bubble.parentElement.appendChild(btns);
                            scrollMessagesBottom();
                        }
                    } else if (type === "session") {
                        if (payload.sid) setSid(payload.sid);
                    } else if (type === "done") {
                        hideThinking();
                        if (bubble) bubble.classList.remove("streaming");
                        enhanceTables(bubble);
                        parseAndRenderChoices(bubble);
                    }
                });
            }
        }
        streaming = false;
        if (sendBtn) sendBtn.disabled = false;
    }

    function handleEvent(raw, cb) {
        let type = null; let data = "";
        for (const line of raw.split("\n")) {
            if (line.startsWith("event: ")) type = line.slice(7).trim();
            else if (line.startsWith("data: ")) data += line.slice(6);
        }
        if (!type) return;
        try { cb(type, data ? JSON.parse(data) : {}); }
        catch (e) { console.error("bad sse line", raw, e); }
    }

    // ── Artifacts ─────────────────────────────────────────────
    function showArtifact(payload) {
        const body = $("#artifact-body");
        const empty = $("#artifact-empty");
        if (empty) empty.style.display = "none";
        if (body) body.style.display = "block";

        const sub = $("#artifact-subtitle");
        if (sub) sub.textContent = payload.subtitle || "";

        const card = document.createElement("div");
        card.className = "artifact-card";
        const title = payload.title || "Canvas";
        const kind = payload.kind || "note";
        card.innerHTML = `
            <div class="meta">${kind}</div>
            <h4>${title}</h4>
            <div class="body">${renderArtifactHTML(payload)}</div>
        `;
        body.prepend(card);
        enhanceTables(card);

        // Render Plotly charts
        if (payload.kind === "chart" && payload.figure) {
            const chartDiv = card.querySelector(".body");
            const chartId = "chart-" + Math.random().toString(36).slice(2, 8);
            const plotContainer = document.createElement("div");
            plotContainer.id = chartId;
            plotContainer.style.width = "100%";
            plotContainer.style.minHeight = "300px";
            chartDiv.innerHTML = "";
            chartDiv.appendChild(plotContainer);
            if (window.Plotly) {
                Plotly.newPlot(chartId, payload.figure.data, payload.figure.layout, { responsive: true });
            }
        }

        document.querySelector(".app").classList.remove("pane-closed");
        const rp = $("#right-pane");
        if (rp) rp.classList.add("open");
        const ab = $("#artifact-btn");
        if (ab) ab.classList.add("active");
    }

    function renderArtifactHTML(p) {
        if (p.kind === "chart") {
            return '<div style="color:var(--ink-muted);font-size:12px">Loading chart...</div>';
        }
        if (p.kind === "table" && Array.isArray(p.rows)) {
            if (!p.rows.length) return '<p><em>No rows.</em></p>';
            const cols = p.columns || Object.keys(p.rows[0]);
            const head = "<tr>" + cols.map(c => `<th>${c}</th>`).join("") + "</tr>";
            const tbody = p.rows.map(r => "<tr>" + cols.map(c => `<td>${formatCell(r[c])}</td>`).join("") + "</tr>").join("");
            return `<table class="artifact-table">${head}${tbody}</table>`;
        }
        if (p.kind === "citations" && Array.isArray(p.items)) {
            return p.items.map(it => `
                <div style="margin-bottom:.6rem;">
                    <div style="color:var(--ink);font-size:.8rem;font-weight:500;">${it.title || ""}</div>
                    <div style="color:var(--ink-dim);font-size:.68rem;font-family:monospace;">${it.url ? `<a href="${it.url}" target="_blank" style="color:var(--ink-muted)">link</a>` : ""} ${it.score ? `score ${Number(it.score).toFixed(2)}` : ""}</div>
                    <div style="color:var(--ink-muted);font-size:.75rem;margin-top:.25rem;">${(it.snippet || "").replace(/\n/g,"<br>")}</div>
                </div>
            `).join("");
        }
        if (p.body_md) {
            return renderMarkdownLite(p.body_md);
        }
        return `<pre style="font-size:11px;overflow-x:auto">${JSON.stringify(p, null, 2)}</pre>`;
    }

    function formatCell(v) {
        if (v === null || v === undefined) return "--";
        if (typeof v === "number") return v.toLocaleString();
        if (typeof v === "object") return JSON.stringify(v);
        return String(v);
    }

    // ── UI helpers ────────────────────────────────────────────
    window.toggleLeftPane = () => {
        const lp = $(".left-pane");
        const lo = $(".left-overlay");
        if (lp) lp.classList.toggle("open");
        if (lo) lo.classList.toggle("visible");
    };
    window.toggleArtifactPane = () => {
        const r = $("#right-pane");
        const app = $(".app");
        if (!r) return;
        if (r.classList.contains("open")) {
            r.classList.remove("open");
            if (app) app.classList.add("pane-closed");
            const ab = $("#artifact-btn");
            if (ab) ab.classList.remove("active");
        } else {
            r.classList.add("open");
            if (app) app.classList.remove("pane-closed");
            const ab = $("#artifact-btn");
            if (ab) ab.classList.add("active");
        }
    };
    window.toggleGroup = (id) => {
        const el = document.getElementById(id);
        if (el) el.classList.toggle("open");
        const btn = document.getElementById("btn-" + id);
        if (btn) btn.classList.toggle("open");
    };
    window.handleKey = (ev) => {
        if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); sendMessage(ev); }
    };
    window.autoResize = (el) => {
        el.style.height = "auto";
        el.style.height = Math.min(el.scrollHeight, 240) + "px";
    };
    window.fillChat = (text) => {
        const ta = $("#chat-input");
        if (!ta) return;
        ta.value = text;
        ta.focus();
        autoResize(ta);
    };
    window.agentClick = (prefix) => {
        const ta = $("#chat-input");
        if (ta) {
            fillChat(prefix);
        } else {
            window.location.href = "/app?prefill=" + encodeURIComponent(prefix);
        }
    };
    window.newChat = () => { window.location.href = "/app"; };
    window.showSignIn = () => {
        const o = $("#signin-overlay");
        if (o) o.classList.add("visible");
        switchAuthTab('login');
        const e = $("#login-email");
        if (e) e.focus();
    };
    window.switchAuthTab = (tab) => {
        // Hide all forms
        const login = $("#auth-form-login");
        const register = $("#auth-form-register");
        const forgot = $("#auth-form-forgot");
        if (login) login.style.display = "none";
        if (register) register.style.display = "none";
        if (forgot) forgot.style.display = "none";
        // Deactivate all tabs
        const tabLogin = $("#auth-tab-login");
        const tabRegister = $("#auth-tab-register");
        if (tabLogin) tabLogin.classList.remove("active");
        if (tabRegister) tabRegister.classList.remove("active");
        // Show selected
        if (tab === "login" && login) {
            login.style.display = "block";
            if (tabLogin) tabLogin.classList.add("active");
        } else if (tab === "register" && register) {
            register.style.display = "block";
            if (tabRegister) tabRegister.classList.add("active");
        } else if (tab === "forgot" && forgot) {
            forgot.style.display = "block";
        }
        // Clear errors
        const le = $("#login-error"); if (le) le.textContent = "";
        const re = $("#reg-error"); if (re) re.textContent = "";
        const rs = $("#reg-success"); if (rs) rs.textContent = "";
        const fm = $("#forgot-msg"); if (fm) fm.textContent = "";
    };
    window.showForgotPassword = (ev) => {
        if (ev) ev.preventDefault();
        switchAuthTab('forgot');
    };
    window.doLogin = async () => {
        const email = ($("#login-email") || {}).value || "";
        const password = ($("#login-password") || {}).value || "";
        const errEl = $("#login-error");
        if (!email.trim() || !password) {
            if (errEl) errEl.textContent = "Email and password are required";
            return;
        }
        try {
            const r = await fetch("/auth/login", {
                method: "POST",
                body: new URLSearchParams({ email: email.trim(), password }),
            });
            const data = await r.json();
            if (r.ok && data.ok) {
                window.location.reload();
            } else if (data.error === "no_password") {
                if (errEl) errEl.textContent = "Please set a password for your account";
            } else {
                if (errEl) errEl.textContent = data.error || "Login failed";
            }
        } catch (e) {
            if (errEl) errEl.textContent = "Network error";
        }
    };
    window.doRegister = async () => {
        const name = ($("#reg-name") || {}).value || "";
        const email = ($("#reg-email") || {}).value || "";
        const password = ($("#reg-password") || {}).value || "";
        const errEl = $("#reg-error");
        const succEl = $("#reg-success");
        if (errEl) errEl.textContent = "";
        if (succEl) succEl.textContent = "";
        if (!email.trim() || !password) {
            if (errEl) errEl.textContent = "Email and password are required";
            return;
        }
        if (password.length < 6) {
            if (errEl) errEl.textContent = "Password must be at least 6 characters";
            return;
        }
        try {
            const r = await fetch("/auth/register", {
                method: "POST",
                body: new URLSearchParams({ name, email: email.trim(), password }),
            });
            const data = await r.json();
            if (r.ok && data.ok) {
                if (succEl) succEl.textContent = data.message || "Check your email to verify your account";
            } else {
                if (errEl) errEl.textContent = data.error || "Registration failed";
            }
        } catch (e) {
            if (errEl) errEl.textContent = "Network error";
        }
    };
    window.doForgot = async () => {
        const email = ($("#forgot-email") || {}).value || "";
        const msgEl = $("#forgot-msg");
        if (!email.trim()) {
            if (msgEl) { msgEl.textContent = "Please enter your email"; msgEl.className = "text-red-500 text-sm mb-2"; }
            return;
        }
        try {
            const r = await fetch("/auth/forgot", {
                method: "POST",
                body: new URLSearchParams({ email: email.trim() }),
            });
            const data = await r.json();
            if (msgEl) {
                msgEl.textContent = data.message || "If an account exists, a reset link has been sent";
                msgEl.className = "text-green-600 text-sm mb-2";
            }
        } catch (e) {
            if (msgEl) { msgEl.textContent = "Network error"; msgEl.className = "text-red-500 text-sm mb-2"; }
        }
    };
    window.signOut = async () => {
        await fetch("/auth/logout", { method: "POST" });
        window.location.reload();
    };
    window.copyChat = () => {
        const msgs = document.querySelectorAll(".msg");
        const lines = [];
        msgs.forEach(m => {
            const role = m.classList.contains("msg-user") ? "You" : "Kanvas";
            const bubble = m.querySelector(".msg-bubble");
            if (bubble) lines.push(`${role}: ${bubble.textContent.trim()}`);
        });
        navigator.clipboard.writeText(lines.join("\n\n")).then(() => {
            const btn = document.getElementById("copy-chat-btn");
            if (btn) { btn.textContent = "Copied!"; setTimeout(() => { btn.textContent = "Copy"; }, 1500); }
        });
    };
    window.shareChat = async () => {
        if (!currentSessionId) return;
        const btn = document.getElementById("share-btn");
        try {
            const resp = await fetch("/api/chat/share", {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: "sid=" + encodeURIComponent(currentSessionId),
            });
            const data = await resp.json();
            if (data.url) {
                try {
                    await navigator.clipboard.writeText(data.url);
                    if (btn) { btn.textContent = "✓ Copied"; setTimeout(() => { btn.textContent = "🔗"; }, 2000); }
                } catch (_) {
                    window.prompt("Share link:", data.url);
                }
            }
        } catch (e) {
            if (btn) { btn.textContent = "Error"; setTimeout(() => { btn.textContent = "🔗"; }, 2000); }
        }
    };

    function parseAndRenderChoices(bubble) {
        if (!bubble || !window.location.pathname.includes("art-guru")) return;
        const parent = bubble.parentElement;
        if (!parent || parent.querySelector(".choice-buttons")) return;

        const text = bubble.textContent || "";
        const lines = text.split("\n");
        const choices = [];
        for (const line of lines) {
            const m = line.match(/^\s*(\d)[.)]\s*(.+)/) ||
                       line.match(/^\s*(\d)\s*[-–—]\s*(.+)/);
            if (m && choices.length < 4) {
                choices.push({ num: m[1], label: m[2].trim().substring(0, 120) });
            }
        }
        // Fallback: if no numbered choices found, look for bold action lines at end
        if (choices.length < 2) {
            const lastLines = lines.slice(-6).filter(l => l.trim().length > 10);
            let idx = 0;
            for (const line of lastLines) {
                const actionMatch = line.match(/^\s*(?:\*\*)?(?:Buy|Sell|Visit|Save|Trade|Bid|Create|Explore|Invest|Skip|Hold|Accept|Decline|Use|Attend)\b/i);
                if (actionMatch && idx < 3) {
                    idx++;
                    choices.push({ num: String(idx), label: line.trim().replace(/^\*\*|\*\*$/g, '').substring(0, 120) });
                }
            }
        }
        if (choices.length < 2) return;

        const btns = document.createElement("div");
        btns.className = "choice-buttons";
        choices.forEach(opt => {
            const b = document.createElement("button");
            b.className = "choice-btn";
            b.textContent = opt.label;
            b.onclick = () => {
                btns.querySelectorAll(".choice-btn").forEach(x => x.disabled = true);
                b.classList.add("choice-selected");
                fillChat(opt.num);
                sendMessage(null);
            };
            btns.appendChild(b);
        });
        parent.appendChild(btns);
        scrollMessagesBottom();
    }

    document.querySelectorAll(".msg-bubble").forEach(b => enhanceTables(b));

    /* ── News: lazy load + polling ───────────────────────────── */
    (function startNews() {
        const intervalEl = document.getElementById("news-interval");
        const seconds = intervalEl ? parseInt(intervalEl.textContent, 10) : 1800;

        async function refreshNews() {
            try {
                const r = await fetch("/api/news");
                if (!r.ok) return;
                const data = await r.json();
                const container = document.getElementById("artifact-empty");
                if (!container || !data.items || !data.items.length) return;
                container.innerHTML = data.items.map(it => `
                    <div class="py-3 border-b border-gray-50">
                        <a href="${it.url || '#'}" target="_blank"
                           class="text-sm font-medium text-black no-underline hover:underline leading-snug block">${it.title || 'Untitled'}</a>
                        <div class="flex gap-2 mt-1">
                            <span class="text-[10px] font-medium text-gray-400">${it.source || ''}</span>
                            ${it.published ? `<span class="text-[10px] text-gray-300">${it.published.slice(0,10)}</span>` : ''}
                        </div>
                        ${it.snippet ? `<p class="text-xs text-gray-400 mt-1 leading-relaxed line-clamp-2">${it.snippet}</p>` : ''}
                    </div>
                `).join('');
            } catch (e) { /* silent */ }
        }

        refreshNews();
        if (seconds >= 60) setInterval(refreshNews, seconds * 1000);
    })();

    // On mobile, start with news pane closed
    if (window.innerWidth <= 768) {
        const rp = $("#right-pane");
        if (rp) rp.classList.remove("open");
        const app = $(".app");
        if (app) app.classList.add("pane-closed");
    }

    window.toggleLangDropdown = (ev) => {
        ev.stopPropagation();
        const menu = document.getElementById("lang-dd-menu");
        if (menu) menu.classList.toggle("open");
    };
    document.addEventListener("click", () => {
        const menu = document.getElementById("lang-dd-menu");
        if (menu) menu.classList.remove("open");
    });

    window.sendMessage = sendMessage;
    window.renderMarkdownLite = renderMarkdownLite;
    window.enhanceTables = enhanceTables;
})();
