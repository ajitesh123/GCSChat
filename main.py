import re
import warnings

import streamlit as st
from snowflake.snowpark.exceptions import SnowparkSQLException

from chain import load_chain

# from utils.snow_connect import SnowflakeConnection
from utils.snowchat_ui import StreamlitUICallbackHandler, message_func
from utils.snowddl import Snowddl

warnings.filterwarnings("ignore")
chat_history = []
snow_ddl = Snowddl()

st.title("snowChat")
st.caption("Talk your way through data")
model = st.radio(
    "",
    options=["✨ GPT-3.5", "♾️ codellama", "⛰️ Mixtral"],
    index=0,
    horizontal=True,
)
st.session_state["model"] = model

INITIAL_MESSAGE = [
    {"role": "user", "content": "Hi!"},
    {
        "role": "assistant",
        "content": "Hey there, I'm Chatty McQueryFace, your SQL-speaking sidekick, ready to chat up Snowflake and fetch answers faster than a snowball fight in summer! ❄️🔍",
    },
]

with open("ui/sidebar.md", "r") as sidebar_file:
    sidebar_content = sidebar_file.read()

with open("ui/styles.md", "r") as styles_file:
    styles_content = styles_file.read()

# Display the DDL for the selected table
st.sidebar.markdown(sidebar_content)

# Create a sidebar with a dropdown menu
selected_table = st.sidebar.selectbox(
    "Select a table:", options=list(snow_ddl.ddl_dict.keys())
)
st.sidebar.markdown(f"### DDL for {selected_table} table")
st.sidebar.code(snow_ddl.ddl_dict[selected_table], language="sql")

# Add a reset button
if st.sidebar.button("Reset Chat"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.session_state["messages"] = INITIAL_MESSAGE
    st.session_state["history"] = []

st.sidebar.markdown(
    "**Note:** <span style='color:red'>The snowflake data retrieval is disabled for now.</span>",
    unsafe_allow_html=True,
)

st.write(styles_content, unsafe_allow_html=True)

# Initialize the chat messages history
if "messages" not in st.session_state.keys():
    st.session_state["messages"] = INITIAL_MESSAGE

if "history" not in st.session_state:
    st.session_state["history"] = []

if "model" not in st.session_state:
    st.session_state["model"] = model

# Prompt for user input and save
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages:
    message_func(
        message["content"],
        True if message["role"] == "user" else False,
        True if message["role"] == "data" else False,
    )

callback_handler = StreamlitUICallbackHandler()

chain = load_chain(st.session_state["model"], callback_handler)


def append_chat_history(question, answer):
    st.session_state["history"].append((question, answer))


def get_sql(text):
    sql_match = re.search(r"```sql\n(.*)\n```", text, re.DOTALL)
    return sql_match.group(1) if sql_match else None


def append_message(content, role="assistant"):
    """Appends a message to the session state messages."""
    if content.strip():
        st.session_state.messages.append({"role": role, "content": content})


def handle_sql_exception(query, conn, e, retries=2):
    append_message("Uh oh, I made an error, let me try to fix it..")
    error_message = (
        "You gave me a wrong SQL. FIX The SQL query by searching the schema definition:  \n```sql\n"
        + query
        + "\n```\n Error message: \n "
        + str(e)
    )
    new_query = chain({"question": error_message, "chat_history": ""})["answer"]
    append_message(new_query)
    if get_sql(new_query) and retries > 0:
        return execute_sql(get_sql(new_query), conn, retries - 1)
    else:
        append_message("I'm sorry, I couldn't fix the error. Please try again.")
        return None


def execute_sql(query, conn, retries=2):
    if re.match(r"^\s*(drop|alter|truncate|delete|insert|update)\s", query, re.I):
        append_message("Sorry, I can't execute queries that can modify the database.")
        return None
    try:
        return conn.sql(query).collect()
    except SnowparkSQLException as e:
        return handle_sql_exception(query, conn, e, retries)


if (
    "messages" in st.session_state
    and st.session_state["messages"][-1]["role"] != "assistant"
):
    user_input_content = st.session_state["messages"][-1]["content"]
    # print(f"User input content is: {user_input_content}")

    if isinstance(user_input_content, str):
        result = chain.invoke(
            {
                "question": user_input_content,
                "chat_history": [h for h in st.session_state["history"]],
            }
        )
        append_message(result.content)

        # if get_sql(result):
        #     conn = SnowflakeConnection().get_session()
        #     df = execute_sql(get_sql(result), conn)
        #     if df is not None:
        #         callback_handler.display_dataframe(df)
        #         append_message(df, "data", True)
uploaded_file = st.sidebar.file_uploader("Upload PDF", type="pdf")
if uploaded_file is not None:
    public_url = GCloudStorage('your-bucket-name').upload_blob(uploaded_file, uploaded_file.name)
    extracted_text = PDFExtractor().extract_text(uploaded_file)
    DocumentProcessor().process(extracted_text)
    question = st.text_input("Ask a question about the document:")
    if question:
        answer = StreamlitUICallbackHandler().query_document(question)
        st.write(answer)
try:
    # Existing file upload and processing logic...
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
