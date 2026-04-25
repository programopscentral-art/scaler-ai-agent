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

  <!-- Session form -->
  <div class="card form-card">
    <h2>Start a session</h2>
    <p class="muted form-desc">
      Enter both WhatsApp numbers. The BDA gets the pre-call brief; you approve the PDF
      before it reaches the lead.
    </p>

    <WhatsAppOptIn variant="full" />

    <div class="field">
      <label for="bda">BDA WhatsApp Number</label>
      <input id="bda" placeholder="+91 98765 43210" bind:value={bda_phone} />
    </div>
    <div class="field">
      <label for="ev">Evaluator WhatsApp Number</label>
      <input id="ev" placeholder="+91 98765 43210" bind:value={evaluator_phone} />
    </div>

    {#if error}<div class="error">{error}</div>{/if}

    <button class="btn-primary full" disabled={loading} on:click={start}>
      {#if loading}<span class="spinner"></span>Starting session...{:else}Start Session →{/if}
    </button>

    <p class="muted hint">Make sure both numbers have joined the Twilio WhatsApp sandbox first.</p>
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

  /* Form card */
  .form-card {
    width: 100%;
    max-width: 520px;
    padding: 32px;
  }
  .form-card h2 { font-size: 20px; font-weight: 700; margin-bottom: 6px; }
  .form-desc { margin-bottom: 20px; line-height: 1.5; }
  .full { width: 100%; margin-top: 6px; }
  .hint { margin-top: 14px; text-align: center; }
</style>
