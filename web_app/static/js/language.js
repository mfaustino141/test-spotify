// Language handling functionality
function setLanguage(lang) {
    localStorage.setItem('language', lang);
    translatePage();
}

function translatePage() {
    const currentLang = localStorage.getItem('language') || 'en';
    document.documentElement.setAttribute('lang', currentLang);

    // Update language selector
    const languageSelect = document.getElementById('language-select');
    if (languageSelect) {
        languageSelect.value = currentLang;
    }

    // Translate all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (translations[currentLang] && translations[currentLang][key]) {
            // Handle placeholder attribute for inputs
            if (element.hasAttribute('placeholder')) {
                element.placeholder = translations[currentLang][key];
            } else {
                element.textContent = translations[currentLang][key];
            }
        }
    });
}

// Apply translation on page load
document.addEventListener('DOMContentLoaded', () => {
    translatePage();
});
