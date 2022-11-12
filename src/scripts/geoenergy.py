import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from scipy.constants import pi
import pygfunction as gt
import pandas as pd

class Geoenergy:
    def __init__(self, demand_arr, temperature, cop, thermal_conductivity, groundwater_table):
        self.demand_arr = demand_arr - demand_arr/cop
        self.temperature = temperature
        self.thermal_conductivity = thermal_conductivity
        self.groundwater_table = groundwater_table
        self.calculation([60, 70, 80, 90, 100, 110], 3, 1.5)

    def load(self, x, YEARS, arr):
        arr = arr * 1000
        stacked_arr = []
        for i in range(0, YEARS):
            stacked_arr.append(arr)
        stacked_arr = np.array(stacked_arr)
        arr = np.vstack([stacked_arr]).flatten()
        return arr

    def calculation(self, kWh_per_meter_list, years, temperature_limit):
        demand = np.sum(self.demand_arr)
        for kWh_per_meter in kWh_per_meter_list:
            meter = demand/kWh_per_meter

            # Borehole dimensions
            D = 1         # Borehole buried depth (m)
            H = meter     # Borehole length (m)
            r_b = 0.057   # Borehole radius (m)

            # Pipe dimensions
            rp_out = 0.0211     # Pipe outer radius (m)
            rp_in = 0.0147      # Pipe inner radius (m)
            D_s = 0.03         # Shank spacing (m)
            epsilon = 1.0e-6    # Pipe roughness (m)

            # Pipe positions
            pos_single = [(-D_s, 0.), (D_s, 0.)]

            # Ground properties
            alpha = 1.0e-6      # Ground thermal diffusivity (m2/s)
            k_s = self.thermal_conductivity           # Ground thermal conductivity (W/m.K)
            T_g = self.temperature + 0.004*meter # Undisturbed ground temperature (degC)

            # Grout properties
            k_g = 0.6           # Grout thermal conductivity (W/m.K)

            # Pipe properties
            k_p = 0.42           # Pipe thermal conductivity (W/m.K)

            # Fluid properties
            m_flow = 0.5       # Total fluid mass flow rate (kg/s)
            fluid = gt.media.Fluid('MEA', 5)
            cp_f = fluid.cp     # Fluid specific isobaric heat capacity (J/kg.K)
            den_f = fluid.rho   # Fluid density (kg/m3)
            visc_f = fluid.mu   # Fluid dynamic viscosity (kg/m.s)
            k_f = fluid.k       # Fluid thermal conductivity (W/m.K)

            # g-Function calculation options
            options = {'nSegments': 8, 'disp': True}

            # Simulation parameters      
            dt = 3600                   # Time step (s)
            tmax = years * 8760 * 3600  # Maximum time (s)
            Nt = int(np.ceil(tmax/dt))  # Number of time steps
            time = dt * np.arange(1, Nt+1)

            # Evaluate heat extraction rate
            Q = self.load(time/3600., years, self.demand_arr)

            # Load aggregation scheme
            LoadAgg = gt.load_aggregation.ClaessonJaved(dt, tmax)

            # The field contains only one borehole
            borehole = gt.boreholes.Borehole(H, D, r_b, x=0., y=0.)
            boreField = [borehole]

            # Get time values needed for g-function evaluation
            time_req = LoadAgg.get_times_for_simulation()

            # Calculate g-function
            gFunc = gt.gfunction.gFunction(boreField, alpha, time=time_req, options=options)

            # Initialize load aggregation scheme
            LoadAgg.initialize(gFunc.gFunc/(2*pi*k_s))

            # Pipe thermal resistance
            R_p = gt.pipes.conduction_thermal_resistance_circular_pipe(rp_in, rp_out, k_p)
            # Fluid to inner pipe wall thermal resistance (Single U-tube)
            h_f = gt.pipes.convective_heat_transfer_coefficient_circular_pipe(m_flow, rp_in, visc_f, den_f, k_f, cp_f, epsilon)
            R_f_ser = 1.0/(h_f*2*pi*rp_in)

            # Single U-tube
            SingleUTube = gt.pipes.SingleUTube(pos_single, rp_in, rp_out, borehole, k_s, k_g, R_f_ser + R_p)

            T_b = np.zeros(Nt)
            T_f_in_single = np.zeros(Nt)
            T_f_out_single = np.zeros(Nt)
            for i, (t, Q_b_i) in enumerate(zip(time, Q)):
                # Increment time step by (1)
                LoadAgg.next_time_step(t)

                # Apply current load
                LoadAgg.set_current_load(Q_b_i/H)

                # Evaluate borehole wall temperature
                deltaT_b = LoadAgg.temporal_superposition()
                T_b[i] = T_g - deltaT_b

                # Evaluate inlet fluid temperature
                T_f_in_single[i] = SingleUTube.get_inlet_temperature(Q[i], T_b[i], m_flow, cp_f)

                # Evaluate outlet fluid temperature
                T_f_out_single[i] = SingleUTube.get_outlet_temperature(T_f_in_single[i], T_b[i], m_flow, cp_f)
            
            if np.min(T_b) < temperature_limit:
                # Configure figure and axes
                fig = gt.utilities._initialize_figure()

                # Plot heat extraction rates
                hours = np.arange(1, Nt+1) * dt / 3600.

                ax2 = fig.add_subplot(212)
                # Axis labels
                ax2.set_xlabel(r'Tid [hours]')
                ax2.set_ylabel(r'Temperatur [degC]')
                gt.utilities._format_axes(ax2)

                # Plot temperatures
                ax2.plot(hours, T_b, 'k-', lw=2, label='Borehullsvegg')
                #ax2.plot(hours, T_f_out_single, '--',label='Til varmepumpe')

                ax2.legend()
                break         
        st.pyplot(plt)
        self.min_temperature = np.min(T_b)
        self.meter = meter
        self.kWh_per_meter = kWh_per_meter  
