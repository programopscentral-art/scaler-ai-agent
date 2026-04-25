<script>
  import { goto } from '$app/navigation';
  import { api } from '$lib/api.js';
  import { session } from '$lib/stores.js';
  import WhatsAppOptIn from '$lib/WhatsAppOptIn.svelte';

  let bda_phone = '';
  let evaluator_phone = '';
  let loading = false;
  let error = '';

  async function start() {
    error = '';
    if (!bda_phone || !evaluator_phone) {
      error = 'Both phone numbers are required.';
      return;
    }
    loading = true;
    try {
      const res = await api.onboard(evaluator_phone, bda_phone);
      session.set({ session_id: res.session_id, bda_phone, evaluator_phone });
      goto('/generate');
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  const flowSteps = [
    { icon: '👤', label: 'Lead Profile', sub: 'Background & intent' },
    { icon: '💬', label: 'BDA Brief', sub: 'WhatsApp before the call' },
    { icon: '📄', label: 'PDF Generation', sub: 'Transcript or audio' },
    { icon: '✅', label: 'Approve & Send', sub: 'Human gate before delivery' },
  ];
</script>

<div class="page">
  <!-- Hero -->
  <div class="hero">
    <div class="brand">
      <div class="logo">S</div>
      <span class="brand-name">scaler</span>
    </div>
    <h1>Sales <span class="highlight">AI Agent</span></h1>
    <p class="tagline">
      Personalised pre-call briefs and lead-specific PDFs — powered by Gemini 2.5 Flash,
      delivered on WhatsApp in under 60 seconds.
    </p>

    <!-- Workflow flow -->
    <div class="flow">
      {#each flowSteps as step, i}
        {#if i > 0}
          <div class="flow-arrow">→</div>
        {/if}
        <div class="flow-card">
          <div class="flow-icon">{step.icon}</div>
          <strong>{step.label}</strong>
          <span>{step.sub}</span>
        </div>
      {/each}
    </div>
  </div>

  <!-- Evaluator quick-start guide -->
  <div class="card guide-card">
    <div class="guide-title">
      <span class="guide-icon">🧭</span>
      <strong>Evaluator quick-start — 4 steps</strong>
    </div>
    <ol class="guide-steps">
      <li>
        <span class="guide-num">1</span>
        <span><strong>Join the WhatsApp sandbox</strong> — open WhatsApp, message <code>+1 415 523 8886</code>, send <code>join fix-orange</code>. You'll get a confirmation. Do this once per phone number.</span>
      </li>
      <li>
        <span class="guide-num">2</span>
        <span><strong>Enter your number in both fields below</strong> — for evaluation, use the same number as both "BDA" and "Evaluator". The BDA field is who receives the pre-call WhatsApp brief.</span>
      </li>
      <li>
        <span class="guide-num">3</span>
        <span><strong>Pick a preset persona</strong> (Rohan / Karthik / Meera) or enter a custom lead on the next page. Paste the call transcript, then click <em>Generate &amp; Send Nudge</em> and <em>Generate PDF</em>.</span>
      </li>
      <li>
        <span class="guide-num">4</span>
        <span><strong>Approve the PDF</strong> on the final screen — enter the lead's number and click Approve. The PDF link arrives on WhatsApp.</span>
      </li>
    </ol>
  </div>

  <!-- Session form -->
  <div class="card form-card">
    <h2>Start a session</h2>

    <WhatsAppOptIn variant="full" />

    <div class="field">
      <label for="bda">BDA WhatsApp Number</label>
      <input id="bda" placeholder="+91 98765 43210" bind:value={bda_phone} />
      <p class="field-hint">This number receives the AI-generated pre-call brief on WhatsApp.</p>
    </div>
    <div class="field">
      <label for="ev">Evaluator / Your WhatsApp Number</label>
      <input id="ev" placeholder="+91 98765 43210" bind:value={evaluator_phone} />
      <p class="field-hint">Stored for session tracking. Use the same number as above to receive everything on one phone.</p>
    </div>

    {#if error}<div class="error">{error}</div>{/if}

    <button class="btn-primary full" disabled={loading} on:click={start}>
      {#if loading}<span class="spinner"></span>Starting session...{:else}Start Session →{/if}
    </button>
  </div>
</div>

<style>
  .page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 52px 24px 48px;
    background:
      radial-gradient(900px 500px at 5% -10%, rgba(27,79,216,0.09), transparent 60%),
      radial-gradient(700px 400px at 105% 110%, rgba(245,158,11,0.07), transparent 60%),
      var(--bg);
  }

  /* Hero */
  .hero {
    text-align: center;
    max-width: 820px;
    margin-bottom: 40px;
  }
  .brand {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 22px;
    color: var(--text-secondary);
    font-weight: 700;
    letter-spacing: 0.4px;
  }
  .logo {
    width: 36px; height: 36px;
    border-radius: 9px;
    background: var(--blue-primary);
    color: white;
    display: grid; place-items: center;
    font-weight: 800; font-size: 20px;
  }
  .brand-name { font-size: 18px; }

  h1 {
    font-size: 44px;
    font-weight: 800;
    letter-spacing: -1px;
    margin-bottom: 14px;
    line-height: 1.1;
  }
  .highlight {
    background: linear-gradient(135deg, var(--blue-primary), #6366F1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .tagline {
    font-size: 16px;
    color: var(--text-secondary);
    line-height: 1.65;
    max-width: 500px;
    margin: 0 auto 36px;
  }

  /* Flow cards */
  .flow {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    flex-wrap: wrap;
  }
  .flow-card {
    background: white;
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px 20px;
    text-align: center;
    min-width: 136px;
    box-shadow: var(--shadow);
    transition: transform 0.15s, box-shadow 0.15s;
  }
  .flow-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); }
  .flow-icon { font-size: 26px; margin-bottom: 8px; }
  .flow-card strong { display: block; font-size: 13px; font-weight: 700; color: var(--text-primary); margin-bottom: 3px; }
  .flow-card span { font-size: 11px; color: var(--text-muted); }
  .flow-arrow { color: var(--text-muted); font-size: 18px; font-weight: 300; padding: 0 2px; }

  /* Evaluator guide card */
  .guide-card {
    width: 100%;
    max-width: 520px;
    padding: 20px 24px;
    background: #FFFBEB;
    border: 1px solid #FDE68A;
    border-left: 4px solid #F59E0B;
    margin-bottom: 14px;
  }
  .guide-title {
    display: flex; align-items: center; gap: 8px;
    font-size: 14px; margin-bottom: 14px;
  }
  .guide-icon { font-size: 18px; }
  .guide-steps {
    list-style: none; padding: 0; margin: 0;
    display: flex; flex-direction: column; gap: 10px;
  }
  .guide-steps li {
    display: flex; gap: 12px; align-items: flex-start;
    font-size: 13px; line-height: 1.55; color: var(--text-secondary);
  }
  .guide-num {
    min-width: 22px; height: 22px;
    border-radius: 50%;
    background: #F59E0B; color: white;
    display: grid; place-items: center;
    font-size: 11px; font-weight: 800;
    flex-shrink: 0; margin-top: 1px;
  }
  .guide-steps code {
    background: white; border: 1px solid #FDE68A;
    padding: 1px 6px; border-radius: 4px;
    font-size: 12px; color: #92400E; font-weight: 600;
  }

  /* Form card */
  .form-card {
    width: 100%;
    max-width: 520px;
    padding: 32px;
  }
  .form-card h2 { font-size: 20px; font-weight: 700; margin-bottom: 16px; }
  .field-hint { font-size: 11.5px; color: var(--text-muted); margin-top: 5px; line-height: 1.4; }
  .full { width: 100%; margin-top: 6px; }
</style>
