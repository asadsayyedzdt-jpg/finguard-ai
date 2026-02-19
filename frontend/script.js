// ============================================
// CONFIGURATION
// ============================================
const API_BASE_URL = 'http://127.0.0.1:5000/api';

// ============================================
// TAB NAVIGATION
// ============================================



// ============================================
// WEBSOCKET CONNECTION
// ============================================

let socket = null;

// Initialize WebSocket connection
function initializeWebSocket() {
    console.log('🔌 Connecting to WebSocket...');
    
    socket = io('http://127.0.0.1:5000');
    
    socket.on('connect', function() {
        console.log('✅ WebSocket connected');
        showToast('Connected to live updates', 'success');
    });
    
    socket.on('disconnect', function() {
        console.log('❌ WebSocket disconnected');
        showToast('Disconnected from live updates', 'error');
    });
    
    // Listen for new transactions
    socket.on('new_transaction', function(data) {
        console.log('📥 New transaction received:', data);
        handleNewTransaction(data.transaction);
    });
    
    // Listen for new alerts
    socket.on('new_alert', function(data) {
        console.log('🚨 New alert received:', data);
        handleNewAlert(data.alert);
        showToast(`New ${data.alert.severity} alert!`, 'warning');
    });
    
    // Listen for stats updates
    socket.on('stats_update', function(data) {
        console.log('📊 Stats updated:', data);
        updateDashboardStats(data.stats);
    });
}

// Handle new transaction (real-time update)
function handleNewTransaction(transaction) {
    // Add to transactions table if on dashboard
    if (document.getElementById('dashboard-tab').classList.contains('active')) {
        prependTransactionToTable(transaction);
    }
    
    // Show notification if flagged
    if (transaction.flagged) {
        showNotification('Suspicious Transaction Detected!', 
            `₹${formatNumber(transaction.amount)} flagged with risk score ${transaction.risk_score}`);
    }
}

// Handle new alert (real-time update)
function handleNewAlert(alert) {
    // Add to alerts list if on dashboard
    if (document.getElementById('dashboard-tab').classList.contains('active')) {
        prependAlertToList(alert);
    }
    
    // Play sound or show browser notification
    playAlertSound();
}

// Prepend transaction to table (add at top)
function prependTransactionToTable(transaction) {
    const tbody = document.querySelector('#recent-transactions table tbody');
    if (tbody) {
        const row = document.createElement('tr');
        row.className = 'new-item-highlight';  // Add highlight animation
        row.innerHTML = `
            <td>${transaction.id}</td>
            <td>₹${formatNumber(transaction.amount)}</td>
            <td>
                <span class="risk-badge risk-${transaction.risk_level.toLowerCase()}">
                    ${transaction.risk_score}/100
                </span>
            </td>
            <td>
                ${transaction.flagged ? 
                    '<i class="fas fa-flag" style="color: var(--danger);"></i> Flagged' : 
                    '<i class="fas fa-check" style="color: var(--secondary);"></i> Clear'}
            </td>
        `;
        
        tbody.insertBefore(row, tbody.firstChild);
        
        // Remove highlight after animation
        setTimeout(() => {
            row.classList.remove('new-item-highlight');
        }, 2000);
        
        // Remove last row if more than 5
        if (tbody.children.length > 5) {
            tbody.removeChild(tbody.lastChild);
        }
    }
}

