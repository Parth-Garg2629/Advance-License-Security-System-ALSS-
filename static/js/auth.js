// =====================================================
// AUTH CONFIG (LOCKED)
// =====================================================
const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";
const FORCE_PASSWORD_KEY = "force_password_change";

// =====================================================
// TOKEN HELPERS
// =====================================================
function getAccessToken() {
    try {
        return localStorage.getItem(ACCESS_TOKEN_KEY);
    } catch {
        return null;
    }
}

function getRefreshToken() {
    try {
        return localStorage.getItem(REFRESH_TOKEN_KEY);
    } catch {
        return null;
    }
}

function mustChangePassword() {
    try {
        return localStorage.getItem(FORCE_PASSWORD_KEY) === "1";
    } catch {
        return false;
    }
}

function setTokens(access, refresh = null, forceChange = false) {
    try {
        if (access) localStorage.setItem(ACCESS_TOKEN_KEY, access);
        if (refresh) localStorage.setItem(REFRESH_TOKEN_KEY, refresh);

        if (forceChange) {
            localStorage.setItem(FORCE_PASSWORD_KEY, "1");
        } else {
            localStorage.removeItem(FORCE_PASSWORD_KEY);
        }
    } catch {}
}

function clearAuth(reason = null) {
    try {
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        localStorage.removeItem(FORCE_PASSWORD_KEY);
    } catch {}

    window.dispatchEvent(
        new CustomEvent("auth:logout", {
            detail: { reason },
        })
    );
}

// =====================================================
// AUTH FETCH (JWT SAFE WRAPPER — FINAL)
// =====================================================
async function authFetch(url, options = {}, retry = false) {
    const token = getAccessToken();

    if (!token) {
        clearAuth("unauthorized");
        window.location.href = "/login";
        return null;
    }

    // -------------------------------------------------
    // FORCE PASSWORD CHANGE (CLIENT SIDE GUARD)
    // -------------------------------------------------
    if (
        mustChangePassword() &&
        !url.startsWith("/auth/") &&
        !window.location.pathname.startsWith("/change-password")
    ) {
        window.location.href = "/change-password";
        return null;
    }

    const headers = {
        ...(options.headers || {}),
        Authorization: `Bearer ${token}`,
    };

    if (options.body && !headers["Content-Type"]) {
        headers["Content-Type"] = "application/json";
    }

    let res;
    try {
        res = await fetch(url, { ...options, headers });
    } catch (e) {
        console.error("Network error:", e);
        return null;
    }

    // -------------------------------------------------
    // ACCESS TOKEN EXPIRED → TRY REFRESH (ONCE)
    // -------------------------------------------------
    if (res.status === 401 && !retry && getRefreshToken()) {
        const refreshed = await refreshAccessToken();
        if (!refreshed) {
            clearAuth("session_expired");
            window.location.href = "/login";
            return null;
        }
        return authFetch(url, options, true);
    }

    // -------------------------------------------------
    // TEMP PASSWORD ENFORCEMENT (SERVER SIGNAL)
    // -------------------------------------------------
    if (res.status === 403) {
        try {
            const data = await res.clone().json();

            if (data?.error === "password_change_required") {
                localStorage.setItem(FORCE_PASSWORD_KEY, "1");

                if (!window.location.pathname.startsWith("/change-password")) {
                    window.location.href = "/change-password";
                }

                return null;
            }

            // IMPORTANT:
            // Any OTHER 403 must NOT redirect (RBAC, validation, etc.)
            return res;

        } catch {
            return res;
        }
    }

    // -------------------------------------------------
    // FINAL UNAUTHORIZED (NO LOOPS)
    // -------------------------------------------------
    if (res.status === 401) {
        clearAuth("unauthorized");
        window.location.href = "/login";
        return null;
    }

    // -------------------------------------------------
    // RATE LIMIT (UI EVENT ONLY)
    // -------------------------------------------------
    if (res.status === 429) {
        window.dispatchEvent(
            new CustomEvent("auth:rate_limited")
        );
        return null;
    }

    return res;
}

// =====================================================
// LOGIN (SINGLE ENTRY — FINAL)
// =====================================================
async function login(username, password) {
    const res = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
    });

    let data = {};
    try {
        data = await res.json();
    } catch {}

    if (!res.ok) {
        throw new Error(data.error || "Login failed");
    }

    setTokens(
        data.access_token,
        data.refresh_token,
        data.force_password_change === true
    );

    // -------------------------------------------------
    // FORCE PASSWORD CHANGE FLOW
    // -------------------------------------------------
    if (data.force_password_change === true) {
        window.location.href = "/change-password";
        return;
    }

    // -------------------------------------------------
    // BACKEND DECIDES REDIRECT
    // -------------------------------------------------
    window.location.href = data.redirect || "/admin/dashboard";
}

// =====================================================
// REFRESH TOKEN (NO SIDE EFFECTS)
// =====================================================
async function refreshAccessToken() {
    try {
        const refresh = getRefreshToken();
        if (!refresh) return false;

        const res = await fetch("/auth/refresh", {
            method: "POST",
            headers: {
                Authorization: `Bearer ${refresh}`,
            },
        });

        if (!res.ok) return false;

        const data = await res.json();
        if (!data.access_token) return false;

        localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token);
        return true;
    } catch (e) {
        console.error("Refresh failed:", e);
        return false;
    }
}

// =====================================================
// LOGOUT (FINAL)
// =====================================================
async function logout() {
    try {
        await authFetch("/auth/logout", { method: "POST" });
    } catch {}

    clearAuth("manual");
    window.location.href = "/login";
}

// =====================================================
// SECURE FILE DOWNLOAD (FINAL)
// =====================================================
async function authDownload(url, filename) {
    const res = await authFetch(url, { method: "GET" });
    if (!res || !res.ok) {
        alert("Export failed");
        return;
    }

    const blob = await res.blob();
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(link.href);
}
