/**
 * FinGuard AI - Enterprise Frontend Logic
 * Handles State Management, UI Interactions, and API Integration
 */

const API_BASE_URL = 'http://127.0.0.1:5000/api';
let networkGraph = null;

// ==========================================
// 1. INITIALIZATION & EVENT LISTENERS
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initMobileMenu();
    initNetworkGraph();
    initFileUploads();
    initForms();
    
    // Simulate initial data load for the dashboard
    setTimeout(() => {
        updateDashboardMetrics({
            total: 12458,
            flagged: 342,
            alerts: 12,
            volume: 84500000
        });
        showToast('System connected to live transaction feed', 'success');
    }, 1500);
});

// ==========================================
// 2. NAVIGATION & LAYOUT (FIXED TAB LOGIC)
// ==========================================
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const tabContents = document.querySelectorAll('.tab-content');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetTab = link.getAttribute('data-tab');

            // 1. Remove active state from all links
            navLinks.forEach(l => {
                l.classList.remove('active');
                l.setAttribute('aria-selected', 'false');
            });
            
            // 2. Add active state to clicked link
            link.classList.add('active');
            link.setAttribute('aria-selected', 'true');

            // 3. Hide all tab contents completely
            tabContents.forEach(content => {
                content.classList.remove('active');
                content.style.display = 'none';
            });
            
            // 4. Show the targeted tab
            const activeContent = document.getElementById(`${targetTab}-tab`);
            if (activeContent) {
                activeContent.style.display = 'block';
                // Small delay to allow display:block to apply before adding opacity class
                setTimeout(() => {
                    activeContent.classList.add('active');
                }, 10);
            }

            // Close mobile menu if open
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) sidebar.classList.remove('mobile-open');
        });
    });
}

function initMobileMenu() {
    const toggleBtn = document.getElementById('mobile-menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('mobile-open');
            if(sidebar.classList.contains('mobile-open')) {
                sidebar.style.position = 'fixed';
                sidebar.style.left = '0';
                sidebar.style.height = '100vh';
                sidebar.style.boxShadow = '0 0 50px rgba(0,0,0,0.5)';
            } else {
                sidebar.style.left = '-260px';
            }
        });
    }
}

// ==========================================
// 3. NETWORK GRAPH SIMULATION (VIS.JS)
// ==========================================
function initNetworkGraph() {
    const simulateBtn = document.getElementById('simulate-mule-btn');
    if (simulateBtn) {
        simulateBtn.addEventListener('click', renderNetworkGraph);
    }
}

async function renderNetworkGraph() {
    const container = document.getElementById('network-graph');
    if (!container) return;
    
    showSystemLoading(true, "Scanning network for anomalous layering patterns...");
    
    // Simulate API Delay for dramatic effect
    await new Promise(resolve => setTimeout(resolve, 2000));
    showSystemLoading(false);
    
    try {
        const nodes = new vis.DataSet([
            {id: 1, label: "Origin: USR-992\n(Compromised)", group: "danger", color: "#ef4444", value: 30},
            {id: 2, label: "Mule Account A\n(Student)", group: "warning", color: "#f59e0b", value: 15},
            {id: 3, label: "Mule Account B\n(Dormant)", group: "warning", color: "#f59e0b", value: 15},
            {id: 4, label: "Mule Account C\n(New)", group: "warning", color: "#f59e0b", value: 15},
            {id: 5, label: "Offshore Dest.\n(Cayman Islands)", group: "critical", color: "#8b5cf6", value: 40}
        ]);

        const edges = new vis.DataSet([
            {from: 1, to: 2, label: "₹49,999", color: {color: "#ef4444"}},
            {from: 1, to: 3, label: "₹49,500", color: {color: "#ef4444"}},
            {from: 1, to: 4, label: "₹49,000", color: {color: "#ef4444"}},
            {from: 2, to: 5, label: "₹48,500", color: {color: "#f59e0b"}},
            {from: 3, to: 5, label: "₹48,000", color: {color: "#f59e0b"}},
            {from: 4, to: 5, label: "₹47,500", color: {color: "#f59e0b"}}
        ]);

        const options = {
            nodes: {
                shape: 'dot',
                font: { size: 14, color: '#f8fafc', face: 'Inter' },
                borderWidth: 2,
                shadow: true
            },
            edges: {
                width: 2,
                arrows: { to: { enabled: true, scaleFactor: 0.8 } },
                font: { align: 'top', color: '#94a3b8', strokeWidth: 0, size: 12 },
                smooth: { type: 'curvedCW', roundness: 0.2 }
            },
            physics: {
                solver: 'forceAtlas2Based',
                forceAtlas2Based: { gravitationalConstant: -100, centralGravity: 0.01, springLength: 200 },
                stabilization: { iterations: 150 }
            }
        };

        if (networkGraph) networkGraph.destroy();
        networkGraph = new vis.Network(container, {nodes, edges}, options);
        showToast('Structuring & layering pattern detected!', 'error');

    } catch (error) {
        console.error("Graph render failed", error);
        showToast('Engine failed to map network.', 'error');
    }
}

