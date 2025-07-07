/**
 * Material Icons Loader
 * Ensures proper Material Icons font loading and prevents duplicate rendering
 */

// Wait for Material Icons font to be fully loaded
function waitForMaterialIcons() {
    return new Promise((resolve) => {
        if (document.fonts && document.fonts.ready) {
            document.fonts.ready.then(() => {
                // Check if Material Icons font is loaded
                const testElement = document.createElement('span');
                testElement.style.fontFamily = '"Material Icons"';
                testElement.style.position = 'absolute';
                testElement.style.left = '-9999px';
                testElement.textContent = 'home';
                document.body.appendChild(testElement);
                
                const isLoaded = getComputedStyle(testElement).fontFamily.includes('Material Icons');
                document.body.removeChild(testElement);
                
                if (isLoaded) {
                    resolve();
                } else {
                    // Fallback: wait a bit more
                    setTimeout(resolve, 100);
                }
            });
        } else {
            // Fallback for older browsers
            setTimeout(resolve, 200);
        }
    });
}

// Fix Material Icons display
function fixMaterialIcons() {
    waitForMaterialIcons().then(() => {
        // Fix floating chat icon specifically
        const chatIcon = document.getElementById('chat-toggle-icon');
        if (chatIcon) {
            // Remove any conflicting styles or content
            chatIcon.style.removeProperty('background');
            chatIcon.style.removeProperty('background-image');
            
            // Ensure proper Material Icons setup
            chatIcon.classList.add('material-icons');
            chatIcon.textContent = 'auto_awesome';
            chatIcon.style.fontFamily = '"Material Icons"';
            chatIcon.style.speak = 'none';
            chatIcon.style.fontStyle = 'normal';
            chatIcon.style.fontWeight = 'normal';
            chatIcon.style.fontVariant = 'normal';
            chatIcon.style.textTransform = 'none';
            chatIcon.style.lineHeight = '1';
            chatIcon.style.webkitFontSmoothing = 'antialiased';
        }
        
        // Fix all Material Icons on the page
        const allIcons = document.querySelectorAll('.material-icons');
        allIcons.forEach(icon => {
            // Remove any background images that might interfere
            icon.style.removeProperty('background');
            icon.style.removeProperty('background-image');
            
            // Ensure proper font properties
            icon.style.fontFamily = '"Material Icons"';
            icon.style.speak = 'none';
            icon.style.fontStyle = 'normal';
            icon.style.fontWeight = 'normal';
            icon.style.fontVariant = 'normal';
            icon.style.textTransform = 'none';
            icon.style.lineHeight = '1';
            icon.style.webkitFontSmoothing = 'antialiased';
        });
    });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', fixMaterialIcons);
} else {
    fixMaterialIcons();
}

// Also fix icons when new content is added dynamically
const observer = new MutationObserver((mutations) => {
    let shouldFix = false;
    mutations.forEach((mutation) => {
        if (mutation.addedNodes.length > 0) {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1) { // Element node
                    if (node.classList && node.classList.contains('material-icons')) {
                        shouldFix = true;
                    }
                    if (node.querySelectorAll && node.querySelectorAll('.material-icons').length > 0) {
                        shouldFix = true;
                    }
                }
            });
        }
    });
    
    if (shouldFix) {
        setTimeout(fixMaterialIcons, 10);
    }
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});