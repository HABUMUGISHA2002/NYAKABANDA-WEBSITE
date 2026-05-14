const root = document.documentElement;
const storedTheme = localStorage.getItem("theme");
if (storedTheme) root.dataset.theme = storedTheme;

document.querySelector(".theme-toggle")?.addEventListener("click", () => {
  root.dataset.theme = root.dataset.theme === "dark" ? "" : "dark";
  localStorage.setItem("theme", root.dataset.theme || "light");
});

document.querySelector(".menu-toggle")?.addEventListener("click", () => {
  document.querySelector(".nav-links")?.classList.toggle("open");
});

/* Flash message auto-dismiss */
document.querySelectorAll(".alert").forEach((el) => {
  setTimeout(() => { el.style.opacity = "0"; el.style.transform = "translateX(100%)"; setTimeout(() => el.remove(), 400); }, 4000);
});

/* Delete confirmation */
document.querySelectorAll("form[action*='/delete']").forEach((form) => {
  form.addEventListener("submit", (e) => {
    if (!confirm("Are you sure you want to delete this item?")) e.preventDefault();
  });
});

/* Active nav highlighting */
const currentPath = window.location.pathname;
document.querySelectorAll(".nav-links a, .sidebar a").forEach((a) => {
  const href = a.getAttribute("href");
  if (href && href !== "#" && currentPath.startsWith(href) && href !== "/") a.style.color = "var(--primary)";
  if (href && currentPath === "/" && href === "/") a.style.color = "var(--primary)";
});

function drawChart(canvas, rows, colors) {
  if (!canvas || !rows?.length) return;
  const ctx = canvas.getContext("2d");
  const ratio = window.devicePixelRatio || 1;
  const width = canvas.clientWidth;
  const height = 260;
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  ctx.scale(ratio, ratio);
  ctx.clearRect(0, 0, width, height);

  const max = Math.max(...rows.map((row) => Number(row.value) || 0), 1);
  const gap = 18;
  const barWidth = (width - gap * (rows.length + 1)) / rows.length;
  rows.forEach((row, index) => {
    const value = Number(row.value) || 0;
    const barHeight = (value / max) * 170;
    const x = gap + index * (barWidth + gap);
    const y = 210 - barHeight;
    ctx.fillStyle = colors[index % colors.length];
    ctx.roundRect(x, y, barWidth, barHeight, 8);
    ctx.fill();
    ctx.fillStyle = getComputedStyle(root).getPropertyValue("--text");
    ctx.font = "700 13px system-ui";
    ctx.fillText(row.label, x, 238);
    ctx.fillText(value, x, y - 8);
  });
}

document.querySelectorAll("canvas[data-values]").forEach((canvas, index) => {
  drawChart(canvas, JSON.parse(canvas.dataset.values), index ? ["#0f8b6f", "#f2a541", "#4f7cac", "#c2413b"] : ["#0f8b6f", "#4f7cac", "#f2a541"]);
});
