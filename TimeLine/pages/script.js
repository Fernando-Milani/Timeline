// ===============================
// Variáveis Globais
// ===============================
let GLOBAL_DATA = {
  events: {},
  periods: {}
};

let currentMin;
let currentMax;
let absoluteMin;
let absoluteMax;

const ZOOM_FACTOR = 0.1; // 10% por scroll
const DRAG_PADDING_RATIO = 0.5; // permite arrastar até 50% do range visível além dos limites


// ===============================
// Carrega os dados JSON
// ===============================
async function loadData() {
  const [eventsRes, periodsRes] = await Promise.all([
    fetch("../data/timeline_events.json"),
    fetch("../data/timeline_periods.json")
  ]);

  const eventsData = await eventsRes.json();
  const periodsData = await periodsRes.json();

  return {
    events: eventsData.events,
    periods: periodsData.periods
  };
}

async function loadContentFile(filename) {
  try {
    const response = await fetch(`../data/content/${filename}`);
    if (!response.ok) throw new Error("Arquivo não encontrado");

    return await response.text();
  } catch (error) {
    console.error("Erro ao carregar conteúdo:", error);
    return "<p>Conteúdo não disponível.</p>";
  }
}

function formatYear(year) {
  year = Math.floor(year);

  const absYear = Math.abs(year);

  let formatted;

  if (absYear >= 1_000_000_000) {
    formatted = (absYear / 1_000_000_000).toFixed(1).replace(/\.0$/, "") + " Bi";
  } 
  else if (absYear >= 1_000_000) {
    formatted = (absYear / 1_000_000).toFixed(1).replace(/\.0$/, "") + " Mi";
  } 
  else {
    formatted = absYear.toString();
  }

  if (year < 0) {
    return formatted + " a.C.";
  }

  return formatted;
}

// ===============================
// Converte data para ano numérico
// ===============================
function yearFromDate(dateStr) {
  dateStr = dateStr.trim();

  if (dateStr.startsWith("-")) {
    const parts = dateStr.slice(1).split("-");
    const year = parseInt(parts[0], 10);
    return isNaN(year) ? 0 : -year;
  } else {
    const parts = dateStr.split("-");
    const year = parseInt(parts[0], 10);
    return isNaN(year) ? 0 : year;
  }
}

// ===============================
// Calcula limites absolutos
// ===============================
function calculateBounds(events, periods) {
  const years = [];

  Object.values(events).forEach(e => {
    years.push(yearFromDate(e.date));
  });

  Object.values(periods).forEach(p => {
    years.push(p.startYear, p.endYear);
  });

  const min = Math.min(...years);
  const max = Math.max(...years);

  return {
    min,
    max: min === max ? min + 1 : max
  };
}

// ===============================
// Converte ano para porcentagem
// ===============================
function yearToPercent(year, min, max) {
  return ((year - min)/  (max - min)) * 100;
}

// ===============================
// Régua
// ===============================
function renderScale() {
  const scale = document.getElementById("timeline-scale");
  if (!scale) return;

  scale.innerHTML = "";

  const range = currentMax - currentMin;

  let divisions = 5;
  if (range < 50) divisions = 4;
  if (range < 10) divisions = 3;

  const step = range / (divisions - 1);

  for (let i = 0; i < divisions; i++) {
    const year = currentMin + step * i;
    const percent = (i / (divisions - 1)) * 100;

    const mark = document.createElement("div");
    mark.className = "scale-mark";

    mark.style.left = percent + "%";
    mark.textContent = formatYear(year);

    scale.appendChild(mark);
  }
}

// ===============================
// LOD - Decide se evento e período aparecem
// ===============================
function shouldRenderEvent(event) {
  const visibleRange = currentMax - currentMin;
  const totalRange = absoluteMax - absoluteMin;

  const zoomPercent = visibleRange / totalRange; 
  const importance = event.importance || 5;

  const zoomLevel = 1 - zoomPercent;
  const threshold = Math.pow((10 - importance) / 10, 1.5);

  return zoomLevel >= threshold;
}

function shouldRenderPeriod(period) {
  const visibleRange = currentMax - currentMin;
  const totalRange = absoluteMax - absoluteMin;

  const zoomPercent = visibleRange / totalRange;
  const zoomLevel = 1 - zoomPercent;

  const importance = period.importance || 5;

  // importância 10 = threshold 0
  // importância 1 = threshold 0.9
  const threshold = (10 - importance) / 10;

  return zoomLevel >= threshold;
}

// ===============================
// Render principal
// ===============================
async function renderTimeline() {
  const { events, periods } = await loadData();

  GLOBAL_DATA.events = events;
  GLOBAL_DATA.periods = periods;

  const bounds = calculateBounds(events, periods);

  absoluteMin = bounds.min;
  absoluteMax = bounds.max;

  // Garante que tudo fique positivo para log
  logOffset = Math.abs(absoluteMin) + 1;

  currentMin = absoluteMin;
  currentMax = absoluteMax;

  redrawTimeline();
  renderResults();
  setupZoom();
  setupDrag();

  const searchInput = document.getElementById("searchInput");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      renderResults(e.target.value);
    });
  }
  renderScale();
}

