from transformers import pipeline

chatbot = pipeline("text-generation",model="distilgpt2")

def ask_ai(question):

    res = chatbot(question,max_length=120)
    return res[0]["generated_text"]


def attendance_risk(records):

    late=0

    for r in records:
        if r["status"]=="Late":
            late+=1

    if late>=5:
        return "High Risk"
    elif late>=2:
        return "Medium Risk"
    else:
        return "Low Risk"
