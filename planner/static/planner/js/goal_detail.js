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

function showMilestoneError(message) {
  const error = document.querySelector("[data-milestone-error]");
  if (!error) {
    return;
  }

  error.textContent = message;
  error.hidden = false;
}

function clearMilestoneError() {
  const error = document.querySelector("[data-milestone-error]");
  if (!error) {
    return;
  }

  error.textContent = "";
  error.hidden = true;
}

function updateProgress(progress) {
  const bar = document.querySelector("[data-goal-progress-bar]");
  const value = document.querySelector("[data-goal-progress-value]");
  const count = document.querySelector("[data-goal-progress-count]");

  if (bar) {
    bar.style.width = `${progress.percentage}%`;
  }

  if (value) {
    value.textContent = `${progress.percentage}%`;
  }

  if (count) {
    count.textContent = `${progress.completed_milestones} of ${progress.total_milestones} milestones complete.`;
  }
}

function updateMilestoneState(item, milestone) {
  const button = item.querySelector(".milestone-check");
  const input = item.querySelector("input[name='is_complete']");
  const meta = item.querySelector("[data-milestone-meta]");
  const completedText = milestone.completed_at
    ? ` · Completed ${new Date(milestone.completed_at).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
      })}`
    : "";

  item.classList.toggle("is-complete", milestone.is_complete);

  if (button) {
    button.textContent = milestone.is_complete ? "Complete" : "Mark complete";
    button.setAttribute("aria-pressed", milestone.is_complete ? "true" : "false");
  }

  if (input) {
    input.value = milestone.is_complete ? "false" : "true";
  }

  if (meta) {
    const dueText = meta.dataset.dueText || "";
    meta.textContent = `Order ${milestone.order}${dueText}${completedText}`;
  }
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify(payload),
  });
  const body = await response.json();

  if (!response.ok || !body.ok) {
    throw new Error(body.message || "The milestone update failed.");
  }

  return body.data;
}

function milestoneIds(list) {
  return Array.from(list.querySelectorAll("[data-milestone-id]")).map((item) => Number(item.dataset.milestoneId));
}

async function saveOrder(list) {
  const goalId = Number(list.dataset.goalId);
  const data = await postJson("/api/milestones/reorder/", {
    goal_id: goalId,
    milestone_ids: milestoneIds(list),
  });

  data.milestones.forEach((milestone) => {
    const item = list.querySelector(`[data-milestone-id="${milestone.id}"]`);
    if (item) {
      updateMilestoneState(item, milestone);
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-milestone-toggle]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      clearMilestoneError();

      const item = form.closest("[data-milestone-id]");
      const button = form.querySelector("button");
      const input = form.querySelector("input[name='is_complete']");

      if (!item || !input) {
        return;
      }

      button?.classList.add("is-loading");
      button?.setAttribute("disabled", "disabled");

      try {
        const data = await postJson(form.action, { is_complete: input.value === "true" });
        updateMilestoneState(item, data.milestone);
        updateProgress(data.goal_progress);
      } catch (error) {
        showMilestoneError(error.message);
      } finally {
        button?.classList.remove("is-loading");
        button?.removeAttribute("disabled");
      }
    });
  });

  const list = document.querySelector("[data-milestone-list]");
  if (!list) {
    return;
  }

  list.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-reorder]");
    if (!button) {
      return;
    }

    clearMilestoneError();
    const item = button.closest("[data-milestone-id]");
    const direction = button.dataset.reorder;

    if (direction === "up" && item.previousElementSibling) {
      list.insertBefore(item, item.previousElementSibling);
    } else if (direction === "down" && item.nextElementSibling) {
      list.insertBefore(item.nextElementSibling, item);
    } else {
      return;
    }

    button.classList.add("is-loading");
    button.setAttribute("disabled", "disabled");

    try {
      await saveOrder(list);
    } catch (error) {
      showMilestoneError(error.message);
    } finally {
      button.classList.remove("is-loading");
      button.removeAttribute("disabled");
    }
  });
});
