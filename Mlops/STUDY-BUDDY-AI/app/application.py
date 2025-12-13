import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from dotenv import load_dotenv
from app.components.helpers import QuizManager, rerun
from app.config.config import AVAILABLE_MODELS

load_dotenv()


def main():
    st.set_page_config(page_title="Study Buddy AI", page_icon="🎓")

    if 'quiz_manager' not in st.session_state:
        st.session_state.quiz_manager = QuizManager()

    if 'quiz_generated' not in st.session_state:
        st.session_state.quiz_generated = False

    if 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = False

    if 'rerun_trigger' not in st.session_state:
        st.session_state.rerun_trigger = False

    st.title("Study Buddy AI - Multi-Model Edition")

    st.sidebar.header("Quiz Settings")

    # Model Selection
    model_name = st.sidebar.selectbox(
        "Select AI Model",
        options=list(AVAILABLE_MODELS.keys()),
        index=0,
        help="Choose from multiple AI models including Groq and OpenAI"
    )

    # Show model info
    model_config = AVAILABLE_MODELS[model_name]
    st.sidebar.info(f"Provider: {model_config['provider'].upper()}\nModel: {model_config['model_name']}")

    question_type = st.sidebar.selectbox(
        "Select Question Type",
        ["Multiple Choice", "Fill in the Blank"],
        index=0
    )

    topic = st.sidebar.text_input("Enter Topic", placeholder="e.g., Indian History, Geography")

    difficulty = st.sidebar.selectbox(
        "Difficulty Level",
        ["Easy", "Medium", "Hard"],
        index=1
    )

    num_questions = st.sidebar.number_input(
        "Number of Questions",
        min_value=1, max_value=10, value=5
    )

    if st.sidebar.button("Generate Quiz"):
        if not topic:
            st.sidebar.error("Please enter a topic!")
        else:
            st.session_state.quiz_submitted = False

            # Use LCEL-based chain for question generation with selected model
            with st.spinner(f"Generating quiz using {model_name}..."):
                success = st.session_state.quiz_manager.generate_questions(
                    topic, question_type, difficulty, num_questions, model_name
                )

            st.session_state.quiz_generated = success
            rerun()

    if st.session_state.quiz_generated and st.session_state.quiz_manager.questions:
        st.header("Quiz")
        st.session_state.quiz_manager.attempt_quiz()

        if st.button("Submit Quiz"):
            st.session_state.quiz_manager.evaluate_quiz()
            st.session_state.quiz_submitted = True
            rerun()

    if st.session_state.quiz_submitted:
        st.header("Quiz Results")
        results_df = st.session_state.quiz_manager.generate_result_dataframe()

        if not results_df.empty:
            correct_count = results_df["is_correct"].sum()
            total_questions = len(results_df)
            score_percentage = (correct_count/total_questions)*100
            st.write(f"Score: {score_percentage:.1f}%")

            for _, result in results_df.iterrows():
                question_num = result['question_number']
                if result['is_correct']:
                    st.success(f"✅ Question {question_num}: {result['question']}")
                else:
                    st.error(f"❌ Question {question_num}: {result['question']}")
                    st.write(f"Your answer: {result['user_answer']}")
                    st.write(f"Correct answer: {result['correct_answer']}")

                st.markdown("---")

            if st.button("Save Results"):
                saved_file = st.session_state.quiz_manager.save_to_csv()
                if saved_file:
                    with open(saved_file, 'rb') as f:
                        st.download_button(
                            label="Download Results",
                            data=f.read(),
                            file_name=os.path.basename(saved_file),
                            mime='text/csv'
                        )
                else:
                    st.warning("No results available")


if __name__ == "__main__":
    main()