// Prepend alert to list
function prependAlertToList(alert) {
    const container = document.getElementById('recent-alerts');
    if (container) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert-item ${alert.severity.toLowerCase()} new-item-highlight`;
        alertDiv.innerHTML = `
            <div class="alert-header">
                <span class="alert-title">
                    <i class="fas fa-exclamation-triangle"></i>
                    Transaction ${alert.transaction_id}
                </span>
                <span class="risk-badge risk-${alert.severity.toLowerCase()}">
                    ${alert.severity}
                </span>
            </div>
            <p style="font-size: 0.875rem; color: #6b7280; margin-top: 0.5rem;">
                ${alert.description}
            </p>
        `;
        
        container.insertBefore(alertDiv, container.firstChild);
        
        // Remove highlight after animation
        setTimeout(() => {
            alertDiv.classList.remove('new-item-highlight');
        }, 2000);
        
        // Remove last alert if more than 5
        if (container.children.length > 5) {
            container.removeChild(container.lastChild);
        }
    }
}

// Show browser notification
function showNotification(title, message) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, {
            body: message,
            icon: '/favicon.ico',
            badge: '/favicon.ico'
        });
    }
}

// Play alert sound
function playAlertSound() {
    // Create a simple beep sound
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 800;
    oscillator.type = 'sine';
    
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
}

// Request notification permission
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // ... existing code ...
    
    // Initialize WebSocket
    initializeWebSocket();
    
    // Request notification permission
    requestNotificationPermission();
});



document.addEventListener('DOMContentLoaded', function() {
    // Tab switching
    const navLinks = document.querySelectorAll('.nav-link');
    const tabContents = document.querySelectorAll('.tab-content');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all
            navLinks.forEach(l => l.classList.remove('active'));
            tabContents.forEach(t => t.classList.remove('active'));
            
            // Add active class to clicked
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab') + '-tab';
            document.getElementById(tabId).classList.add('active');
            
            // Load data if dashboard
            if (tabId === 'dashboard-tab') {
                loadDashboard();
            }
        });
    });
    
    // Load dashboard on page load
    loadDashboard();
    
    // Setup form handlers
    setupKYCForm();
    setupAMLForm();
});

// ============================================
// DASHBOARD FUNCTIONS
// ============================================
async function loadDashboard() {
    try {
        // Load statistics
        const statsResponse = await fetch(`${API_BASE_URL}/dashboard/stats`);
        const statsData = await statsResponse.json();
        
        if (statsData.success) {
            updateDashboardStats(statsData.data);
        }
        
        // Load recent transactions
        const txnResponse = await fetch(`${API_BASE_URL}/transactions/recent?limit=5`);
        const txnData = await txnResponse.json();
        
        if (txnData.success) {
            displayRecentTransactions(txnData.data);
        }
        
        // Load recent alerts
        const alertResponse = await fetch(`${API_BASE_URL}/alerts/recent?limit=5`);
        const alertData = await alertResponse.json();
        
        if (alertData.success) {
            displayRecentAlerts(alertData.data);
        }
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showToast('Error loading dashboard data', 'error');
    }
}

function updateDashboardStats(stats) {
    document.getElementById('total-transactions').textContent = stats.total_transactions;
    document.getElementById('flagged-transactions').textContent = stats.flagged_transactions;
    document.getElementById('open-alerts').textContent = stats.open_alerts;
    document.getElementById('total-volume').textContent = `₹${formatNumber(stats.total_volume)}`;
}

function displayRecentTransactions(transactions) {
    const container = document.getElementById('recent-transactions');
    
    if (transactions.length === 0) {
        container.innerHTML = '<p class="loading">No transactions yet</p>';
        return;
    }
    
    const table = `
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Amount</th>
                    <th>Risk</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                ${transactions.map(txn => `
                    <tr>
                        <td>${txn.id}</td>
                        <td>₹${formatNumber(txn.amount)}</td>
                        <td>
                            <span class="risk-badge risk-${txn.risk_level.toLowerCase()}">
                                ${txn.risk_score}/100
                            </span>
                        </td>
                        <td>
                            ${txn.is_flagged ? 
                                '<i class="fas fa-flag" style="color: var(--danger);"></i> Flagged' : 
                                '<i class="fas fa-check" style="color: var(--secondary);"></i> Clear'}
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    container.innerHTML = table;
}

function displayRecentAlerts(alerts) {
    const container = document.getElementById('recent-alerts');
    
    if (alerts.length === 0) {
        container.innerHTML = '<p class="loading">No alerts</p>';
        return;
    }
    
    const alertsHTML = alerts.map(alert => `
        <div class="alert-item ${alert.severity.toLowerCase()}">
            <div class="alert-header">
                <span class="alert-title">
                    <i class="fas fa-exclamation-triangle"></i>
                    Transaction ${alert.transaction_id}
                </span>
                <span class="risk-badge risk-${alert.severity.toLowerCase()}">
                    ${alert.severity}
                </span>
            </div>
            <p style="font-size: 0.875rem; color: #6b7280; margin-top: 0.5rem;">
                ${alert.flags && alert.flags.length > 0 ? alert.flags[0].message : 'Flagged for review'}
            </p>
        </div>
    `).join('');
    
    container.innerHTML = alertsHTML;
}

// ============================================
// KYC FORM
// ============================================
function setupKYCForm() {
    const form = document.getElementById('kyc-form');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            full_name: document.getElementById('full-name').value,
            document_type: document.getElementById('doc-type').value,
            document_number: document.getElementById('doc-number').value
        };
        
        showLoading(true);
        
        try {
            const response = await fetch(`${API_BASE_URL}/kyc/verify`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            showLoading(false);
            
            if (data.success) {
                displayKYCResult(data.data);
                showToast('Document verified successfully!', 'success');
            } else {
                showToast('Verification failed: ' + data.error, 'error');
            }
            
        } catch (error) {
            showLoading(false);
            console.error('Error:', error);
            showToast('Error verifying document', 'error');
        }
    });
}

function displayKYCResult(result) {
    const container = document.getElementById('kyc-result');
    const content = document.getElementById('kyc-result-content');
    
    const statusIcon = result.valid ? 
        '<i class="fas fa-check-circle" style="color: var(--secondary);"></i>' :
        '<i class="fas fa-times-circle" style="color: var(--danger);"></i>';
    
    content.innerHTML = `
        <div class="result-item">
            <span class="result-label">Status</span>
            <span class="result-value">
                ${statusIcon} ${result.valid ? 'Valid' : 'Invalid'}
            </span>
        </div>
        <div class="result-item">
            <span class="result-label">Document Type</span>
            <span class="result-value">${result.document_type}</span>
        </div>
        <div class="result-item">
            <span class="result-label">Name</span>
            <span class="result-value">${result.full_name}</span>
        </div>
        <div class="result-item">
            <span class="result-label">Message</span>
            <span class="result-value">${result.message}</span>
        </div>
        ${result.confidence ? `
            <div class="result-item">
                <span class="result-label">Confidence</span>
                <span class="result-value">${result.confidence}%</span>
            </div>
        ` : ''}
    `;
    
    container.style.display = 'block';
}

// ============================================
// AML FORM
// ============================================
function setupAMLForm() {
    const form = document.getElementById('aml-form');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            user_id: document.getElementById('user-id').value,
            amount: parseFloat(document.getElementById('amount').value),
            recipient: document.getElementById('recipient').value,
            description: document.getElementById('description').value
        };
        
        showLoading(true);
        
        try {
            const response = await fetch(`${API_BASE_URL}/aml/check`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            showLoading(false);
            
            if (data.success) {
                displayAMLResult(data.data);
                showToast('Transaction analyzed successfully!', 'success');
                
                // Reload dashboard if on dashboard tab
                if (document.getElementById('dashboard-tab').classList.contains('active')) {
                    loadDashboard();
                }
            } else {
                showToast('Analysis failed: ' + data.error, 'error');
            }
            
        } catch (error) {
            showLoading(false);
            console.error('Error:', error);
            showToast('Error analyzing transaction', 'error');
        }
    });
}

function displayAMLResult(data) {
    const container = document.getElementById('aml-result');
    const content = document.getElementById('aml-result-content');
    
    const ruleAnalysis = data.rule_analysis;
    const mlAnalysis = data.ml_analysis;
    const transaction = data.transaction;
    
    // Flags HTML
    let flagsHTML = '';
    if (ruleAnalysis.flags && ruleAnalysis.flags.length > 0) {
        flagsHTML = `
            <div class="result-item" style="flex-direction: column; align-items: flex-start;">
                <span class="result-label">🚩 Rule-Based Flags:</span>
                <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                    ${ruleAnalysis.flags.map(flag => `
                        <li style="margin-bottom: 0.5rem;">
                            <strong>${flag.rule}</strong> (${flag.severity}): ${flag.message}
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }
    
    // ML Analysis HTML
    let mlHTML = '';
    if (mlAnalysis.ml_available) {
        const mlColor = mlAnalysis.ml_fraud_probability > 0.7 ? 'var(--danger)' : 
                       mlAnalysis.ml_fraud_probability > 0.5 ? 'var(--warning)' : 
                       'var(--secondary)';
        
        mlHTML = `
            <div style="background: var(--light); padding: 1rem; border-radius: var(--radius-md); margin-top: 1rem;">
                <h4 style="margin-bottom: 1rem; color: var(--primary);">
                    🤖 Machine Learning Analysis
                </h4>
                <div class="result-item">
                    <span class="result-label">Fraud Probability</span>
                    <span class="result-value" style="color: ${mlColor}; font-weight: bold;">
                        ${(mlAnalysis.ml_fraud_probability * 100).toFixed(1)}%
                    </span>
                </div>
                <div class="result-item">
                    <span class="result-label">ML Prediction</span>
                    <span class="result-value">
                        ${mlAnalysis.ml_prediction === 'fraud' ? '⚠️ Fraud' : '✅ Legitimate'}
                    </span>
                </div>
                <div class="result-item">
                    <span class="result-label">Confidence</span>
                    <span class="result-value">${mlAnalysis.ml_confidence.toFixed(1)}%</span>
                </div>
            </div>
        `;
        
        // ML Explanation
        if (data.ml_explanation && data.ml_explanation.length > 0) {
            mlHTML += `
                <div style="margin-top: 1rem;">
                    <h5 style="margin-bottom: 0.5rem;">Top Contributing Factors:</h5>
                    <ul style="padding-left: 1.5rem; font-size: 0.9rem;">
                        ${data.ml_explanation.map(exp => `
                            <li>${exp.feature}: ${exp.value} (importance: ${(exp.importance * 100).toFixed(1)}%)</li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }
    }
    
    content.innerHTML = `
        <div class="result-item">
            <span class="result-label">Transaction ID</span>
            <span class="result-value">${transaction.id}</span>
        </div>
        <div class="result-item">
            <span class="result-label">Amount</span>
            <span class="result-value">₹${formatNumber(transaction.amount)}</span>
        </div>
        <div class="result-item">
            <span class="result-label">Combined Risk Score</span>
            <span class="result-value">
                <span class="risk-badge risk-${ruleAnalysis.risk_level.toLowerCase()}">
                    ${data.combined_risk_score}/100
                </span>
            </span>
        </div>
        <div class="result-item">
            <span class="result-label">Rule-Based Score</span>
            <span class="result-value">${transaction.rule_risk_score}/100</span>
        </div>
        <div class="result-item">
            <span class="result-label">Final Decision</span>
            <span class="result-value">
                ${data.decision === 'FLAGGED' ? 
                    '<i class="fas fa-flag" style="color: var(--danger);"></i> Flagged for Review' : 
                    '<i class="fas fa-check" style="color: var(--secondary);"></i> Approved'}
            </span>
        </div>
        ${flagsHTML}
        ${mlHTML}
    `;
    
    container.style.display = 'block';
}

// ============================================
// UTILITY FUNCTIONS
// ============================================
function formatNumber(num) {
    return new Intl.NumberFormat('en-IN').format(num);
}

function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    overlay.style.display = show ? 'flex' : 'none';
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}


// ============================================
// METHOD SWITCHING (OCR vs Manual)
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    // ... existing code ...
    
    setupMethodSwitching();
    setupOCRForm();
});

function setupMethodSwitching() {
    const methodButtons = document.querySelectorAll('.method-btn');
    const ocrMethod = document.getElementById('ocr-method');
    const manualMethod = document.getElementById('manual-method');
    
    methodButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all
            methodButtons.forEach(b => b.classList.remove('active'));
            
            // Add active to clicked
            this.classList.add('active');
            
            // Show/hide methods
            const method = this.getAttribute('data-method');
            if (method === 'ocr') {
                ocrMethod.style.display = 'block';
                manualMethod.style.display = 'none';
            } else {
                ocrMethod.style.display = 'none';
                manualMethod.style.display = 'block';
            }
        });
    });
}

// ============================================
// FILE UPLOAD HANDLING
// ============================================
function setupOCRForm() {
    const fileInput = document.getElementById('document-file');
    const uploadArea = document.getElementById('file-upload-area');
    const placeholder = uploadArea.querySelector('.upload-placeholder');
    const preview = document.getElementById('file-preview');
    const previewImage = document.getElementById('preview-image');
    const removeBtn = document.getElementById('remove-file-btn');
    const ocrForm = document.getElementById('ocr-form');
    
    // Click to upload
    uploadArea.addEventListener('click', function(e) {
        if (e.target !== removeBtn && !removeBtn.contains(e.target)) {
            fileInput.click();
        }
    });
    
    // File selected
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            displayFilePreview(file);
        }
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            fileInput.files = e.dataTransfer.files;
            displayFilePreview(file);
        } else {
            showToast('Please upload an image file', 'error');
        }
    });
    
    // Remove file
    removeBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        fileInput.value = '';
        placeholder.style.display = 'block';
        preview.style.display = 'none';
    });
    
    // Form submission
    ocrForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        await processOCR();
    });
}

function displayFilePreview(file) {
    const placeholder = document.querySelector('.upload-placeholder');
    const preview = document.getElementById('file-preview');
    const previewImage = document.getElementById('preview-image');
    
    // Read file and display
    const reader = new FileReader();
    reader.onload = function(e) {
        previewImage.src = e.target.result;
        placeholder.style.display = 'none';
        preview.style.display = 'block';
    };
    reader.readAsDataURL(file);
}

// ============================================
// OCR PROCESSING
// ============================================
async function processOCR() {
    const fileInput = document.getElementById('document-file');
    const docType = document.getElementById('doc-type-ocr').value;
    
    if (!fileInput.files || !fileInput.files[0]) {
        showToast('Please select a file', 'error');
        return;
    }
    
    const file = fileInput.files[0];
    
    // Create FormData
    const formData = new FormData();
    formData.append('document', file);
    formData.append('document_type', docType);
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/kyc/ocr`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        showLoading(false);
        
        if (data.success) {
            displayOCRResult(data.data);
            showToast('Document processed successfully!', 'success');
        } else {
            showToast('OCR failed: ' + data.error, 'error');
        }
        
    } catch (error) {
        showLoading(false);
        console.error('Error:', error);
        showToast('Error processing document', 'error');
    }
}

function displayOCRResult(result) {
    const container = document.getElementById('kyc-result');
    const content = document.getElementById('kyc-result-content');
    
    const details = result.extracted_details;
    const validation = result.validation;
    
    // Status icon
    const statusIcon = validation.is_valid ? 
        '<i class="fas fa-check-circle" style="color: var(--secondary); font-size: 3rem;"></i>' :
        '<i class="fas fa-times-circle" style="color: var(--danger); font-size: 3rem;"></i>';
    
    // Confidence color
    const confidence = result.ocr_confidence;
    const confColor = confidence >= 80 ? 'high' : confidence >= 60 ? 'medium' : 'low';
    
    // Build extracted fields HTML
    let fieldsHTML = '';
    for (const [key, value] of Object.entries(details)) {
        if (value && key !== 'document_type') {
            const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            fieldsHTML += `
                <div class="extracted-field">
                    <span class="field-label">${label}:</span>
                    <span class="field-value">${value}</span>
                </div>
            `;
        }
    }
    
    // Issues HTML
    let issuesHTML = '';
    if (validation.issues && validation.issues.length > 0) {
        issuesHTML = `
            <div style="background: #fef2f2; padding: 1rem; border-radius: var(--radius-md); margin-top: 1rem;">
                <h4 style="color: var(--danger); margin-bottom: 0.5rem;">
                    <i class="fas fa-exclamation-triangle"></i> Issues Found:
                </h4>
                <ul style="margin-left: 1.5rem; color: var(--danger);">
                    ${validation.issues.map(issue => `<li>${issue}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    content.innerHTML = `
        <div style="text-align: center; margin-bottom: 1.5rem;">
            ${statusIcon}
            <h3 style="margin-top: 0.5rem; color: ${validation.is_valid ? 'var(--secondary)' : 'var(--danger)'};">
                ${validation.is_valid ? 'Document Verified' : 'Verification Failed'}
            </h3>
        </div>
        
        <div class="result-item">
            <span class="result-label">Document Type</span>
            <span class="result-value">${result.document_type.toUpperCase()}</span>
        </div>
        
        <div class="result-item">
            <span class="result-label">OCR Confidence</span>
            <span class="result-value">
                ${confidence.toFixed(1)}%
                <div class="confidence-bar">
                    <div class="confidence-fill ${confColor}" style="width: ${confidence}%"></div>
                </div>
            </span>
        </div>
        
        <div class="result-item">
            <span class="result-label">Confidence Level</span>
            <span class="result-value">
                <span class="risk-badge risk-${validation.confidence_level}">
                    ${validation.confidence_level.toUpperCase()}
                </span>
            </span>
        </div>
        
        <div class="ocr-details">
            <h4><i class="fas fa-list"></i> Extracted Information</h4>
            ${fieldsHTML}
        </div>
        
        ${issuesHTML}
        
        <div style="margin-top: 1rem; padding: 1rem; background: var(--light); border-radius: var(--radius-md); font-size: 0.875rem; color: #6b7280;">
            <strong>Raw Text:</strong>
            <pre style="margin-top: 0.5rem; white-space: pre-wrap; font-family: monospace;">${result.raw_text}</pre>
        </div>
    `;
    
    container.style.display = 'block';
    
    // Scroll to result
    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}




// ============================================
// GLOBAL VARIABLES FOR MULTI-STEP VERIFICATION
// ============================================
let ocrResult = null;
let documentImageFile = null;

// ============================================
// STEP NAVIGATION
// ============================================
function goToStep(stepNumber) {
    // Hide all steps
    document.querySelectorAll('.verification-step').forEach(step => {
        step.style.display = 'none';
    });
    
    // Show target step
    document.getElementById(`step-${stepNumber}`).style.display = 'block';
    
    // Update step indicator
    document.querySelectorAll('.step').forEach((step, index) => {
        step.classList.remove('active', 'completed');
        if (index + 1 < stepNumber) {
            step.classList.add('completed');
        } else if (index + 1 === stepNumber) {
            step.classList.add('active');
        }
    });
}

function resetVerification() {
    ocrResult = null;
    documentImageFile = null;
    
    // Reset forms
    document.getElementById('ocr-form').reset();
    document.getElementById('selfie-form').reset();
    
    // Reset file previews
    document.querySelector('.upload-placeholder').style.display = 'block';
    document.getElementById('file-preview').style.display = 'none';
    document.querySelector('#selfie-upload-area .upload-placeholder').style.display = 'block';
    document.getElementById('selfie-preview').style.display = 'none';
    
    // Go to step 1
    goToStep(1);
}

// ============================================
// ENHANCED OCR FORM (Step 1)
// ============================================
function setupOCRForm() {
    const fileInput = document.getElementById('document-file');
    const uploadArea = document.getElementById('file-upload-area');
    const placeholder = uploadArea.querySelector('.upload-placeholder');
    const preview = document.getElementById('file-preview');
    const previewImage = document.getElementById('preview-image');
    const removeBtn = document.getElementById('remove-file-btn');
    const ocrForm = document.getElementById('ocr-form');
    
    // Click to upload
    uploadArea.addEventListener('click', function(e) {
        if (e.target !== removeBtn && !removeBtn.contains(e.target)) {
            fileInput.click();
        }
    });
    
    // File selected
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            documentImageFile = file;
            displayFilePreview(file);
        }
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            fileInput.files = e.dataTransfer.files;
            documentImageFile = file;
            displayFilePreview(file);
        } else {
            showToast('Please upload an image file', 'error');
        }
    });
    
    // Remove file
    removeBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        fileInput.value = '';
        documentImageFile = null;
        placeholder.style.display = 'block';
        preview.style.display = 'none';
    });
    
    // Form submission - Process OCR and move to step 2
    ocrForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        await processOCRAndContinue();
    });
    
    // Setup selfie form
    setupSelfieForm();
}

