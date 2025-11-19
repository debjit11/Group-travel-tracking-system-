// Handle form submission
document.getElementById('regForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const form = document.getElementById('regForm');
    const msgDiv = document.getElementById('msg');
    
    // Get form data
    const formData = new FormData(form);
    
    try {
        // Send POST request to Flask backend
        const response = await fetch('/api/register', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            msgDiv.textContent = result.message;
            msgDiv.style.color = 'green';
            form.reset();
        } else {
            msgDiv.textContent = result.message;
            msgDiv.style.color = 'red';
        }
    } catch (error) {
        msgDiv.textContent = 'Error: ' + error.message;
        msgDiv.style.color = 'red';
    }
});

// Load available groups (optional - you can fetch from backend)
function loadGroups() {
    const groups = [
        { id: 1, name: 'Group A' },
        { id: 2, name: 'Group B' },
        { id: 3, name: 'Group C' }
    ];
    
    const groupsList = document.getElementById('groups-list');
    groupsList.innerHTML = groups.map(group => 
        `<div class="group-card"><h3>${group.name}</h3><p>Group ID: ${group.id}</p></div>`
    ).join('');
}