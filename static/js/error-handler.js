/**
 * Global Error Handler for APE Pumps Application
 * Provides robust error handling and fallback mechanisms
 */

// Global error handler to catch JavaScript syntax errors
window.addEventListener('error', function(event) {
    console.warn('JavaScript Error Caught:', event.error);
    console.warn('Error Details:', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
    });
    
    // Prevent the error from breaking the application
    event.preventDefault();
    return true;
});

// Global unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(event) {
    console.warn('Unhandled Promise Rejection:', event.reason);
    event.preventDefault();
});

// Array validation helper
function safeForEach(array, callback) {
    if (Array.isArray(array) && typeof callback === 'function') {
        array.forEach(callback);
    }
}

// Export for use in other modules
window.safeForEach = safeForEach;