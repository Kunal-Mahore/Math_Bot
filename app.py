import streamlit as st
from google.generativeai import GenerativeModel
import google.generativeai as genai
import numpy as np
import plotly.graph_objects as go
import re
from io import StringIO
from PyPDF2 import PdfReader
import math

# Configure API
api_key = "AIzaSyAyHHb4-p9VJyxx8VahaYwiPNJYKolfZ7s"
genai.configure(api_key=api_key)
model = GenerativeModel("gemini-1.5-pro")

# Streamlit setup
st.set_page_config(page_title="Math Bot", layout="wide")

st.markdown("""
    <style>
    body {
        background-color: white;
    }
    .css-1d391kg {background-color: white;}
    .css-1aumxhk {background-color: white;}
    </style>
""", unsafe_allow_html=True)

st.title("Math Bot")
st.write("Ask me any math question — I can help you solve it!")

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "history" not in st.session_state:
    st.session_state.history = []

# Sidebar
with st.sidebar:
    st.header("Options")
    clear_button = st.button("Clear History")
    history_button = st.button("Show Math History")
    uploaded_pdf = st.file_uploader("Upload a PDF with math problems", type="pdf")
    sidebar_option = st.radio("Choose an option", options=["Math Chatbot", "Scientific Calculator"])

# Helper functions
def display_history():
    st.subheader("Your Math History")
    for i, history_item in enumerate(st.session_state.history, 1):
        st.write(f"{i}. {history_item['problem']} | Solution: {history_item['solution']}")

def plot_graph(equation):
    match = re.search(r'y\s*=\s*(.*)', equation)
    if not match:
        st.warning("Please provide a valid mathematical expression (e.g., 'y = x^2').")
        return

    math_expression = match.group(1)
    invalid_chars = re.findall(r'[^0-9\+\-\*/\^x\(\)\.\ ]', math_expression)
    if invalid_chars:
        st.warning(f"Invalid characters detected: {', '.join(invalid_chars)}")
        return

    try:
        x = np.linspace(-10, 10, 400)
        y = eval(math_expression.replace("^", "**"))
        fig = go.Figure(data=go.Scatter(x=x, y=y, mode='lines', name=math_expression))
        fig.update_layout(title=f"Graph of {math_expression}", xaxis_title="x", yaxis_title="y")
        st.plotly_chart(fig)
    except Exception as e:
        st.warning(f"Error plotting the graph: {e}")

def save_to_history(problem, solution):
    st.session_state.history.append({"problem": problem, "solution": solution})

def extract_pdf_text(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# PDF Extraction
if uploaded_pdf is not None:
    pdf_text = extract_pdf_text(uploaded_pdf)
    st.sidebar.text_area("Extracted PDF Text", pdf_text, height=300)

# After extracting PDF text
if uploaded_pdf is not None:
    pdf_text = extract_pdf_text(uploaded_pdf)
    st.sidebar.text_area("Extracted PDF Text", pdf_text, height=300)

    if pdf_text.strip():  # If there's some text extracted
        st.subheader("Solving problems from uploaded PDF...")
        with st.spinner("Thinking..."):
            try:
                math_prompt = (
                    "You are a helpful and strict math tutor. Only answer math-related questions. "
                    "Solve all the following problems extracted from a PDF. "
                    "Format all math properly using LaTeX inside $$...$$."
                )
                full_prompt = f"{math_prompt}\n\nExtracted Problems:\n{pdf_text}"
                response = model.generate_content(full_prompt)
                reply = response.text
                st.markdown(reply, unsafe_allow_html=True)
                save_to_history("Problems from PDF", reply)
            except Exception as e:
                st.error(f"Sorry, couldn't solve the problems. Error: {str(e)}")


# Clear History
if clear_button:
    st.session_state.messages = []
    st.session_state.history = []
    st.success("History cleared!")

# Main App Logic
if sidebar_option == "Math Chatbot":
    user_query = st.chat_input("Enter your math question here...")

    if user_query:
        with st.chat_message("user"):
            st.markdown(user_query)
        st.session_state.messages.append({"role": "user", "content": user_query})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    math_prompt = (
                        "You are a helpful and strict math tutor. Only answer math-related questions. "
                        "If the user asks anything else, respond: 'I can only help with math problems!'"
                    )
                    full_prompt = f"{math_prompt}\nUser: {user_query}"
                    response = model.generate_content(full_prompt)
                    reply = response.text
                except Exception as e:
                    reply = f"Sorry, I couldn't solve that. Error: {str(e)}"

            st.markdown(reply, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            save_to_history(user_query, reply)

            if "plot" in user_query.lower() or "graph" in user_query.lower():
                plot_graph(user_query)

    if history_button:
        display_history()

elif sidebar_option == "Scientific Calculator":
    st.subheader("Scientific Calculator")
    calc_input = st.text_input("Enter expression:", "", help="Use functions like sin, cos, log, sqrt, etc.")
    calc_result = None

    if calc_input:
        try:
            calc_result = eval(calc_input, {"__builtins__": None}, {
                'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
                'log': math.log, 'sqrt': math.sqrt, 'pi': math.pi, 'e': math.e,
                'exp': math.exp, 'log10': math.log10
            })
        except Exception as e:
            calc_result = f"Error: {str(e)}"

    if calc_result is not None:
        st.write(f"Result: {calc_result}")
