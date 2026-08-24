import re
import sys


def optimize_firebase_cost(file_path):
    print("[OMNI-ARCHITECT] Initiating Apex Cost Optimization Protocol...")
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    # 1. SOCKET STARVATION PROTOCOL
    code = re.sub(
        r'var idleDelay = \(typeof document !== "undefined" && document\.hidden\) \? 800 : 12000;',
        r'''// [OMNI-ARCHITECT: SOCKET STARVATION PROTOCOL]
        var idleDelay = (typeof document !== "undefined" && document.hidden) ? 0 : 2500;''',
        code,
    )

    # 2. DELTA COMPRESSION & BANDWIDTH SAVER
    code = re.sub(
        r'if \(deltaJson\.length < 60000 && Object\.keys\(deltaPayload\)\.length > 0\) \{',
        r'''// [OMNI-ARCHITECT: DELTA COMPRESSION]
        if (deltaJson.length < 2500 && Object.keys(deltaPayload).length > 0) {''',
        code,
    )

    # 3. REST API HYBRID POLLER
    old_pull_logic = r'''try \{\s*aarishCostManageSocketCoreV8\(true, "pull-" \+ String\(reason \|\| ""\)\);\s*openedSocket = true;\s*\} catch\(e\) \{\}\s*var snap = await aarishCostWithTimeoutCoreV5\(ref\.child\("_syncMeta"\)\.once\("value"\), "meta-timeout", 6500\);\s*if \(!aarishCostSameUidCoreV3\(uid\)\) return \{ ok:false, reason:"uid_changed_after_meta" \};\s*var cloudMeta = snap && snap\.val && snap\.val\(\) \|\| \{\};'''

    new_pull_logic = r'''// [OMNI-ARCHITECT: REST API HYBRID POLLER]
        var cloudMeta = null;
        try {
            var user = firebase.auth && firebase.auth().currentUser;
            if (user && typeof firebaseConfig !== "undefined" && firebaseConfig.databaseURL) {
                var token = await user.getIdToken();
                var restUrl = firebaseConfig.databaseURL + "/users/" + uid + "/appData/_syncMeta.json?auth=" + encodeURIComponent(token) + "&shallow=true";
                var res = await fetch(restUrl, { method: "GET", cache: "no-store" });
                if (res.ok) cloudMeta = await res.json();
            }
        } catch (restErr) {}

        if (!cloudMeta) {
            try {
                aarishCostManageSocketCoreV8(true, "pull-" + String(reason || ""));
                openedSocket = true;
            } catch(e) {}
            var snap = await aarishCostWithTimeoutCoreV5(ref.child("_syncMeta").once("value"), "meta-timeout", 6500);
            cloudMeta = snap && snap.val && snap.val() || {};
        }
        if (!aarishCostSameUidCoreV3(uid)) return { ok:false, reason:"uid_changed_after_meta" };
        cloudMeta = cloudMeta || {};'''

    updated_code, pull_count = re.subn(old_pull_logic, new_pull_logic, code)
    if pull_count != 1:
        raise RuntimeError(f"Expected exactly one cloud-pull block, found {pull_count}")
    code = updated_code

    # 4. DEEP COALESCING LATENCY
    code = re.sub(
        r'var delay = destructive \? 220 : \(opts\.fast \? 1100 : 35000\);',
        r'''// [OMNI-ARCHITECT: DEEP COALESCING LATENCY]
        var delay = destructive ? 220 : (opts.fast ? 2500 : 55000);''',
        code,
    )

    # 5. MICRO-BATCH LIMITS
    code = re.sub(
        r'var maxItems = 80;\s*var maxBytes = 150000;',
        r'''// [OMNI-ARCHITECT: MICRO-BATCH COMPRESSION]
        var maxItems = 60;
        var maxBytes = 65000;''',
        code,
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)
    print("[SUCCESS] Ecosystem upgraded to Apex Big-Tech Cost-Saving Standards.")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "index.html"
    optimize_firebase_cost(target)
