import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
from app.components.question_chain import generate_mcq, generate_fill_blank


def rerun():
    """Trigger Streamlit rerun."""
    st.session_state['rerun_trigger'] = not st.session_state.get('rerun_trigger', False)


class QuizManager:
    """Manages quiz generation, user attempts, evaluation, and results."""

    def __init__(self):
        self.questions = []
        self.user_answers = []
        self.results = []

    def generate_questions(self, topic: str, question_type: str, difficulty: str, num_questions: int, model_name: str = "Groq - LLaMA 3.1 8B", persona: str = "Friendly Tutor"):
        """Generate questions using LCEL chains with selected model and persona."""
        self.questions = []
        self.user_answers = []
        self.results = []

        try:
            for _ in range(num_questions):
                if question_type == "Multiple Choice":
                    # Use LCEL chain for MCQ generation with selected model and persona
                    question = generate_mcq(topic, difficulty.lower(), model_name=model_name, persona=persona)

                    self.questions.append({
                        'type': 'MCQ',
                        'question': question.question,
                        'options': question.options,
                        'correct_answer': question.correct_answer
                    })

                else:
                    # Use LCEL chain for Fill Blank generation with selected model and persona
                    question = generate_fill_blank(topic, difficulty.lower(), model_name=model_name, persona=persona)

                    self.questions.append({
                        'type': 'Fill in the blank',
                        'question': question.question,
                        'correct_answer': question.answer
                    })
        except Exception as e:
            st.error(f"Error generating question: {e}")
            return False

        return True

    def attempt_quiz(self):
        """Display quiz questions and collect user answers."""
        for i, q in enumerate(self.questions):
            st.markdown(f"**Question {i+1}: {q['question']}**")

            if q['type'] == 'MCQ':
                user_answer = st.radio(
                    f"Select an answer for Question {i+1}",
                    q['options'],
                    key=f"mcq_{i}"
                )
                self.user_answers.append(user_answer)

            else:
                user_answer = st.text_input(
                    f"Fill in the blank for Question {i+1}",
                    key=f"fill_blank_{i}"
                )
                self.user_answers.append(user_answer)

    def evaluate_quiz(self):
        """Evaluate quiz answers and store results."""
        self.results = []

        for i, (q, user_ans) in enumerate(zip(self.questions, self.user_answers)):
            result_dict = {
                'question_number': i+1,
                'question': q['question'],
                'question_type': q["type"],
                'user_answer': user_ans,
                'correct_answer': q["correct_answer"],
                "is_correct": False
            }

            if q['type'] == 'MCQ':
                result_dict['options'] = q['options']
                result_dict["is_correct"] = user_ans == q["correct_answer"]

            else:
                result_dict['options'] = []
                result_dict["is_correct"] = user_ans.strip().lower() == q['correct_answer'].strip().lower()

            self.results.append(result_dict)

    def generate_result_dataframe(self):
        """Generate pandas DataFrame from results."""
        if not self.results:
            return pd.DataFrame()

        return pd.DataFrame(self.results)

    def save_to_csv(self, filename_prefix="quiz_results"):
        """Save results to CSV file."""
        if not self.results:
            st.warning("No results to save!")
            return None

        df = self.generate_result_dataframe()

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{filename_prefix}_{timestamp}.csv"

        os.makedirs('results', exist_ok=True)
        full_path = os.path.join('results', unique_filename)

        try:
            df.to_csv(full_path, index=False)
            st.success("Results saved successfully!")
            return full_path

        except Exception as e:
            st.error(f"Failed to save results: {e}")
            return None
