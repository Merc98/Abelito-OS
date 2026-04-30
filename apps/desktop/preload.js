const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('abelAPI', {
  invokeSkill: (skill, action, params) => {
    // Ideally this talks to the local CEO API via fetch or IPC
    // For simplicity, we'll assume the CEO API is running at localhost:8000
    return fetch(`http://localhost:8000/skills/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ skill, action, params })
    }).then(res => res.json());
  },
  getSystemStatus: () => {
    return fetch(`http://localhost:8000/health`).then(res => res.json());
  }
});
