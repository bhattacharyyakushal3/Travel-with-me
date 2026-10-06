# ============================================================
# INDIA TOURIST PLANNER
# STREAMLIT FRONTEND - SERVER BASED VERSION
# Developed by Dr. Kushal Bhattacharyya
# ============================================================

import streamlit as st

from backend import (
    get_destination,
    create_itinerary,
    calculate_estimated_cost
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="India Tourist Planner By Dr. Kushal Bhattacharyya",
    page_icon="🇮🇳",
    layout="wide"
)


# ============================================================
# HEADER
# ============================================================

st.title(
    "🇮🇳 India Tourist Planner"
)

st.subheader(
    "By Dr. Kushal Bhattacharyya"
)

st.write(
    "Plan your trip to destinations across India using "
    "online geographic and tourist-location data."
)

st.divider()


# ============================================================
# INITIAL SESSION STATE
# ============================================================

if "destination_data" not in st.session_state:

    st.session_state.destination_data = None


if "searched_destination" not in st.session_state:

    st.session_state.searched_destination = ""


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header(
    "⚙️ Trip Settings"
)


# ============================================================
# TRAVELLER NAME
# ============================================================

name = st.sidebar.text_input(
    "Traveller Name",
    value="",
    placeholder="Enter traveller name"
)


# ============================================================
# NUMBER OF ADULTS
# ============================================================

adults = st.sidebar.number_input(
    "Number of Adults",
    min_value=1,
    max_value=50,
    value=2,
    step=1
)


# ============================================================
# NUMBER OF CHILDREN
# ============================================================

children = st.sidebar.number_input(
    "Number of Children",
    min_value=0,
    max_value=50,
    value=0,
    step=1
)


# ============================================================
# NUMBER OF DAYS
# ============================================================

days = st.sidebar.number_input(
    "Number of Days",
    min_value=1,
    max_value=30,
    value=3,
    step=1
)


# ============================================================
# BUDGET CATEGORY
# ============================================================

budget = st.sidebar.selectbox(
    "Budget Category",
    [
        "Budget",
        "Standard",
        "Premium"
    ]
)


# ============================================================
# DESTINATION SEARCH
# ============================================================

st.header(
    "📍 Search Tourist Destination"
)

st.write(
    "Enter any tourist destination in India. "
    "The application will retrieve location and "
    "tourist-attraction information from online servers."
)


destination = st.text_input(
    "Enter Destination",
    value=st.session_state.searched_destination,
    placeholder="Example: Darjeeling, Jaipur, Goa, Kolkata, Delhi"
)


# ============================================================
# SEARCH BUTTON
# ============================================================

search_destination = st.button(
    "🔎 Search Destination",
    use_container_width=True
)


# ============================================================
# FETCH DESTINATION DATA
# ============================================================

if search_destination:

    if not destination.strip():

        st.warning(
            "Please enter a tourist destination."
        )

        st.session_state.destination_data = None

    else:

        with st.spinner(
            "Fetching destination information from online servers..."
        ):

            destination_data = get_destination(
                destination.strip()
            )


        if destination_data is None:

            st.error(
                "Unable to find this destination. "
                "Please check the spelling and try again."
            )

            st.session_state.destination_data = None

        else:

            st.session_state.destination_data = (
                destination_data
            )

            st.session_state.searched_destination = (
                destination.strip()
            )

            st.success(
                "Destination information retrieved successfully!"
            )


# ============================================================
# DISPLAY DESTINATION DATA
# ============================================================

destination_data = (
    st.session_state.destination_data
)


