// Main JavaScript functionality for the financial management system

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initFormAnimations();
    initTableInteractions();
    initNotifications();
    initMobileMenu();
    formatCurrency();
    
    // Auto-dismiss flash messages
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            if (alert.classList.contains('show')) {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 300);
            }
        });
    }, 5000);
});

// Form animations and interactions
function initFormAnimations() {
    const forms = document.querySelectorAll('.financial-form, .auth-form');
    
    forms.forEach(form => {
        // Add focus animations to inputs
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
            });
            
            input.addEventListener('blur', function() {
                if (!this.value) {
                    this.parentElement.classList.remove('focused');
                }
            });
            
            // Check if input already has value on page load
            if (input.value) {
                input.parentElement.classList.add('focused');
            }
        });
        
        // Form submission animation
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.style.transform = 'scale(0.95)';
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';
            }
        });
    });
}

// Table interactions
function initTableInteractions() {
    const tables = document.querySelectorAll('.financial-table');
    
    tables.forEach(table => {
        // Add hover effects to rows
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            row.addEventListener('mouseenter', function() {
                this.style.transform = 'translateX(5px)';
            });
            
            row.addEventListener('mouseleave', function() {
                this.style.transform = 'translateX(0)';
            });
        });
        
        // Add click animations to action buttons
        const actionBtns = table.querySelectorAll('.btn-action');
        actionBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                // Create ripple effect
                const ripple = document.createElement('span');
                ripple.style.cssText = `
                    position: absolute;
                    border-radius: 50%;
                    background: rgba(255, 255, 255, 0.6);
                    transform: scale(0);
                    animation: ripple 0.6s linear;
                    pointer-events: none;
                `;
                
                const rect = this.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                ripple.style.width = ripple.style.height = size + 'px';
                ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
                ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
                
                this.style.position = 'relative';
                this.appendChild(ripple);
                
                setTimeout(() => ripple.remove(), 600);
            });
        });
    });
}

// Notification system
function initNotifications() {
    // Create notification container if it doesn't exist
    if (!document.querySelector('.notification-container')) {
        const container = document.createElement('div');
        container.className = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            max-width: 400px;
        `;
        document.body.appendChild(container);
    }
}

// Show custom notification
function showNotification(message, type = 'info', duration = 5000) {
    const container = document.querySelector('.notification-container');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        border-radius: 10px;
        padding: 15px 20px;
        margin-bottom: 10px;
        border-left: 4px solid ${getTypeColor(type)};
        color: white;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
    
    notification.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="
                background: none;
                border: none;
                color: white;
                font-size: 18px;
                cursor: pointer;
                padding: 0;
                margin-left: 15px;
            ">&times;</button>
        </div>
    `;
    
    container.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Auto remove
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

function getTypeColor(type) {
    const colors = {
        success: '#1aaf8f',
        error: '#e74c3c',
        warning: '#f8a45c',
        info: '#0275ea'
    };
    return colors[type] || colors.info;
}

// Mobile menu functionality
function initMobileMenu() {
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    if (window.innerWidth <= 768) {
        // Create mobile menu toggle
        const menuToggle = document.createElement('button');
        menuToggle.className = 'mobile-menu-toggle';
        menuToggle.innerHTML = '<i class="fas fa-bars"></i>';
        menuToggle.style.cssText = `
            position: fixed;
            top: 20px;
            left: 20px;
            z-index: 1001;
            background: rgba(2, 117, 234, 0.9);
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            color: white;
            font-size: 18px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        `;
        
        document.body.appendChild(menuToggle);
        
        menuToggle.addEventListener('click', () => {
            if (sidebar) {
                sidebar.style.transform = sidebar.style.transform === 'translateX(0%)' 
                    ? 'translateX(-100%)' 
                    : 'translateX(0%)';
            }
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!sidebar?.contains(e.target) && !menuToggle.contains(e.target)) {
                if (sidebar) {
                    sidebar.style.transform = 'translateX(-100%)';
                }
            }
        });
    }
}

// Format currency values
function formatCurrency() {
    const currencyElements = document.querySelectorAll('.currency, .value');
    
    currencyElements.forEach(element => {
        const value = parseFloat(element.textContent.replace(/[^\d.-]/g, ''));
        if (!isNaN(value)) {
            element.textContent = `R$ ${value.toLocaleString('pt-BR', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            })}`;
        }
    });
}

// Utility functions
function formatDate(date) {
    return new Date(date).toLocaleDateString('pt-BR');
}

function calculateDaysDifference(date1, date2) {
    const diffTime = Math.abs(date2 - date1);
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

// Form validation helpers
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validateCurrency(value) {
    const num = parseFloat(value);
    return !isNaN(num) && num >= 0;
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .form-group.focused label {
        color: #0275ea;
        transform: translateY(-5px);
        font-size: 0.9rem;
    }
    
    .notification {
        animation: slideInRight 0.3s ease;
    }
    
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .mobile-menu-toggle:hover {
        transform: scale(1.1);
        background: rgba(2, 117, 234, 1) !important;
    }
`;

document.head.appendChild(style);

// Export functions for global use
window.showNotification = showNotification;
window.formatCurrency = formatCurrency;