// ===============================
// Redesenha TL conforme zoom
// ===============================
function redrawTimeline() {
  const timeline = document.getElementById("timeline");
  const { events, periods } = GLOBAL_DATA;

  /* =========================
     PERÍODOS
  ========================= */

  const existingPeriods = new Map();
  timeline.querySelectorAll(".period").forEach(el => {
    existingPeriods.set(el.dataset.id, el);
  });

  Object.values(periods).forEach(period => {
    const id = period.id;

    const inRange =
      period.endYear >= currentMin &&
      period.startYear <= currentMax;

    const shouldShow = inRange && shouldRenderPeriod(period);

    let element = existingPeriods.get(id);

    if (shouldShow) {
      const left = yearToPercent(period.startYear, currentMin, currentMax);
      const right = yearToPercent(period.endYear, currentMin, currentMax);
      const width = right - left;

      if (!element) {
        element = document.createElement("div");
        element.className = "period";
        element.dataset.id = id;
        element.textContent = period.title;

        element.addEventListener("click", () => {
          openContent(period.title, period.contentFile);
        });

        element.style.left = left + "%";
        element.style.width = width + "%";

        timeline.appendChild(element);

        requestAnimationFrame(() => {
          element.classList.add("visible");
        });

      } else {
        element.style.left = left + "%";
        element.style.width = width + "%";
        element.classList.add("visible");
        existingPeriods.delete(id);
      }

    } else if (element) {
      element.classList.remove("visible");

      element.addEventListener("transitionend", function handler() {
        element.removeEventListener("transitionend", handler);
        if (!element.classList.contains("visible")) {
          element.remove();
        }
      });

      existingPeriods.delete(id);
    }
  });

  /* =========================
     EVENTOS
  ========================= */

  const existingEvents = new Map();
  timeline.querySelectorAll(".event").forEach(el => {
    existingEvents.set(el.dataset.id, el);
  });

  Object.values(events).forEach(event => {
    const year = yearFromDate(event.date);
    const id = event.id;

    const inRange = year >= currentMin && year <= currentMax;
    const shouldShow = inRange && shouldRenderEvent(event);

    let element = existingEvents.get(id);

    if (shouldShow) {
      const left = yearToPercent(year, currentMin, currentMax);

      if (!element) {
        element = document.createElement("div");
        element.className = "event";
        element.dataset.id = id;

        element.innerHTML = `
          <div class="event-dot"></div>
          <div class="event-title">${event.title}</div>
        `;

        element.addEventListener("click", () => {
          openContent(event.title, event.contentFile);
        });

        element.style.left = left + "%";

        timeline.appendChild(element);

        requestAnimationFrame(() => {
          element.classList.add("visible");
        });

      } else {
        element.style.left = left + "%";
        element.classList.add("visible");
        existingEvents.delete(id);
      }

    } else if (element) {
      element.classList.remove("visible");

      element.addEventListener("transitionend", function handler() {
        element.removeEventListener("transitionend", handler);
        if (!element.classList.contains("visible")) {
          element.remove();
        }
      });

      existingEvents.delete(id);
    }
  });
}

// ===============================
// Zoom com scroll (mouse como centro)
// ===============================
function setupZoom() {
  const container = document.querySelector(".timeline-container");

  container.addEventListener("wheel", (e) => {
    e.preventDefault();

    const rect = container.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const percent = mouseX / rect.width;

    const range = currentMax - currentMin;
    const totalRange = absoluteMax - absoluteMin;
    const zoomAmount = range * ZOOM_FACTOR;

    let newMin = currentMin;
    let newMax = currentMax;

    if (e.deltaY < 0) {
      // Zoom in
      newMin += zoomAmount * percent;
      newMax -= zoomAmount * (1 - percent);
    } else {
      // Zoom out
      newMin -= zoomAmount * percent;
      newMax += zoomAmount * (1 - percent);
    }

    const newRange = newMax - newMin;

    // Limite mínimo de zoom
    if (newRange < 5) return;

    //  Limite máximo de zoom (range original)
    if (newRange > totalRange) return;

    currentMin = newMin;
    currentMax = newMax;

    redrawTimeline();
    renderScale();
  });
}

