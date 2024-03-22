import os

import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPEN_AI_KEY")
checklist_context = """
        You are a technical bootcamp's Enrollment Coach (EC) Manager. 
        EC rubric: 
            A. Are they asking lead what motivated them to look into BloomTech?
            B. Are we talking about the weekly time commitment and the length of the program?
            C. Are we talking about any of the value props (job or money back guarantee, 
            flexibility, beginner friendly, try before you buy (RFT))?
            D. Are we asking lead if they are looking into competitors?
            E. Are they scheduling another call with the lead?
            F. Are we offering to demo the product?
            G. Are we tasking the lead to complete enrollment and engage with the product?
            H. Do we provide a good overview of the program, tuition options and expectations?
            I. Are the coaches attempting to overcome obstacles?
        to see if the enrollment coach hit all items in the rubric.
        """

lead_question_context = """
        You are a technical bootcamp's Enrollment Coach (EC) Manager 
        reviewing the Enrollment Coach's performance. 
        """


def checklist_analysis(transcript):
    prompt = f"""Analyze this {transcript} to see if the EC hit all rubric points.""" + \
             """Use the following format: {rubric point key: True/False}.
             do not add any other escape characters. Don't add \n. 
             Don't add numbers to the beginning, just use the key and value.
             Only use questions.
             """
    result = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": checklist_context},
            {"role": "user", "content": prompt},
        ],
    )
    return result.get("choices")[0].get("message").get("content")


def lead_questions_analysis(transcript):
    prompt = f"""First determine which speaker is the Enrollment Coach and which is the Lead in this transcript:
             {transcript}
             Next, give me all questions from the Lead and if the Enrollment Coach answered the question
             in the conversation in this format:""" + """ {"question asked": Boolean} 
             """ + """ where 
             the boolean is based on whether the question asked by the Lead was answered by the 
             Enrollment Coach in the conversation. Do not tell me who the speakers are. Only give me the
             dictionary, do not add anything else."""
    result = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": lead_question_context},
            {"role": "user", "content": prompt},
        ],
    )
    return result.get("choices")[0].get("message").get("content")


def summarize(input_list):
    prompt = f"""I have a list where the values are lists of questions. 
    Take this list of questions: {input_list} and 
    give me a short summary of the questions. Don't add escape characters.
    Don't mention what you're summarizing, just provide the summary in a string. 
    """
    result = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    return result.get("choices")[0].get("message").get("content")
