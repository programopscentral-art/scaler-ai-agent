// Frontend API client. In dev, vite proxies /api → backend.
// In prod, FastAPI serves the SvelteKit build, so /api is same-origin.

const BASE = '';

async function jsonFetch(path, opts = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
    ...opts
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json();
}

export const api = {
  sandboxInfo: () => jsonFetch('/api/sandbox-info'),

  onboard: (evaluator_phone, bda_phone) =>
    jsonFetch('/api/onboard', {
      method: 'POST',
      body: JSON.stringify({ evaluator_phone, bda_phone })
    }),

  registerLead: (lead, bda_phone, session_id) =>
    jsonFetch('/api/register-lead', {
      method: 'POST',
      body: JSON.stringify({ lead, bda_phone, session_id })
    }),

  generateNudge: (lead, bda_phone, session_id) =>
    jsonFetch('/api/generate-nudge', {
      method: 'POST',
      body: JSON.stringify({ lead, bda_phone, session_id })
    }),

  generatePdf: (lead, transcript, session_id, lead_id) =>
    jsonFetch('/api/generate-pdf', {
      method: 'POST',
      body: JSON.stringify({ lead, transcript, session_id, lead_id })
    }),

  transcribeAudio: async (audioFile, lead, session_id, lead_id) => {
    const form = new FormData();
    form.append('audio', audioFile);
    form.append('lead_json', JSON.stringify(lead));
    form.append('session_id', session_id);
    form.append('lead_id', lead_id);
    const res = await fetch('/api/transcribe-audio', { method: 'POST', body: form });
    if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
    return res.json();
  },

  approve: (content_id, action, lead_phone, edited_cover_message = null) =>
    jsonFetch('/api/approve', {
      method: 'POST',
      body: JSON.stringify({ content_id, action, lead_phone, edited_cover_message })
    })
};
