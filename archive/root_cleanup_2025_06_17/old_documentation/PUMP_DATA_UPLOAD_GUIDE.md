# APE Pumps Data Upload Guide
## Adding 300+ Additional Pump Performance Datasets

## Current Database Status
- **Current Pumps**: 3 authentic APE pumps (6 K 6 VANE, 6/8 ALE, 5 K)
- **Target Expansion**: 300+ additional pump performance datasets
- **Database Location**: `data/pumps_database.json`
- **Format**: JSON with objPump structure containing performance curves and specifications

## Method 1: Direct JSON Database Expansion (Recommended for Bulk Upload)

### Current Database Structure
```json
{
  "metadata": {
    "version": "1.0",
    "last_updated": "2025-06-09",
    "description": "APE Pumps database",
    "pump_count": 303
  },
  "pumps": [
    {
      "objPump": {
        "pPumpCode": "6 K 6 VANE",
        "pPumpTestSpeed": "1460",
        "pFilter1": "APE PUMPS",
        "pM_FLOW": "10;72;109;159;220;267;309|10;73;191;243;300;380;414",
        "pM_HEAD": "43.2;42.1;40.8;38.9;36.2;33.8;30.7|58.1;56.8;52.1;48.6;44.5;38.9;35.2",
        "pM_EFF": "0;60;70;76;79;82;77|0;60;74;78;81;82;78.9"
      }
    }
  ]
}
```

### Required Fields for Each Pump
- **pPumpCode**: Unique pump identifier
- **pPumpTestSpeed**: Test speed (RPM)
- **pFilter1**: Manufacturer (APE PUMPS)
- **pM_FLOW**: Flow rate data points (separated by ; for points, | for curves)
- **pM_HEAD**: Head data points (matching flow points)
- **pM_EFF**: Efficiency data points (matching flow points)
- **pM_POW**: Power consumption data points
- **pM_NPSH**: NPSH required data points

### Steps to Add Pump Data
1. **Backup Current Database**
   ```bash
   cp data/pumps_database.json data/pumps_database_backup.json
   ```

2. **Edit pumps_database.json**
   - Open in text editor or JSON editor
   - Add new pump objects to the "pumps" array
   - Update metadata pump_count
   - Validate JSON syntax

3. **Restart Application**
   - Application automatically loads updated database
   - Verify new pumps appear in selection interface

## Method 2: CSV Import with Conversion Script

### Create CSV Template
```csv
pump_code,test_speed,manufacturer,flow_points,head_points,efficiency_points,power_points,npsh_points
"8 K 8 VANE",1450,"APE PUMPS","0;120;180;240;300;360","45.2;44.1;42.8;40.9;38.2;35.1","0;65;75;81;84;79","0;85;95;105;115;125","2.1;2.3;2.8;3.2;3.8;4.5"
```

### Conversion Script (csv_to_pump_json.py)
```python
import csv
import json
from datetime import datetime

def convert_csv_to_pump_json(csv_file, output_file):
    """Convert CSV pump data to APE pump database format"""
    
    pumps = []
    
    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            pump_obj = {
                "objPump": {
                    "pPumpCode": row['pump_code'],
                    "pPumpTestSpeed": row['test_speed'],
                    "pFilter1": row['manufacturer'],
                    "pSuppName": row['manufacturer'],
                    "pM_FLOW": row['flow_points'],
                    "pM_HEAD": row['head_points'],
                    "pM_EFF": row['efficiency_points'],
                    "pM_POW": row['power_points'],
                    "pM_NPSH": row['npsh_points'],
                    "pVarD": "True",
                    "pVarN": "True",
                    "nPolyOrder": "3",
                    "pHeadCurvesNo": "1"
                }
            }
            pumps.append(pump_obj)
    
    database = {
        "metadata": {
            "version": "2.0",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "description": f"APE Pumps database with {len(pumps)} pumps",
            "pump_count": len(pumps)
        },
        "pumps": pumps
    }
    
    with open(output_file, 'w') as out_file:
        json.dump(database, out_file, indent=2)
    
    print(f"Converted {len(pumps)} pumps to {output_file}")

# Usage
convert_csv_to_pump_json('pump_data.csv', 'data/pumps_database.json')
```

## Method 3: Web Interface Upload (For Individual Pumps)

### Access Admin Interface
1. Navigate to `/admin` in your application
2. Use "Document Library" for PDF datasheets
3. Use direct database editing for performance data

