// Global app functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert && alert.parentNode) {
                const bsAlert = new bootstrap.Alert(alert);
                if (bsAlert) {
                    bsAlert.close();
                }
            }
        }, 5000);
    });

    // Currency formatting for input fields
    const currencyInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
    currencyInputs.forEach(input => {
        input.addEventListener('input', function() {
            if (this.value && !isNaN(this.value)) {
                // Format as currency when user stops typing
                clearTimeout(this.formatTimer);
                this.formatTimer = setTimeout(() => {
                    if (this.value) {
                        this.value = parseFloat(this.value).toFixed(2);
                    }
                }, 1000);
            }
        });
    });

    // Confirm before marking transactions as paid
    const payButtons = document.querySelectorAll('form[action*="/pagar"] button[type="submit"]');
    payButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Tem certeza que deseja marcar esta transação como paga?')) {
                e.preventDefault();
            }
        });
    });

    // Auto-calculate percentage for budget progress bars
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const width = bar.style.width;
        if (width) {
            const percentage = parseFloat(width);
            bar.setAttribute('aria-valuenow', percentage);
        }
    });

    // Sidebar mobile toggle
    const sidebarToggle = document.querySelector('[data-sidebar-toggle]');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }

    // Mobile menu toggle for responsive design
    const mobileToggle = document.createElement('button');
    mobileToggle.className = 'mobile-menu-toggle d-md-none';
    mobileToggle.innerHTML = '<i class="fas fa-bars"></i>';
    mobileToggle.setAttribute('data-sidebar-toggle', '');
    
    const topBar = document.querySelector('.top-bar');
    if (topBar && window.innerWidth <= 768) {
        topBar.insertBefore(mobileToggle, topBar.firstChild);
        
        mobileToggle.addEventListener('click', function() {
            if (sidebar) {
                sidebar.classList.toggle('show');
            }
        });
    }

    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                
                // Focus on first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
            form.classList.add('was-validated');
        });
    });

    // Date input helpers
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        // Set today as default if no value and input is for 'data'
        if (!input.value && input.id === 'data') {
            const today = new Date();
            input.value = today.toISOString().split('T')[0];
        }
        
        // Set today as default for data_vencimento if it's empty
        if (!input.value && input.id === 'data_vencimento') {
            const today = new Date();
            input.value = today.toISOString().split('T')[0];
        }
    });

    // Search and filter functionality
    const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="Pesquisar"]');
    searchInputs.forEach(input => {
        let searchTimer;
        input.addEventListener('input', function() {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => {
                performSearch(this.value);
            }, 500);
        });
    });

    // Table row highlighting
    const tableRows = document.querySelectorAll('table tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = 'rgba(106, 13, 173, 0.05)';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });

    // Category type filter for forms
    const tipoSelect = document.getElementById('tipo');
    const categoriaSelect = document.getElementById('categoria_id');
    
    if (tipoSelect && categoriaSelect) {
        tipoSelect.addEventListener('change', function() {
            const tipo = this.value;
            const options = categoriaSelect.querySelectorAll('option');
            
            options.forEach(option => {
                if (option.value === '') {
                    option.style.display = 'block';
                    return;
                }
                
                // Show/hide options based on data attributes or text content
                // This would need to be enhanced based on actual category data structure
                option.style.display = 'block';
            });
        });
    }

    // Auto-update category preview in category form
    updateCategoryPreview();
});

// Search functionality
function performSearch(query) {
    if (!query) return;
    
    const tableRows = document.querySelectorAll('table tbody tr');
    const searchTerm = query.toLowerCase();
    
    tableRows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Format currency for display
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Format date for display
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('pt-BR');
}

// Show loading state
function showLoading(element) {
    element.classList.add('loading');
    const originalText = element.innerHTML;
    element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Carregando...';
    return originalText;
}

// Hide loading state
function hideLoading(element, originalText) {
    element.classList.remove('loading');
    element.innerHTML = originalText;
}

// Show success message
function showSuccess(message) {
    showAlert(message, 'success');
}

// Show error message
function showError(message) {
    showAlert(message, 'danger');
}

