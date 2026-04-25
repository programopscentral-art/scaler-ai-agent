<script>
  import { goto } from '$app/navigation';
  import { session, currentLead, currentNudge, currentPdf, currentTranscript } from '$lib/stores.js';
  export let activeStep = 1;

  const steps = [
    { n: 1, label: 'Lead profile' },
    { n: 2, label: 'Nudge' },
    { n: 3, label: 'PDF' },
    { n: 4, label: 'Approve' },
  ];

  function logout() {
    session.set({ session_id: null, bda_phone: '', evaluator_phone: '' });
    currentLead.set(null);
    currentNudge.set(null);
    currentPdf.set(null);
    currentTranscript.set('');
    goto('/');
  }
</script>

<aside class="sidebar">
  <div class="brand">
    <div class="logo">S</div>
    <span>scaler</span>
  </div>

  <ol class="steps">
    {#each steps as s}
      <li class:active={s.n === activeStep} class:done={s.n < activeStep}>
        <span class="step-num">
          {#if s.n < activeStep}✓{:else}{s.n}{/if}
        </span>
        {s.label}
      </li>
    {/each}
  </ol>

  {#if $session?.session_id}
    <div class="session-info">
      <p class="label-tiny">Session</p>
      <p class="mono">{$session.session_id?.slice(0, 8) || '—'}</p>
      <p class="label-tiny" style="margin-top:10px">BDA</p>
      <p class="mono">{$session.bda_phone}</p>
    </div>
  {/if}

  <button class="logout-btn" on:click={logout}>
    ↩ New session
  </button>
</aside>

<style>
  .sidebar {
    background: white;
    border-right: 1px solid var(--border);
    padding: 28px 22px;
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    width: 260px;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 700;
    margin-bottom: 36px;
  }
  .logo {
    width: 30px; height: 30px;
    border-radius: 7px;
    background: var(--blue-primary);
    color: white;
    display: grid; place-items: center;
    font-weight: 800;
  }

  .steps { list-style: none; padding: 0; }
  .steps li {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 0;
    color: var(--text-muted);
    font-size: 14px;
    font-weight: 500;
    transition: color 0.2s;
  }

  .step-num {
    width: 24px; height: 24px;
    border-radius: 50%;
    background: var(--bg);
    color: var(--text-muted);
    display: grid; place-items: center;
    font-size: 12px; font-weight: 700;
    flex-shrink: 0;
    transition: background 0.2s, color 0.2s;
  }

  .steps li.active { color: var(--text-primary); font-weight: 700; }
  .steps li.active .step-num { background: var(--blue-primary); color: white; }

  .steps li.done { color: var(--success); font-weight: 600; }
  .steps li.done .step-num { background: var(--success); color: white; font-size: 11px; }

  .session-info {
    margin-top: auto;
    padding-top: 20px;
    border-top: 1px solid var(--border);
    font-size: 12px;
  }
  .label-tiny { color: var(--text-muted); font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
  .mono { font-family: ui-monospace, monospace; font-size: 12px; color: var(--text-secondary); margin-top: 2px; }

  .logout-btn {
    margin-top: 16px;
    width: 100%;
    padding: 9px 0;
    background: none;
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text-muted);
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s, color 0.15s, border-color 0.15s;
  }
  .logout-btn:hover {
    background: #fef2f2;
    border-color: #fca5a5;
    color: #dc2626;
  }
</style>