async function processOCRAndContinue() {
    const fileInput = document.getElementById('document-file');
    const docType = document.getElementById('doc-type-ocr').value;
    
    if (!fileInput.files || !fileInput.files[0]) {
        showToast('Please select a file', 'error');
        return;
    }
    
    const file = fileInput.files[0];
    
    // Create FormData
    const formData = new FormData();
    formData.append('document', file);
    formData.append('document_type', docType);
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/kyc/ocr`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        showLoading(false);
        
        if (data.success) {
            ocrResult = data.data;
            showToast('Document processed! Now upload selfie', 'success');
            goToStep(2);
        } else {
            showToast('OCR failed: ' + data.error, 'error');
        }
        
    } catch (error) {
        showLoading(false);
        console.error('Error:', error);
        showToast('Error processing document', 'error');
    }
}

// ============================================
// SELFIE FORM (Step 2)
// ============================================
function setupSelfieForm() {
    const selfieInput = document.getElementById('selfie-file');
    const uploadArea = document.getElementById('selfie-upload-area');
    const placeholder = uploadArea.querySelector('.upload-placeholder');
    const preview = document.getElementById('selfie-preview');
    const previewImage = document.getElementById('selfie-preview-image');
    const removeBtn = document.getElementById('remove-selfie-btn');
    const selfieForm = document.getElementById('selfie-form');
    
    // Click to upload
    uploadArea.addEventListener('click', function(e) {
        if (e.target !== removeBtn && !removeBtn.contains(e.target)) {
            selfieInput.click();
        }
    });
    
    // File selected
    selfieInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                placeholder.style.display = 'none';
                preview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
    });
    
    // Remove file
    removeBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        selfieInput.value = '';
        placeholder.style.display = 'block';
        preview.style.display = 'none';
    });
    
    // Form submission - Process face comparison
    selfieForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        await processFaceComparison();
    });
}

// ============================================
// FACE COMPARISON
// ============================================
async function processFaceComparison() {
    const selfieInput = document.getElementById('selfie-file');
    
    if (!documentImageFile) {
        showToast('Document image not found. Please start over.', 'error');
        goToStep(1);
        return;
    }
    
    if (!selfieInput.files || !selfieInput.files[0]) {
        showToast('Please select a selfie', 'error');
        return;
    }
    
    const selfieFile = selfieInput.files[0];
    
    // Create FormData with both images
    const formData = new FormData();
    formData.append('document_image', documentImageFile);
    formData.append('selfie_image', selfieFile);
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/kyc/face-compare`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        showLoading(false);
        
        if (data.success) {
            displayCombinedResults(ocrResult, data.data);
            showToast('Verification complete!', 'success');
            goToStep(3);
        } else {
            showToast('Face comparison failed: ' + data.error, 'error');
        }
        
    } catch (error) {
        showLoading(false);
        console.error('Error:', error);
        showToast('Error comparing faces', 'error');
    }
}

