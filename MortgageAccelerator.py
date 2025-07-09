import streamlit as st
import math
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Mortgage Accelerator", layout="centered")
st.markdown("<h5 style='text-align:center; margin-top:-40px;'>Mortgage Calculator Maximizer</h5>", unsafe_allow_html=True)

# --- Tabs for Navigation ---
tabs = st.tabs(["📊 Calculator", "📅 Amortization Schedule"])

with tabs[0]:
    with st.expander("⚙️ Advanced Options", expanded=False):
        col_adv1, col_adv2 = st.columns(2)
    with col_adv1:
        lock_payment = st.checkbox("Lock Payment Amount", value=False)
    with col_adv2:
        lock_frequency = st.checkbox("Lock Payment Frequency", value=False, disabled=lock_payment)
    if lock_frequency:
        lock_payment = False

    # --- Inputs ---
    with st.container():
        st.markdown("<h6>Loan Parameters</h6>", unsafe_allow_html=True)
        col1, col2, col_summary = st.columns([1, 1, 1.2])

        with col1:
            home_price = st.number_input("Home Price ($)", min_value=0.0, value=500000.0, step=1000.0)
            down_percent = st.slider("Down Payment (%)", 0.0, 100.0, value=20.0, step=0.1)
            if lock_payment:
                loan_term_years = st.number_input("Loan Term (Years)", min_value=1, max_value=50, value=30, disabled=True)
            else:
                loan_term_years = st.number_input("Loan Term (Years)", min_value=1, max_value=50, value=30)
            interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=25.0, value=3.0, step=0.001, format="%.3f")

        with col2:
            freq_options = ["Monthly", "Bi-Weekly", "Weekly", "Every X Days"]
            payment_frequency = st.selectbox("Payment Frequency", freq_options)
            if payment_frequency == "Every X Days":
                custom_days = st.number_input("Custom Days", min_value=1, max_value=365, value=30)
            else:
                custom_days = 30
            user_payment = st.number_input("Your Desired Base Payment ($)", min_value=0.0, value=0.0, key='user_payment') if lock_payment else None

    

    with st.container():
        st.markdown("<h6>Taxes & Extras</h6>", unsafe_allow_html=True)
        col3, col4 = st.columns(2)

        with col3:
            property_tax_percent = st.number_input("Property Tax (%)", min_value=0.0, value=1.2)
            hoa = st.number_input("HOA ($/month)", min_value=0.0, value=0.0)
            insurance = st.number_input("Home Insurance ($/year)", min_value=0.0, value=1200.0)

        with col4:
            pmi_percent = st.number_input("PMI (%)", min_value=0.0, value=0.0)
            extra_payment = st.number_input("Extra Payment ($)", min_value=0.0, value=0.0)
            extra_freq = st.selectbox("Extra Payment Frequency", freq_options)
            if extra_freq == "Every X Days":
                extra_custom_days = st.number_input("Extra Payment Custom Days", min_value=1, max_value=365, value=30)
            else:
                extra_custom_days = 30
            

# --- Computation ---
down_payment = home_price * (down_percent / 100)
loan_amount = home_price - down_payment
annual_rate = interest_rate / 100

if payment_frequency == "Monthly":
    payments_per_year = 12
    frequency_label = "Monthly"
elif payment_frequency == "Bi-Weekly":
    payments_per_year = 26
    frequency_label = "Bi-Weekly"
elif payment_frequency == "Weekly":
    payments_per_year = 52
    frequency_label = "Weekly"
elif payment_frequency == "Every X Days":
    payments_per_year = 365 / custom_days if custom_days > 0 else 12
    frequency_label = f"Every {custom_days} Days"
else:
    payments_per_year = 12
    frequency_label = "Monthly"
    payments_per_year = 365 / custom_days

period_rate = annual_rate / payments_per_year if annual_rate > 0 else 0

if lock_payment and user_payment and user_payment > 0:
    def calculate_term(P, r, A):
        if r == 0:
            return P / A
        n = math.log(A / (A - r * P)) / math.log(1 + r)
        return n

    total_payments = int(calculate_term(loan_amount, period_rate, user_payment))
    payment = user_payment
    loan_term_years = total_payments / payments_per_year

elif lock_frequency:
    # Recalculate frequency instead of term
    if loan_term_years > 0:
        total_payments = int(loan_term_years * payments_per_year)
        if period_rate > 0:
            payment = loan_amount * (period_rate * (1 + period_rate) ** total_payments) / ((1 + period_rate) ** total_payments - 1)
        else:
            payment = loan_amount / total_payments
    else:
        total_payments = 0
        payment = 0
