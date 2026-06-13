(function () {
  const tokenState = {
    access: "",
    refresh: "",
  };

  function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split(";") : [];
    const prefix = `${name}=`;

    for (const cookie of cookies) {
      const trimmed = cookie.trim();
      if (trimmed.startsWith(prefix)) {
        return decodeURIComponent(trimmed.slice(prefix.length));
      }
    }

    return "";
  }

  function setTokens(tokens) {
    tokenState.access = tokens?.access || "";
    tokenState.refresh = tokens?.refresh || "";
  }

  function clearTokens() {
    tokenState.access = "";
    tokenState.refresh = "";
  }

  async function parseStandardResponse(response, fallbackMessage) {
    const body = await response.json();

    if (!response.ok || !body.ok) {
      throw new Error(body.message || fallbackMessage || "The request failed.");
    }

    return body.data;
  }

  async function request(url, options = {}) {
    const method = options.method || "GET";
    const headers = {
      "Accept": "application/json",
      "X-Requested-With": "XMLHttpRequest",
      ...(options.headers || {}),
    };

    if (options.json !== undefined) {
      headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(options.json);
    }

    if (!["GET", "HEAD", "OPTIONS", "TRACE"].includes(method.toUpperCase())) {
      headers["X-CSRFToken"] = getCookie("csrftoken");
    }

    if (tokenState.access) {
      headers.Authorization = `Bearer ${tokenState.access}`;
    }

    return fetch(url, {
      ...options,
      method,
      headers,
    });
  }

  async function getJson(url, options = {}) {
    const response = await request(url, { ...options, method: "GET" });
    return parseStandardResponse(response, options.fallbackMessage);
  }

  async function postJson(url, payload, options = {}) {
    const response = await request(url, { ...options, method: "POST", json: payload });
    return parseStandardResponse(response, options.fallbackMessage);
  }

  async function refreshAccessToken(url) {
    if (!tokenState.refresh) {
      throw new Error("No refresh token is available.");
    }

    const data = await postJson(url, { refresh: tokenState.refresh });
    setTokens(data.tokens);
    return data.tokens;
  }

  window.SkillSprintApi = {
    clearTokens,
    getJson,
    postJson,
    refreshAccessToken,
    setTokens,
  };
})();
