<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { api } from '$lib/api.js';
  import { currentPdf, currentLead, session } from '$lib/stores.js';
  import Sidebar from '$lib/Sidebar.svelte';
  import WhatsAppOptIn from '$lib/WhatsAppOptIn.svelte';

  let leadPhone = '';
  let editedMessage = '';
  let editing = false;
  let loading = false;
  let result = null;
  let error = '';

  onMount(() => {
    if (!$currentPdf) goto('/generate');
    editedMessage = $currentPdf?.cover_message || '';
  });

  async function send(action) {
    error = '';
    if (!leadPhone) {
      error = "Lead's WhatsApp number is required to send.";
      return;
    }
    loading = true;
    try {
      const msg = action === 'edit' ? editedMessage : null;
      const res = await api.approve($currentPdf.content_id, action, leadPhone, msg);
      result = res;
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  async function skip() {
    loading = true;
    try {
      const res = await api.approve($currentPdf.content_id, 'skip', '');
      result = res;
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  const CATEGORY_COLORS = {
    roi_cost:        { bg: '#FEF3C7', color: '#92400E' },
    curriculum_depth:{ bg: '#DBEAFE', color: '#1E40AF' },
    career_outcome:  { bg: '#D1FAE5', color: '#065F46' },
    program_fit:     { bg: '#EDE9FE', color: '#5B21B6' },
    personal_doubt:  { bg: '#FCE7F3', color: '#9D174D' },
  };
  function catStyle(cat) {
    const c = CATEGORY_COLORS[cat?.toLowerCase().replace('/', '_')] || { bg: '#F1F5F9', color: '#475569' };
    return `background:${c.bg};color:${c.color}`;
  }
</script>

<div class="layout">
  <Sidebar activeStep={4} />

  <main class="main">
    {#if result}
      <!-- Success / skip state -->
      <div class="success-wrap">
        {#if result.status === 'sent'}
          <div class="success-icon">✅</div>
          <h1>PDF sent to lead!</h1>
          <p class="muted">The cover message and PDF link were delivered to {leadPhone} via WhatsApp.</p>
        {:else}
          <div class="success-icon skip">⏭️</div>
          <h1>Send skipped</h1>
          <p class="muted">Nothing was sent to the lead. You can process another lead below.</p>
        {/if}
        <button class="btn-primary" style="margin-top:28px" on:click={() => goto('/generate')}>
          Process another lead →
        </button>
      </div>
    {:else}
      <header class="page-header">
        <div>
          <h1>Approval gate</h1>
          <p class="muted">Review the PDF and cover message. Nothing is sent to <strong>{$currentLead?.name || 'the lead'}</strong> until you approve.</p>
        </div>
      </header>

      <div class="split">
        <!-- PDF preview -->
        <div class="card preview-card">
          <h3 class="card-title">📄 PDF Preview</h3>
          {#if $currentPdf?.pdf_url}
            <iframe src={$currentPdf.pdf_url} title="Lead PDF" frameborder="0"></iframe>
            <a href={$currentPdf.pdf_url} target="_blank" rel="noopener" class="open-link">
              Open in new tab ↗
            </a>
          {:else}
            <div class="no-pdf muted">No PDF URL available</div>
          {/if}
        </div>

        <!-- Review panel -->
        <div class="review-col">
          <div class="card review-card">
            <h3 class="card-title">💬 Cover Message</h3>

            <WhatsAppOptIn variant="compact" />

            <div class="field">
              <label>Lead's WhatsApp Number *</label>
              <input bind:value={leadPhone} placeholder="+91 98765 43210" />
            </div>

            <div class="field">
              <label>{editing ? 'Editing message' : 'Cover message'}</label>
              {#if editing}
                <textarea bind:value={editedMessage} rows="7"></textarea>
              {:else}
                <div class="message-preview">{$currentPdf?.cover_message}</div>
              {/if}
            </div>

            {#if error}<div class="error">{error}</div>{/if}

            <div class="actions">
              {#if !editing}
                <button class="btn-success action-btn" disabled={loading} on:click={() => send('approve')}>
                  {#if loading}<span class="spinner"></span>{/if}
                  ✅ Approve &amp; Send
                </button>
                <button class="btn-primary action-btn" disabled={loading} on:click={() => editing = true}>
                  ✏️ Edit Message
                </button>
              {:else}
                <button class="btn-success action-btn" disabled={loading} on:click={() => send('edit')}>
                  {#if loading}<span class="spinner"></span>{/if}
                  ✅ Send Edited
                </button>
                <button class="btn-ghost action-btn" disabled={loading} on:click={() => editing = false}>
                  Cancel edit
                </button>
              {/if}
              <button class="btn-ghost action-btn skip-btn" disabled={loading} on:click={skip}>
                ⏭️ Skip — Don't Send
              </button>
            </div>
          </div>

          <!-- Extracted questions accordion -->
          {#if $currentPdf?.questions?.length}
            <div class="card questions-card">
              <details open>
                <summary>
                  <span>🔍 Extracted questions</span>
                  <span class="q-count">{$currentPdf.questions.length}</span>
                </summary>
                <ul class="q-list">
                  {#each $currentPdf.questions as q}
                    <li class="q-item">
                      <div class="q-header">
                        <span class="q-cat" style={catStyle(q.category)}>{q.category?.replace('_', ' ')}</span>
                      </div>
                      <p class="q-text">{q.question_text}</p>
                      {#if q.underlying_fear}
                        <p class="q-fear">Fear: {q.underlying_fear}</p>
                      {/if}
                    </li>
                  {/each}
                </ul>
              </details>
            </div>
          {/if}
        </div>
      </div>
    {/if}
  </main>
</div>

<style>
  .layout { display: grid; grid-template-columns: 260px 1fr; min-height: 100vh; }
  .main { padding: 36px 48px; max-width: 1300px; }

  /* Success screen */
  .success-wrap {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    min-height: 70vh; text-align: center; max-width: 480px; margin: 0 auto;
  }
  .success-icon { font-size: 64px; margin-bottom: 20px; }
  .success-icon.skip { font-size: 52px; }
  .success-wrap h1 { font-size: 28px; margin-bottom: 10px; }

  /* Page header */
  .page-header { margin-bottom: 22px; }
  .page-header h1 { font-size: 26px; margin-bottom: 4px; }

  /* Split layout */
  .split { display: grid; grid-template-columns: 1.15fr 1fr; gap: 18px; align-items: start; }

  /* Preview card */
  .preview-card { padding: 20px; }
  .card-title { font-size: 14px; font-weight: 700; color: var(--text-primary); margin-bottom: 14px; }
  .preview-card iframe { width: 100%; height: 68vh; border-radius: 8px; border: 1px solid var(--border); background: var(--bg); }
  .open-link { display: inline-block; margin-top: 10px; font-size: 12px; color: var(--text-muted); }
  .open-link:hover { color: var(--blue-primary); }
  .no-pdf { padding: 40px; text-align: center; }

  /* Review panel */
  .review-col { display: flex; flex-direction: column; gap: 14px; }
  .review-card { padding: 20px; }

  .message-preview {
    background: var(--blue-light);
    padding: 14px;
    border-left: 3px solid var(--blue-primary);
    border-radius: 6px;
    font-size: 14px; line-height: 1.6;
    white-space: pre-wrap;
    color: var(--text-primary);
  }

  .actions { display: flex; flex-direction: column; gap: 8px; margin-top: 16px; }
  .action-btn { width: 100%; }
  .skip-btn { opacity: 0.7; }
  .skip-btn:hover { opacity: 1; }

  /* Questions card */
  .questions-card { padding: 0; overflow: hidden; }
  .questions-card details { padding: 0; }
  .questions-card summary {
    cursor: pointer;
    padding: 16px 20px;
    font-size: 13px; font-weight: 700;
    color: var(--text-secondary);
    display: flex; align-items: center; justify-content: space-between;
    user-select: none;
    list-style: none;
  }
  .questions-card summary::-webkit-details-marker { display: none; }
  .q-count {
    background: var(--blue-primary); color: white;
    font-size: 11px; font-weight: 700;
    padding: 2px 8px; border-radius: 999px;
  }
  .q-list { list-style: none; padding: 0 20px 16px; display: flex; flex-direction: column; gap: 10px; }
  .q-item {
    background: var(--bg);
    border-radius: 8px;
    padding: 12px 14px;
    font-size: 13px;
  }
  .q-header { margin-bottom: 6px; }
  .q-cat {
    display: inline-block;
    font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px;
    padding: 3px 8px; border-radius: 999px;
  }
  .q-text { color: var(--text-primary); font-weight: 600; line-height: 1.45; margin-bottom: 4px; }
  .q-fear { color: var(--text-muted); font-size: 12px; font-style: italic; }
</style>
