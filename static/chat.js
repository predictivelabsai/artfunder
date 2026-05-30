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

    function appendToolLog(bubble, name, args) {
        let log = bubble.parentElement.querySelector(".tool-log");
        if (!log) {
            log = document.createElement("div");
            log.className = "tool-log";
            bubble.parentElement.appendChild(log);
        }
        const step = document.createElement("div");
        step.className = "tool-step";
        const argStr = args ? JSON.stringify(args).slice(0, 140) : "";
        step.innerHTML = `-> <span class="tool-name">${name}</span> <span class="tool-args">${argStr}</span>`;
        log.appendChild(step);
    }

    function scrollMessagesBottom() {
        const m = $("#messages");
        if (m) m.scrollTop = m.scrollHeight;
    }

    function renderMarkdownLite(text) {
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
    let thinker = null;
    function showThinking(bubble) {
        if (!bubble) return;
        thinker = {
            started: Date.now(),
            tool: null,
            el: document.createElement("div"),
            timerId: null,
        };
        thinker.el.className = "thinking-indicator";
        thinker.el.innerHTML = `<span class="dot"></span><span class="label">Thinking... <span class="secs">0s</span></span>`;
        bubble.parentElement.insertBefore(thinker.el, bubble);
        thinker.timerId = setInterval(updateThinking, 500);
    }
    function updateThinking() {
        if (!thinker) return;
        const secs = Math.floor((Date.now() - thinker.started) / 1000);
        const label = thinker.tool
            ? `Thinking... <span class="secs">${secs}s</span> -- calling <code>${thinker.tool}</code>`
            : `Thinking... <span class="secs">${secs}s</span>`;
        thinker.el.querySelector(".label").innerHTML = label;
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
    window.updateSampleCards = (slug) => {
        const row = $("#sample-cards-row");
        if (!row) return;
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
                        setThinkingTool(payload.name);
                        appendToolLog(bubble || addBubble("assistant", "", ""), payload.name, payload.args);
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
    window.newChat = () => { window.location.href = "/app"; };
    window.showSignIn = () => {
        const o = $("#signin-overlay");
        if (o) o.classList.add("visible");
        const e = $("#signin-email");
        if (e) e.focus();
    };
    window.doSignIn = async () => {
        const email = ($("#signin-email") || {}).value || "";
        if (!email.trim()) return;
        const r = await fetch("/app/auth/signin", { method: "POST", body: new URLSearchParams({ email: email.trim() }) });
        if (r.ok) window.location.reload();
    };
    window.signOut = async () => {
        await fetch("/app/auth/signout", { method: "POST" });
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

    window.sendMessage = sendMessage;
    window.renderMarkdownLite = renderMarkdownLite;
    window.enhanceTables = enhanceTables;
})();
