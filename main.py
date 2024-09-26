import streamlit as st
import pandas as pd
import plotly.express as px
from scraper import scrape_race_data
from database import (
    init_db,
    create_race,
    get_races,
    archive_race,
    get_archived_races,
    save_lap_times,
    save_positions,
    get_lap_times,
    get_positions,
    get_car_numbers,
    verify_admin,
    create_initial_admin,
    get_admin_by_email,
    remove_race,
    create_driver,
    get_drivers,
    update_driver,
    create_driver_change,
    get_driver_changes,
)
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
from datetime import datetime, timedelta

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info("Initializing database and creating initial admin user")
init_db()
create_initial_admin()

st.set_page_config(
    page_title="Multi-Car Lap Time Tracker",
    page_icon="assets/favicon.svg",
    layout="wide",
)

# Implement live leaderboard functionality
def live_leaderboard(race_id):
    st.subheader("Live Leaderboard")
    
    placeholder = st.empty()
    
    while True:
        # Fetch latest lap times and positions
        lap_times = get_lap_times(race_id)
        positions = get_positions(race_id)
        
        # Process data for leaderboard
        leaderboard_data = []
        for car_number in set([lt.car_number for lt in lap_times] + [p.car_number for p in positions]):
            car_lap_times = [lt for lt in lap_times if lt.car_number == car_number]
            car_positions = [p for p in positions if p.car_number == car_number]
            
            if car_lap_times and car_positions:
                latest_position = car_positions[-1].position
                total_laps = len(car_lap_times)
                total_time = sum([lt.time for lt in car_lap_times])
                avg_lap_time = total_time / total_laps if total_laps > 0 else 0
                
                leaderboard_data.append({
                    "Position": latest_position,
                    "Car Number": car_number,
                    "Total Laps": total_laps,
                    "Avg Lap Time": f"{avg_lap_time:.2f}",
                    "Last Lap Time": f"{car_lap_times[-1].time:.2f}" if car_lap_times else "N/A"
                })
        
        # Sort leaderboard by position
        leaderboard_data.sort(key=lambda x: x["Position"])
        
        # Display leaderboard
        with placeholder.container():
            st.table(pd.DataFrame(leaderboard_data))
        
        # Wait for a short time before updating
        st.experimental_rerun()

# Update the main function to include the live leaderboard
def main():
    st.title("Multi-Car Lap Time Tracker")

    menu = ["Home", "Race Management", "Driver Management", "Admin Login"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.subheader("Home")
        races = get_races()
        if races:
            selected_race = st.selectbox("Select a race", races, format_func=lambda x: x['name'])
            if selected_race:
                st.write(f"Selected race: {selected_race['name']}")
                st.write(f"Date: {selected_race['date']}")
                
                live_leaderboard(selected_race['id'])
        else:
            st.write("No races available. Please create a race in the Race Management section.")

    elif choice == "Race Management":
        race_menu()

    elif choice == "Driver Management":
        driver_menu()

    elif choice == "Admin Login":
        admin_login()

if __name__ == "__main__":
    main()

# Rest of the main.py file remains unchanged
# ...
