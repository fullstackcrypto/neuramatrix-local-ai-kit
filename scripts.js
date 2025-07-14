// Smooth scrolling
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Intersection observer
const faders = document.querySelectorAll('.fade-in, .fade-in-up');
const options = { threshold: 0.3 };

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.animationPlayState = 'running';
            observer.unobserve(entry.target);
        }
    });
}, options);

faders.forEach(fader => {
    observer.observe(fader);
});

// Reactive hovers
document.querySelectorAll('.cta-button, .buy-button').forEach(button => {
    button.addEventListener('mouseenter', () => { button.style.boxShadow = '0 0 10px #00ffcc'; });
    button.addEventListener('mouseleave', () => { button.style.boxShadow = 'none'; });
});

console.log('Site operational - verified at 09:36 PM EDT, July 13, 2025');
