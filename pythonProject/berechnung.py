def calculate_wind_power(A, v):
    # Definieren Sie die Konstanten
    rho = 1.2255  # Luftdichte in kg/m³
    efficiency = 0.4  # Angenommene Effizienz der Turbine (40%)

    # Berechnung der theoretischen Leistung
    PWind = (rho / 2) * A * v ** 3

    # Berechnung der tatsächlichen Leistung unter Berücksichtigung der Effizienz
    PEffective = PWind * efficiency

    return PEffective


def calculate_annual_energy_output(power):
    # Berechnung der jährlichen Energieproduktion in kWh
    hours_per_year = 24 * 365
    annual_energy_output = power * hours_per_year / 1000  # Umrechnung von Watt in kW
    return annual_energy_output


def calculate_co2_savings(annual_energy_output, co2_per_kwh=0.5):
    # Berechnung der CO2-Einsparung in kg
    co2_savings = annual_energy_output * co2_per_kwh
    return co2_savings


def calculate_total_co2_savings(annual_co2_savings, years):
    # Berechnung der Gesamteinsparung in kg CO2 über die angegebene Anzahl von Jahren
    total_co2_savings = annual_co2_savings * years
    return total_co2_savings


# Beispielwerte
A = float(input("Geben Sie die Fläche der Turbine in Quadratmetern (m²) ein: "))
v = float(input("Geben Sie die Windgeschwindigkeit in Metern pro Sekunde (m/s) ein: "))
years = int(input("Geben Sie die Anzahl der Jahre ein, für die die Turbine genutzt werden soll: "))

# Berechnung der tatsächlichen Leistung unter Berücksichtigung der Effizienz
wind_power = calculate_wind_power(A, v)
print(f"Die effektive Leistung der Windturbine beträgt: {round(wind_power, 2)} W")

# Berechnung der jährlichen Energieproduktion
annual_energy_output = calculate_annual_energy_output(wind_power)
print(f"Die jährliche Energieproduktion beträgt: {round(annual_energy_output, 2)} kWh")

# Berechnung der jährlichen CO2-Einsparung
annual_co2_savings = calculate_co2_savings(annual_energy_output)
print(f"Die jährliche CO2-Einsparung beträgt: {round(annual_co2_savings, 2)} kg CO2")

# Berechnung der Gesamteinsparung über die angegebene Anzahl von Jahren
total_co2_savings = calculate_total_co2_savings(annual_co2_savings, years)
print(f"Die Gesamteinsparung über {years} Jahre beträgt: {round(total_co2_savings, 2)} kg CO2")