// ==========================================
// 4. KYC & FILE UPLOAD DRAG-AND-DROP UX
// ==========================================
function initFileUploads() {
    setupDropZone('file-upload-area', 'document-file', 'file-preview', 'preview-image', 'remove-file-btn');
    setupDropZone('selfie-upload-area', 'selfie-file', 'selfie-preview', 'selfie-preview-image', 'remove-selfie-btn');
}

function setupDropZone(zoneId, inputId, previewId, imgId, removeBtnId) {
    const zone = document.getElementById(zoneId);
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    const img = document.getElementById(imgId);
    const removeBtn = document.getElementById(removeBtnId);

    // Safety check: Don't run if the elements aren't on the page
    if (!zone || !input || !preview || !img || !removeBtn) return;

    const emptyState = zone.querySelector('.upload-state-empty');

    zone.addEventListener('click', (e) => {
        if (e.target !== removeBtn && !removeBtn.contains(e.target)) {
            input.click();
        }
    });

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        zone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) { e.preventDefault(); e.stopPropagation(); }

    ['dragenter', 'dragover'].forEach(eventName => {
        zone.addEventListener(eventName, () => zone.style.borderColor = 'var(--primary)', false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        zone.addEventListener(eventName, () => zone.style.borderColor = '#334155', false);
    });

    zone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length) {
            input.files = files;
            handleFiles(files[0]);
        }
    });

    input.addEventListener('change', function() {
        if (this.files && this.files[0]) handleFiles(this.files[0]);
    });

    function handleFiles(file) {
        if (!file.type.startsWith('image/')) {
            showToast('Please upload an image file.', 'error');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            img.src = e.target.result;
            if (emptyState) emptyState.style.display = 'none';
            preview.style.display = 'block';
            zone.style.padding = '1rem';
        };
        reader.readAsDataURL(file);
    }

    removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        input.value = '';
        img.src = '';
        preview.style.display = 'none';
        if (emptyState) emptyState.style.display = 'block';
        zone.style.padding = '2.5rem 1rem';
    });
}

// KYC Step Navigation
window.goToStep = function(stepNumber) {
    document.querySelectorAll('.verification-step').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.steps-indicator .step').forEach(el => el.classList.remove('active'));
    
    const targetStep = document.getElementById(`step-${stepNumber}`);
    if (targetStep) targetStep.style.display = 'block';
    
    for(let i = 1; i <= stepNumber; i++) {
        const stepDot = document.querySelector(`.steps-indicator .step[data-step="${i}"]`);
        if(stepDot) stepDot.classList.add('active');
    }
};

window.resetVerification = function() {
    const ocrForm = document.getElementById('ocr-form');
    const selfieForm = document.getElementById('selfie-form');
    if (ocrForm) ocrForm.reset();
    if (selfieForm) selfieForm.reset();
    
    const rmFileBtn = document.getElementById('remove-file-btn');
    const rmSelfieBtn = document.getElementById('remove-selfie-btn');
    if (rmFileBtn) rmFileBtn.click();
    if (rmSelfieBtn) rmSelfieBtn.click();
    
    goToStep(1);
};

