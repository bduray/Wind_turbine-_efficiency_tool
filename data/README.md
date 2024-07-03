# Wind Turbine Efficiency Evaluation Tool

## Overview

This tool helps assess the potential energy output and environmental impact of using small wind turbines in urban environments. It integrates wind speed data, terrain height data, and wind direction data to provide a comprehensive analysis of wind energy potential specific locations.

## Installation

1. Navigate to the project directory. Replace `<project_directory>` with the path to the directory where the project files are located:
   ```
   cd <project_directory>
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. To run the Streamlit application, type the following command in the terminal:
   ```
   streamlit run data/webapp_wind_LCA.py
   ```

2. Follow the steps on the web interface:
   - Enter the requested values
   - Select a location on the interactive map
   - Click "Calculate" to get the results
   - View the results, including the effective power output, annual energy production, and CO2 savings
   - If results are not as expected, review the height map for potential alternative locations and start from the beginning

## Project Structure

- **data/**: Directory containing the necessary files for the project.
  - **webapp_wind_LCA.py**: main file for the Streamlit web app
  - **requirements.txt**: list of required Python packages
  - **readme.txt**: instructions and overview of the project
  - **en_100m_klas.tif**: TIFF file with wind speed data

## Key Features

- Interactive map for selecting turbine locations
- Automated calculations for wind speed adjustment and energy output
- Visualization of CO2 savings compared to fossil fuels
- User-friendly interface requiring minimal input

## Future Work

- Extend functionality beyond the NRW region
- Refine wind speed reduction calculations
- Improve height data accuracy and drag coefficient estimates




