import streamlit as st
import time

# Set page config early
st.set_page_config(page_title="ZomatoAI", page_icon="🍽️", layout="wide")

from zomato_ai.preferences import Preference, PriceRange
from zomato_ai.recommendation import get_recommendations
from zomato_ai.llm_orchestrator import generate_llm_recommendations
from zomato_ai.config import get_groq_api_key

st.title("ZomatoAI – Discover Extraordinary Dining 🍽️")
st.write("AI-powered dining recommendations, tailored perfectly to your taste.")

# Check for API key (Streamlit secrets or env)
api_key = get_groq_api_key()
if not api_key and "GROQ_API_KEY" in st.secrets:
    import os
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
    api_key = st.secrets["GROQ_API_KEY"]

if not api_key:
    st.warning("No GROQ_API_KEY found. Recommendations will use fallback responses. Set it in `.env` or Streamlit Secrets.")

with st.sidebar:
    st.header("Your Preferences")
    
    place = st.text_input("Location", placeholder="e.g. Banashankari", value="Banashankari")
    
    col1, col2 = st.columns(2)
    with col1:
        min_price = st.number_input("Min Cost (₹)", min_value=0, value=0, step=100)
    with col2:
        max_price = st.number_input("Max Cost (₹)", min_value=0, value=2000, step=100)
        
    min_rating = st.slider("Min Rating", min_value=0.0, max_value=5.0, value=4.0, step=0.1)
    
    cuisines_input = st.text_input("Cuisines (comma separated)", placeholder="e.g. North Indian, Cafe")
    
    search_clicked = st.button("Discover", type="primary", use_container_width=True)

if search_clicked:
    if not place.strip():
        st.error("Please enter a location.")
    else:
        with st.spinner("Curating top dining spots..."):
            # Prepare preferences
            price_range = None
            if min_price > 0 or max_price > 0:
                price_range = PriceRange(min=min_price, max=max_price if max_price > 0 else 10000)
                
            cuisines = [c.strip() for c in cuisines_input.split(',')] if cuisines_input.strip() else []
            
            pref = Preference(
                place=place.strip(),
                price_range=price_range,
                min_rating=min_rating,
                cuisines=cuisines
            )
            
            # 1. Fetch Candidates from DB
            start = time.time()
            candidates = get_recommendations(pref, limit=20, candidate_limit=200)
            
            if not candidates:
                st.warning(f"No restaurants found matching your criteria in **{place}**.")
            else:
                st.info(f"Found {len(candidates)} candidates. Asking AI to rank the best options...")
                
                # 2. Get LLM feedback
                limit = 6
                final_recs = generate_llm_recommendations(pref, candidates, limit=limit)
                
                elapsed = time.time() - start
                st.success(f"Selected top {len(final_recs)} spots in {elapsed:.2f} seconds!")
                
                # 3. Display Results
                cols = st.columns(3)
                for idx, rec in enumerate(final_recs):
                    col = cols[idx % 3]
                    with col:
                        with st.container(border=True):
                            rating = rec.get("avg_rating", "N/A")
                            rating_str = f"⭐ {rating:.1f}" if isinstance(rating, (int, float)) else "⭐ N/A"
                            
                            st.subheader(f"#{rec.get('rank', idx+1)} {rec.get('name', 'Unknown')}")
                            st.caption(f"📍 {rec.get('location')}  |  {rating_str}")
                            
                            cost = rec.get("avg_cost_for_two")
                            cost_str = f"₹{cost} for 2" if cost else "Price N/A"
                            st.write(f"**Cost:** {cost_str}")
                            
                            cuis_list = rec.get("cuisines", [])
                            if cuis_list:
                                st.write(f"**Cuisines:** {', '.join(cuis_list[:3])}")
                                
                            best_for = rec.get('best_for', [])
                            if best_for:
                                st.write(f"**Best for:** {', '.join(best_for)}")
                                
                            st.info(rec.get("summary_reason", "A great matching dining spot!"))
