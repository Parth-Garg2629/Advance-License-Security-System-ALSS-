// =====================================================
// GLOBAL UI HELPERS (ALSS) — FINAL STABLE VERSION
// =====================================================

document.addEventListener("DOMContentLoaded", async () => {
    try {
        if (!isUiPage()) return;

        await enforceRoleUI();
        bindLogoutListener();
    } catch (e) {
        console.error("UI initialization failed", e);
    }
});

// =====================================================
// PAGE TYPE CHECK (STRICT)
// =====================================================
function isUiPage() {
    const path = window.location.pathname;

    // Never run on API routes
    if (path.startsWith("/api/")) return false;
    if (path.startsWith("/auth/")) return false;

    return (
        path.startsWith("/admin") ||
        path.startsWith("/super") ||
        path.startsWith("/client")
    );
}

// =====================================================
// ROLE BASED UI VISIBILITY (JWT-AWARE, SAFE)
// =====================================================
async function enforceRoleUI() {
    /*
      IMPORTANT:
      - UI ONLY
      - No redirects
      - No token mutation
      - Backend is source of truth
      - Uses authFetch for token refresh safety
    */

    // Try admin / superadmin context
    try {
        const res = await authFetch("/admin/api/profile");
        if (res && res.ok) {
            const user = await res.json();
            applyRoleVisibility(user.role);
            return;
        }
    } catch {
        // silent fail
    }

    // Fallback: client context
    try {
        const clientRes = await authFetch("/client/api/dashboard");
        if (clientRes && clientRes.ok) {
            applyRoleVisibility("COMPANY_VIEWER");
            return;
        }
    } catch {
        // silent fail
    }
}

// =====================================================
// APPLY ROLE VISIBILITY (DOM ONLY)
// =====================================================
function applyRoleVisibility(role) {
    // ADMIN-ONLY ELEMENTS
    document
        .querySelectorAll("[data-requires-admin]")
        .forEach(el => {
            if (role === "COMPANY_VIEWER") {
                el.remove();
            }
        });

    // SUPER ADMIN ONLY
    document
        .querySelectorAll("[data-requires-superadmin]")
        .forEach(el => {
            if (role !== "SUPER_ADMIN") {
                el.remove();
            }
        });

    // CLIENT ONLY
    document
        .querySelectorAll("[data-client-only]")
        .forEach(el => {
            if (role !== "COMPANY_VIEWER") {
                el.remove();
            }
        });
}

// =====================================================
// LOGOUT EVENT LISTENER
// =====================================================
function bindLogoutListener() {
    window.addEventListener("auth:logout", () => {
        console.log("User logged out");
    });
}