// ===============================
// Deslizar TL com mouse
// ===============================
function setupDrag() {
  const container = document.querySelector(".timeline-container");

  let isDragging = false;
  let startX = 0;
  let startMin = 0;
  let startMax = 0;

  container.addEventListener("mousedown", (e) => {
    isDragging = true;
    startX = e.clientX;
    startMin = currentMin;
    startMax = currentMax;
    container.style.cursor = "grabbing";
  });

  window.addEventListener("mouseup", () => {
    isDragging = false;
    container.style.cursor = "grab";
  });

  window.addEventListener("mousemove", (e) => {
    if (!isDragging) return;

    const rect = container.getBoundingClientRect();
    const dx = e.clientX - startX;

    const visibleRange = startMax - startMin;
    const yearsPerPixel = visibleRange / rect.width;
    const offsetYears = dx * yearsPerPixel;

    let newMin = startMin - offsetYears;
    let newMax = startMax - offsetYears;

    // margem virtual proporcional ao zoom
    const padding = visibleRange * DRAG_PADDING_RATIO;

    const minLimit = absoluteMin - padding;
    const maxLimit = absoluteMax + padding;

    if (newMin < minLimit) {
      newMin = minLimit;
      newMax = newMin + visibleRange;
    }

    if (newMax > maxLimit) {
      newMax = maxLimit;
      newMin = newMax - visibleRange;
    }

    currentMin = newMin;
    currentMax = newMax;

    redrawTimeline();
    renderScale();
  });
}

// ===============================
// Busca
// ===============================
function normalizeText(text) {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

// ===============================
// Extrai conteúdo dos elementos da TL
// ===============================
async function openContent(title, contentFile) {
  if (!contentFile) return;

  const content = await loadContentFile(contentFile);

  document.getElementById("content-title").textContent = title;
  document.getElementById("content-body").innerHTML = content;

  document.getElementById("content-panel").classList.add("open");
}

// ===============================
// Renderiza Cards abaixo da TL
// ===============================
async function renderResults(filterText = "") {
  const container = document.getElementById("results");
  if (!container) return;

  container.innerHTML = "";

  let resultsCount = 0;

  const search = normalizeText(filterText.trim());
  const showAll = search === "";

  // ---------------------------
  // EVENTOS
  // ---------------------------
  for (const event of Object.values(GLOBAL_DATA.events)) {

    const title = normalizeText(event.title);
    const date = normalizeText(event.date);
    const tags = (event.tags || []).map(t => normalizeText(t));
    const categories = (event.categories || []).map(c => normalizeText(c));

    const matches =
      showAll ||
      title.includes(search) ||
      date.includes(search) ||
      tags.some(tag => tag.includes(search)) ||
      categories.some(cat => cat.includes(search));

    if (!matches) continue;

    resultsCount++; // CONTA RESULTADO

    const div = document.createElement("div");
    div.className = "result-card";

    if (event.contentFile) {
      const image = await extractImageFromContent(event.contentFile);
      if (image) {
        div.style.backgroundImage = `url(${image})`;
        div.style.backgroundSize = "cover";
        div.style.backgroundPosition = "center";
        div.style.color = "white";
      }
    }

    div.innerHTML = `
      <div class="result-type">Evento</div>
      <div class="result-title">${event.title}</div>
      <div>${formatYear(yearFromDate(event.date))}</div>
    `;

    container.appendChild(div);

    div.addEventListener("click", () => {
      openContent(event.title, event.contentFile);
    });
  }

  // ---------------------------
  // PERÍODOS
  // ---------------------------
  for (const period of Object.values(GLOBAL_DATA.periods)) {

    const title = normalizeText(period.title);

    const matches =
      showAll ||
      title.includes(search) ||
      String(period.startYear).includes(search) ||
      String(period.endYear).includes(search);

    if (!matches) continue;

    resultsCount++; // CONTA RESULTADO

    const div = document.createElement("div");
    div.className = "result-card";

    if (period.contentFile) {
      const image = await extractImageFromContent(period.contentFile);
      if (image) {
        div.style.backgroundImage = `url(${image})`;
        div.style.backgroundSize = "cover";
        div.style.backgroundPosition = "center";
        div.style.color = "white";
      }
    }

    div.innerHTML = `
      <div class="result-type">Período</div>
      <div class="result-title">${period.title}</div>
      <div>${formatYear(period.startYear)} – ${formatYear(period.endYear)}</div>
    `;

    container.appendChild(div);
    div.addEventListener("click", () => {
      openContent(period.title, period.contentFile);
    });
  }

  // ============================
  // SE NÃO HOUVER RESULTADOS
  // ============================
  if (resultsCount === 0 && !showAll) {
    container.innerHTML = `
      <div class="no-results">
        <h2>Nenhum resultado encontrado</h2>
        <p>Tente buscar por outro termo.</p>
      </div>
    `;
  }
}

// ===============================
// Preenche imagem no card
// ===============================
async function extractImageFromContent(contentRef) {
  try {
    const res = await fetch(`../data/content/${contentRef}`);
    if (!res.ok) return null;

    const text = await res.text();

    const parser = new DOMParser();
    const doc = parser.parseFromString(text, "text/html");

    const img = doc.querySelector("img");
    return img ? img.src : null;

  } catch (err) {
    console.warn("Erro ao carregar conteúdo:", err);
    return null;
  }
}

document.getElementById("close-content").addEventListener("click", () => {
  const panel = document.getElementById("content-panel");
  panel.classList.remove("open");

  // Limpa conteúdo antigo
  document.getElementById("content-title").textContent = "";
  document.getElementById("content-body").innerHTML = "<p>Selecione um evento para ver o conteúdo.</p>";
});



// ===============================
// Inicializa
// ===============================
renderTimeline();