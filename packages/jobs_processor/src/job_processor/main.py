from openai import OpenAI

from job_processor.db import Job, session

client = OpenAI(
    api_key="ollama-key",
    base_url="http://127.0.0.1:8001/v1",
)

cv = (
    "I worked for 2.5 years in backend and mainly looking for backend position. But fullstack and software developer options are also interesting for me."
    "Here are some highlight in my current position"
    "Integrated firmware update functionality for embedded devices using WebSerial technology, streamlining the update process and enhancing user experience."
    "● Transitioned API server and endpoints to an asynchronous architecture, achieving a 15x performance improvement."
    "● Tripled the speed of the CI/CD pipeline, significantly reducing deployment times and boosting development productivity."
    "● Designed and implemented a role-based access control (RBAC) service for maintenance operations, enhancing security and operational efficiency."
    "● Implemented critical security enhancements to the application, strengthening protection against vulnerabilities and ensuring compliance with industry standards."
    "● Developed and integrated backend support for third-party hardware, enabling seamless interoperability and expanding device compatibility."
    "Here are my skill:"
    "Programming/scripting languages: Python, Rust, HTML, CSS, JS, Bash"
    "Frameworks: FastAPI, Django, gRPC, Svelte"
    "Technologies: Git, REST, RPC, Websockets, WebSerial"
    "DevOps: Docker, Gitlab CI/CD, Github Actions, AWS (S3, ECS, Lambda, Cloudwatch, SQS, SNS), Terraform PM tools: Slack, Notion, Jira, Zendesk"
    "Soft skills: Fast learner, Team player, Able to take responsibility Languages: English (C1), German (B2), Ukrainian (Native), Russian (C2)"
)


for job in session.query(Job).all():
    response = client.chat.completions.create(
        model="llama3:8b",
        messages=[
            {
                "role": "system",
                "content": f"You are evaluating if my CV is a good fit for the job. You should only provide a numerical score between 0 and 10 and nothing else. Here is my cv: {cv}",
            },
            {"role": "user", "content": str(job.description)},
        ],
        stream=False,
    )
    break
