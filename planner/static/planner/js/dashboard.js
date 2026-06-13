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
  return window.SkillSprintApi.postJson(url, { status }, {
    fallbackMessage: "The session update failed.",
  });
}

function updateDashboardCounts(summary) {
  const upcoming = document.querySelector("[data-upcoming-sessions-count]");
  const completed = document.querySelector("[data-completed-sessions-count]");
  const overdue = document.querySelector("[data-overdue-milestones-count]");
  const recentNotes = document.querySelector("[data-recent-notes-count]");
  const milestoneCompletion = document.querySelector("[data-milestone-completion]");
  const sessionCompletion = document.querySelector("[data-session-completion]");

  if (upcoming && typeof summary.upcoming_sessions_count === "number") {
    upcoming.textContent = summary.upcoming_sessions_count;
  }

  if (completed && typeof summary.completed_sessions_count === "number") {
    completed.textContent = summary.completed_sessions_count;
  }

  if (overdue && typeof summary.overdue_milestones_count === "number") {
    overdue.textContent = summary.overdue_milestones_count;
  }

  if (recentNotes && typeof summary.recent_notes_count === "number") {
    recentNotes.textContent = summary.recent_notes_count;
  }

  if (milestoneCompletion && typeof summary.milestone_completion_percentage === "number") {
    milestoneCompletion.textContent = `${summary.milestone_completion_percentage}%`;
  }

  if (sessionCompletion && typeof summary.session_completion_percentage === "number") {
    sessionCompletion.textContent = `${summary.session_completion_percentage}%`;
  }
}

function showDashboardError(message) {
  const error = document.querySelector("[data-dashboard-error]");
  if (!error) {
    return;
  }

  error.textContent = message;
  error.hidden = false;
}

function clearDashboardError() {
  const error = document.querySelector("[data-dashboard-error]");
  if (!error) {
    return;
  }

  error.textContent = "";
  error.hidden = true;
}

async function fetchDashboardSummary(url) {
  const data = await window.SkillSprintApi.getJson(url, {
    fallbackMessage: "The dashboard refresh failed.",
  });
  return data.summary;
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

  const filterForm = document.querySelector("[data-dashboard-filter-form]");
  if (filterForm) {
    filterForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      clearDashboardError();

      const submitButton = filterForm.querySelector("button[type='submit']");
      const summaryUrl = filterForm.dataset.summaryUrl;
      const params = new URLSearchParams(new FormData(filterForm));
      const url = `${summaryUrl}?${params.toString()}`;

      submitButton?.classList.add("is-loading");
      submitButton?.setAttribute("disabled", "disabled");

      try {
        const summary = await fetchDashboardSummary(url);
        updateDashboardCounts(summary);
        window.history.replaceState(null, "", `${window.location.pathname}?${params.toString()}`);
      } catch (error) {
        showDashboardError(error.message);
      } finally {
        submitButton?.classList.remove("is-loading");
        submitButton?.removeAttribute("disabled");
      }
    });
  }
});
