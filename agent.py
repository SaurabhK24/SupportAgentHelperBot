from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser, SystemPrompt
import asyncio
from openai import OpenAI


client = OpenAI()

llm = ChatOpenAI(model="gpt-4o")

infoArray = []

class MySystemPrompt(SystemPrompt):
    def important_rules(self) -> str:
        # Get existing rules from parent class
        existing_rules = super().important_rules()

        # Add your custom rules
        new_rules = """
9. MOST IMPORTANT RULE:
- Make sure to extract information endpoint by endpoint. Open all subsections of the endpoint. You will see a triangle toggle button to open a smaller subsection with more detailed information about that specifc endpoint. Click this button in each subsection to reveal more detail information about each API endpoint and learn all the information about the endpoints and parameters. If there are nested subsections with more information, click the triangle toggle button to open the nested subsection and extract the information from there. Continue this process until you have extracted all the information about the endpoint.!!!
"""     # Make sure to use this pattern otherwise the exiting rules will be lost
        return f'{existing_rules}\n{new_rules}'
    
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


async def main():
    # Create a browser instance
    browser = Browser()
    
    # Create a browser context that can be reused
    async with await browser.new_context() as context:
        # First agent with first task
        agent = Agent(
            task="Extract all the information from https://crustdata.notion.site/Crustdata-Dataset-API-Detailed-Examples-b83bd0f1ec09452bb0c2cac811bba88c and learn all the API endpoints and parameters.",
            llm=llm,
            use_vision=True,
            save_conversation_path="logs3/conversation.json",
            browser_context=context,
            system_prompt_class=MySystemPrompt

        )
        
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
            browser_context=context,
            system_prompt_class=MySystemPrompt

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
    '''
    completion = client.chat.completions.create(
        model="o1",
        messages=[
            {"role": "developer", "content": "You are a chatbot that can answer questions about the crustdata APIs. You have the following information: " + "\n".join(infoArray[0])},
            {"role": "user", "content": "Tell me about the Crustdata Discovery And Enrichment APIs in its entirety. I want to know all the endpoints and parameters and how to use them."}
        ]
        )
        print(completion.choices[0].message)

    '''
    


    await browser.close()



asyncio.run(main())