### Single Pump Addition via Web
```python
# Add route for pump data upload
@app.route('/admin/add_pump', methods=['GET', 'POST'])
def add_pump():
    if request.method == 'POST':
        pump_data = {
            "objPump": {
                "pPumpCode": request.form['pump_code'],
                "pPumpTestSpeed": request.form['test_speed'],
                "pFilter1": "APE PUMPS",
                "pM_FLOW": request.form['flow_data'],
                "pM_HEAD": request.form['head_data'],
                "pM_EFF": request.form['efficiency_data']
            }
        }
        
        # Load current database
        with open('data/pumps_database.json', 'r') as f:
            db = json.load(f)
        
        # Add new pump
        db['pumps'].append(pump_data)
        db['metadata']['pump_count'] = len(db['pumps'])
        db['metadata']['last_updated'] = datetime.now().strftime("%Y-%m-%d")
        
        # Save updated database
        with open('data/pumps_database.json', 'w') as f:
            json.dump(db, f, indent=2)
        
        flash('Pump added successfully!', 'success')
        return redirect(url_for('add_pump'))
    
    return render_template('admin/add_pump.html')
```

## Method 4: Excel Import with Python Script

### Excel Template Structure
- Column A: Pump Code
- Column B: Test Speed
- Column C-H: Flow Points (6 points)
- Column I-N: Head Points (6 points)
- Column O-T: Efficiency Points (6 points)
- Column U-Z: Power Points (6 points)

### Excel Conversion Script
```python
import pandas as pd
import json

def excel_to_pump_database(excel_file, sheet_name='Pumps'):
    """Convert Excel pump data to database format"""
    
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    pumps = []
    
    for index, row in df.iterrows():
        # Extract flow, head, efficiency data
        flow_points = ';'.join([str(row[f'Flow_{i}']) for i in range(1, 7)])
        head_points = ';'.join([str(row[f'Head_{i}']) for i in range(1, 7)])
        eff_points = ';'.join([str(row[f'Eff_{i}']) for i in range(1, 7)])
        
        pump_obj = {
            "objPump": {
                "pPumpCode": row['Pump_Code'],
                "pPumpTestSpeed": str(row['Test_Speed']),
                "pFilter1": "APE PUMPS",
                "pSuppName": "APE PUMPS",
                "pM_FLOW": flow_points,
                "pM_HEAD": head_points,
                "pM_EFF": eff_points,
                "pVarD": "True",
                "pVarN": "True"
            }
        }
        pumps.append(pump_obj)
    
    return pumps
```

## Validation and Testing

### Data Validation Checks
1. **Pump Code Uniqueness**: Ensure no duplicate pump codes
2. **Data Point Consistency**: Flow, head, efficiency arrays must have same length
3. **Numerical Validation**: All performance values must be valid numbers
4. **Performance Curves**: Verify realistic pump characteristics

### Testing New Pumps
1. **Individual Pump Test**: Select new pump in interface
2. **Performance Verification**: Check calculated operating points
3. **Chart Rendering**: Verify performance curves display correctly
4. **PDF Generation**: Test report generation for new pumps

## Recommended Workflow for 300 Pumps

1. **Prepare Data**: Organize pump data in CSV or Excel format
2. **Validate Sample**: Test conversion with 5-10 pumps first
3. **Backup Database**: Create backup before bulk import
4. **Convert Data**: Use appropriate conversion script
5. **Validate Database**: Check JSON syntax and structure
6. **Test Application**: Verify new pumps load correctly
7. **Performance Check**: Test selection and reporting with new pumps

## Database Performance Considerations

### For 300+ Pumps
- **Loading Time**: Database loads in memory (< 1 second for 300 pumps)
- **Search Performance**: Linear search suitable for 300 pumps
- **Memory Usage**: ~50MB for complete database with performance curves
- **Indexing**: Consider pump code indexing for faster lookup

### Optimization Options
- **Database Migration**: Consider PostgreSQL for >1000 pumps
- **Caching**: Implement pump data caching for frequently accessed pumps
- **Lazy Loading**: Load pump details on demand rather than all at startup

## Support and Troubleshooting

### Common Issues
- **JSON Syntax Errors**: Use JSON validator before uploading
- **Data Format Mismatches**: Ensure consistent data point formats
- **Performance Curve Errors**: Verify realistic pump characteristics
- **Memory Issues**: Monitor application memory with large databases

### Getting Help
- **Validation Errors**: Check application logs for specific error messages
- **Performance Issues**: Monitor response times during pump selection
- **Data Quality**: Use built-in pump validation functions