// ============================================
// DISPLAY COMBINED RESULTS
// ============================================
function displayCombinedResults(ocrData, faceData) {
    const container = document.getElementById('combined-results');
    
    const comparison = faceData.comparison;
    const verification = faceData.verification;
    const ageAnalysis = faceData.age_analysis;
    const features = faceData.feature_comparison;
    
    // Determine similarity level
    const similarity = comparison.similarity_percentage;
    const similarityLevel = similarity >= 80 ? 'high' : similarity >= 60 ? 'medium' : 'low';
    
    // Age warning HTML
    let ageWarningHTML = '';
    if (ageAnalysis.significant_gap) {
        ageWarningHTML = `
            <div class="age-warning">
                <h4><i class="fas fa-exclamation-triangle"></i> Age Difference Detected</h4>
                <p>Estimated age gap of ~${ageAnalysis.age_gap} years between document and selfie.</p>
                <p>Verification threshold has been adjusted accordingly.</p>
            </div>
        `;
    }
    
    // Feature comparison HTML
    const featuresHTML = Object.entries(features).map(([key, value]) => {
        const name = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        const icon = value.match ? 
            '<i class="fas fa-check-circle match-icon yes"></i>' :
            '<i class="fas fa-times-circle match-icon no"></i>';
        
        return `
            <div class="feature-item">
                <span class="feature-name">${name}</span>
                <div class="feature-match">
                    <span>${value.similarity}%</span>
                    ${icon}
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = `
        <!-- Overall Verdict -->
        <div style="text-align: center; padding: 2rem; background: ${comparison.is_match ? '#d1fae5' : '#fef2f2'}; border-radius: var(--radius-md); margin-bottom: 2rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">
                ${comparison.is_match ? '✅' : '❌'}
            </div>
            <h2 style="color: ${comparison.is_match ? '#065f46' : '#991b1b'}; margin-bottom: 0.5rem;">
                ${verification.verdict}
            </h2>
            <p style="color: #6b7280; font-size: 1.1rem;">
                ${verification.message}
            </p>
        </div>
        
        <!-- Similarity Meter -->
        <div class="similarity-meter">
            <h3 style="margin-bottom: 1rem;">Face Similarity Score</h3>
            <div class="similarity-circle ${similarityLevel}">
                ${similarity.toFixed(1)}%
            </div>
            <p style="color: #6b7280;">Confidence: ${comparison.confidence}%</p>
        </div>
        
        ${ageWarningHTML}
        
        <!-- OCR Results Summary -->
        <div class="card" style="margin: 2rem 0;">
            <h3><i class="fas fa-id-card"></i> Document Information</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
                ${Object.entries(ocrData.extracted_details).map(([key, value]) => {
                    if (value && key !== 'document_type') {
                        const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        return `
                            <div class="result-item">
                                <span class="result-label">${label}</span>
                                <span class="result-value">${value}</span>
                            </div>
                        `;
                    }
                    return '';
                }).join('')}
            </div>
        </div>
        
        <!-- Feature Comparison -->
        <div class="card">
            <h3><i class="fas fa-search"></i> Detailed Feature Analysis</h3>
            <div class="feature-comparison-list">
                ${featuresHTML}
            </div>
        </div>
        
        <!-- Recommendation -->
        <div class="card" style="background: var(--light); border-left: 4px solid var(--primary);">
            <h3><i class="fas fa-lightbulb"></i> Recommendation</h3>
            <p style="color: var(--dark); font-size: 1.1rem; margin: 1rem 0;">
                ${verification.recommendation}
            </p>
        </div>
    `;
}

async function generateReport() {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/reports/generate`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        showLoading(false);
        
        if (data.success) {
            showToast('Report generated successfully!', 'success');
            // In a real app, you'd download the file here
            alert(`Report generated: ${data.data.filename}\nSaved to backend/reports/ folder`);
        } else {
            showToast('Failed to generate report: ' + data.error, 'error');
        }
        
    } catch (error) {
        showLoading(false);
        showToast('Error generating report', 'error');
    }
}