let ws;
const messagesDiv = document.getElementById('chat-messages');
const inputField = document.getElementById('chat-input');
let currentResponseDiv = null;

function connectWS() {
    ws = new WebSocket(`ws://${window.location.host}/ws/chat`);
    
    ws.onopen = () => {
        document.getElementById('ws-status').textContent = 'Connected';
        document.getElementById('ws-status').style.color = 'var(--success)';
    };
    
    ws.onclose = () => {
        document.getElementById('ws-status').textContent = 'Disconnected (Reconnecting...)';
        document.getElementById('ws-status').style.color = 'var(--error)';
        setTimeout(connectWS, 3000);
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleEvent(data);
    };
}

function handleEvent(event) {
    if (event.type === 'response_chunk') {
        if (!currentResponseDiv) {
            currentResponseDiv = document.createElement('div');
            currentResponseDiv.className = 'message assistant markdown-body';
            messagesDiv.appendChild(currentResponseDiv);
        }
        currentResponseDiv.innerHTML = marked.parse(currentResponseDiv.dataset.raw = (currentResponseDiv.dataset.raw || '') + event.data.content);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    } else if (event.type === 'tool_call') {
        currentResponseDiv = null; // Next text goes to new bubble
        const div = document.createElement('div');
        div.className = 'message tool';
        div.innerHTML = `<strong>🛠️ Tool: ${event.data.tool_call.function.name}</strong><br><code>${event.data.tool_call.function.arguments}</code>`;
        div.id = `tool-${event.data.tool_call.id}`;
        messagesDiv.appendChild(div);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    } else if (event.type === 'tool_result') {
        const div = document.getElementById(`tool-${event.data.tool_call_id}`);
        if (div) {
            div.innerHTML += `<hr><pre>${event.data.result}</pre>`;
        }
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        updateContext();
        loadMemories();
    } else if (event.type === 'done' || event.type === 'error') {
        currentResponseDiv = null;
        updateContext();
    }
}

function sendMessage() {
    const text = inputField.value.trim();
    if (!text) return;
    
    const div = document.createElement('div');
    div.className = 'message user';
    div.textContent = text;
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    ws.send(JSON.stringify({ message: text }));
    inputField.value = '';
    
    setTimeout(updateContext, 500);
}

inputField.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

async function loadMemories(query = '') {
    const url = query ? `/api/memory/search?q=${encodeURIComponent(query)}` : '/api/memory';
    const res = await fetch(url);
    const memories = await res.json();
    const list = document.getElementById('memory-list');
    list.innerHTML = memories.map(m => `
        <div class="memory-card">
            <strong>[${m.category}]</strong> ${m.content}
        </div>
    `).join('');
}

let searchTimeout;
function searchMemories() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        loadMemories(document.getElementById('memory-search').value);
    }, 300);
}

function addMemory() {
    const text = prompt('Enter memory content:');
    if (text) {
        fetch('/api/memory', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({content: text, category: 'manual'})
        }).then(() => loadMemories());
    }
}

async function updateContext() {
    const res = await fetch('/api/context');
    const data = await res.json();
    
    const bar = document.getElementById('token-bar-fill');
    bar.style.width = `${data.usage_percent}%`;
    bar.style.background = data.usage_percent > 90 ? 'var(--error)' : 'linear-gradient(90deg, var(--success), var(--accent))';
    
    document.getElementById('token-stats').textContent = `${data.total_tokens} / ${data.max_tokens} (${data.usage_percent}%)`;
    
    document.getElementById('context-breakdown').innerHTML = data.per_message_tokens.map(m => `
        <div class="context-item">
            <span>${m.role}: ${m.preview}</span>
            <span>${m.tokens}</span>
        </div>
    `).join('');
}

async function clearConversation() {
    await fetch('/api/conversations/clear', { method: 'POST' });
    messagesDiv.innerHTML = '';
    updateContext();
}

async function fetchTools() {
    const res = await fetch('/api/tools');
    const tools = await res.json();
    document.getElementById('tool-count').textContent = tools.length;
}

// Init
connectWS();
loadMemories();
updateContext();
fetchTools();
