import os
import re

TARGET_FILE = "index.html"

# The Ultimate Smart Logic Engine Block
OMNI_AI_ENGINE_BLOCK = """<!-- AARISH_AI_PROMPT_AUTOPASTE_ENGINE_V1_START -->
<script>
// ========================== OMNI AI ENGINE - HEADLESS SURGICAL CORE ==========================
// 1. THE PROMPT INJECTOR : AI को सिर्फ काम की चीजें दिखाना (Compact Snapshot)
window.generateAndCopyAIPrompt = function() {
    haptic();
    showLoader("PREPARING AI PROMPT...");

    const dbSnapshot = {
        udhar: udharDB.map(u => ({ id: u.id, name: u.name, amount: u.amount, type: u.type })),
        expense: expenseDB.map(e => ({ id: e.id, category: e.category, amount: e.amount, date: e.date })),
        diary: diaryDB.map(d => ({ id: d.id, title: d.title, date: d.date })),
        milk: Object.keys(milkDB || {}).reduce((acc, name) => {
            acc[name] = (milkDB[name].records || []).map(r => ({
                id: r.id,
                date: r.date,
                morning: r.morning,
                evening: r.evening
            }));
            return acc;
        }, {}),
        salary: Object.keys(salaryDB || {}).reduce((acc, name) => {
            acc[name] = (salaryDB[name].records || []).map(r => ({
                id: r.id,
                date: r.date,
                amount: r.amount
            }));
            return acc;
        }, {})
    };

    const systemPrompt = `You are "Aarish Omni‑Secretary", an elite AI assistant for the Aarish Dairy Pro app.\n\nHere is the current snapshot of my database (use it to resolve existing IDs and names):\n\\`\\`\\`json\n${JSON.stringify(dbSnapshot)}\n\\`\\`\\`\n\nI will give you a natural language command (Hindi or English). You MUST decide if the command wants to ADD, EDIT, or DELETE an entry.\n\n**OUTPUT RULES (STRICT)**:\n- Return ONLY a single JSON object with a top‑level key "actions" that holds an array of action objects.\n- Do NOT include any explanatory text, markdown, or code fences.\n- Each action object must have these fields:\n  - "module": "udhar" | "expense" | "diary" | "milk" | "salary"\n  - "action": "ADD" | "EDIT" | "DELETE"\n  - "id": (for EDIT/DELETE) the exact ID from the snapshot; (for ADD) leave empty or omit.\n  - "parentId": (for milk/salary only) the exact customer/employee name.\n  - "data": an object containing the fields to set/change (amount, date, category, title, content, morning, evening, etc.)\n\n**EXAMPLES**:\n- For DELETE: {"actions":[{"module":"udhar","action":"DELETE","id":"udh_abc123"}]}\n- For EDIT: {"actions":[{"module":"milk","action":"EDIT","id":"mlk_xyz","parentId":"Ramu","data":{"amount":70}}]}\n- For ADD: {"actions":[{"module":"expense","action":"ADD","data":{"category":"Tea","amount":20,"date":"2026-08-27"}}]}\n\nAlways use the exact existing ID for edits/deletes. Do not invent IDs.`;

    navigator.clipboard.writeText(systemPrompt)
        .then(() => {
            hideLoader();
            showToast("✅ AI Prompt Copied! Paste into ChatGPT/Gemini.");
        })
        .catch(() => {
            hideLoader();
            showToast("⚠️ Clipboard failed. Allow permissions.");
        });
};

// ========================== 2. THE HEADLESS EXECUTOR ==========================
const OmniAIEngine = {
    async execute(task) {
        const { module, action, id, parentId, data } = task;
        const safeId = id || window.aarishV98Id('ai');

        if (['udhar', 'expense', 'diary'].includes(module)) {
            let targetDB, dbName, firebaseFn;
            if (module === 'udhar') {
                targetDB = udharDB; dbName = 'udharDB'; firebaseFn = window.aarishFirebaseLaterV48;
            } else if (module === 'expense') {
                targetDB = expenseDB; dbName = 'expenseDB'; firebaseFn = window.aarishFirebaseLaterV48;
            } else {
                targetDB = diaryDB; dbName = 'diaryDB'; firebaseFn = window.diaryFirebaseCoreV1 || window.aarishFirebaseLaterV48;
            }

            if (action === 'DELETE') {
                targetDB = targetDB.filter(x => String(x.id) !== String(id));
            } else if (action === 'EDIT') {
                const idx = targetDB.findIndex(x => String(x.id) === String(id));
                if (idx > -1) targetDB[idx] = { ...targetDB[idx], ...data, updated: Date.now() };
            } else if (action === 'ADD') {
                targetDB.unshift({ id: safeId, ...data, createdAt: Date.now() });
            }

            if (module === 'udhar') { udharDB = targetDB; await firebaseFn(dbName, 'set', udharDB); }
            else if (module === 'expense') { expenseDB = targetDB; await firebaseFn(dbName, 'set', expenseDB); }
            else { diaryDB = targetDB; if (typeof window.setDiaryDBCoreV1 === 'function') window.setDiaryDBCoreV1(diaryDB); await firebaseFn(dbName, 'set', diaryDB); }
            return;
        }

        if (['milk', 'salary'].includes(module)) {
            if (!parentId) return;
            let coreDB = (module === 'milk') ? milkDB : salaryDB;
            if (!coreDB[parentId]) {
                if (action === 'ADD') coreDB[parentId] = { records: [] };
                else return;
            }

            let records = coreDB[parentId].records || [];
            if (action === 'DELETE') records = records.filter(x => String(x.id) !== String(id));
            else if (action === 'EDIT') {
                const idx = records.findIndex(x => String(x.id) === String(id));
                if (idx > -1) records[idx] = { ...records[idx], ...data, updated: Date.now() };
            } else if (action === 'ADD') {
                records.push({ id: safeId, ...data, createdAt: Date.now() });
            }

            coreDB[parentId].records = records;

            if (module === 'milk') await window.aarishMilkFirebaseWriteCore(`milkDB/${parentId}`, 'set', coreDB[parentId], 'ai-surgery');
            else await window.salaryFirebaseCoreV1(`salaryDB/${parentId}`, 'set', coreDB[parentId], { fast: true });
        }
    }
};

// ========================== 3. THE INTERCEPTOR (AI JSON BOX) ==========================
window.handleAIPaste = async function() {
    const inputEl = document.getElementById('ai-json-paste');
    if (!inputEl) return;
    const raw = String(inputEl.value || '').trim();
    if (!raw) return;

    let jsonStr = raw;
    try {
        const cleaned = raw.replace(/^```(?:json)?\\s*/, '').replace(/\\s*```$/, '');
        const match = cleaned.match(/\\{[\\s\\S]*\\}/);
        if (match) jsonStr = match[0];
        const parsed = JSON.parse(jsonStr);

        if (!parsed.actions || !Array.isArray(parsed.actions)) return;

        showLoader("OMNI ENGINE EXECUTING...");
        for (const task of parsed.actions) await OmniAIEngine.execute(task);

        if (typeof updateDashboard === 'function') updateDashboard();
        if (typeof updateActiveScreen === 'function') updateActiveScreen();

        inputEl.value = '';
        if (typeof closeModal === 'function') closeModal('gemini-key-modal');
        showToast("✅ AI Surgery Complete!");
    } catch (e) {
        console.warn("OmniAI parse error:", e);
    } finally {
        hideLoader();
    }
};

let __aarishAIPasteDebounceTimerV1 = null;
window.__aarishProcessAIPasteV1 = function() {
    if (__aarishAIPasteDebounceTimerV1) clearTimeout(__aarishAIPasteDebounceTimerV1);
    __aarishAIPasteDebounceTimerV1 = setTimeout(() => {
        __aarishAIPasteDebounceTimerV1 = null;
        window.handleAIPaste();
    }, 700);
};

window.OmniAIEngine = OmniAIEngine;
</script>
<!-- AARISH_AI_PROMPT_AUTOPASTE_ENGINE_V1_END -->"""

