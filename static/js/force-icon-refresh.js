/**
 * Force Icon Refresh Script
 * Eliminates cached robot icons and forces lightbulb display
 */

// Force immediate icon updates on page load
document.addEventListener('DOMContentLoaded', function() {
    // Force floating chat icon update with proper Material Icons display
    function forceIconUpdate() {
        const floatingIcon = document.getElementById('chat-toggle-icon');
        if (floatingIcon) {
            // Clear any duplicate content and set proper icon
            floatingIcon.textContent = 'auto_awesome';
            // Ensure Material Icons font is applied
            if (!floatingIcon.classList.contains('material-icons')) {
                floatingIcon.classList.add('material-icons');
            }
        }
        
        // Clean up any robot icons and ensure proper Material Icons class
        const materialIcons = document.querySelectorAll('.material-icons');
        if (materialIcons && materialIcons.length > 0) {
            materialIcons.forEach(icon => {
                if (icon.textContent.includes('smart_toy') || 
                    icon.textContent.includes('psychology') || 
                    icon.textContent.includes('lightbulb')) {
                    icon.textContent = 'auto_awesome';
                }
                // Ensure proper Material Icons font is loaded
                if (!icon.style.fontFamily) {
                    icon.style.fontFamily = '"Material Icons"';
                }
            });
        }
    }
    
    // Multiple update attempts to override cache
    forceIconUpdate();
    setTimeout(forceIconUpdate, 50);
    setTimeout(forceIconUpdate, 200);
    setTimeout(forceIconUpdate, 500);
});