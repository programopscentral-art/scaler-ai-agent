<script>
  import { onMount, tick } from 'svelte';
  import { goto } from '$app/navigation';
  import { api } from '$lib/api.js';
  import { session, currentLead, currentNudge, currentPdf, currentTranscript } from '$lib/stores.js';
  import Sidebar from '$lib/Sidebar.svelte';

  // Three preset personas + custom
  const PRESETS = {
    rohan: {
      name: 'Rohan Sharma', company: 'TCS', experience_years: 4,
      role: 'Backend Developer', persona_type: 'rohan',
      intent: 'I want to switch from a service company to a product company like Flipkart or Swiggy.',
      linkedin_summary: '4 years at TCS in Java backend. BTech CSE Tier-2. Self-taught DSA via LeetCode. Recently completed a Coursera Algorithms course.'
    },
    karthik: {
      name: 'Karthik Iyer', company: 'Google', experience_years: 9,
      role: 'Senior Software Engineer', persona_type: 'karthik',
      intent: 'I want to move into ML/AI roles. Reading papers but stuck on practical system design at scale.',
      linkedin_summary: 'IIT Madras, 9 years at Google in distributed systems. L5 SWE. Mentors juniors. Skeptical of bootcamps but open to structured advanced programs.'
    },
    meera: {
      name: 'Meera Patel', company: 'Tier-3 Engineering College', experience_years: 0,
      role: 'Final Year B.Tech Student', persona_type: 'meera',
      intent: 'I need a job. My family wants me to take the government job offer but I want to work at a product company. I don\'t know if I can afford Scaler or even clear the entrance test.',
      linkedin_summary: 'Final year B.Tech student, Tier-3 college, 0 YoE. No LinkedIn. Family income below ₹3.5L/year. Government job offer on the table. First-generation graduate.'
    }
  };

  const PRESET_META = {
    rohan:   { color: '#3B82F6', bg: '#EFF6FF', tag: 'Service → Product' },
    karthik: { color: '#8B5CF6', bg: '#F5F3FF', tag: 'Senior · ML/AI move' },
    meera:   { color: '#F59E0B', bg: '#FFFBEB', tag: 'Student · Career pivot' },
  };

  let lead = {
    name: '', company: '', experience_years: null, role: '',
    intent: '', linkedin_summary: '', persona_type: 'custom'
  };

  let inputMode = 'transcript'; // 'transcript' | 'audio'
  let transcript = '';
  let audioFile = null;
  let audioFileName = '';

  let loadingNudge = false;
  let loadingPdf = false;
  let nudgeSent = false;
  let error = '';
  let leadIdLocal = null;
  let activePreset = null;

  onMount(async () => {
    // tick() lets the store propagate its value before we check —
    // prevents a false redirect when navigating here right after session.set()
    await tick();
    if (!$session.session_id) {
      goto('/');
      return;
    }
    if ($currentLead) {
      lead = {
        name: $currentLead.name || '',
        company: $currentLead.company || '',
        experience_years: $currentLead.experience_years ?? null,
        role: $currentLead.role || '',
        intent: $currentLead.intent || '',
        linkedin_summary: $currentLead.linkedin_summary || '',
        persona_type: $currentLead.persona_type || 'custom'
      };
      leadIdLocal = $currentLead.lead_id || null;
      nudgeSent = !!$currentNudge;
      activePreset = $currentLead.persona_type !== 'custom' ? $currentLead.persona_type : null;
    }
    if ($currentTranscript) transcript = $currentTranscript;
  });

  $: currentTranscript.set(transcript);

  function loadPreset(key) {
    if (key === 'custom') {
      lead = { name: '', company: '', experience_years: null, role: '', intent: '', linkedin_summary: '', persona_type: 'custom' };
      activePreset = null;
    } else {
      lead = { ...PRESETS[key] };
      activePreset = key;
    }
    nudgeSent = false;
    leadIdLocal = null;
  }

  function onAudioPick(e) {
    const f = e.target.files?.[0];
    if (f) { audioFile = f; audioFileName = f.name; }
  }

  async function makeNudge() {
    error = '';
    if (!lead.name || !lead.intent) {
      error = 'Name and intent are required.';
      return;
    }
    loadingNudge = true;
    try {
      const res = await api.generateNudge(lead, $session.bda_phone, $session.session_id);
      currentLead.set({ ...lead, lead_id: res.lead_id });
      currentNudge.set({ text: res.nudge_text, status: res.whatsapp_status });
      leadIdLocal = res.lead_id;
      nudgeSent = true;
      goto('/nudge');
    } catch (e) {
      error = e.message;
    } finally {
      loadingNudge = false;
    }
  }

  async function makePdf() {
    error = '';
    if (!lead.name) {
      error = 'Name is required.';
      return;
    }
    if (!leadIdLocal) {
      try {
        loadingPdf = true;
        const res = await api.registerLead(lead, $session.bda_phone, $session.session_id);
        leadIdLocal = res.lead_id;
        currentLead.set({ ...lead, lead_id: res.lead_id });
      } catch (e) {
        error = 'Failed to register lead: ' + e.message;
        loadingPdf = false;
        return;
      }
    }

    loadingPdf = true;
    try {
      let res;
      if (inputMode === 'transcript') {
        if (!transcript || transcript.length < 30) {
          error = 'Transcript must be at least 30 characters.';
          loadingPdf = false;
          return;
        }
        res = await api.generatePdf(lead, transcript, $session.session_id, leadIdLocal);
      } else {
        if (!audioFile) {
          error = 'Please upload an audio file.';
          loadingPdf = false;
          return;
        }
        res = await api.transcribeAudio(audioFile, lead, $session.session_id, leadIdLocal);
      }
      currentPdf.set({
        content_id: res.content_id,
        pdf_url: res.pdf_url,
        cover_message: res.cover_message,
        questions: res.extracted_questions,
        transcript: res.transcript || transcript
      });
      goto('/approve');
    } catch (e) {
      error = e.message;
    } finally {
      loadingPdf = false;
    }
  }