else:
    total_payments = int(loan_term_years * payments_per_year)
    if period_rate > 0:
        payment = loan_amount * (period_rate * (1 + period_rate) ** total_payments) / ((1 + period_rate) ** total_payments - 1)
    else:
        payment = loan_amount / total_payments

# Costs per period
tax_per_period = (home_price * property_tax_percent / 100) / payments_per_year
insurance_per_period = insurance / payments_per_year
hoa_per_period = hoa * 12 / payments_per_year
pmi_per_period = (loan_amount * pmi_percent / 100) / payments_per_year

# Adjust extra payments
if extra_freq == "Monthly":
    extra_per_period = (extra_payment * 12) / payments_per_year
elif extra_freq == "Bi-Weekly":
    extra_per_period = (extra_payment * 26) / payments_per_year
elif extra_freq == "Weekly":
    extra_per_period = (extra_payment * 52) / payments_per_year
elif extra_freq == "Every X Days":
    extra_payments_per_year = 365 / extra_custom_days if extra_custom_days and extra_custom_days > 0 else 0
    extra_per_period = (extra_payment * extra_payments_per_year) / payments_per_year
else:
    extra_per_period = extra_payment

total_payment = payment + tax_per_period + insurance_per_period + hoa_per_period + pmi_per_period + extra_per_period

# Amortization Table with Extra Payments
from datetime import date, timedelta
start_date = date.today()
payment_interval_days = int(365 / payments_per_year)
balance = loan_amount
schedule = []
payment_dates = []
interest_paid = 0
months_saved = 0
for i in range(1, total_payments + 1):
    payment_date = start_date + timedelta(days=(i - 1) * payment_interval_days)
    payment_dates.append(payment_date)
    interest = balance * period_rate
    principal = payment - interest
    total_principal = principal + extra_per_period
    balance -= total_principal
    interest_paid += interest
    schedule.append((i, balance if balance > 0 else 0, interest_paid))
    if balance <= 0:
        months_saved = total_payments - i
        break

schedule_df = pd.DataFrame(schedule, columns=["Payment #", "Remaining Balance", "Cumulative Interest"])
schedule_df.insert(1, "Payment Date", payment_dates)

with col_summary:
    summary_html = (
        f"<div style='padding:10px; background:#e5fbe5; border-radius:10px; margin-top:10px;'>"
        f"<h6 style='margin-bottom:5px;'>Summary</h6>"
        f"<p style='margin:0'>"
        f"Loan: <b>${loan_amount:,.0f}</b><br>"
        f"Down Payment: <b>${down_payment:,.0f}</b><br>"
        f"Payment/Period: <b style='color:red;'>${payment:,.2f}</b>"
        f"</p></div>"
    )
    st.markdown(summary_html, unsafe_allow_html=True)

# --- Output ---
with tabs[0]:
    st.markdown("---")
    st.markdown("<h6>Summary</h6>", unsafe_allow_html=True)
    st.write(f"**Loan Amount:** ${loan_amount:,.2f}")
    st.write(f"**Down Payment:** ${down_payment:,.2f}")
    st.write(f"**Start Date:** {start_date.strftime('%b %d, %Y')}")
    st.write(f"**End Date:** {payment_dates[-1].strftime('%b %d, %Y') if payment_dates else 'N/A'}")
    st.write(f"**Base Payment per Period:** ${payment:,.2f}")
    st.markdown(f"**Total Payment per {frequency_label} (Incl. Taxes & Extras):** <span style='color:red;'>${total_payment:,.2f}</span>", unsafe_allow_html=True)
    if extra_payment > 0:
        st.write(f"**Time Saved by Extra Payments:** {months_saved/payments_per_year:.2f} years")
        st.write(f"**Interest Saved:** ${schedule_df['Cumulative Interest'].iloc[-1]:,.2f}")
    if lock_payment:
        st.write(f"**Calculated Loan Term for Desired Payment:** {loan_term_years:.2f} years")

# --- Amortization Tab ---
with tabs[1]:
    st.markdown("<h6>Amortization Schedule</h6>", unsafe_allow_html=True)
    fig, ax = plt.subplots()
    ax.plot(schedule_df["Payment #"], schedule_df["Remaining Balance"], label="Remaining Balance")
    ax.set_xlabel("Payment Number")
    ax.set_ylabel("Balance ($)")
    ax.set_title("Loan Balance Over Time")
    ax.grid(True)
    st.pyplot(fig)
    st.dataframe(schedule_df.head(50))
    csv = schedule_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Full Schedule as CSV", data=csv, file_name="amortization_schedule.csv", mime="text/csv")

