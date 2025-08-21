#!/usr/bin/env python
"""
Script to update pump_options.html template to display VFD information
"""

import re

# Read the template file
with open('templates/pump_options.html', 'r') as f:
    content = f.read()

# Define the old TRIM metric pattern
old_pattern = r'''<div class="metric-item">
                            <span class="metric-label-inline">TRIM</span>
                            <span class="metric-value-inline">
                                {% if pump\.get\('trim_percent'\) %}
                                    {{ \(100 - pump\['trim_percent'\]\)\|round\|int }}%
                                {% else %}
                                    0%
                                {% endif %}
                            </span>
                        </div>'''

# Define the new VFD-aware metric pattern
new_pattern = '''<div class="metric-item">
                            {% if pump.get('sizing_method') == 'Speed Variation' or pump.get('vfd_required') %}
                                <span class="metric-label-inline">VFD</span>
                                <span class="metric-value-inline">
                                    {% if pump.get('speed_ratio') %}
                                        {{ pump['speed_ratio']|round|int }}%
                                    {% elif pump.get('required_speed_rpm') %}
                                        {{ pump['required_speed_rpm']|round|int }}rpm
                                    {% else %}
                                        Req'd
                                    {% endif %}
                                </span>
                            {% else %}
                                <span class="metric-label-inline">TRIM</span>
                                <span class="metric-value-inline">
                                    {% if pump.get('trim_percent') %}
                                        {{ (100 - pump['trim_percent'])|round|int }}%
                                    {% else %}
                                        0%
                                    {% endif %}
                                </span>
                            {% endif %}
                        </div>'''

# Count occurrences
count = content.count('<span class="metric-label-inline">TRIM</span>')
print(f"Found {count} occurrences of TRIM metric")

# Replace all occurrences
content = content.replace('''<div class="metric-item">
                            <span class="metric-label-inline">TRIM</span>
                            <span class="metric-value-inline">
                                {% if pump.get('trim_percent') %}
                                    {{ (100 - pump['trim_percent'])|round|int }}%
                                {% else %}
                                    0%
                                {% endif %}
                            </span>
                        </div>''', new_pattern)

# Write the updated content back
with open('templates/pump_options.html', 'w') as f:
    f.write(content)

print("Template updated successfully!")
print("All TRIM metrics will now display VFD information when applicable")