</script>

<div class="layout">
  <Sidebar activeStep={1} />

  <main class="main">
    <header class="page-header">
      <div>
        <h1>Generate intelligence</h1>
        <p class="muted">Pick a persona or fill in a custom lead. We'll brief the BDA and prep a personalised PDF.</p>
      </div>
    </header>

    <!-- Preset cards -->
    <div class="presets">
      {#each Object.entries(PRESETS) as [key, p]}
        {@const meta = PRESET_META[key]}
        <button
          class="preset"
          class:selected={activePreset === key}
          style="--accent:{meta.color};--accent-bg:{meta.bg}"
          on:click={() => loadPreset(key)}
        >
          <div class="preset-top">
            <strong>{p.name}</strong>
            <span class="preset-tag" style="background:{meta.bg};color:{meta.color}">{meta.tag}</span>
          </div>
          <span class="preset-sub">{p.company} · {p.experience_years === 0 ? 'Fresher' : p.experience_years + 'y'}</span>
        </button>
      {/each}
      <button class="preset preset-custom" class:selected={activePreset === null && !lead.name} on:click={() => loadPreset('custom')}>
        <div class="preset-top">
          <strong>Custom</strong>
        </div>
        <span class="preset-sub">Start from scratch</span>
      </button>
    </div>

    <!-- Lead profile card -->
    <div class="card">
      <h2 class="section-title">
        <span class="step-badge">1</span>
        Lead Profile
      </h2>
      <div class="field-row">
        <div class="field">
          <label>Name *</label>
          <input bind:value={lead.name} placeholder="Rohan Sharma" />
        </div>
        <div class="field">
          <label>Company / College</label>
          <input bind:value={lead.company} placeholder="TCS" />
        </div>
      </div>
      <div class="field-row">
        <div class="field">
          <label>Current Role</label>
          <input bind:value={lead.role} placeholder="Backend Developer" />
        </div>
        <div class="field">
          <label>Experience (years)</label>
          <input type="number" bind:value={lead.experience_years} placeholder="4" />
        </div>
      </div>
      <div class="field">
        <label>Intent (what they want) *</label>
        <textarea bind:value={lead.intent} rows="2" placeholder="Switch to a product company..."></textarea>
      </div>
      <div class="field">
        <label>LinkedIn / background summary</label>
        <textarea bind:value={lead.linkedin_summary} rows="3" placeholder="4 years at TCS, BTech Tier-2..."></textarea>
      </div>
    </div>

    <!-- Call input card -->
    <div class="card" style="margin-top:16px">
      <h2 class="section-title">
        <span class="step-badge">2</span>
        Call Input <span class="section-hint">(for PDF generation)</span>
      </h2>

      <div class="toggle">
        <button class:on={inputMode==='transcript'} on:click={() => inputMode='transcript'}>📝 Transcript</button>
        <button class:on={inputMode==='audio'} on:click={() => inputMode='audio'}>🎤 Audio Recording</button>
      </div>

      {#if inputMode === 'transcript'}
        <div class="field" style="margin-top:14px">
          <label>Paste call transcript</label>
          <textarea
            bind:value={transcript}
            rows="10"
            placeholder="BDA: Hi Rohan, thanks for taking the time...&#10;Rohan: Yeah, I had a quick question about the fees..."
          ></textarea>
        </div>
      {:else}
        <div class="drop">
          <input type="file" id="audio" accept="audio/*" on:change={onAudioPick} hidden />
          <label for="audio" class="drop-label">
            <div class="drop-icon">🎤</div>
            <div><strong>{audioFileName || 'Click to upload audio file'}</strong></div>
            <div class="muted">mp3 / wav / m4a · max 25 MB</div>
          </label>
        </div>
      {/if}
    </div>

    {#if error}<div class="error" style="margin-top:16px">{error}</div>{/if}

    <div class="actions">
      <button class="btn-ghost" on:click={makeNudge} disabled={loadingNudge || loadingPdf}>
        {#if loadingNudge}<span class="spinner spinner-dark"></span>Briefing BDA...{:else}1️⃣ Generate &amp; Send Nudge{/if}
      </button>
      <button class="btn-primary" on:click={makePdf} disabled={loadingPdf || loadingNudge}>
        {#if loadingPdf}<span class="spinner"></span>Building PDF...{:else}2️⃣ Generate PDF →{/if}
      </button>
    </div>
  </main>
</div>

<style>
  .layout {
    display: grid;
    grid-template-columns: 260px 1fr;
    min-height: 100vh;
  }

  .main { padding: 36px 48px; max-width: 920px; }

  .page-header { margin-bottom: 22px; }
  .page-header h1 { font-size: 26px; margin-bottom: 4px; }

  /* Preset cards */
  .presets { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 22px; }
  .preset {
    background: white;
    border: 2px solid var(--border);
    border-radius: 12px;
    padding: 14px 14px 12px;
    text-align: left;
    cursor: pointer;
    display: flex; flex-direction: column; gap: 6px;
    font-family: inherit;
    transition: all 0.15s;
  }
  .preset:hover { border-color: var(--accent, var(--blue-primary)); transform: translateY(-1px); box-shadow: var(--shadow); }
  .preset.selected { border-color: var(--accent, var(--blue-primary)); background: var(--accent-bg, var(--blue-light)); }
  .preset-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 6px; }
  .preset-top strong { font-size: 14px; color: var(--text-primary); }
  .preset-tag { font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 999px; white-space: nowrap; flex-shrink: 0; }
  .preset-sub { font-size: 12px; color: var(--text-muted); }
  .preset-custom { border-style: dashed; background: var(--bg); }
  .preset-custom:hover { border-color: var(--text-secondary); }

  /* Section headers */
  .section-title {
    font-size: 15px; font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 16px;
    display: flex; align-items: center; gap: 10px;
  }
  .step-badge {
    width: 22px; height: 22px;
    border-radius: 50%;
    background: var(--blue-primary); color: white;
    display: grid; place-items: center;
    font-size: 11px; font-weight: 800;
    flex-shrink: 0;
  }
  .section-hint { font-weight: 400; color: var(--text-muted); font-size: 13px; }

  /* Toggle */
  .toggle { display: inline-flex; background: var(--bg); border-radius: 8px; padding: 4px; gap: 4px; }
  .toggle button {
    background: transparent; border: none; padding: 8px 16px; border-radius: 6px;
    font-size: 13px; font-weight: 600; color: var(--text-secondary); cursor: pointer;
    font-family: inherit;
  }
  .toggle button.on { background: white; color: var(--blue-primary); box-shadow: var(--shadow); }

  /* Drop zone */
  .drop { margin-top: 14px; }
  .drop-label {
    display: block; padding: 32px; border: 2px dashed var(--border); border-radius: 12px;
    text-align: center; cursor: pointer; transition: all 0.15s;
  }
  .drop-label:hover { border-color: var(--blue-primary); background: var(--blue-light); }
  .drop-icon { font-size: 32px; margin-bottom: 8px; }

  /* Actions */
  .actions { display: flex; gap: 12px; margin-top: 22px; justify-content: flex-end; }

  .spinner-dark {
    border-color: rgba(0,0,0,0.15);
    border-top-color: var(--text-secondary);
  }
</style>
