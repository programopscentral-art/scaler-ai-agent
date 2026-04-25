<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { currentNudge, currentLead, session } from '$lib/stores.js';
  import Sidebar from '$lib/Sidebar.svelte';
  import WhatsAppOptIn from '$lib/WhatsAppOptIn.svelte';

  onMount(() => {
    if (!$currentNudge) goto('/generate');
  });

  $: sent = $currentNudge?.status?.success;
  $: skipped = $currentNudge?.status?.skipped;

  // Fake timestamp for the WhatsApp bubble
  const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
</script>

<div class="layout">
  <Sidebar activeStep={2} />

  <main class="main">
    <header class="page-header">
      <div>
        <h1>Pre-call brief sent</h1>
        <p class="muted">The BDA will receive this on WhatsApp before calling {$currentLead?.name || 'the lead'}.</p>
      </div>
      {#if sent}
        <span class="badge badge-success">✓ Delivered to {$session.bda_phone}</span>
      {:else if skipped}
        <span class="badge badge-pending">Twilio not configured — preview only</span>
      {:else}
        <span class="badge badge-pending">Pending</span>
      {/if}
    </header>

    <WhatsAppOptIn variant="compact" />

    <!-- WhatsApp phone mockup -->
    <div class="phone-wrap">
      <div class="phone">
        <div class="phone-statusbar">
          <span>9:41</span>
          <span>●●●</span>
        </div>
        <div class="phone-header">
          <div class="avatar">S</div>
          <div class="contact-info">
            <strong>Scaler AI Agent</strong>
            <div class="online">online</div>
          </div>
        </div>
        <div class="chat-area">
          <div class="bubble">
            <pre>{$currentNudge?.text || ''}</pre>
            <div class="bubble-meta">
              <span class="timestamp">{timestamp}</span>
              {#if sent}
                <span class="ticks read">✓✓</span>
              {:else}
                <span class="ticks">✓</span>
              {/if}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="actions">
      <button class="btn-ghost" on:click={() => goto('/generate')}>← Back to profile</button>
      <button class="btn-primary" on:click={() => goto('/generate')}>Continue to PDF →</button>
    </div>
  </main>
</div>

<style>
  .layout { display: grid; grid-template-columns: 260px 1fr; min-height: 100vh; }

  .main { padding: 36px 48px; max-width: 860px; }

  .page-header {
    display: flex; align-items: flex-start; justify-content: space-between;
    gap: 16px; margin-bottom: 22px; flex-wrap: wrap;
  }
  .page-header h1 { font-size: 24px; margin-bottom: 4px; }

  /* Phone mockup */
  .phone-wrap { display: flex; justify-content: center; padding: 16px 0 24px; }
  .phone {
    width: 100%; max-width: 400px;
    background: #ECE5DD;
    border-radius: 28px;
    overflow: hidden;
    box-shadow: 0 8px 40px rgba(0,0,0,0.18), 0 2px 8px rgba(0,0,0,0.1);
    border: 6px solid #1a1a1a;
  }
  .phone-statusbar {
    background: #075E54;
    color: rgba(255,255,255,0.8);
    font-size: 11px;
    padding: 6px 14px 4px;
    display: flex; justify-content: space-between;
  }
  .phone-header {
    background: #075E54;
    display: flex; gap: 10px; align-items: center;
    padding: 8px 14px 12px;
    color: white;
  }
  .avatar {
    width: 38px; height: 38px;
    border-radius: 50%;
    background: rgba(255,255,255,0.2);
    display: grid; place-items: center;
    font-weight: 800; font-size: 16px;
    flex-shrink: 0;
  }
  .contact-info strong { display: block; font-size: 15px; }
  .online { font-size: 11px; color: rgba(255,255,255,0.75); margin-top: 1px; }

  .chat-area { padding: 14px 12px 16px; }
  .bubble {
    background: white;
    border-radius: 8px 8px 8px 0;
    padding: 10px 14px 8px;
    box-shadow: 0 1px 1px rgba(0,0,0,0.1);
    max-width: 100%;
  }
  .bubble pre {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13.5px; line-height: 1.55;
    color: var(--text-primary);
    white-space: pre-wrap; word-wrap: break-word;
    margin: 0;
  }
  .bubble-meta {
    display: flex; align-items: center; justify-content: flex-end;
    gap: 4px; margin-top: 6px;
  }
  .timestamp { font-size: 11px; color: #667781; }
  .ticks { font-size: 12px; color: #667781; }
  .ticks.read { color: #53BDEB; }

  .actions { display: flex; gap: 12px; justify-content: flex-end; }
</style>