// Show alert
function showAlert(message, type = 'info') {
    const alertContainer = document.querySelector('.content') || document.body;
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type} alert-dismissible fade show`;
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.insertBefore(alertElement, alertContainer.firstChild);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (alertElement && alertElement.parentNode) {
            const bsAlert = new bootstrap.Alert(alertElement);
            if (bsAlert) {
                bsAlert.close();
            }
        }
    }, 5000);
}

// Utility function to debounce events
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Confirm dialog
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Format numbers for better readability
function formatNumber(number) {
    return new Intl.NumberFormat('pt-BR').format(number);
}

// Validate Brazilian email format
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Generate random color for categories
function getRandomColor() {
    const colors = [
        '#6a0dad', '#28a745', '#dc3545', '#ffc107', '#17a2b8',
        '#6610f2', '#e83e8c', '#20c997', '#fd7e14', '#6f42c1'
    ];
    return colors[Math.floor(Math.random() * colors.length)];
}

// Category preview functionality (for category form)
function updateCategoryPreview() {
    const nomeInput = document.getElementById('nome');
    const tipoInput = document.getElementById('tipo');
    const corInput = document.getElementById('cor');
    const iconeInput = document.getElementById('icone');
    
    const previewIcon = document.getElementById('category-preview-icon');
    const previewName = document.getElementById('category-preview-name');
    const previewType = document.getElementById('category-preview-type');
    
    if (!previewIcon || !previewName || !previewType) return;
    
    function updatePreview() {
        if (nomeInput) previewName.textContent = nomeInput.value || 'Nome da Categoria';
        if (tipoInput) previewType.textContent = tipoInput.value || 'Tipo';
        if (corInput) previewIcon.style.backgroundColor = corInput.value;
        if (iconeInput) previewIcon.textContent = iconeInput.value;
    }
    
    if (nomeInput) nomeInput.addEventListener('input', updatePreview);
    if (tipoInput) tipoInput.addEventListener('change', updatePreview);
    if (corInput) corInput.addEventListener('change', updatePreview);
    if (iconeInput) iconeInput.addEventListener('change', updatePreview);
    
    // Initial update
    updatePreview();
}

// Handle window resize for responsive behavior
window.addEventListener('resize', function() {
    const sidebar = document.querySelector('.sidebar');
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    
    if (window.innerWidth > 768) {
        if (sidebar) {
            sidebar.classList.remove('show');
        }
    }
});

// Auto-submit filters with debounce
function autoSubmitFilters() {
    const filterForms = document.querySelectorAll('form[method="GET"]');
    
    filterForms.forEach(form => {
        const inputs = form.querySelectorAll('select, input[type="date"], input[type="text"]');
        
        inputs.forEach(input => {
            const debouncedSubmit = debounce(() => {
                form.submit();
            }, 500);
            
            if (input.type === 'text' || input.type === 'date') {
                input.addEventListener('input', debouncedSubmit);
            } else {
                input.addEventListener('change', () => form.submit());
            }
        });
    });
}

// Initialize auto-submit filters when DOM is loaded
document.addEventListener('DOMContentLoaded', autoSubmitFilters);

// Export utilities for global access
window.FinanceApp = {
    formatCurrency,
    formatDate,
    showLoading,
    hideLoading,
    showSuccess,
    showError,
    showAlert,
    debounce,
    confirmAction,
    formatNumber,
    isValidEmail,
    getRandomColor,
    updateCategoryPreview,
    performSearch
};

// Handle form submission with loading states
document.addEventListener('submit', function(e) {
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    
    if (submitBtn && !form.classList.contains('no-loading')) {
        const originalText = showLoading(submitBtn);
        
        // Restore button after a delay if form is still on page
        setTimeout(() => {
            if (document.contains(submitBtn)) {
                hideLoading(submitBtn, originalText);
            }
        }, 3000);
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + N for new transaction
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        const newTransactionLink = document.querySelector('a[href*="nova"]');
        if (newTransactionLink) {
            newTransactionLink.click();
        }
    }
    
    // Escape to close modals or forms
    if (e.key === 'Escape') {
        const cancelBtn = document.querySelector('.btn-outline-secondary[href*="cancel"], a[href]:contains("Cancelar")');
        if (cancelBtn) {
            cancelBtn.click();
        }
    }
});
