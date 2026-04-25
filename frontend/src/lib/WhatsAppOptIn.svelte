<script>
  import { onMount } from 'svelte';
  import { api } from './api.js';

  // variant: 'full' (onboarding) | 'compact' (nudge/approve)
  export let variant = 'full';

  let info = null;
  let loading = true;
  let copied = '';
  let openWaUrl = '';

  onMount(async () => {
    try {
      // Cache per-session so we don't re-fetch on every page navigation
      const cached = sessionStorage.getItem('_sandbox_info');
      if (cached) {
        info = JSON.parse(cached);
      } else {
        info = await api.sandboxInfo();
        sessionStorage.setItem('_sandbox_info', JSON.stringify(info));
      }
      const digits = (info.sandbox_number || '').replace(/[^0-9]/g, '');
      const text = encodeURIComponent(info.join_message || '');
      openWaUrl = `https://wa.me/${digits}?text=${text}`;
    } catch (_) {
      info = null;
    } finally {
      loading = false;
    }
  });

  async function copy(value, label) {
    try {
      await navigator.clipboard.writeText(value);
      copied = label;
      setTimeout(() => (copied = ''), 1600);
    } catch (_) {}
  }
</script>

{#if loading}
  <!-- silent while loading, avoids layout flash -->
{:else if !info || !info.twilio_configured}
  <div class="callout warn" class:compact={variant === 'compact'}>
    <strong>WhatsApp not configured.</strong>
    Messages won't be delivered — you'll still see them in this UI.
  </div>
{:else if variant === 'full'}
  <div class="callout">
    <div class="head">
      <span class="dot">📲</span>
      <strong>One-time WhatsApp setup (30 seconds)</strong>
    </div>
    <p class="lead">
      To receive messages from this app, opt in your WhatsApp number to our Twilio sandbox.
      Do this once per phone — the same number can act as both BDA and lead.
    </p>

    <ol class="steps">
      <li>
        Open WhatsApp and start a chat with
        <button class="chip" on:click={() => copy(info.sandbox_number, 'number')}>
          {info.sandbox_number}
          <span class="copy-hint">{copied === 'number' ? '✓ Copied' : 'Copy'}</span>
        </button>
      </li>
      <li>
        Send the message
        <button class="chip" on:click={() => copy(info.join_message, 'code')}>
          {info.join_message}
          <span class="copy-hint">{copied === 'code' ? '✓ Copied' : 'Copy'}</span>
        </button>
      </li>
      <li>You'll receive <em>"Sandbox: ✅ You are all set!"</em> — that number is now whitelisted.</li>
    </ol>

    <a href={openWaUrl} target="_blank" rel="noopener" class="open-wa">
      📱 Open WhatsApp with the join message pre-filled →
    </a>
  </div>
{:else}
  <details class="callout compact">
    <summary>📲 First time? Opt in to receive WhatsApp messages</summary>
    <ol class="steps small">
      <li>WhatsApp <strong>{info.sandbox_number}</strong></li>
      <li>Send <code>{info.join_message}</code></li>
      <li>Wait for the "you are all set" reply</li>
    </ol>
    <a href={openWaUrl} target="_blank" rel="noopener" class="open-wa small">
      Open WhatsApp pre-filled →
    </a>
  </details>
{/if}

<style>
  .callout {
    background: #ECFDF5;
    border: 1px solid #A7F3D0;
    border-left: 4px solid #059669;
    border-radius: 10px;
    padding: 16px 18px;
    margin: 14px 0 18px;
    font-size: 13.5px;
    color: var(--text-primary);
  }
  .callout.warn {
    background: #FEF3C7;
    border-color: #FDE68A;
    border-left-color: #D97706;
    color: #78350F;
    font-weight: 500;
  }
  .callout.compact {
    padding: 10px 14px;
    margin: 10px 0;
    font-size: 12.5px;
  }
  .callout.compact summary {
    cursor: pointer;
    font-weight: 600;
    color: #047857;
    list-style: none;
  }
  .callout.compact summary::-webkit-details-marker { display: none; }
  .callout.compact summary:hover { text-decoration: underline; }

  .head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-size: 14px; }
  .dot { font-size: 18px; }
  .lead { color: var(--text-secondary); margin-bottom: 12px; line-height: 1.5; }

  .steps { margin: 0 0 12px 20px; padding: 0; }
  .steps li { padding: 6px 0; line-height: 1.7; }
  .steps.small li { padding: 3px 0; line-height: 1.5; }

  .chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: white;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 4px 10px;
    margin: 0 4px;
    font-family: ui-monospace, monospace;
    font-size: 13px;
    font-weight: 600;
    color: var(--blue-primary);
    cursor: pointer;
    transition: all 0.15s;
  }
  .chip:hover { background: var(--blue-light); border-color: var(--blue-primary); }
  .copy-hint {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 11px;
    font-weight: 500;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .open-wa {
    display: inline-block;
    background: #25D366;
    color: white !important;
    padding: 8px 14px;
    border-radius: 7px;
    font-weight: 600;
    text-decoration: none !important;
    font-size: 13px;
    margin-top: 4px;
  }
  .open-wa:hover { background: #1DA851; }
  .open-wa.small { padding: 6px 10px; font-size: 12px; margin-top: 8px; }

  code {
    background: white;
    border: 1px solid var(--border);
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 12px;
    color: var(--blue-primary);
  }
</style>
