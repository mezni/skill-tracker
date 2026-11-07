/* SkillTrack Studio frontend.
 * Talks only to the /api surface; no business rules live here beyond display.
 */

const view = document.getElementById("view");
const modalRoot = document.getElementById("modal-root");
const toastRoot = document.getElementById("toast-root");

const state = {
  tab: "dashboard",
  topics: [],
  projects: [],
  logs: [],
  dashboard: null,
  search: "",
  category: "All",
  projectFilter: "All",
  darkMode: localStorage.getItem("theme") === "dark",
};

const COLOR_CLASSES = {
  indigo: "bg-indigo-500",
  blue: "bg-blue-500",
  purple: "bg-purple-500",
  emerald: "bg-emerald-500",
  amber: "bg-amber-500",
  rose: "bg-rose-500",
  slate: "bg-slate-500",
  cyan: "bg-cyan-500",
  pink: "bg-pink-500",
};

const STATUS_CLASSES = {
  Active: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  Planning: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  Paused: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  Completed: "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300",
};

const ICONS = {
  square:
    '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>',
  check:
    '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
  edit:
    '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>',
  trash:
    '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/></svg>',
  clock:
    '<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 14"/></svg>',
  calendar:
    '<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
  link:
    '<svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>',
  x:
    '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
  plus:
    '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
};

