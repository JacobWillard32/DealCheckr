import streamlit as st
import openai

# ---------------------- Sidebar Inputs ----------------------
st.title("📊 DealCheckr: Rental & Flip Analyzer")

# Select deal type
deal_type = st.sidebar.radio("Deal Type", ["Rental", "Flip", "Both"])
recommend_strategy = st.sidebar.checkbox("Let AI recommend best strategy?")

# Basic inputs
purchase_price = st.sidebar.number_input("Purchase Price ($)", value=250000)
rehab_cost = st.sidebar.number_input("Rehab Cost ($)", value=30000)
arv = st.sidebar.number_input("After Repair Value (ARV) ($)", value=350000)
monthly_rent = st.sidebar.number_input("Monthly Rent Estimate ($)", value=1800)
annual_taxes = st.sidebar.number_input("Annual Property Taxes ($)", value=3500)
units = st.sidebar.number_input("Number of Units", value=1)

# Property insurance (0.8% of purchase price default)
default_insurance = round(purchase_price * 0.008)
annual_insurance = st.sidebar.number_input("Annual Property Insurance ($)", value=default_insurance, step=50)

# ---------------------- Deal Analysis Function ----------------------
def analyze_deal(purchase_price, rehab_cost, arv, monthly_rent, annual_taxes, units, annual_insurance, deal_type):
    down_payment_pct = 0.20
    interest_rate = 0.075
    loan_term_years = 30
    opex_per_unit = 150 * 12

    loan_amount = purchase_price * (1 - down_payment_pct)
    monthly_mortgage = loan_amount * (interest_rate / 12) / (1 - (1 + interest_rate / 12) ** (-loan_term_years * 12))
    annual_mortgage = monthly_mortgage * 12

    results = {}

    if deal_type in ["Rental", "Both"]:
        gross_annual_rent = monthly_rent * 12 * units
        annual_opex = opex_per_unit * units
        total_expenses = annual_taxes + annual_insurance + annual_opex
        noi = gross_annual_rent - total_expenses
        cap_rate = (noi / purchase_price) * 100
        dscr = noi / annual_mortgage
        coc_return = (noi - annual_mortgage) / (purchase_price * down_payment_pct) * 100

        results.update({
            "Cap Rate": round(cap_rate, 2),
            "DSCR": round(dscr, 2),
            "CoC Return": round(coc_return, 2),
            "NOI": round(noi, 2),
        })

    if deal_type in ["Flip", "Both"]:
        flip_profit = arv - purchase_price - rehab_cost - (arv * 0.08)
        flip_roi = (flip_profit / (purchase_price + rehab_cost)) * 100

        results.update({
            "Flip Profit": round(flip_profit, 2),
            "Flip ROI": round(flip_roi, 2),
        })

    results.update({
        "Annual Mortgage": round(annual_mortgage, 2),
        "Monthly Mortgage": round(monthly_mortgage, 2),
    })

    return results

# ---------------------- Run Analysis ----------------------
if st.sidebar.button("Run Analysis"):
    results = analyze_deal(
        purchase_price, rehab_cost, arv, monthly_rent,
        annual_taxes, units, annual_insurance, deal_type
    )

    st.subheader("📈 Deal Analysis Results")
    for key, value in results.items():
        st.write(f"**{key}:** ${value:,.2f}" if "Mortgage" in key or "NOI" in key else f"**{key}:** {value}%")

    # ---------------------- GPT-4 Investment Summary ----------------------
    prompt = f"""
    You are a real estate investment analyst AI.

    Analyze the following deal metrics and generate a summary with:
    - Strengths and weaknesses
    - Red flags
    - Suggestions to improve the deal
    - Score from A+ to F
    {"- Recommend whether this should be a rental, flip, or both based on ROI and DSCR." if recommend_strategy else ""}

    Deal:
    - Purchase Price: ${purchase_price}
    - Monthly Rent: ${monthly_rent}
    - Annual Taxes: ${annual_taxes}
    - Units: {units}
    - Cap Rate: {results.get('Cap Rate', 'N/A')}%
    - DSCR: {results.get('DSCR', 'N/A')}
    - CoC Return: {results.get('CoC Return', 'N/A')}%
    - Flip ROI: {results.get('Flip ROI', 'N/A')}%
    """

    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    with st.spinner("Generating AI insight..."):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a real estate investment analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )
            st.subheader("🤖 AI Investment Summary")
            st.markdown(response.choices[0].message.content)
        except Exception as e:
            st.error(f"Error calling OpenAI: {e}")



