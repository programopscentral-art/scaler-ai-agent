import { writable } from 'svelte/store';
import { browser } from '$app/environment';

function persistent(key, initial) {
  let value = initial;
  if (browser) {
    try {
      const raw = localStorage.getItem(key);
      if (raw) value = JSON.parse(raw);
    } catch (_) {}
  }
  const store = writable(value);
  if (browser) {
    store.subscribe((v) => {
      try {
        localStorage.setItem(key, JSON.stringify(v));
      } catch (_) {}
    });
  }
  return store;
}

export const session = persistent('scaler_session', {
  session_id: null,
  bda_phone: '',
  evaluator_phone: ''
});

export const currentLead = persistent('scaler_lead', null);
export const currentNudge = persistent('scaler_nudge', null);
export const currentPdf = persistent('scaler_pdf', null);
export const currentTranscript = persistent('scaler_transcript', '');