// --- API client ------------------------------------------------------------
async function api(path, options = {}) {
  const config = { ...options };
  if (config.body && !(config.body instanceof FormData)) {
    config.headers = { "Content-Type": "application/json", ...(config.headers || {}) };
  }
  const response = await fetch(path, config);
  if (!response.ok) {
    let detail = response.statusText || `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body.detail) {
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  if (response.status === 204) return null;
  return response.json();
}

const API = {
  dashboard: () => api("/api/dashboard"),
  topics: () => api("/api/topics"),
  projects: () => api("/api/projects"),
  logs: () => api("/api/logs"),
  createTopic: (payload) => api("/api/topics", { method: "POST", body: JSON.stringify(payload) }),
  updateTopic: (id, payload) =>
    api(`/api/topics/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteTopic: (id) => api(`/api/topics/${id}`, { method: "DELETE" }),
  addModule: (topicId, title) =>
    api(`/api/topics/${topicId}/modules`, {
      method: "POST",
      body: JSON.stringify({ title }),
    }),
  toggleModule: (topicId, moduleId) =>
    api(`/api/topics/${topicId}/modules/${moduleId}/toggle`, { method: "PATCH" }),
  createProject: (payload) =>
    api("/api/projects", { method: "POST", body: JSON.stringify(payload) }),
  updateProject: (id, payload) =>
    api(`/api/projects/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteProject: (id) => api(`/api/projects/${id}`, { method: "DELETE" }),
  addTask: (projectId, title) =>
    api(`/api/projects/${projectId}/tasks`, {
      method: "POST",
      body: JSON.stringify({ title }),
    }),
  toggleTask: (projectId, taskId) =>
    api(`/api/projects/${projectId}/tasks/${taskId}/toggle`, { method: "PATCH" }),
  createLog: (payload) => api("/api/logs", { method: "POST", body: JSON.stringify(payload) }),
  importFile: (file) => {
    const body = new FormData();
    body.append("file", file);
    return api("/api/import", { method: "POST", body });
  },
};

// --- Helpers ---------------------------------------------------------------
const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char],
  );

const dot = (color) => COLOR_CLASSES[color] || COLOR_CLASSES.indigo;

function toast(message, variant = "success") {
  const palette =
    variant === "error"
      ? "bg-red-600 text-white"
      : "bg-slate-900 text-white dark:bg-white dark:text-slate-900";
  const node = document.createElement("div");
  node.className = `px-4 py-2 rounded-lg shadow-lg text-sm font-semibold animate-fadeIn ${palette}`;
  node.textContent = message;
  toastRoot.appendChild(node);
  setTimeout(() => node.remove(), 3200);
}

function progressBar(percentage, color = "bg-indigo-600") {
  return `
    <div class="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
      <div class="${color} h-full rounded-full transition-all duration-300" style="width:${percentage}%"></div>
    </div>`;
}

function emptyState(message, hint = "") {
  return `
    <div class="text-center py-12 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800">
      <p class="text-sm font-semibold text-slate-600 dark:text-slate-400">${esc(message)}</p>
      ${hint ? `<p class="text-xs text-slate-400 mt-1">${esc(hint)}</p>` : ""}
    </div>`;
}

// --- Data loading ----------------------------------------------------------
async function refresh({ silent = false } = {}) {
  try {
    const [dashboard, topics, projects, logs] = await Promise.all([
      API.dashboard(),
      API.topics(),
      API.projects(),
      API.logs(),
    ]);
    Object.assign(state, { dashboard, topics, projects, logs });
    render();
    if (!silent) toast("Saved");
  } catch (error) {
    toast(error.message, "error");
  }
}

// --- Themes and tabs -------------------------------------------------------
const THEME_ICONS = {
  moon:
    '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/></svg>',
  sun:
    '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
};

function applyTheme() {
  document.documentElement.classList.toggle("dark", state.darkMode);
  const icon = document.getElementById("theme-icon");
  if (icon) icon.innerHTML = state.darkMode ? THEME_ICONS.sun : THEME_ICONS.moon;
}

function renderTabs() {
  const active =
    "bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-300 shadow-sm";
  const idle =
    "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200";
  document.querySelectorAll("#tabs [data-tab]").forEach((button) => {
    button.className = `flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
      button.dataset.tab === state.tab ? active : idle
    }`;
  });
}

function render() {
  applyTheme();
  renderTabs();
  const views = {
    dashboard: dashboardView,
    topics: topicsView,
    projects: projectsView,
    activity: activityView,
  };
  view.innerHTML = (views[state.tab] || dashboardView)();
  view.classList.remove("animate-fadeIn");
  void view.offsetWidth;
  view.classList.add("animate-fadeIn");
}

// --- Dashboard -------------------------------------------------------------
function dashboardView() {
  const summary = state.dashboard;
  if (!summary) return emptyState("Loading dashboard…");

  const topicRows = state.topics.slice(0, 3).map(topicRow).join("");
  const projectCards = state.projects.slice(0, 4).map(projectSpotlight).join("");
  const recent = summary.recentLogs.length
    ? summary.recentLogs.map(recentLogRow).join("")
    : '<p class="text-xs text-slate-400 text-center py-6">No study sessions logged yet.</p>';

  return `
    <div class="space-y-8">
      <section class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-600 via-indigo-700 to-purple-800 p-6 sm:p-8 text-white shadow-xl">
        <div class="relative z-10 space-y-2 max-w-2xl">
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-white/20 backdrop-blur-md">Overview Dashboard</span>
          <h2 class="text-2xl sm:text-3xl font-bold tracking-tight">Keep Building Your Knowledge Base</h2>
          <p class="text-indigo-100 text-sm sm:text-base">Track study milestones, organize side projects, and visualize your progress over time.</p>
          <div class="pt-2 flex flex-wrap gap-3">
            <button data-action="open-log-modal" class="px-4 py-2 bg-white text-indigo-700 hover:bg-indigo-50 font-semibold rounded-lg text-xs sm:text-sm shadow transition">Log Quick Session</button>
            <button data-action="open-project-modal" class="px-4 py-2 bg-indigo-500/30 hover:bg-indigo-500/40 text-white font-semibold rounded-lg text-xs sm:text-sm backdrop-blur-sm border border-white/20 transition">New Project</button>
            <button data-action="export" class="px-4 py-2 bg-indigo-500/30 hover:bg-indigo-500/40 text-white font-semibold rounded-lg text-xs sm:text-sm backdrop-blur-sm border border-white/20 transition">Export Excel</button>
            <button data-action="import" class="px-4 py-2 bg-indigo-500/30 hover:bg-indigo-500/40 text-white font-semibold rounded-lg text-xs sm:text-sm backdrop-blur-sm border border-white/20 transition">Import Excel</button>
          </div>
        </div>
      </section>

      <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        ${statCard("Active Topics", summary.activeTopicsCount, `${summary.completedModules} of ${summary.totalModules} modules complete`)}
        ${statCard("Active Projects", summary.activeProjectsCount, `${summary.completedProjectsCount} completed total`)}
        ${statCard("Total Study Time", `${Number(summary.totalHoursLogged).toFixed(1)} hrs`, "Across all logged sessions")}
        ${statCard("Module Completion", `${summary.moduleCompletionPct}%`, "Overall checklist progress", true)}
      </section>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 space-y-6">
          <section class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-base font-bold">Learning Topic Progress</h3>
              <button data-action="tab" data-tab="topics" class="text-xs text-indigo-600 dark:text-indigo-400 hover:underline font-semibold">View All →</button>
            </div>
            <div class="space-y-4">${topicRows || emptyState("No topics yet.")}</div>
          </section>

          <section class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-base font-bold">Active Projects Spotlight</h3>
              <button data-action="tab" data-tab="projects" class="text-xs text-indigo-600 dark:text-indigo-400 hover:underline font-semibold">Manage Projects →</button>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">${projectCards || emptyState("No projects yet.")}</div>
          </section>
        </div>

        <div class="space-y-6">
          <section class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-base font-bold">Recent Activity</h3>
              <button data-action="tab" data-tab="activity" class="text-xs text-indigo-600 dark:text-indigo-400 hover:underline font-semibold">Log History</button>
            </div>
            <div class="relative pl-4 border-l-2 border-slate-200 dark:border-slate-800 space-y-4">${recent}</div>
          </section>
          <section class="p-5 rounded-xl bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-950/30 dark:to-indigo-950/30 border border-purple-100 dark:border-purple-900/50">
            <p class="text-xs text-slate-600 dark:text-slate-300 leading-relaxed italic">"Consistency outperforms intensity. Small daily study logs lead to compound knowledge gains."</p>
          </section>
        </div>
      </div>
    </div>`;
}

function statCard(label, value, caption, showBar = false) {
  return `
    <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
      <p class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">${esc(
        label,
      )}</p>
      <h3 class="text-2xl font-bold mt-1">${esc(String(value))}</h3>
      ${showBar ? progressBar(Number.parseFloat(value) || 0) : ""}
      <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">${esc(caption)}</p>
    </div>`;
}

function topicRow(topic) {
  return `
    <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center space-x-2">
          <span class="w-3 h-3 rounded-full ${dot(topic.color)}"></span>
          <span class="font-semibold text-sm">${esc(topic.title)}</span>
        </div>
        <span class="text-xs font-bold text-slate-600 dark:text-slate-400">${topic.completedModules}/${topic.totalModules} (${topic.completionPercentage}%)</span>
      </div>
      ${progressBar(topic.completionPercentage)}
    </div>`;
}

function projectSpotlight(project) {
  return `
    <div class="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/40 hover:border-indigo-300 transition space-y-3">
      <div class="flex items-center justify-between">
        <span class="text-[10px] font-bold px-2 py-0.5 rounded-full ${STATUS_CLASSES[project.status] || ""}">${esc(
          project.status,
        )}</span>
        <span class="text-xs text-slate-400">${Number(project.hoursSpent)}h</span>
      </div>
      <h4 class="font-semibold text-sm line-clamp-1">${esc(project.title)}</h4>
      <p class="text-xs text-slate-500 dark:text-slate-400 line-clamp-2">${esc(project.description)}</p>
      ${progressBar(project.taskCompletionPercentage, "bg-purple-600")}
    </div>`;
}

function recentLogRow(log) {
  return `
    <div class="relative">
      <div class="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-indigo-600 ring-4 ring-white dark:ring-slate-900"></div>
      <div class="flex items-center justify-between">
        <span class="text-xs font-semibold line-clamp-1">${esc(log.topicTitle)}</span>
        <span class="text-[11px] font-bold text-indigo-600 dark:text-indigo-400 whitespace-nowrap ml-2">+${Number(
          log.hours,
        )}h</span>
      </div>
      <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-2">${esc(
        log.note || "No notes added.",
      )}</p>
      <span class="text-[10px] text-slate-400 mt-1 block">${esc(log.date)}</span>
    </div>`;
}

// --- Topics ----------------------------------------------------------------
function filteredTopics() {
  const term = state.search.trim().toLowerCase();
  return state.topics.filter((topic) => {
    const matchesTerm =
      !term ||
      topic.title.toLowerCase().includes(term) ||
      (topic.description || "").toLowerCase().includes(term);
    const matchesCategory = state.category === "All" || topic.category === state.category;
    return matchesTerm && matchesCategory;
  });
}

function topicsView() {
  const categories = ["All", ...new Set(state.topics.map((topic) => topic.category).filter(Boolean))];
  return `
    <div class="space-y-6">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 class="text-xl font-bold">Learning Topics Tracker</h2>
          <p class="text-xs text-slate-500 dark:text-slate-400">Organize core domains, sub-modules, and study takeaways.</p>
        </div>
        <button data-action="open-topic-modal" class="flex items-center justify-center space-x-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-xl shadow-sm transition">${ICONS.plus}<span>Add New Topic</span></button>
      </div>

      <div class="flex flex-col sm:flex-row gap-3 bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <input data-search type="search" placeholder="Search topics or takeaways…" value="${esc(
          state.search,
        )}" class="flex-1 px-3 py-1.5 text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        <select data-category class="py-1.5 px-3 text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium">
          ${categories
            .map(
              (category) =>
                `<option value="${esc(category)}" ${
                  category === state.category ? "selected" : ""
                }>${esc(category)}</option>`,
            )
            .join("")}
        </select>
      </div>

      <div id="topics-grid">${topicsGrid()}</div>
    </div>`;
}

function topicsGrid() {
  const topics = filteredTopics();
  if (!topics.length) return emptyState("No learning topics found.", "Try a broader search or add a topic.");
  return `<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">${topics
    .map(topicCard)
    .join("")}</div>`;
}

function topicCard(topic) {
  const modules = topic.modules.length
    ? topic.modules
        .map(
          (module) => `
        <div class="flex items-start space-x-2 text-xs">
          <button data-action="toggle-module" data-topic="${topic.id}" data-module="${module.id}" class="mt-0.5 ${
            module.completed
              ? "text-emerald-500"
              : "text-slate-300 dark:text-slate-600 hover:text-indigo-600"
          }" aria-label="Toggle module ${esc(module.title)}">${module.completed ? ICONS.check : ICONS.square}</button>
          <span class="flex-1 ${
            module.completed ? "line-through text-slate-400 dark:text-slate-500" : ""
          }">${esc(module.title)}</span>
        </div>`,
        )
        .join("")
    : '<p class="text-xs text-slate-400">No modules yet.</p>';

  return `
    <article class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl flex flex-col shadow-sm hover:shadow-md transition">
      <div class="p-5 border-b border-slate-100 dark:border-slate-800/80">
        <div class="flex items-start justify-between">
          <span class="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">${esc(
            topic.category || "General",
          )}</span>
          <div class="flex items-center space-x-1">
            <button data-action="edit-topic" data-id="${topic.id}" class="p-1 text-slate-400 hover:text-indigo-600 rounded transition" title="Edit topic">${ICONS.edit}</button>
            <button data-action="delete-topic" data-id="${topic.id}" class="p-1 text-slate-400 hover:text-red-600 rounded transition" title="Delete topic">${ICONS.trash}</button>
          </div>
        </div>
        <h3 class="text-lg font-bold mt-2 flex items-center">
          <span class="w-3 h-3 rounded-full ${dot(topic.color)} mr-2 shrink-0"></span>
          <span>${esc(topic.title)}</span>
        </h3>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">${esc(topic.description)}</p>
        <div class="mt-4 space-y-1">
          <div class="flex justify-between text-xs font-semibold">
            <span class="text-slate-500">Progress</span>
            <span class="text-indigo-600 dark:text-indigo-400">${topic.completedModules}/${topic.totalModules} (${topic.completionPercentage}%)</span>
          </div>
          ${progressBar(topic.completionPercentage)}
        </div>
      </div>
      <div class="p-5 space-y-3 flex-1">
        <h4 class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Modules &amp; Milestones</h4>
        <div class="space-y-2 max-h-48 overflow-y-auto pr-1">${modules}</div>
        <form data-form="module" data-topic="${topic.id}" class="flex items-center space-x-1 pt-2">
          <input name="title" type="text" required placeholder="+ Add module…" class="flex-1 px-2.5 py-1 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500" />
          <button type="submit" class="px-2 py-1 bg-slate-200 dark:bg-slate-700 hover:bg-indigo-600 hover:text-white rounded-md text-xs font-semibold transition">Add</button>
        </form>
      </div>
      ${
        topic.notes
          ? `<div class="px-5 py-3 bg-slate-50 dark:bg-slate-800/40 rounded-b-xl border-t border-slate-100 dark:border-slate-800/80 text-xs">
              <span class="font-semibold text-slate-500 dark:text-slate-400 block mb-0.5">Key Takeaway:</span>
              <p class="text-slate-600 dark:text-slate-300 italic line-clamp-2">${esc(topic.notes)}</p>
            </div>`
          : ""
      }
    </article>`;
}

// --- Projects --------------------------------------------------------------
function projectsView() {
  const statuses = ["All", "Active", "Planning", "Paused", "Completed"];
  const projects =
    state.projectFilter === "All"
      ? state.projects
      : state.projects.filter((project) => project.status === state.projectFilter);

  return `
    <div class="space-y-6">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 class="text-xl font-bold">Project Portfolio Tracker</h2>
          <p class="text-xs text-slate-500 dark:text-slate-400">Track execution of side projects linked to your learning topics.</p>
        </div>
        <button data-action="open-project-modal" class="flex items-center justify-center space-x-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-xl shadow-sm transition">${ICONS.plus}<span>New Project</span></button>
      </div>

      <div class="flex border-b border-slate-200 dark:border-slate-800 space-x-4 overflow-x-auto">
        ${statuses
          .map(
            (status) => `
          <button data-action="project-filter" data-status="${status}" class="pb-2 text-xs sm:text-sm font-semibold transition border-b-2 whitespace-nowrap ${
            state.projectFilter === status
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
          }">${status}</button>`,
          )
          .join("")}
      </div>

      ${
        projects.length
          ? `<div class="grid grid-cols-1 md:grid-cols-2 gap-6">${projects
              .map(projectCard)
              .join("")}</div>`
          : emptyState(`No projects found for status: ${state.projectFilter}`)
      }
    </div>`;
}

function projectCard(project) {
  const topic = state.topics.find((item) => item.id === project.topicId);
  const tasks = project.tasks.length
    ? project.tasks
        .map(
          (task) => `
        <div class="flex items-start space-x-2 text-xs">
          <button data-action="toggle-task" data-project="${project.id}" data-task="${task.id}" class="mt-0.5 ${
            task.completed ? "text-purple-600" : "text-slate-300 dark:text-slate-600 hover:text-purple-600"
          }" aria-label="Toggle task ${esc(task.title)}">${task.completed ? ICONS.check : ICONS.square}</button>
          <span class="flex-1 ${
            task.completed ? "line-through text-slate-400 dark:text-slate-500" : ""
          }">${esc(task.title)}</span>
        </div>`,
        )
        .join("")
    : '<p class="text-xs text-slate-400">No tasks yet.</p>';

  return `
    <article class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm hover:shadow-md transition flex flex-col justify-between space-y-4">
      <div>
        <div class="flex items-center justify-between mb-2 gap-2">
          <div class="flex items-center space-x-2 flex-wrap">
            <span class="text-xs font-bold px-2.5 py-0.5 rounded-full ${STATUS_CLASSES[project.status] || ""}">${esc(
              project.status,
            )}</span>
            ${
              topic
                ? `<span class="text-xs text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/60 px-2 py-0.5 rounded-md font-medium">${esc(
                    topic.title,
                  )}</span>`
                : ""
            }
          </div>
          <div class="flex items-center space-x-1">
            <button data-action="edit-project" data-id="${project.id}" class="p-1 text-slate-400 hover:text-indigo-600 transition" title="Edit project">${ICONS.edit}</button>
            <button data-action="delete-project" data-id="${project.id}" class="p-1 text-slate-400 hover:text-red-600 transition" title="Delete project">${ICONS.trash}</button>
          </div>
        </div>
        <h3 class="text-lg font-bold">${esc(project.title)}</h3>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">${esc(project.description)}</p>
        ${
          project.techStack.length
            ? `<div class="flex flex-wrap gap-1.5 mt-3">${project.techStack
                .map(
                  (tech) =>
                    `<span class="text-[11px] font-mono bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">${esc(
                      tech,
                    )}</span>`,
                )
                .join("")}</div>`
            : ""
        }
      </div>

      <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 py-2 border-y border-slate-100 dark:border-slate-800 gap-2">
        <div class="flex items-center space-x-4 flex-wrap">
          <span class="flex items-center gap-1">${ICONS.clock}${Number(project.hoursSpent)} hrs spent</span>
          ${
            project.targetDate
              ? `<span class="flex items-center gap-1">${ICONS.calendar}Target: ${esc(project.targetDate)}</span>`
              : ""
          }
        </div>
        ${
          project.repoUrl
            ? `<a href="${esc(project.repoUrl)}" target="_blank" rel="noreferrer" class="flex items-center text-indigo-600 dark:text-indigo-400 hover:underline font-semibold">Repo ${ICONS.link}</a>`
            : ""
        }
      </div>

      <div class="space-y-2">
        <div class="flex items-center justify-between text-xs">
          <span class="font-bold text-slate-600 dark:text-slate-300">Task Checklist</span>
          <span class="text-slate-400 font-medium">${project.completedTasks}/${project.totalTasks} Done</span>
        </div>
        <div class="space-y-1.5 max-h-36 overflow-y-auto pr-1">${tasks}</div>
        <form data-form="task" data-project="${project.id}" class="flex items-center space-x-1 pt-1">
          <input name="title" type="text" required placeholder="+ Add task…" class="flex-1 px-2 py-1 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md focus:outline-none focus:ring-1 focus:ring-purple-500" />
          <button type="submit" class="px-2 py-1 bg-slate-200 dark:bg-slate-700 hover:bg-purple-600 hover:text-white rounded-md text-xs font-semibold transition">Add</button>
        </form>
      </div>
    </article>`;
}

// --- Activity --------------------------------------------------------------
function activityView() {
  return `
    <div class="space-y-6">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 class="text-xl font-bold">Study &amp; Activity Logs</h2>
          <p class="text-xs text-slate-500 dark:text-slate-400">Detailed historical record of your focus hours and takeaway notes.</p>
        </div>
        <button data-action="open-log-modal" class="flex items-center justify-center space-x-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-xl shadow-sm transition">${ICONS.plus}<span>Log Study Session</span></button>
      </div>
      ${
        state.logs.length
          ? `<div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
              <div class="overflow-x-auto">
                <table class="w-full text-left text-xs sm:text-sm">
                  <thead class="bg-slate-50 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400 font-semibold border-b border-slate-200 dark:border-slate-800">
                    <tr><th class="p-3 sm:p-4">Date</th><th class="p-3 sm:p-4">Topic / Focus</th><th class="p-3 sm:p-4">Hours Logged</th><th class="p-3 sm:p-4">Notes &amp; Takeaways</th></tr>
                  </thead>
                  <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                    ${state.logs
                      .map(
                        (log) => `
                      <tr class="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition">
                        <td class="p-3 sm:p-4 font-mono text-slate-500 dark:text-slate-400 whitespace-nowrap">${esc(
                          log.date,
                        )}</td>
                        <td class="p-3 sm:p-4 font-semibold whitespace-nowrap">${esc(log.topicTitle)}</td>
                        <td class="p-3 sm:p-4"><span class="inline-flex items-center px-2 py-0.5 rounded-md font-bold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400">${Number(
                          log.hours,
                        )} hrs</span></td>
                        <td class="p-3 sm:p-4 text-slate-600 dark:text-slate-300">${esc(log.note) || "—"}</td>
                      </tr>`,
                      )
                      .join("")}
                  </tbody>
                </table>
              </div>
            </div>`
          : emptyState("No activity logs recorded yet.")
      }
    </div>`;
}

// --- Modals ----------------------------------------------------------------
function modalShell(title, body, accent = "indigo") {
  return `
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 w-full max-w-md rounded-2xl p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto" role="dialog" aria-modal="true" aria-label="${esc(
        title,
      )}">
        <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
          <h3 class="text-lg font-bold text-${accent}-600 dark:text-${accent}-400">${esc(title)}</h3>
          <button data-action="close-modal" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200" aria-label="Close dialog">${ICONS.x}</button>
        </div>
        ${body}
      </div>
    </div>`;
}

function field(label, inner) {
  return `<label class="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">${esc(
    label,
  )}${inner}</label>`;
}

const inputClass =
  "w-full p-2 text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500";

function openTopicModal(topic = null) {
  const selected = topic?.color || "indigo";
  modalRoot.innerHTML = modalShell(
    topic ? "Edit Topic" : "Add New Learning Topic",
    `<form data-form="topic" data-id="${topic?.id || ""}" class="space-y-4">
      ${field(
        "Topic Title",
        `<input name="title" required value="${esc(topic?.title || "")}" class="${inputClass}" />`,
      )}
      ${field(
        "Category Domain",
        `<input name="category" required value="${esc(topic?.category || "Engineering")}" class="${inputClass}" />`,
      )}
      <div>
        <span class="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Badge Accent Color</span>
        <input type="hidden" name="color" value="${esc(selected)}" />
        <div class="flex items-center space-x-2 pt-1">
          ${Object.keys(COLOR_CLASSES)
            .map(
              (color) => `
            <button type="button" data-action="pick-color" data-color="${color}" class="w-6 h-6 rounded-full ${
              COLOR_CLASSES[color]
            } transition ${color === selected ? "ring-2 ring-offset-2 ring-indigo-600" : "opacity-70 hover:opacity-100"}" aria-label="Select ${color}"></button>`,
            )
            .join("")}
        </div>
      </div>
      ${field(
        "Description",
        `<textarea name="description" rows="2" class="${inputClass}">${esc(topic?.description || "")}</textarea>`,
      )}
      ${field(
        "Key Takeaway / Notes",
        `<textarea name="notes" rows="2" class="${inputClass}">${esc(topic?.notes || "")}</textarea>`,
      )}
      ${modalActions("Save Topic")}
    </form>`,
  );
  focusFirstInput();
}

function openProjectModal(project = null) {
  modalRoot.innerHTML = modalShell(
    project ? "Edit Project" : "Add New Project",
    `<form data-form="project" data-id="${project?.id || ""}" class="space-y-4">
      ${field(
        "Project Title",
        `<input name="title" required value="${esc(project?.title || "")}" class="${inputClass}" />`,
      )}
      <div class="grid grid-cols-2 gap-3">
        ${field(
          "Status",
          `<select name="status" class="${inputClass}">
            ${["Planning", "Active", "Paused", "Completed"]
              .map(
                (status) =>
                  `<option value="${status}" ${
                    (project?.status || "Active") === status ? "selected" : ""
                  }>${status}</option>`,
              )
              .join("")}
          </select>`,
        )}
        ${field(
          "Linked Topic",
          `<select name="topicId" class="${inputClass}">
            <option value="">Standalone</option>
            ${state.topics
              .map(
                (topic) =>
                  `<option value="${topic.id}" ${
                    project?.topicId === topic.id ? "selected" : ""
                  }>${esc(topic.title)}</option>`,
              )
              .join("")}
          </select>`,
        )}
      </div>
      <div class="grid grid-cols-2 gap-3">
        ${field(
          "Target Date",
          `<input type="date" name="targetDate" value="${esc(project?.targetDate || "")}" class="${inputClass}" />`,
        )}
        ${field(
          "Repo URL",
          `<input type="url" name="repoUrl" value="${esc(project?.repoUrl || "")}" placeholder="https://github.com/…" class="${inputClass}" />`,
        )}
      </div>
      ${field(
        "Tech Stack (comma-separated)",
        `<input name="techStack" value="${esc((project?.techStack || []).join(", "))}" class="${inputClass}" />`,
      )}
      ${field(
        "Description & Goals",
        `<textarea name="description" rows="3" class="${inputClass}">${esc(project?.description || "")}</textarea>`,
      )}
      ${modalActions("Save Project")}
    </form>`,
    "purple",
  );
  focusFirstInput();
}

function openLogModal() {
  if (!state.topics.length) {
    toast("Add a learning topic before logging a session.", "error");
    return;
  }
  const today = new Date().toISOString().slice(0, 10);
  modalRoot.innerHTML = modalShell(
    "Log Study Session",
    `<form data-form="log" class="space-y-4">
      ${field(
        "Learning Topic",
        `<select name="topicId" required class="${inputClass}">
          ${state.topics.map((topic) => `<option value="${topic.id}">${esc(topic.title)}</option>`).join("")}
        </select>`,
      )}
      ${field(
        "Link to Project (optional)",
        `<select name="projectId" class="${inputClass}">
          <option value="">None</option>
          ${state.projects
            .map((project) => `<option value="${project.id}">${esc(project.title)}</option>`)
            .join("")}
        </select>`,
      )}
      <div class="grid grid-cols-2 gap-3">
        ${field(
          "Hours Spent",
          `<input type="number" name="hours" step="0.25" min="0.25" max="24" value="1" required class="${inputClass}" />`,
        )}
        ${field(
          "Date",
          `<input type="date" name="date" value="${today}" required class="${inputClass}" />`,
        )}
      </div>
      ${field(
        "Study Takeaways & Notes",
        `<textarea name="note" rows="3" placeholder="What did you learn?" class="${inputClass}"></textarea>`,
      )}
      ${modalActions("Save Activity Log")}
    </form>`,
  );
  focusFirstInput();
}

function modalActions(label) {
  return `
    <div class="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100 dark:border-slate-800">
      <button type="button" data-action="close-modal" class="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg">Cancel</button>
      <button type="submit" class="px-4 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition">${esc(
        label,
      )}</button>
    </div>`;
}

function focusFirstInput() {
  requestAnimationFrame(() => {
    const first = modalRoot.querySelector("input, select, textarea");
    if (first) first.focus();
  });
}

function closeModal() {
  modalRoot.innerHTML = "";
}

function confirmDialog(message, confirmLabel = "Delete") {
  return new Promise((resolve) => {
    modalRoot.innerHTML = modalShell(
      "Please confirm",
      `<p class="text-sm text-slate-600 dark:text-slate-300">${esc(message)}</p>
       <div class="flex justify-end space-x-2 pt-2">
         <button data-confirm="no" class="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg">Cancel</button>
         <button data-confirm="yes" class="px-4 py-2 text-xs font-semibold bg-red-600 hover:bg-red-700 text-white rounded-lg">${esc(
           confirmLabel,
         )}</button>
       </div>`,
    );
    const handler = (event) => {
      const button = event.target.closest("[data-confirm]");
      if (!button) return;
      modalRoot.removeEventListener("click", handler);
      closeModal();
      resolve(button.dataset.confirm === "yes");
    };
    modalRoot.addEventListener("click", handler);
  });
}

async function pickAndImport() {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
  input.addEventListener("change", async () => {
    const [file] = input.files || [];
    if (!file) return;

    const shouldReplace = await confirmDialog(
      "Importing replaces all current topics, projects, and logs. Export a backup first if unsure.",
      "Replace data",
    );
    if (!shouldReplace) return;

    try {
      const summary = await API.importFile(file);
      await refresh({ silent: true });
      toast(
        `Imported ${summary.topicsImported} topics, ${summary.projectsImported} projects, ${summary.logsImported} logs`,
      );
    } catch (error) {
      toast(error.message, "error");
    }
  });
  input.click();
}

// --- Event handling --------------------------------------------------------
document.addEventListener("click", async (event) => {
  const target = event.target.closest("[data-action]");
  if (!target) return;

  const { action } = target.dataset;
  try {
    switch (action) {
      case "tab":
        state.tab = target.dataset.tab;
        render();
        break;
      case "theme":
        state.darkMode = !state.darkMode;
        localStorage.setItem("theme", state.darkMode ? "dark" : "light");
        applyTheme();
        break;
      case "open-topic-modal":
        openTopicModal();
        break;
      case "open-project-modal":
        openProjectModal();
        break;
      case "open-log-modal":
        openLogModal();
        break;
      case "export":
        window.location.assign("/api/export");
        break;
      case "import":
        await pickAndImport();
        break;
      case "close-modal":
        closeModal();
        break;
      case "edit-topic":
        openTopicModal(state.topics.find((topic) => topic.id === target.dataset.id));
        break;
      case "edit-project":
        openProjectModal(state.projects.find((project) => project.id === target.dataset.id));
        break;
      case "delete-topic":
        if (await confirmDialog("Delete this topic? Logs stay, but the topic link is removed.")) {
          await API.deleteTopic(target.dataset.id);
          await refresh({ silent: true });
          toast("Topic deleted");
        }
        break;
      case "delete-project":
        if (await confirmDialog("Delete this project and all of its tasks?")) {
          await API.deleteProject(target.dataset.id);
          await refresh({ silent: true });
          toast("Project deleted");
        }
        break;
      case "toggle-module":
        await API.toggleModule(target.dataset.topic, target.dataset.module);
        await refresh({ silent: true });
        break;
      case "toggle-task":
        await API.toggleTask(target.dataset.project, target.dataset.task);
        await refresh({ silent: true });
        break;
      case "project-filter":
        state.projectFilter = target.dataset.status;
        render();
        break;
      case "pick-color": {
        const hidden = modalRoot.querySelector('input[name="color"]');
        if (hidden) hidden.value = target.dataset.color;
        target.parentElement.querySelectorAll("[data-action='pick-color']").forEach((button) => {
          button.classList.toggle("ring-2", button === target);
          button.classList.toggle("ring-offset-2", button === target);
          button.classList.toggle("ring-indigo-600", button === target);
          button.classList.toggle("opacity-70", button !== target);
        });
        break;
      }
      default:
        break;
    }
  } catch (error) {
    toast(error.message, "error");
  }
});

document.addEventListener("submit", async (event) => {
  const form = event.target.closest("form[data-form]");
  if (!form) return;
  event.preventDefault();

  const data = Object.fromEntries(new FormData(form).entries());
  const kind = form.dataset.form;

  try {
    if (kind === "topic") {
      const payload = {
        title: data.title,
        category: data.category,
        color: data.color,
        description: data.description,
        notes: data.notes,
      };
      if (form.dataset.id) {
        await API.updateTopic(form.dataset.id, payload);
      } else {
        await API.createTopic(payload);
      }
      closeModal();
      await refresh();
    } else if (kind === "project") {
      const payload = {
        title: data.title,
        topicId: data.topicId || null,
        status: data.status,
        targetDate: data.targetDate || null,
        repoUrl: data.repoUrl || null,
        techStack: (data.techStack || "")
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        description: data.description,
      };
      if (form.dataset.id) {
        await API.updateProject(form.dataset.id, payload);
      } else {
        await API.createProject(payload);
      }
      closeModal();
      await refresh();
    } else if (kind === "log") {
      await API.createLog({
        topicId: data.topicId,
        projectId: data.projectId || null,
        hours: Number(data.hours),
        date: data.date,
        note: data.note,
      });
      closeModal();
      await refresh();
    } else if (kind === "module") {
      await API.addModule(form.dataset.topic, data.title);
      await refresh({ silent: true });
      toast("Module added");
    } else if (kind === "task") {
      await API.addTask(form.dataset.project, data.title);
      await refresh({ silent: true });
      toast("Task added");
    }
  } catch (error) {
    toast(error.message, "error");
  }
});

document.addEventListener("input", (event) => {
  if (!event.target.matches("[data-search]")) return;
  state.search = event.target.value;
  const grid = document.getElementById("topics-grid");
  if (grid) grid.innerHTML = topicsGrid();
});

document.addEventListener("change", (event) => {
  if (!event.target.matches("[data-category]")) return;
  state.category = event.target.value;
  const grid = document.getElementById("topics-grid");
  if (grid) grid.innerHTML = topicsGrid();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && modalRoot.innerHTML.trim()) closeModal();
});

// --- Boot ------------------------------------------------------------------
applyTheme();
refresh({ silent: true });
