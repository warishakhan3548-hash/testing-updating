export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // 1. HOME PAGE (Checking if Worker is alive)
    if (url.pathname === "/") {
      return new Response("🤖 Aarish AI Agent is Live & Running!", { status: 200 });
    }

    // 2. THE HANDSHAKE ENDPOINT (/connect?code=AAR-XXXX-YYYY)
    if (url.pathname === "/connect") {
      const code = url.searchParams.get("code");
      if (!code) return new Response("❌ Error: Pairing code missing.", { status: 400 });

      // Firebase RTDB URL (Tumhara apna Database)
      const FIREBASE_URL = "https://diary-book-21a91-default-rtdb.firebaseio.com";
      
      // Environment variable se Secret nikalenge
      const FIREBASE_SECRET = env.FIREBASE_SECRET; 

      if (!FIREBASE_SECRET) {
          return new Response("❌ Error: FIREBASE_SECRET is not set in Cloudflare.", { status: 500 });
      }

      // Firebase ka direct API link
      const dbUrl = `${FIREBASE_URL}/ai_agent_links/${code}.json?auth=${FIREBASE_SECRET}`;

      try {
        // Step A: Check if code exists in Firebase
        const getRes = await fetch(dbUrl);
        const data = await getRes.json();

        if (!data) {
          return new Response("❌ Error: Invalid or expired pairing code.", { status: 404 });
        }

        if (data.status === "connected") {
          return new Response("✅ Already connected to user!", { status: 200 });
        }

        // Step B: Handshake - Update status to 'connected'
        const updateRes = await fetch(dbUrl, {
          method: "PATCH",
          body: JSON.stringify({ status: "connected" })
        });

        if (updateRes.ok) {
          return new Response(`🎉 Success! Handshake complete. UID: ${data.uid} is now connected.`, { status: 200 });
        } else {
          return new Response("❌ Error: Failed to update Firebase.", { status: 500 });
        }
      } catch (error) {
        return new Response(`❌ Error: ${error.message}`, { status: 500 });
      }
    }

    // ---------------------------------------------------------
    // 3. OMNI-SECURE AI ACTION ROUTER (/action)
    // ---------------------------------------------------------
    const actionCorsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type"
    };

    if (url.pathname === "/action" && request.method === "POST") {
      try {
        const body = await request.json();
        const { code, action_type, payload } = body || {};

        if (!code || !action_type || !payload || typeof payload !== "object") {
          return new Response("❌ Error: Missing code, action_type, or payload.", { status: 400, headers: actionCorsHeaders });
        }

        const FIREBASE_URL = "https://diary-book-21a91-default-rtdb.firebaseio.com";
        const FIREBASE_SECRET = env.FIREBASE_SECRET;

        if (!FIREBASE_SECRET) {
          return new Response("❌ Error: FIREBASE_SECRET is missing. Check Cloudflare variables.", { status: 500, headers: actionCorsHeaders });
        }

        // STEP A: Authenticate AI Code
        const verifyUrl = `${FIREBASE_URL}/ai_agent_links/${encodeURIComponent(code)}.json?auth=${encodeURIComponent(FIREBASE_SECRET)}`;
        const verifyRes = await fetch(verifyUrl);
        const agentData = await verifyRes.json();

        if (!agentData || agentData.status !== "connected" || !agentData.uid) {
          return new Response("❌ Error: Invalid or disconnected access code.", { status: 403, headers: actionCorsHeaders });
        }

        const uid = agentData.uid;

        // STEP B: Validation and deterministic ID generation
        const generateId = (prefix) => prefix + '_' + Date.now() + '_' + Math.random().toString(36).slice(2, 10);
        const today = new Date().toISOString().split('T')[0];
        const safeSegment = (value) => String(value).trim().replace(/[.#$[\]/]/g, "_").slice(0, 120);
        const safeDate = (value) => /^\d{4}-\d{2}-\d{2}$/.test(String(value || "")) ? String(value) : today;
        const safeAmount = (value) => {
          const amount = Number(value);
          if (!Number.isFinite(amount) || amount <= 0) throw new Error("Amount must be a positive number");
          return amount;
        };

        let safePath = "";
        let safePayload = null;

        // Strict Routing Logic (No Blind Trust on AI)
        switch (action_type) {
          case "ADD_UDHAR": {
            if (!payload.name || payload.amount === undefined || payload.amount === null) throw new Error("Missing name or amount");
            const udhId = generateId('udh');
            safePath = `udharDB/${udhId}`;
            safePayload = {
              id: udhId,
              name: String(payload.name).trim(),
              amount: safeAmount(payload.amount),
              type: payload.flow === "debit" ? "debit" : "credit",
              date: safeDate(payload.date)
            };
            break;
          }

          case "ADD_MILK": {
            if (!payload.name) throw new Error("Missing customer name");
            const mlkId = generateId('mlk');
            const customerKey = safeSegment(payload.name);
            if (!customerKey) throw new Error("Customer name is invalid");
            safePath = `milkDB/${customerKey}/records/${mlkId}`;
            safePayload = {
              id: mlkId,
              date: safeDate(payload.date),
              morning: Number(payload.morning || 0),
              evening: Number(payload.evening || 0),
              flow: payload.flow === "taken" ? "taken" : "given"
            };
            if (![safePayload.morning, safePayload.evening].every(Number.isFinite) || safePayload.morning < 0 || safePayload.evening < 0) {
              throw new Error("Milk quantities must be non-negative numbers");
            }
            break;
          }

          case "ADD_EXPENSE": {
            if (!payload.category || payload.amount === undefined || payload.amount === null) throw new Error("Missing category or amount");
            const expId = generateId('exp');
            safePath = `expenseDB/${expId}`;
            safePayload = {
              id: expId,
              category: String(payload.category).trim(),
              amount: safeAmount(payload.amount),
              date: safeDate(payload.date)
            };
            break;
          }

          case "ADD_SALARY": {
            if (!payload.name || payload.amount === undefined || payload.amount === null) throw new Error("Missing employee name or amount");
            const salId = generateId('sal');
            const employeeKey = safeSegment(payload.name);
            if (!employeeKey) throw new Error("Employee name is invalid");
            safePath = `salaryDB/${employeeKey}/records/${salId}`;
            safePayload = {
              id: salId,
              name: String(payload.name).trim(),
              date: safeDate(payload.date),
              amount: safeAmount(payload.amount)
            };
            break;
          }

          case "ADD_DIARY": {
            if (!payload.title || !payload.content) throw new Error("Missing title or content");
            const diaId = generateId('dia');
            safePath = `diaryDB/${diaId}`;
            safePayload = {
              id: diaId,
              title: String(payload.title).trim(),
              content: String(payload.content),
              date: safeDate(payload.date),
              updated: Date.now()
            };
            break;
          }

          default:
            return new Response(`❌ Error: Unknown action_type: ${action_type}`, { status: 400, headers: actionCorsHeaders });
        }

        // STEP C: Execute safely on Firebase
        const dbUrl = `${FIREBASE_URL}/users/${encodeURIComponent(uid)}/appData/${safePath}.json?auth=${encodeURIComponent(FIREBASE_SECRET)}`;
        const actionRes = await fetch(dbUrl, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(safePayload)
        });

        if (actionRes.ok) {
          return new Response(JSON.stringify({ success: true, message: `✅ ${action_type} added securely!` }), {
            status: 200,
            headers: { ...actionCorsHeaders, "Content-Type": "application/json" }
          });
        }

        return new Response("❌ Error: Firebase DB write failed.", { status: 500, headers: actionCorsHeaders });
      } catch (error) {
        return new Response(`❌ Error: ${error.message}`, { status: 500, headers: actionCorsHeaders });
      }
    }

    // ---------------------------------------------------------
    // 4. CORS Preflight Handler (Crucial for AI Browser Plugins)
    // ---------------------------------------------------------
    if (url.pathname === "/action" && request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          ...actionCorsHeaders,
          "Access-Control-Max-Age": "86400"
        }
      });
    }

    return new Response("Not Found", { status: 404 });
  },
};

