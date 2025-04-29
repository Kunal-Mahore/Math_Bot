import streamlit as st
from google.generativeai import GenerativeModel
import google.generativeai as genai
import numpy as np
import plotly.graph_objects as go
import re
from io import StringIO
from PyPDF2 import PdfReader
import math
from PIL import Image

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
    uploaded_image = st.file_uploader("Upload an image with a math problem", type=["jpg", "jpeg", "png"])
    sidebar_option = st.radio("Choose an option", options=["Math Chatbot", "Scientific Calculator", "Graph Plotter"])

# Helper Functions
def display_history():
    st.subheader("Your Math History")
    for i, history_item in enumerate(st.session_state.history, 1):
        st.write(f"{i}. {history_item['problem']} | Solution: {history_item['solution']}")

def plot_graph(equation):
    match = re.search(r'y\s*=\s*(.*)', equation)
    if not match:
        st.warning("Please provide a valid equation (e.g., 'y = x^2').")
        return

    math_expression = match.group(1).replace("^", "**")
    x = np.linspace(-10, 10, 400)

    allowed_names = {
        "x": x,
        "sin": np.sin,
        "cos": np.cos,
        "tan": np.tan,
        "log": np.log,
        "sqrt": np.sqrt,
        "exp": np.exp,
        "abs": np.abs,
        "pi": np.pi,
        "e": np.e
    }

    try:
        y = eval(math_expression, {"__builtins__": {}}, allowed_names)
        fig = go.Figure(data=go.Scatter(x=x, y=y, mode='lines'))
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

# Process uploaded PDF
if uploaded_pdf is not None:
    pdf_text = extract_pdf_text(uploaded_pdf)
    st.sidebar.text_area("Extracted PDF Text", pdf_text, height=300)

    if pdf_text.strip():
        st.subheader("Solving problems from uploaded PDF...")
        with st.spinner("Thinking..."):
            try:
                math_prompt = (
                    "You are a helpful and strict math tutor. Only answer math-related questions. "
                    "Solve all the following problems extracted from a PDF. "
                    "Mention each step clearly."
                    "For multi-step problems, provide the steps in a structured format or table"
                    "Format all math properly using LaTeX inside $$...$$."
                )
                full_prompt = f"{math_prompt}\n\nExtracted Problems:\n{pdf_text}"
                response = model.generate_content(full_prompt)
                reply = response.text
                st.markdown(reply, unsafe_allow_html=True)
                save_to_history("Problems from PDF", reply)
            except Exception as e:
                st.error(f"Sorry, couldn't solve the problems. Error: {str(e)}")

# Process uploaded image
if uploaded_image is not None:
    st.subheader("Solving problem from uploaded image...")
    with st.spinner("Thinking..."):
        try:
            image = Image.open(uploaded_image)
            response = model.generate_content([
                "You are a strict math tutor. Read the math problem from this image and solve it in detail. Mention each step clearly.use simple representation format like tables etc where needed. Use LaTeX formatting for equations inside $$...$$.",
                image
            ])
            reply = response.text
            st.markdown(reply, unsafe_allow_html=True)
            save_to_history("Image problem", reply)
        except Exception as e:
            st.error(f"Couldn't process the image. Error: {str(e)}")

# Clear History
if clear_button:
    st.session_state.messages = []
    st.session_state.history = []
    st.success("History cleared!")

# App Logic
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
                        "For multi-step problems, provide the steps in a structured format or table, and use LaTeX formatting for equations inside $$...$$."
                    )
                    full_prompt = f"{math_prompt}\nUser: {user_query}"
                    response = model.generate_content(full_prompt)
                    reply = response.text
                except Exception as e:
                    reply = f"Sorry, I couldn't solve that. Error: {str(e)}"

            st.markdown(reply, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            save_to_history(user_query, reply)

elif sidebar_option == "Scientific Calculator":
    st.subheader("Scientific Calculator")
    calc_input = st.text_input("Enter expression:(e.g.,e**2)", "", help="Use functions like sin, cos, log, sqrt, etc.")
    calc_result = None

    if calc_input:
        try:
            calc_result = eval(calc_input, {"__builtins__": None}, {
                'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
                'log': math.log, 'sqrt': math.sqrt, 'pi': math.pi, 'e': math.e,
                'exp': math.exp, 'log10': math.log10
            })
        except Exception as e:
            calc_result = f"Error: use the correct format."

    if calc_result is not None:
        st.write(f"Result: {calc_result}")

elif sidebar_option == "Graph Plotter":
    st.subheader("Graph Plotter")
    equation_input = st.text_input("Enter equation (e.g., y = x^2):")
    plot_button = st.button("Plot Graph")

    if plot_button and equation_input:
        plot_graph(equation_input)

# Show history if requested
if history_button:
    display_history()
