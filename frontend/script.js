// Address of your backend. Change this when you deploy the backend online.
const API = "http://127.0.0.1:8000";

let currentSkills = [];
let selectedFile = null;

const $ = (id) => document.getElementById(id);

// Build elements with textContent (NOT innerHTML) so text from job data can never run as code
function el(tag, className, text) {
  const e = document.createElement(tag);
  if (className) e.className = className;
  if (text !== undefined && text !== null) e.textContent = text;
  return e;
}

// Only allow normal web links
function safeUrl(u) {
  try {
    const x = new URL(u);
    return x.protocol === "http:" || x.protocol === "https:" ? x.href : null;
  } catch (e) {
    return null;
  }
}

function makeLink(text, url, className) {
  const href = safeUrl(url);
  if (!href) return null;
  const a = el("a", className, text);
  a.href = href;
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  return a;
}

function chips(list, kind) {
  const box = el("div", "chips");
  list.forEach((s) => box.appendChild(el("span", "chip " + (kind || ""), s)));
  return box;
}

function show(viewId) {
  ["upload-view", "results-view", "gap-view"].forEach((id) =>
    $(id).classList.toggle("hidden", id !== viewId)
  );
  window.scrollTo(0, 0);
}

function errorText(data, fallback) {
  return data && typeof data.detail === "string" ? data.detail : fallback;
}

// ---------- Screen 1: upload ----------
function setFile(f) {
  selectedFile = f;
  $("file-name").textContent = f ? f.name : "No file chosen";
  $("analyze-btn").disabled = !f;
  $("error").textContent = "";
}

$("file-input").addEventListener("change", (e) => setFile(e.target.files[0] || null));

const dz = $("dropzone");
["dragenter", "dragover"].forEach((ev) =>
  dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("drag"); })
);
["dragleave", "drop"].forEach((ev) =>
  dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove("drag"); })
);
dz.addEventListener("drop", (e) => {
  const f = e.dataTransfer.files[0];
  if (f) setFile(f);
});