if destination_data is not None:

    # ========================================================
    # DESTINATION INFORMATION
    # ========================================================

    st.divider()

    st.header(
        "📌 Destination Information"
    )


    col1, col2, col3 = st.columns(3)


    # --------------------------------------------------------
    # DESTINATION
    # --------------------------------------------------------

    with col1:

        st.metric(
            "Destination",
            destination_data["name"]
        )


    # --------------------------------------------------------
    # STATE
    # --------------------------------------------------------

    with col2:

        st.metric(
            "State / UT",
            destination_data["state"]
        )


    # --------------------------------------------------------
    # RECOMMENDED DAYS
    # --------------------------------------------------------

    with col3:

        st.metric(
            "Recommended Days",
            destination_data["recommended_days"]
        )


    # ========================================================
    # DESCRIPTION
    # ========================================================

    st.info(
        destination_data["description"]
    )


    # ========================================================
    # LOCATION INFORMATION
    # ========================================================

    with st.expander(
        "🌐 Location Information"
    ):

        col1, col2 = st.columns(2)


        with col1:

            st.write(
                "**Latitude:**"
            )

            st.write(
                destination_data["latitude"]
            )


        with col2:

            st.write(
                "**Longitude:**"
            )

            st.write(
                destination_data["longitude"]
            )


    # ========================================================
    # TOURIST ATTRACTIONS
    # ========================================================

    st.subheader(
        "🏛️ Tourist Attractions"
    )


    places = destination_data.get(
        "places",
        []
    )


    if not places:

        st.warning(
            "No tourist attractions were found "
            "from the online server."
        )

    else:

        st.write(
            f"Found {len(places)} tourist attraction(s)."
        )


        for number, place in enumerate(
            places,
            start=1
        ):

            with st.expander(
                f"📌 {number}. {place['name']}"
            ):

                col1, col2, col3 = st.columns(3)


                # ------------------------------------------------
                # ACTIVITY
                # ------------------------------------------------

                with col1:

                    st.write(
                        "**Activity:**"
                    )

                    st.write(
                        place["activity"]
                    )


                # ------------------------------------------------
                # DURATION
                # ------------------------------------------------

                with col2:

                    st.write(
                        "**Suggested Duration:**"
                    )

                    st.write(
                        place["duration"]
                    )


                # ------------------------------------------------
                # ENTRY COST
                # ------------------------------------------------

                with col3:

                    st.write(
                        "**Entry Cost:**"
                    )

                    if place["entry_cost"] > 0:

                        st.write(
                            f"₹{place['entry_cost']}"
                        )

                    else:

                        st.write(
                            "Not available online"
                        )


    # ========================================================
    # NEARBY HOTELS / GUEST HOUSES / HOME STAYS
    # ========================================================

    st.divider()

    st.subheader(
        "🏨 Nearby Hotels / Guest Houses / Home Stays"
    )

    accommodations = destination_data.get(
        "accommodations",
        []
    )

    if not accommodations:
        st.warning(
            "No accommodation records were returned by the online "
            "geographic server for this destination."
        )
    else:
        contact_count = sum(
            1 for item in accommodations
            if item.get("contact_available")
        )

        st.write(
            f"Found {len(accommodations)} nearby accommodation option(s). "
            f"{contact_count} have a phone, website or email listed."
        )

        # Show at least three choices whenever the backend has them.
        for number, hotel in enumerate(
            accommodations[:max(3, min(10, len(accommodations)))],
            start=1
        ):
            title = (
                f"🏨 {number}. {hotel['name']} "
                f"({hotel.get('type', 'Accommodation')})"
            )

            with st.expander(title):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write("**Distance from destination:**")
                    st.write(
                        f"{hotel.get('distance_km', '?')} km"
                    )

                with col2:
                    st.write("**Contact:**")
                    contact = hotel.get("contact", "")

                    if contact:
                        if hotel.get("contact_type") == "Website":
                            st.markdown(
                                f"[Open website]({contact})"
                            )
                        else:
                            st.write(contact)
                    else:
                        st.write(
                            "No direct phone/website/email listed"
                        )

                with col3:
                    st.write("**Address:**")
                    st.write(
                        hotel.get("address")
                        or "Address not listed online"
                    )

                if hotel.get("phone"):
                    st.write(
                        f"📞 **Phone:** {hotel['phone']}"
                    )

                if hotel.get("email"):
                    st.write(
                        f"✉️ **Email:** {hotel['email']}"
                    )

                if hotel.get("website"):
                    st.write(
                        f"🌐 **Website:** {hotel['website']}"
                    )

        st.info(
            "Accommodation is selected from online geographic data. "
            "Please confirm availability, current rates and contact "
            "details directly before booking."
        )


    # ========================================================
    # GENERATE TOUR PLAN
    # ========================================================

    st.divider()

    st.header(
        "🗓️ Generate Tour Plan"
    )


    st.write(
        "Use the trip settings in the left sidebar "
        "to generate your itinerary."
    )


    generate_plan = st.button(
        "🚀 Generate Tour Plan",
        use_container_width=True
    )


    # ========================================================
    # GENERATE ITINERARY
    # ========================================================

    if generate_plan:

        # ----------------------------------------------------
        # Default traveller name
        # ----------------------------------------------------

        traveller_name = name.strip()


        if not traveller_name:

            traveller_name = "Guest Traveller"


        # ----------------------------------------------------
        # Get destination name
        # ----------------------------------------------------

        selected_destination = (
            destination_data["name"]
        )


        # ----------------------------------------------------
        # Create itinerary
        # ----------------------------------------------------

        with st.spinner(
            "Creating your personalised tour plan..."
        ):

            itinerary = create_itinerary(
                selected_destination,
                days,
                adults,
                children
            )


        # ----------------------------------------------------
        # Calculate cost
        # ----------------------------------------------------

        estimated_cost = calculate_estimated_cost(
            selected_destination,
            days,
            adults,
            children,
            budget
        )


        # ====================================================
        # SUCCESS MESSAGE
        # ====================================================

        st.success(
            "Tour plan generated successfully!"
        )


        # ====================================================
        # TRIP SUMMARY
        # ====================================================

        st.subheader(
            "👤 Trip Summary"
        )


        col1, col2, col3, col4, col5 = st.columns(5)


        # ----------------------------------------------------
        # TRAVELLER
        # ----------------------------------------------------

        with col1:

            st.write(
                "**Traveller**"
            )

            st.write(
                traveller_name
            )


        # ----------------------------------------------------
        # DESTINATION
        # ----------------------------------------------------

        with col2:

            st.write(
                "**Destination**"
            )

            st.write(
                selected_destination
            )


        # ----------------------------------------------------
        # ADULTS
        # ----------------------------------------------------

        with col3:

            st.write(
                "**Adults**"
            )

            st.write(
                adults
            )


        # ----------------------------------------------------
        # CHILDREN
        # ----------------------------------------------------

        with col4:

            st.write(
                "**Children**"
            )

            st.write(
                children
            )


        # ----------------------------------------------------
        # DAYS
        # ----------------------------------------------------

        with col5:

            st.write(
                "**Days**"
            )

            st.write(
                days
            )


        # ====================================================
        # BUDGET
        # ====================================================

        st.subheader(
            "💳 Selected Budget"
        )


        col1, col2 = st.columns(2)


        with col1:

            st.metric(
                "Budget Category",
                budget
            )


        with col2:

            st.metric(
                "Estimated Trip Cost",
                f"₹{estimated_cost:,}"
            )


        st.caption(
            "The estimated cost is an approximate local-trip "
            "estimate based on the selected budget category. "
            "Flights, trains and other long-distance "
            "transportation are not included."
        )


        # ====================================================
        # DAILY ITINERARY
        # ====================================================

        st.subheader(
            "🗓️ Daily Itinerary"
        )


        if not itinerary:

            st.warning(
                "Unable to create an itinerary because "
                "no tourist attractions were returned "
                "from the server."
            )

        else:

            for day_plan in itinerary:

                st.markdown(
                    f"### Day {day_plan['day']} — "
                    f"{day_plan['theme']}"
                )


                for place in day_plan["places"]:

                    st.write(
                        f"📍 **{place['name']}**"
                    )


                    st.write(
                        f"**Activity:** "
                        f"{place['activity']}"
                    )


                    st.write(
                        f"**Duration:** "
                        f"{place['duration']}"
                    )


                    if place["entry_cost"] > 0:

                        st.write(
                            f"**Entry Cost:** "
                            f"₹{place['entry_cost']}"
                        )

                    else:

                        st.write(
                            "**Entry Cost:** "
                            "Not available online"
                        )


                # ------------------------------------------------
                # NEAREST ACCOMMODATION FOR THIS DAY
                # ------------------------------------------------

                accommodation = day_plan.get(
                    "accommodation"
                )

                st.markdown(
                    "#### 🏨 Recommended Stay Near Today's Places"
                )

                if accommodation:

                    st.write(
                        f"**{accommodation['name']}** "
                        f"({accommodation.get('type', 'Accommodation')})"
                    )

                    st.write(
                        f"**Distance from destination:** "
                        f"{accommodation.get('distance_km', '?')} km"
                    )

                    if accommodation.get("phone"):
                        st.write(
                            f"📞 **Phone:** "
                            f"{accommodation['phone']}"
                        )

                    if accommodation.get("email"):
                        st.write(
                            f"✉️ **Email:** "
                            f"{accommodation['email']}"
                        )

                    if accommodation.get("website"):
                        st.markdown(
                            f"🌐 **Website:** "
                            f"[{accommodation['website']}]"
                            f"({accommodation['website']})"
                        )

                    if accommodation.get("address"):
                        st.write(
                            f"📍 **Address:** "
                            f"{accommodation['address']}"
                        )

                    if not accommodation.get("contact_available"):
                        st.caption(
                            "No direct phone, website or email was "
                            "listed in the online geographic data. "
                            "Please verify before booking."
                        )

                else:

                    st.warning(
                        "No nearby accommodation with contact "
                        "information was found for this day's places."
                    )


                st.divider()


        # ====================================================
        # TRAVEL TIPS
        # ====================================================

        st.subheader(
            "💡 Travel Tips"
        )


        tips = destination_data.get(
            "tips",
            []
        )


        for tip in tips:

            st.write(
                f"✅ {tip}"
            )


# ============================================================
# INFORMATION WHEN NO DESTINATION IS SEARCHED
# ============================================================

else:

    st.info(
        "👆 Enter a destination above and click "
        "'Search Destination' to retrieve live "
        "destination information."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🇮🇳 India Tourist Planner | "
    "Developed using Python and Streamlit | "
    "By Dr. Kushal Bhattacharyya"
)