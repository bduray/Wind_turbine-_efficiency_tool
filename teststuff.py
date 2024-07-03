st.write(f"Average Wind Direction: {average_wind_direction:.2f} degrees")
st.write(
    f"Distance to the first height data higher than {h2} meters: {actual_distance:.2f} meters")
st.write(f"Height at the found location: {height_at_new_location:.2f} meters")
if np.isnan(height_at_new_location) or height_at_new_location <= h2:
    wind_speed_reduction = 0
    st.write(
        f"No valid height data found higher than {h2} meters within the maximum search distance.")
    st.write(f"Wind Speed Reduction due to nearby building: {wind_speed_reduction:.2f} m/s")
   st.write(
                        f"Original Wind Speed at ({lat:.2f}, {lon:.2f}) at {h2} meters height: {original_wind_speed:.2f} m/s")
                    st.write(f"Final Wind Speed after reduction: {final_wind_speed:.2f} m/s")
st.write(
    f"Distance to the first height data higher than {h2} meters: {actual_distance:.2f} meters")
st.write(f"Height at the found location: {height_at_new_location:.2f} meters")
wind_power = calculate_wind_power(A, final_wind_speed)
st.write(f"Die effektive Leistung der Windturbine beträgt: **{wind_power:.2f} W**")

annual_energy_output = calculate_annual_energy_output(wind_power)
st.write(f"Die jährliche Energieproduktion beträgt: **{annual_energy_output:.2f} kWh**")

st.success(
    f"Die jährliche CO2-Einsparung im Vergleich zum Erdgas beträgt: **{annual_co2_savings_gas:.2f} kg CO2**")

# Plotting the results with custom colors
fossil_fuel_types = ['Coal', 'Natural Gas', 'Oil', 'Windturbine']
total_savings = [annual_co2_savings_coal, annual_co2_savings_gas, annual_co2_savings_oil, 0]

# Define colors using hex color codes
colors = ['#2d2d96', '#5858cc', '#7e7ed8', '#a4a4e3']

fig, ax = plt.subplots()
ax.bar(fossil_fuel_types, total_savings, color=colors)
ax.set_xlabel('Fossil Fuel Type')
ax.set_ylabel('Total CO2  (kg)')
ax.set_title(f'Total CO2 for energy over a year')

st.pyplot(fig)