$("analyze-btn").addEventListener("click", async () => {
  if (!selectedFile) return;
  $("analyze-btn").disabled = true;
  $("loading").classList.remove("hidden");
  $("error").textContent = "";

  const form = new FormData();
  form.append("file", selectedFile);

  try {
    const res = await fetch(API + "/analyze", { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(errorText(data, "Something went wrong. Please try again."));
    currentSkills = data.skills;
    renderResults(data);
    show("results-view");
  } catch (err) {
    $("error").textContent =
      err instanceof TypeError
        ? "Cannot reach the server. Is the backend running?"
        : err.message;
  } finally {
    $("loading").classList.add("hidden");
    $("analyze-btn").disabled = !selectedFile;
  }
});

// ---------- Screen 2: results ----------
function renderResults(data) {
  $("skills").replaceChildren(...data.skills.map((s) => el("span", "chip", s)));

  const rolesBox = $("roles");
  rolesBox.replaceChildren();
  if (!data.roles.length) {
    rolesBox.appendChild(el("p", "muted", "No roles matched yet. Try adding more skills to your resume."));
  }
  data.roles.forEach((r) => {
    const card = el("div", "card");
    card.appendChild(el("span", "score", r.final_score + "%"));
    card.appendChild(el("h3", "", r.role));
    const bar = el("div", "bar");
    const fill = el("div");
    fill.style.width = Math.min(r.final_score, 100) + "%";
    bar.appendChild(fill);
    card.appendChild(bar);
    card.appendChild(el("div", "label", "You already have"));
    card.appendChild(chips(r.matched_skills, "have"));
    if (r.missing_skills.length) {
      card.appendChild(el("div", "label", "Still missing"));
      card.appendChild(chips(r.missing_skills, "need"));
    }
    const btn = el("button", "btn", "See what to learn");
    btn.addEventListener("click", () => openGap(r.role));
    card.appendChild(btn);
    rolesBox.appendChild(card);
  });

  const jobsBox = $("jobs");
  jobsBox.replaceChildren();
  if (!data.jobs.length) {
    jobsBox.appendChild(el("p", "muted", "No matching jobs found."));
  }
  data.jobs.forEach((j) => {
    const card = el("div", "card");
    card.appendChild(el("span", "score", j.match_percent + "%"));
    card.appendChild(el("h3", "", j.title));
    card.appendChild(el("div", "meta", [j.company, j.location].filter(Boolean).join(" · ")));
    card.appendChild(el("div", "meta", [j.work_type, j.experience_level].filter(Boolean).join(" · ")));
    if (j.skills_you_have.length) {
      card.appendChild(el("div", "label", "Skills you have"));
      card.appendChild(chips(j.skills_you_have, "have"));
    }
    if (j.skills_to_learn.length) {
      card.appendChild(el("div", "label", "Skills to learn"));
      card.appendChild(chips(j.skills_to_learn, "need"));
    }
    const link = makeLink("View and apply →", j.url, "link");
    if (link) {
      const p = el("p");
      p.appendChild(link);
      card.appendChild(p);
    }
    jobsBox.appendChild(card);
  });
}

$("again-btn").addEventListener("click", () => {
  setFile(null);
  $("file-input").value = "";
  show("upload-view");
});

// ---------- Screen 3: skill gap ----------
async function loadRoles() {
  if ($("role-select").options.length) return;
  try {
    const res = await fetch(API + "/roles");
    const data = await res.json();
    data.roles.forEach((r) => {
      const o = el("option", "", r);
      o.value = r;
      $("role-select").appendChild(o);
    });
  } catch (e) { /* the user will see an error when they click Check */ }
}

async function openGap(role) {
  await loadRoles();
  $("role-select").value = role;
  show("gap-view");
  loadGap(role);
}

async function loadGap(role) {
  const out = $("gap-output");
  out.replaceChildren(el("p", "muted", "Checking..."));
  try {
    const res = await fetch(API + "/skill-gap", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ skills: currentSkills, role }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(errorText(data, "Could not load the skill gap."));
    renderGap(data);
  } catch (err) {
    out.replaceChildren(
      el("p", "error", err instanceof TypeError ? "Cannot reach the server." : err.message)
    );
  }
}

function learnItem(item) {
  const box = el("div", "learn-item");
  const title = item.skill + (item.importance_percent != null
    ? "  (asked in " + item.importance_percent + "% of jobs)" : "");
  box.appendChild(el("strong", "", title));
  const links = el("div");
  item.learn.forEach((l) => {
    const a = makeLink(l.name, l.url);
    if (a) links.appendChild(a);
  });
  box.appendChild(links);
  return box;
}

function renderGap(d) {
  const out = $("gap-output");
  out.replaceChildren();
  out.appendChild(el("h3", "", d.role + ": " + d.match_percent + "% match"));
  const bar = el("div", "bar");
  const fill = el("div");
  fill.style.width = d.match_percent + "%";
  bar.appendChild(fill);
  out.appendChild(bar);

  out.appendChild(el("h3", "", "Skills you have"));
  out.appendChild(d.you_have.length ? chips(d.you_have, "have") : el("p", "muted", "None of the core skills yet."));

  out.appendChild(el("h3", "", "Skills you need to learn"));
  if (!d.you_need_to_learn.length) {
    out.appendChild(el("p", "", "Great! You have all the core skills for this role."));
  }
  d.you_need_to_learn.forEach((i) => out.appendChild(learnItem(i)));

  if (d.also_in_demand.length) {
    out.appendChild(el("h3", "", "Also in demand in job postings"));
    d.also_in_demand.forEach((i) => out.appendChild(learnItem(i)));
  }
}

$("gap-btn").addEventListener("click", () => loadGap($("role-select").value));
$("back-btn").addEventListener("click", () => show("results-view"));

loadRoles();