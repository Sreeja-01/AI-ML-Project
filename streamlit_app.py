import streamlit as st

home_page= st.Page(
    page="views/home.py",
    title="Home",
    icon=":material/home:",
    default=True,
)
chatbot_page =st.Page(
    page="views/chatbot.py",
    title="CHATBOT",
    icon=":material/smart_toy:",
)

about_page =st.Page(
    page="views/about.py",
    title="About",
    icon=":material/info:",
)

terms_and_conditions_page =st.Page(
    page="views/terms_and_conditions.py",
    title="Terms and Conditions",
    icon=":material/gavel:",
)


privacy_and_policy_page =st.Page(
    page="views/privacy_and_policy.py",
    title="Privacy and Policy",
    icon=":material/lock:",
)

pg= st.navigation(
    {
        "Info": [about_page,privacy_and_policy_page, terms_and_conditions_page],
        "pages": [home_page,chatbot_page],
    }
)
pg.run()