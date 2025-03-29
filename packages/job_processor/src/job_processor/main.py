from openai import OpenAI
from tqdm import tqdm

from job_processor.db import Job, session

client = OpenAI(
    api_key="ollama-key",
    base_url="http://127.0.0.1:8001/v1",
)

skills = (
    "Here are my skill:"
    "Programming/scripting languages: Python, Rust, HTML, CSS, JS, Bash"
    "Frameworks: FastAPI, Django, gRPC, Svelte"
    "Technologies: Git, REST, RPC, Websockets, WebSerial"
    "DevOps: Docker, Gitlab CI/CD, Github Actions, AWS (S3, ECS, Lambda, Cloudwatch, SQS, SNS), Terraform PM tools: Slack, Notion, Jira, Zendesk"
)

non_processed_jobs = session.query(Job).filter(Job.ai_fit_score == None).all()
for job in tqdm(non_processed_jobs):
    response = client.chat.completions.create(
        model="llama3:8b",
        messages=[
            {
                "role": "system",
                "content": "You are a scoring machine. You cannot output anything except numbers from 0 to 10. Ten means 100% fit. Now rate much does a CV fit for a job description.",
            },
            {
                "role": "user",
                "content": (
                    "I am interested mainly in Backend Developer or Backend focused fullstack or something similar. "
                    "The job should not be an internship, nor for juniors, but also not for very seniors"
                    f"{skills}"
                    f".\n\nHere is job description{job.description}"
                ),
            },
        ],
        stream=False,
    )
    try:
        score = float(response.choices[0].message.content)
    except Exception:
        print(
            f"Error adding to db output: lenght {len(response.choices[0].message.content)}"
        )
        score = 0.0

    session.query(Job).filter(Job.id == job.id).update(
        {Job.ai_fit_score: score}
    )
    session.commit()
