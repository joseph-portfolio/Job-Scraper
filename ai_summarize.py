import aiohttp
import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def summarize(posting) -> str:
    prompt = f"""
    Extract only what is explicitly stated in the job posting. Use this format:

    Summary: A concise 1-2 sentence overview of the role.
    Hard Skills: Technical or job-specific skills required (e.g., programming languages, tools, certifications).
    Soft Skills: Interpersonal or general skills (e.g., communication, teamwork).
    Required Experience: Years of experience, industry background, or specific prior roles mentioned.
    Work Arrangement: On-site, Hybrid or Remote

    Format the output as:

    ```json
    {{ 
        "summary": "str",  
        "hard_skills": "str",  
        "soft_skills": "str",  
        "required_experience": "str"
        "work_arrangement": "str"  
    }}
	
	Job posting: {posting}
    """


    api_token = os.getenv('CHUTES_API')  # Replace with your actual API token
    headers = {
        "Authorization": "Bearer " + api_token,
        "Content-Type": "application/json"
    }
    
    body = {
        "model": "deepseek-ai/DeepSeek-V3-0324",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": True,
        "max_tokens": 1024,
        "temperature": 0
    }

    full_response = []
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "https://llm.chutes.ai/v1/chat/completions",
                headers=headers,
                json=body
            ) as response:
                # Process streaming chunks
                async for line in response.content:
                    if line.startswith(b"data: "):
                        chunk = line[6:].strip()
                        if chunk == b"[DONE]":
                            break
                        try:
                            data = json.loads(chunk.decode())
                            if "choices" in data:
                                content = data["choices"][0].get("delta", {}).get("content", "")
                                if content:
                                    full_response.append(content)
                        except json.JSONDecodeError:
                            continue

                # Combine all chunks and extract JSON
                if full_response:
                    response_str = "".join(full_response)
                    json_str = response_str.strip().strip("```json").strip("```").strip()
                    return json.loads(json_str)
                return None

        except (KeyError, json.JSONDecodeError, aiohttp.ClientError) as e:
            print(f"Error: {e}")
            return None

async def main():
    # Sample posting
    posting = "As an AI Software Engineer, you will be responsible for designing, developing, maintaining, and testing cutting-edge software applications with AI functionality. Your goal will be to bridge the gap between software application features and AI technologies, algorithms, logic, and methodologies. For This Role, You Will Need: Bachelor’s or Master’s degree or equivalent in Engineering, Computer Science, Artificial Intelligence, IT, or any related field. In this Role, Your Responsibilities Will Be: Use different AI technologies including frameworks, libraries, models, and algorithms to solve specific software application problems Integrate machine learning and deep learning algorithms and other frameworks into software applications Collaborate with data engineers and scientists to preprocess and analyze various data sets for training and testing Fine-tune AI models for improved performance and accuracy Integrate AI models into production software Research, analyze, design, develop and deliver end-to-end solutions, staying up to date on latest AI technologies Develop software applications with AI capabilities and features, writing, testing, and deploying code Participate in scrum activities and collaborate closely with stakeholders and global team to ensure technical solutions align with business goals Maintain and update technical documentation to ensure that others can easily understand and extend software application. Other duties that may be assigned in relation to deliverables Who You Are: You are result-oriented and biased towards action. You are nimble learner and adapt quickly when facing new situations. You ask the right questions to accurately analyze situations. You introduce new ways of looking at problems. You anticipate the impact of emerging technologies and make adjustments and recommendations. You have a strong bottom-line orientation. Preferred Qualifications that Set You Apart: At least 2 years’ experience of working with AI/ML projects and have a good grasp of the nature of AI applications. Working experience with frameworks like Haystack, Langchain, Ollama, or similar. Familiarity with best practices in software development, including Agile methodologies and test-driven development, and DevSecOps. Excellent problem-solving skills, good at handling ambiguous requirements, and aptitude to learn new technologies quickly. Strong analytical, communication, and teamwork skills. Ability to work independently and manage multiple tasks simultaneously. Our Culture &amp; Commitment to You At Emerson, we prioritize a workplace where every employee is valued, respected, and empowered to grow. We foster an environment that encourages innovation, collaboration, and diverse perspectives—because we know that great ideas come from great teams. Our commitment to ongoing career development and growing an inclusive culture ensures you have the support to thrive. Whether through mentorship, training, or leadership opportunities, we invest in your success so you can make a lasting impact. We believe diverse teams, working together are key to driving growth and delivering business results. We recognize the importance of employee wellbeing. We prioritize providing competitive benefits plans, a variety of medical insurance plans, Employee Assistance Program, employee resource groups, recognition, and much more. Our culture offers flexible time off plans, including paid parental leave (maternal and paternal), vacation, and holiday leave. "

    result = await summarize(posting)
    if result:
        print(result)
    else:
        print("Failed to summarize the job posting.")

if __name__ == "__main__":
    asyncio.run(main())