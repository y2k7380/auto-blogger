let currentAgent = 'Claude';
let dashboardData = null;

async function loadData() {
    try {
        const response = await fetch('data.json');
        dashboardData = await response.json();
        render();
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

function render() {
    if (!dashboardData) return;

    document.getElementById('last-updated').textContent = `Last Updated: ${dashboardData.last_updated}`;
    
    renderActivities();
    renderPosts();
    renderTrends();
}

function showTab(agent) {
    currentAgent = agent;
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent === agent);
    });
    renderActivities();
}

function renderActivities() {
    const list = document.getElementById('activity-list');
    list.innerHTML = '';
    
    const activities = dashboardData.activities[currentAgent] || [];
    
    activities.forEach(act => {
        const div = document.createElement('div');
        div.className = 'activity-item';
        
        const date = new Date(act.timestamp);
        const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        div.innerHTML = `
            <div class="item-header">
                <span class="timestamp">${timeStr}</span>
            </div>
            <div class="action-text">${act.action}</div>
        `;
        list.appendChild(div);
    });
    
    if (activities.length === 0) {
        list.innerHTML = '<p style="color: var(--text-muted); padding: 1rem;">No recent activities found.</p>';
    }
}

function renderPosts() {
    const list = document.getElementById('posts-list');
    list.innerHTML = '';
    
    const posts = dashboardData.posts || [];
    
    posts.forEach(post => {
        const div = document.createElement('div');
        div.className = 'post-item';
        
        div.innerHTML = `
            <a href="${post.url}" target="_blank" class="post-title">${post.title}</a>
            <div class="item-header">
                <span class="timestamp">${new Date(post.published).toLocaleDateString()}</span>
                <span class="post-status">${post.status}</span>
            </div>
        `;
        list.appendChild(div);
    });
}

function renderTrends() {
    const container = document.getElementById('trends-container');
    container.innerHTML = '';
    
    const trends = dashboardData.trends || {};
    
    for (const [category, items] of Object.entries(trends)) {
        const catDiv = document.createElement('div');
        catDiv.className = 'trend-category';
        
        let itemsHtml = '';
        items.forEach(item => {
            itemsHtml += `
                <div class="trend-list-item">
                    <span class="trend-topic">${item.topic}</span>
                    <span class="trend-detail">${item.detail || ''}</span>
                </div>
            `;
        });
        
        catDiv.innerHTML = `
            <h3>${category}</h3>
            <div class="trend-list">
                ${itemsHtml}
            </div>
        `;
        container.appendChild(catDiv);
    }
}

function refreshData() {
    // In a real app, this would call the backend.
    // Here we'll just show a message or re-fetch.
    alert('Updating Command Center data...');
    loadData();
}

// Initial load
loadData();
