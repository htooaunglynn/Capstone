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

function showSessionError(message) {
  const error = document.querySelector("[data-session-error]");
  if (!error) {
    return;
  }

  error.textContent = message;
  error.hidden = false;
}

function clearSessionError() {
  const error = document.querySelector("[data-session-error]");
  if (!error) {
    return;
  }

  error.textContent = "";
  error.hidden = true;
}

async function postSessionStatus(url, status) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({ status }),
  });
  const body = await response.json();

  if (!response.ok || !body.ok) {
    throw new Error(body.message || "The session update failed.");
  }

  return body.data;
}

function updateDashboardCounts(summary) {
  const upcoming = document.querySelector("[data-upcoming-sessions-count]");
  const completed = document.querySelector("[data-completed-sessions-count]");

  if (upcoming && typeof summary.upcoming_sessions_count === "number") {
    upcoming.textContent = summary.upcoming_sessions_count;
  }

  if (completed && typeof summary.completed_sessions_count === "number") {
    completed.textContent = summary.completed_sessions_count;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-session-status-form]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      clearSessionError();

      const input = form.querySelector("input[name='status']");
      const button = form.querySelector("button");
      const item = form.closest("[data-session-id]");
      const label = item?.querySelector("[data-session-status-label]");

      if (!input) {
        return;
      }

      button?.classList.add("is-loading");
      button?.setAttribute("disabled", "disabled");

      try {
        const data = await postSessionStatus(form.action, input.value);
        if (label) {
          label.textContent = data.session.status_display;
        }
        if (data.dashboard_summary) {
          updateDashboardCounts(data.dashboard_summary);
        }
      } catch (error) {
        showSessionError(error.message);
      } finally {
        button?.classList.remove("is-loading");
        button?.removeAttribute("disabled");
      }
    });
  });
});
