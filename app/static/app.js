const eventsBox = document.getElementById("events");
const message = document.getElementById("message");
const statsBox = document.getElementById("stats");

function show(text, isError = false) {
  message.textContent = text;
  message.className = isError ? "error" : "";
}

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const body = response.status === 204 ? null : await response.json();
  if (!response.ok) throw new Error(body && body.error ? body.error : `request failed (${response.status})`);
  return body;
}

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function eventCard(event) {
  const card = element("article", undefined, "event");
  const head = element("div", undefined, "event-head");
  const info = element("div");
  info.append(element("h3", event.title), element("p", `${event.venue} · ${event.event_date}`, "meta"));
  const seats = element("span", `${event.seats_left} of ${event.capacity} seats left`, event.seats_left === 0 ? "seats full" : "seats");
  head.append(info, seats);

  const form = element("form");
  const name = element("input");
  name.placeholder = "Your name";
  name.required = true;
  const email = element("input");
  email.placeholder = "Email";
  email.type = "email";
  email.required = true;
  const register = element("button", "Register");
  register.disabled = event.seats_left === 0;
  const remove = element("button", "Delete event", "secondary");
  remove.type = "button";
  form.append(name, email, register, remove);

  form.addEventListener("submit", async (submitEvent) => {
    submitEvent.preventDefault();
    try {
      await api(`/api/events/${event.id}/registrations`, { method: "POST", body: JSON.stringify({ name: name.value, email: email.value }) });
      show(`Registered ${name.value} for ${event.title}.`);
      await refresh();
    } catch (error) {
      show(error.message, true);
    }
  });
  remove.addEventListener("click", async () => {
    try {
      await api(`/api/events/${event.id}`, { method: "DELETE" });
      show(`Deleted ${event.title}.`);
      await refresh();
    } catch (error) {
      show(error.message, true);
    }
  });

  card.append(head, form);
  return card;
}

function statCard(value, label) {
  const card = element("div", undefined, "stat");
  card.append(element("strong", String(value)), element("span", label));
  return card;
}

async function refresh() {
  const [events, stats] = await Promise.all([api("/api/events"), api("/api/stats")]);
  statsBox.replaceChildren(
    statCard(stats.events, "events"),
    statCard(stats.registrations, "registrations"),
    statCard(stats.seats_left, "seats left"),
  );
  eventsBox.replaceChildren(...(events.length ? events.map(eventCard) : [element("p", "No events yet.", "meta")]));
}

document.getElementById("event-form").addEventListener("submit", async (submitEvent) => {
  submitEvent.preventDefault();
  const data = Object.fromEntries(new FormData(submitEvent.target));
  data.capacity = Number(data.capacity);
  try {
    const created = await api("/api/events", { method: "POST", body: JSON.stringify(data) });
    submitEvent.target.reset();
    show(`Added ${created.title}.`);
    await refresh();
  } catch (error) {
    show(error.message, true);
  }
});

refresh().catch((error) => show(error.message, true));
