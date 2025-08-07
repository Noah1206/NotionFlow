// Pricing Page JavaScript

class PricingPage {
    constructor() {
        this.init();
    }

    init() {
        this.setupBillingToggle();
        this.setupFAQ();
        this.setupScrollAnimations();
        this.setupPlanButtons();
    }

    setupBillingToggle() {
        const toggle = document.getElementById('billing-toggle');
        const monthlyPrices = document.querySelectorAll('.price-monthly');
        const yearlyPrices = document.querySelectorAll('.price-yearly');

        if (!toggle) return;

        toggle.addEventListener('change', () => {
            const isYearly = toggle.checked;
            
            monthlyPrices.forEach(price => {
                price.style.display = isYearly ? 'none' : 'flex';
            });
            
            yearlyPrices.forEach(price => {
                price.style.display = isYearly ? 'flex' : 'none';
            });

            // Update button text based on billing period
            this.updateButtonText(isYearly);
        });
    }

    updateButtonText(isYearly) {
        const buttons = document.querySelectorAll('.plan-button.primary');
        buttons.forEach(button => {
            if (button.textContent.includes('무료 체험')) {
                button.textContent = isYearly ? '연간 구독으로 시작' : '14일 무료 체험';
            }
        });
    }

    setupFAQ() {
        const faqItems = document.querySelectorAll('.faq-item');
        
        faqItems.forEach(item => {
            const question = item.querySelector('.faq-question');
            
            question.addEventListener('click', () => {
                const isActive = item.classList.contains('active');
                
                // Close all other FAQ items
                faqItems.forEach(otherItem => {
                    if (otherItem !== item) {
                        otherItem.classList.remove('active');
                    }
                });
                
                // Toggle current item
                item.classList.toggle('active', !isActive);
            });
        });
    }

    setupScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);

        // Observe pricing cards
        const pricingCards = document.querySelectorAll('.pricing-card');
        pricingCards.forEach(card => {
            observer.observe(card);
        });

        // Observe FAQ items
        const faqItems = document.querySelectorAll('.faq-item');
        faqItems.forEach(item => {
            observer.observe(item);
        });
    }

    setupPlanButtons() {
        const planButtons = document.querySelectorAll('.plan-button');
        
        planButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const card = button.closest('.pricing-card');
                const planName = card.querySelector('h3').textContent;
                
                // Add ripple effect
                this.createRipple(button, e);
                
                // Track button click (you can integrate with analytics here)
                
                // Handle different plan actions
                this.handlePlanSelection(button, planName);
            });
        });
    }

    createRipple(button, event) {
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transform: scale(0);
            animation: ripple 0.6s linear;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            pointer-events: none;
        `;
        
        button.style.position = 'relative';
        button.style.overflow = 'hidden';
        button.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    handlePlanSelection(button, planName) {
        const buttonText = button.textContent.toLowerCase();
        
        if (buttonText.includes('무료')) {
            // Redirect to signup
            window.location.href = '/signup';
        } else if (buttonText.includes('체험')) {
            // Redirect to trial signup
            window.location.href = '/signup?plan=pro&trial=true';
        } else if (buttonText.includes('문의')) {
            // Open contact form or redirect to contact page
            this.openContactModal();
        }
    }

    openContactModal() {
        // Simple contact modal (you can enhance this)
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        `;
        
        modal.innerHTML = `
            <div style="
                background: white;
                padding: 2rem;
                border-radius: 16px;
                max-width: 400px;
                text-align: center;
            ">
                <h3 style="margin-bottom: 1rem;">영업팀 문의</h3>
                <p style="margin-bottom: 2rem; color: #6b7280;">
                    기업용 솔루션에 대해 문의해주세요. 
                    24시간 이내에 연락드리겠습니다.
                </p>
                <div style="display: flex; gap: 1rem; justify-content: center;">
                    <a href="mailto:sales@notionflow.com" 
                       style="
                           background: #ff3b30;
                           color: white;
                           padding: 0.75rem 1.5rem;
                           border-radius: 8px;
                           text-decoration: none;
                           font-weight: 600;
                       ">
                        이메일 보내기
                    </a>
                    <button onclick="this.closest('.modal').remove()" 
                            style="
                                background: #f3f4f6;
                                color: #374151;
                                padding: 0.75rem 1.5rem;
                                border-radius: 8px;
                                border: none;
                                font-weight: 600;
                                cursor: pointer;
                            ">
                        닫기
                    </button>
                </div>
            </div>
        `;
        
        modal.className = 'modal';
        document.body.appendChild(modal);
        
        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
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
    
    .pricing-card {
        opacity: 0;
        transform: translateY(30px);
        transition: all 0.6s ease;
    }
    
    .pricing-card.animate-in {
        opacity: 1;
        transform: translateY(0);
    }
    
    .faq-item {
        opacity: 0;
        transform: translateX(-20px);
        transition: all 0.5s ease;
    }
    
    .faq-item.animate-in {
        opacity: 1;
        transform: translateX(0);
    }
    
    .pricing-card:nth-child(1) { transition-delay: 0.1s; }
    .pricing-card:nth-child(2) { transition-delay: 0.2s; }
    .pricing-card:nth-child(3) { transition-delay: 0.3s; }
    
    .faq-item:nth-child(1) { transition-delay: 0.1s; }
    .faq-item:nth-child(2) { transition-delay: 0.2s; }
    .faq-item:nth-child(3) { transition-delay: 0.3s; }
    .faq-item:nth-child(4) { transition-delay: 0.4s; }
    .faq-item:nth-child(5) { transition-delay: 0.5s; }
    .faq-item:nth-child(6) { transition-delay: 0.6s; }
`;
document.head.appendChild(style);

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PricingPage();
});

// Add smooth scroll behavior for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add navbar scroll effect
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.style.background = 'rgba(255, 255, 255, 0.95)';
        navbar.style.backdropFilter = 'blur(10px)';
        navbar.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.1)';
    } else {
        navbar.style.background = 'rgba(255, 255, 255, 0.9)';
        navbar.style.backdropFilter = 'blur(5px)';
        navbar.style.boxShadow = '0 1px 2px rgba(0, 0, 0, 0.05)';
    }
}); 