from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser, SystemPrompt, BrowserConfig, Controller, ActionResult
from browser_use.browser.context import BrowserContext

import asyncio
from openai import OpenAI
from pydantic import BaseModel, SecretStr
from typing import List, Optional
import csv
from PyPDF2 import PdfReader
import logging
from pathlib import Path
import sys
import os

# Add the parent directory to the Python path
#sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
print("The path is : ",os.path.dirname(os.path.abspath(__file__)))
# Setup
client = OpenAI()
llm = ChatOpenAI(model="gpt-4o")
controller = Controller()
logger = logging.getLogger(__name__)

# Resume Text
with open("resume.txt", "r") as resume_file:
    resume_text = resume_file.read()
	
# Resume PDF
CV = Path.cwd() / 'resume.pdf'

if not CV.exists():
	raise FileNotFoundError(f'You need to set the path to your cv file in the CV variable. CV file not found at {CV}')

# Info Array
infoArray = []

# Browser Context Setup
browser = Browser(
    config=BrowserConfig(
        # Specify the path to your Chrome executable
        chrome_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS path
        disable_security=True
        # For Windows, typically: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
        # For Linux, typically: '/usr/bin/google-chrome'
    )
)

# Job Model
class Job(BaseModel):
	title: str
	link: str
	company: str
	fit_score: Optional[float] = None
	location: Optional[str] = None
	salary: Optional[str] = None

# System Prompt
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
 - Fill out the application forms using the pre-saved resume text.
 - If a file upload button is found (i.e. a field for a PDF resume), then attempt to fill out the form using only the resume text.
 - Only invoke the 'Upload cv to element' controller function if the form explicitly requires uploading a file.
 - Also, if helpful, use the other controller functions such as 'Save jobs to file' and 'Read my cv for context to fill forms' to complete the application process.
 - Logically decide on the best approach to complete each step accurately.
"""
        return f'{existing_rules}\n{new_rules}'
    

# Save jobs to file - with a score how well it fits to my profile
@controller.action('Save jobs to file - with a score how well it fits to my profile', param_model=Job)
def save_jobs(job: Job):
	print("Saving jobs to file!!!!!!!!!!!!")
	with open('jobs.csv', 'a', newline='') as f:
		writer = csv.writer(f)
		writer.writerow([job.title, job.company, job.link, job.salary, job.location])

	return 'Saved job to file'



@controller.action('Read my cv for context to fill forms')
def read_cv():
	print("Reading cv for context to fill forms!!!!!!!!!!!!")
	pdf = PdfReader(CV)
	text = ''
	for page in pdf.pages:
		text += page.extract_text() or ''
	logger.info(f'Read cv with {len(text)} characters')
	return ActionResult(extracted_content=text, include_in_memory=True)



@controller.action(
	'Upload cv to element - call this function to upload if element is not found, try with different index of the same upload element',
)
async def upload_cv(index: int, browser: BrowserContext):
	print("Uploading cv to element!!!!!!!!!!!!")
	path = str(CV.absolute())
	dom_el = await browser.get_dom_element_by_index(index)

	if dom_el is None:
		return ActionResult(error=f'No element found at index {index}')

	file_upload_dom_el = dom_el.get_file_upload_element()

	if file_upload_dom_el is None:
		logger.info(f'No file upload element found at index {index}')
		return ActionResult(error=f'No file upload element found at index {index}')

	file_upload_el = await browser.get_locate_element(file_upload_dom_el)

	if file_upload_el is None:
		logger.info(f'No file upload element found at index {index}')
		return ActionResult(error=f'No file upload element found at index {index}')

	try:
		await file_upload_el.set_input_files(path)
		msg = f'Successfully uploaded file to index {index}'
		logger.info(msg)
		return ActionResult(extracted_content=msg)
	except Exception as e:
		logger.debug(f'Error in set_input_files: {str(e)}')
		return ActionResult(error=f'Failed to upload file to index {index}')




async def main():    
    
    # First agent with first task
    agent = Agent(
        task="Apply for jobs on https://app.notify.careers/postings using my resume below:\n" +
        f"RESUME:\n{resume_text}\n\n" +
        "If the job application process requires uploading a file, use the 'Upload cv to element' function to upload your PDF resume. If you can complete the application form using just the resume text, do not upload the file.\n" +
        "Additionally, if any further actions can help finalize the application—such as saving job details or reading CV context—then invoke the remaining controller functions ('Save jobs to file' and 'Read my cv for context to fill forms').\n" +
        "Use the job listings available on https://app.notify.careers/postings to submit applications, including details like job title, company name, job URL, and application status in the output.",
        llm=llm,
        use_vision=True,
        save_conversation_path="logs4/conversation.json",
        system_prompt_class=MySystemPrompt,
        browser=browser,
        controller=controller,
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
    
    # Close the browser after all tasks are complete
    await browser.close()



asyncio.run(main())




'''
	 completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "developer", "content": "You are a chatbot agent that is an expert in job applications. You have the following information: " + "\n".join(infoArray[0])},
            {"role": "user", "content": "Can you help me apply for jobs using my resume below:\n" +
            f"RESUME:\n{resume_text}\n\n" +
            "Use the information from the job listings to submit applications. " +
            "Include details like job title, company name, job URL, and your application status in the output."}
        ]
        )
    
    print(completion.choices[0].message)
'''
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