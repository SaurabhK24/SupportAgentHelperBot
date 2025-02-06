from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser, SystemPrompt, BrowserConfig
import asyncio
from openai import OpenAI


client = OpenAI()

llm = ChatOpenAI(model="o3-mini")

with open("resume.txt", "r") as resume_file:
    resume_text = resume_file.read()

infoArray = []

class MySystemPrompt(SystemPrompt):
    def important_rules(self) -> str:
        # Get existing rules from parent class
        existing_rules = super().important_rules()

        # Add your custom rules
        new_rules = """
  Job Application Rules:
- You are an agent tasked with automating the job application process.
- Navigate to the job listings page on the provided job portal.
- Identify job postings that match given criteria.
- Extract key details from each posting.
- Fill out the application forms with the pre-saved resume.
- If a file upload is required (e.g. PDF resume), use the provided resume file.
- Ensure that each step is executed clearly and accurately.
"""     # Make sure to use this pattern otherwise the exiting rules will be lost
        return f'{existing_rules}\n{new_rules}'

'''
class MyNewSystemPrompt(SystemPrompt):
    def important_rules(self) -> str:
        # Get existing rules from parent class
        existing_rules = super().important_rules()

        # Add your custom rules
        new_rules = """
9. MOST IMPORTANT RULE:
- You will be given context from the previous agent. This will include information about the API endpoints and parameters. It has a general structure of the page. Determine if you need to click the triangle toggle button and open the nested subsections to extract more information. If you do, click the triangle toggle button and open the nested subsections to extract more information. If you do not, then do not click the triangle toggle button. !!!
"""     # Make sure to use this pattern otherwise the exiting rules will be lost
        return f'{existing_rules}\n{new_rules}'
'''    

browser = Browser(
    config=BrowserConfig(
        # Specify the path to your Chrome executable
        chrome_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS path
        # For Windows, typically: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
        # For Linux, typically: '/usr/bin/google-chrome'
    )
)


async def main():
        # Create a browser context that can be reused
    
        # First agent with first task
    agent = Agent(
        task="Apply for jobs on https://app.notify.careers/postings using my resume below:\n" +
        f"RESUME:\n{resume_text}\n\n" +
        "Use the job listings available on https://app.notify.careers/postings to submit applications. " +
        "Include details like job title, company name, job URL, and your application status in the output.",
        llm=llm,
        use_vision=True,
        save_conversation_path="logs3/conversation.json",
        system_prompt_class=MySystemPrompt,
        browser=browser
    )
    await agent.run()
        
    history = await agent.run()

    infoArray.append(history.extracted_content())
        
    print("First task completed")
    print("URLs visited:", history.urls())
    print("Extracted content:", history.extracted_content())

    print('-------------------------------------------------------------------------------------')

    secondagent = Agent(
        task="Extract all the information from https://crustdata.notion.site/Crustdata-Dataset-API-Detailed-Examples-b83bd0f1ec09452bb0c2cac811bba88c and learn all the API endpoints and parameters.",
        llm=llm,
        use_vision=True,
        save_conversation_path="logs3/conversation.json",
    )


    '''
         # Second agent with second task
        next_agent = Agent(
            task="Extract all the information from https://crustdata.notion.site/Crustdata-Discovery-And-Enrichment-API-c66d5236e8ea40df8af114f6d447ab48 and learn all the API endpoints and parameters.",
            llm=llm,
            use_vision=True,
            save_conversation_path="logs3/conversation2.json",
            browser_context=context,
            system_prompt_class=MySystemPrompt
        )
        
        history2 = await next_agent.run()
        print("\nSecond task completed")
        print("URLs visited:", history2.urls())
        print("Extracted content:", history2.extracted_content())

        infoArray.append(history2.extracted_content())
    ''' 
       
    
        # Close the browser after all tasks are complete
    
    completion = client.chat.completions.create(
        model="o3-mini",
        messages=[
            {"role": "developer", "content": "You are a chatbot agent that is an expert in job applications. You have the following information: " + "\n".join(infoArray[0])},
            {"role": "user", "content": "Can you help me apply for jobs using my resume below:\n" +
            f"RESUME:\n{resume_text}\n\n" +
            "Use the information from the job listings to submit applications. " +
            "Include details like job title, company name, job URL, and your application status in the output."}
        ]
        )
    
    print(completion.choices[0].message)
    


    await browser.close()



asyncio.run(main())



