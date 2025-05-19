from openai import OpenAI
import streamlit as st

st.set_page_config(page_title="Chatbot", page_icon=":robot_face:", layout="wide")
st.title("Chatbot")

if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False

def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True


if not st.session_state.setup_complete:
    st.subheader("Personal information", divider="rainbow")

    if("name") not in st.session_state:
        st.session_state.name = ""
    if("experience") not in st.session_state:
        st.session_state.experience = ""
    if("skills") not in st.session_state:
        st.session_state.skills = ""

    st.session_state.name = st.text_input("Name", value="", max_chars = 40, placeholder="Enter your name")
    st.session_state.experience = st.text_area("Experience", max_chars = 200, value="", placeholder="Enter your experience")
    st.session_state.skills = st.text_input("Skills", value="", max_chars = 200, placeholder="List your skills")

    if st.session_state.name and st.session_state.experience and st.session_state.skills:
        st.write(f"{st.session_state.name} is a {st.session_state.experience} with skills in {st.session_state.skills}")

    st.subheader("Company and Position", divider="rainbow")

    if("level") not in st.session_state:
        st.session_state.level = "Junior"
    if("position") not in st.session_state:
        st.session_state.position = "Software Engineer"
    if("company") not in st.session_state:
        st.session_state.company = "Google"

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.level = st.radio("Choose Level", options=["Junior", "Mid", "Senior"], index=0)
    with col2:
        st.session_state.position = st.selectbox("Choose Position", options=["Software Engineer", "Data Scientist", "Product Manager"], index=0)

    st.session_state.company = st.selectbox("Choose Company", options=["Google", "Amazon", "Microsoft"], index=0)

    st.write(f"**Your information**: {st.session_state.level} {st.session_state.position} at {st.session_state.company}")
    st.button("Complete Setup", on_click=complete_setup)

if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:
    st.info(
        """
            Start by introducing yourself. 
        """
    )
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4o"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if not st.session_state.messages:
        st.session_state.messages = [{"role": "system", "content": (
            f"You are an HR executive that interviews an interviewee called {st.session_state.name}"
            f"with experience {st.session_state.experience} and skills {st.session_state.skills}"
            f"You should interview him for the position {st.session_state.level} {st.session_state.position}"
            f"at the company {st.session_state.company}"
        )}]

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input("Your answer."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            if st.session_state.user_message_count < 4:
                with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model=st.session_state.openai_model,
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ],
                        stream=True,
                    )
                    response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.user_message_count += 1
        if st.session_state.user_message_count >= 5:
            st.session_state.chat_complete = True
           

if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Fetching feedback...")
    


if st.session_state.feedback_shown:
    st.subheader("Feedback", divider="rainbow")
    st.write(
        f"**Your information**: {st.session_state.level} {st.session_state.position} at {st.session_state.company}"
    )

    conversation_history = "\n".join(
        [f"{message['role']}: {message['content']}" for message in st.session_state.messages]
    ) 

    feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    feedback_complete = feedback_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": """
                You are a helpful tool that provides feedback on an intervieee performance
                Before the feedback give a score of 1 to 10
                Follow this format:
                Overall Score: // your score
                Feedback: // Here you put your feedback
                Give only the feedback do not ask for more information or questions
                """
            },
            {"role": "user", "content": f"""
                This is the interview you need to evaluate.
                Keep in mind that you are only a tool. And you should
                provide feedback based on the interviewee performance.
                Here is the conversation history:
                {conversation_history}
                """}   
        ]
    )
    
    st.write(feedback_complete.choices[0].message.content)

    if st.button("Restart Interview", type="primary"):
        keys_to_delete = list(st.session_state.keys()) 
        for key in keys_to_delete:
            del st.session_state[key]
        st.rerun()
