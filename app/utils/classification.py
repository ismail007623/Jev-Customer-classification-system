from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from app.schemas.ticket import ResponseLLM
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings
from app.core.logging import get_logger

chat_llm = ChatOpenAI(
    model = settings.OPENAI_MODEL,
    api_key= settings.OPENAI_API_KEY,
    temperature=0,
)

logger = get_logger(__name__)


async def get_ticket_itent(name: str , subject: str , issue: str):
    """
    """
    try:
        logger.info("Entring into ticket classification from LLM")

        classification_prompt_str = ChatPromptTemplate.from_template( """
            ## Role
                You are an expert Support Ticket Reviewer and Intent Classifier.

            ## Task
                you will given user name subject and issue .
                Analyze the ticket's **subject** and **issue** to understand the user's main problem.

            Classify the ticket into exactly one of these intents:

                * `billing` — Payments, charges, invoices, refunds, subscriptions, pricing, or other billing-related issues.
                * `technical` — Bugs, errors, system failures, login/access problems, feature issues, performance problems, or other technical issues.

            ## Guidelines
                * Consider both the subject and issue description.
                * Identify the user's **primary issue**, not just keywords.
                * Choose exactly one intent.
                * If multiple issues are mentioned, classify based on the main problem.
                * Do not provide explanations or additional text.

            **INPUT VARIABLES**
                Name: {name}
                Subject: {subject}
                Issue: {issue}

            ## Output Format

                Return only valid JSON:

                {{
                "intent": "billing or technical"
                }}
        """
        )

        #classification_parser = PydanticOutputParser(pydantic_object=ResponseLLM)
        #classification_chain =  classification_prompt_str | chat_llm | classification_parser
        #response = await classification_chain.ainvoke({"name":name ,"subject":subject , "issue":issue})
        #usage = response.usage_metadata
        
        structured_llm = chat_llm.with_structured_output(
            ResponseLLM,
            include_raw=True
        )

        response = await (
            classification_prompt_str | structured_llm
        ).ainvoke({
            "name": name,
            "subject": subject,
            "issue": issue,
        })

        if response["parsing_error"]:
            logger.error(
                f"LLM parsing failed: {response['parsing_error']}"
            )
            raise ValueError("Invalid LLM response")

        parsed = response["parsed"]
        raw = response["raw"]

        usage = raw.usage_metadata or {}

  
        logger.info("Successfully classified ticket from LLM")
        return {
            "result": parsed.intent,
            "token_usage": {
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
            }
        }
  
    except Exception as e:
        logger.error(f"Failed to classified ticket from LLM : {e}")
        raise Exception(f"Failed to classified ticket from LLM : {e}")




    