def perform_surgery():
    if not os.path.exists(TARGET_FILE):
        print(f"❌ CRITICAL: {TARGET_FILE} not found in the current directory.")
        return

    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        codebase = f.read()

    # Smart Logic: Search for existing wrapper markers to surgically replace
    marker_pattern = re.compile(
        r"<!-- AARISH_AI_PROMPT_AUTOPASTE_ENGINE_V1_START -->[\s\S]*?<!-- AARISH_AI_PROMPT_AUTOPASTE_ENGINE_V1_END -->",
        re.MULTILINE
    )

    if marker_pattern.search(codebase):
        print("✅ Omni-Architect: Legacy engine block identified. Initiating surgical replacement...")
        upgraded_codebase = marker_pattern.sub(lambda _match: OMNI_AI_ENGINE_BLOCK, codebase)
    else:
        print("⚠️ Omni-Architect: Engine markers not found. Injecting new core before </body> tag...")
        upgraded_codebase = codebase.replace("</body>", f"{OMNI_AI_ENGINE_BLOCK}\n</body>")

    with open(TARGET_FILE, "w", encoding="utf-8") as f:
        f.write(upgraded_codebase)
    
    print("🚀 PRECISION SURGERY COMPLETE. Dead code eradicated and OmniAIEngine installed.")

if __name__ == "__main__":
    perform_surgery()

# POST-FLIGHT CHECKS
# The surgery eliminates the massive token waste and ensures nested records write smoothly without over-writing parent objects.
# The Business / Projects module is not included in the requested protocol and remains on its existing flow.