// ==========================================
// 5. FORM SUBMISSIONS & API MOCKING
// ==========================================
function initForms() {
    const ocrForm = document.getElementById('ocr-form');
    if (ocrForm) {
        ocrForm.addEventListener('submit', (e) => {
            e.preventDefault();
            goToStep(2);
        });
    }

    const selfieForm = document.getElementById('selfie-form');
    if (selfieForm) {
        selfieForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            showSystemLoading(true, "Running Face Match and OCR Analysis...");
            
            await new Promise(r => setTimeout(r, 2500));
            showSystemLoading(false);
            
            const resultsDiv = document.getElementById('combined-results');
            if (resultsDiv) {
                resultsDiv.innerHTML = `
                    <div class="card" style="border-left: 4px solid var(--success); background: rgba(16, 185, 129, 0.05);">
                        <h3 class="text-success" style="margin-bottom: 10px;"><i class="fas fa-check-circle"></i> Identity Verified Successfully</h3>
                        <p class="text-muted">Document Match: 98.4% | Face Match: 92.1% (Age Adjusted)</p>
                    </div>
                `;
            }
            goToStep(3);
            showToast('KYC Verification Passed', 'success');
        });
    }

    const amlForm = document.getElementById('aml-form');
    if (amlForm) {
        amlForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const amountInput = document.getElementById('amount');
            const amount = amountInput ? amountInput.value : 0;
            const resultContainer = document.getElementById('aml-result');
            const resultContent = document.getElementById('aml-result-content');
            
            showSystemLoading(true, "Evaluating via Random Forest & Isolation Forest Ensembles...");
            await new Promise(r => setTimeout(r, 1800));
            showSystemLoading(false);

            if (resultContainer) resultContainer.style.display = 'block';
            
            if (resultContent) {
                if (amount >= 50000) {
                    resultContent.innerHTML = `
                        <div style="border-left: 4px solid var(--danger); padding-left: 15px;">
                            <h3 class="text-danger mb-2">CRITICAL RISK DETECTED (Score: 85/100)</h3>
                            <p><strong>Primary Driver:</strong> Amount exceeds standard deviation by 4.2x.</p>
                            <p class="text-muted mt-2">Isolation Forest flagged this as a 99th percentile anomaly.</p>
                        </div>
                    `;
                    showToast('High risk transaction blocked', 'error');
                } else {
                    resultContent.innerHTML = `
                        <div style="border-left: 4px solid var(--success); padding-left: 15px;">
                            <h3 class="text-success mb-2">LOW RISK (Score: 12/100)</h3>
                            <p>Transaction pattern matches historical baseline.</p>
                        </div>
                    `;
                    showToast('Transaction analyzed securely', 'success');
                }
            }
        });
    }
}

// ==========================================
// 6. UTILITIES: TOASTS & LOADERS
// ==========================================
function showSystemLoading(show, message = "Processing...") {
    const overlay = document.getElementById('loading-overlay');
    if (!overlay) return;
    
    const text = overlay.querySelector('.overlay-text');
    if (text) text.innerText = message;
    
    if (show) {
        overlay.style.display = 'flex';
        void overlay.offsetWidth;
        overlay.style.opacity = '1';
    } else {
        overlay.style.opacity = '0';
        setTimeout(() => overlay.style.display = 'none', 300);
    }
}

window.showToast = function(message, type = 'info') {
    const container = document.getElementById('toast');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast-message toast-${type}`;
    
    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'exclamation-circle';
    if (type === 'warning') icon = 'exclamation-triangle';

    toast.innerHTML = `<i class="fas fa-${icon}"></i> <span>${message}</span>`;
    
    toast.style.padding = '12px 20px';
    toast.style.marginBottom = '10px';
    toast.style.borderRadius = '8px';
    toast.style.display = 'flex';
    toast.style.alignItems = 'center';
    toast.style.gap = '10px';
    toast.style.fontWeight = '500';
    toast.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.5)';
    toast.style.animation = 'slideInRight 0.3s ease forwards';
    toast.style.color = '#fff';

    if(type === 'success') toast.style.backgroundColor = 'var(--success)';
    else if(type === 'error') toast.style.backgroundColor = 'var(--danger)';
    else if(type === 'warning') toast.style.backgroundColor = 'var(--warning)';
    else toast.style.backgroundColor = 'var(--bg-surface-hover)';

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeOutRight 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
};

// Helper to update dashboard UI elements
function updateDashboardMetrics(metrics) {
    const formatNumber = (num) => new Intl.NumberFormat('en-IN').format(num);
    
    const totalEl = document.getElementById('total-transactions');
    const flaggedEl = document.getElementById('flagged-transactions');
    const openEl = document.getElementById('open-alerts');
    const volumeEl = document.getElementById('total-volume');

    if (totalEl) totalEl.innerText = formatNumber(metrics.total);
    if (flaggedEl) flaggedEl.innerText = formatNumber(metrics.flagged);
    if (openEl) openEl.innerText = metrics.alerts;
    if (volumeEl) volumeEl.innerText = `₹${formatNumber(metrics.volume)}`;
}