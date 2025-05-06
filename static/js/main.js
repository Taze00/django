// Main JavaScript for Berlin Nightlife Portfolio

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Navbar scroll effect
    const navbar = document.querySelector('.main-nav');
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
    
    // Mobile menu toggle
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', function() {
            navToggle.classList.toggle('active');
            navLinks.classList.toggle('active');
        });
        
        // Close mobile menu when clicking a nav link
        document.querySelectorAll('.nav-links a').forEach(link => {
            link.addEventListener('click', function() {
                navToggle.classList.remove('active');
                navLinks.classList.remove('active');
            });
        });
    }
    
    // Active navigation based on scroll position
    const sections = document.querySelectorAll('section');
    const navItems = document.querySelectorAll('.nav-links a');
    
    if (sections.length > 0 && navItems.length > 0) {
        window.addEventListener('scroll', function() {
            let current = '';
            
            sections.forEach(section => {
                const sectionTop = section.offsetTop;
                const sectionHeight = section.clientHeight;
                
                if (window.scrollY >= (sectionTop - 200)) {
                    current = section.getAttribute('id');
                }
            });
            
            navItems.forEach(item => {
                item.classList.remove('active');
                if (item.getAttribute('href') && item.getAttribute('href').substring(1) === current) {
                    item.classList.add('active');
                }
            });
        });
    }
    
    // Typing animation
    const typedTextSpan = document.querySelector('.typed-text');
    if (typedTextSpan) {
        const texts = ['Developer', 'Tech Enthusiast', 'Berlin Native', 'Techno Lover'];
        let textIndex = 0;
        let charIndex = 0;
        let isDeleting = false;
        let typingDelay = 150; // Delay between each character typing
        let deletingDelay = 50; // Delay between each character deletion
        
        function type() {
            const currentText = texts[textIndex];
            
            if (isDeleting) {
                // Remove character
                typedTextSpan.textContent = currentText.substring(0, charIndex - 1);
                charIndex--;
                typingDelay = deletingDelay;
            } else {
                // Add character
                typedTextSpan.textContent = currentText.substring(0, charIndex + 1);
                charIndex++;
                typingDelay = 150;
            }
            
            // If word is complete
            if (!isDeleting && charIndex === currentText.length) {
                // Pause at end of word
                typingDelay = 2000;
                isDeleting = true;
            }
            
            // If word is deleted
            if (isDeleting && charIndex === 0) {
                isDeleting = false;
                textIndex++;
                
                // Cycle back to first word if at end of array
                if (textIndex === texts.length) {
                    textIndex = 0;
                }
                
                // Pause before typing next word
                typingDelay = 500;
            }
            
            setTimeout(type, typingDelay);
        }
        
        // Start typing effect
        setTimeout(type, 1000);
    }
    
    // Initialize portfolio filter with Isotope
    const portfolioGrid = document.querySelector('.portfolio-grid');
    
    if (portfolioGrid && window.Isotope && window.imagesLoaded) {
        // Initialize Isotope after images are loaded
        imagesLoaded(portfolioGrid, function() {
            const iso = new Isotope(portfolioGrid, {
                itemSelector: '.portfolio-item',
                layoutMode: 'fitRows'
            });
            
            // Filter items on button click
            document.querySelectorAll('.portfolio-filter button').forEach(button => {
                button.addEventListener('click', function() {
                    let filterValue = this.getAttribute('data-filter');
                    
                    // Update active state
                    document.querySelectorAll('.portfolio-filter button').forEach(btn => {
                        btn.classList.remove('active');
                    });
                    this.classList.add('active');
                    
                    // Filter items
                    iso.arrange({
                        filter: filterValue === '*' ? null : filterValue
                    });
                });
            });
        });
    }
    
    // Reveal animations on scroll
    const revealElements = document.querySelectorAll('.about-content, .portfolio-item, .club-card');
    
    if (revealElements.length > 0) {
        function revealOnScroll() {
            revealElements.forEach(element => {
                const elementTop = element.getBoundingClientRect().top;
                const elementBottom = element.getBoundingClientRect().bottom;
                
                if (elementTop < window.innerHeight - 100 && elementBottom > 0) {
                    element.classList.add('revealed');
                }
            });
        }
        
        // Initial check
        revealOnScroll();
        
        // Check on scroll
        window.addEventListener('scroll', revealOnScroll);
    }
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const href = this.getAttribute('href');
            if (!href) return;
            
            const target = document.querySelector(href);
            
            if (target) {
                window.scrollTo({
                    top: target.offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Form submission handler
    const contactForm = document.querySelector('.contact-form');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form values
            const name = this.querySelector('input[name="name"]').value;
            const email = this.querySelector('input[name="email"]').value;
            const subject = this.querySelector('input[name="subject"]').value || '';
            const message = this.querySelector('textarea[name="message"]').value;
            
            // Basic validation
            if (!name || !email || !message) {
                alert('Please fill in all required fields');
                return;
            }
            
            // Here you would typically send form data to your backend
            console.log('Form submitted:', { name, email, subject, message });
            
            // Show success message
            const button = this.querySelector('button[type="submit"]');
            if (button) {
                const originalText = button.textContent;
                
                button.textContent = 'Message Sent!';
                button.disabled = true;
                
                // Reset form and button after delay
                setTimeout(() => {
                    this.reset();
                    button.textContent = originalText;
                    button.disabled = false;
                }, 3000);
            }
        });
    }
});

