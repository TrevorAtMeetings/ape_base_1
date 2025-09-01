/**
 * Pump Results Sorting Functionality
 * Handles client-side sorting of pump results by various criteria
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize sorting functionality
    initializeSorting();
});

function initializeSorting() {
    const sortButtons = document.querySelectorAll('.sort-option');
    const preferredList = document.getElementById('preferred-pump-list');
    const allowableList = document.getElementById('allowable-pump-list');
    
    if (sortButtons.length === 0) {
        return;
    }
    
    
    // Add click handlers to all sort buttons
    sortButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const sortKey = this.getAttribute('data-sort');
            const sortOrder = this.getAttribute('data-order');
            
            
            // Update active state
            sortButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Sort both lists
            if (preferredList) {
                sortPumpList(preferredList, sortKey, sortOrder);
            }
            if (allowableList) {
                sortPumpList(allowableList, sortKey, sortOrder);
            }
        });
    });
}

function sortPumpList(listElement, sortKey, sortOrder) {
    const pumpRows = Array.from(listElement.querySelectorAll('.pump-result-row'));
    
    if (pumpRows.length === 0) {
        return;
    }
    
    
    // Sort the array of pump rows
    pumpRows.sort((a, b) => {
        let valueA = getSortValue(a, sortKey);
        let valueB = getSortValue(b, sortKey);
        
        // Handle different data types
        if (typeof valueA === 'string' && typeof valueB === 'string') {
            valueA = valueA.toLowerCase();
            valueB = valueB.toLowerCase();
        }
        
        let comparison = 0;
        if (valueA < valueB) {
            comparison = -1;
        } else if (valueA > valueB) {
            comparison = 1;
        }
        
        // Apply sort order
        return sortOrder === 'desc' ? -comparison : comparison;
    });
    
    // Re-append sorted elements to the list
    pumpRows.forEach((row, index) => {
        // Update rank circle
        const rankCircle = row.querySelector('.pump-rank-circle');
        if (rankCircle) {
            rankCircle.textContent = index + 1;
        }
        
        listElement.appendChild(row);
    });
    
}

function getSortValue(element, sortKey) {
    // Map data attributes to the sort keys
    const dataAttributeMap = {
        'suitability_score': 'data-total-score',
        'efficiency_pct': 'data-efficiency-pct', 
        'power_kw': 'data-power-kw',
        'pump_type': 'data-pump-type',
        'qbep_percentage': 'data-qbp-percent',
        'npshr_m': 'data-npshr-m',
        'pump_code': 'data-pump-code'
    };
    
    const dataAttribute = dataAttributeMap[sortKey];
    if (!dataAttribute) {
        console.warn(`Unknown sort key: ${sortKey}`);
        return '';
    }
    
    const value = element.getAttribute(dataAttribute);
    
    // Convert to appropriate type
    if (dataAttribute === 'data-pump-type' || dataAttribute === 'data-pump-code') {
        return value || '';
    } else {
        return parseFloat(value) || 0;
    }
}