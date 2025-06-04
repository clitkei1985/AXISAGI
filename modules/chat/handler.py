# modules/chat/handler.py

import openai
import logging
from typing import List
from core.config import Config
from core.audit import audit_log
from core.rules import Rules, RuleViolation
from modules.memory.memory import AIMemory

logger = logging.getLogger("axis.chat.handler")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(Config.LOG_PATH)
fh.setFormatter(logging.Formatter("%(asctime)s | CHAT_MODULE | %(levelname)s | %(message)s"))
logger.addHandler(fh)

class ChatHandler:
    """
    Facade for handling chat: stores messages to memory, retrieves relevant context,
    calls OpenAI (or local LLM), and stores the AI response back to memory.
    """

    @staticmethod
    def initialize_api():
        """
        Ensure the OpenAI key is set.
        """
        openai.api_key = Config.OPENAI_API_KEY

    @staticmethod
    def get_contextual_messages(session_id: str, top_k: int = 5) -> List[str]:
        """
        Retrieve the top_k memory texts for this session to use as context.
        """
        try:
            mem = AIMemory(session_id)
            entries = mem.search_memory(query="context", top_k=top_k)
            return [e.text for e in entries]
        except Exception as e:
            logger.exception(f"Error retrieving context for session '{session_id}': {e}")
            return []

    @staticmethod
    def send_user_message(session_id: str, user_message: str) -> str:
        """
        Main entry: store the user’s message, build a prompt including memory,
        call OpenAI, store the response, and return it.
        """
        try:
            Rules.enforce("GOVERNED_BY_IMMUTABLE_REQUIREMENTS")

            # 1) Initialize OpenAI
            ChatHandler.initialize_api()

            # 2) Save user message to memory
            mem = AIMemory(session_id)
            mem.add_memory(text=f"User: {user_message}", tags=["chat", "user"], pinned=False)

            # 3) Retrieve top‐K memory entries as context
            context_texts = mem.search_memory(query=user_message, top_k=5)
            system_prompt = "You are a helpful AI assistant. Use the conversation memory to answer."

            messages = [{"role": "system", "content": system_prompt}]
            # Inject memory snippets as system/context messages
            for snippet in context_texts:
                messages.append({"role": "system", "content": f"Memory: {snippet}"})

            # 4) Append the actual user message
            messages.append({"role": "user", "content": user_message})

            # 5) Call OpenAI ChatCompletion
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=512,
            )

            ai_reply = response.choices[0].message.content.strip()

            # 6) Save AI’s response to memory
            mem.add_memory(text=f"AI: {ai_reply}", tags=["chat", "ai"], pinned=False)

            audit_log(
                user_id=session_id,
                module="chat",
                action="send_user_message",
                status="OK",
                details=f"prompt_len={len(user_message)}; context_items={len(context_texts)}"
            )
            logger.info(f"Session '{session_id}': AI reply stored to memory.")

            return ai_reply

        except RuleViolation as rv:
            audit_log(
                user_id=session_id,
                module="chat",
                action="send_user_message",
                status="RULE_VIOLATION",
                details=str(rv)
            )
            logger.warning(f"RuleViolation in session '{session_id}': {rv}")
            raise
        except Exception as e:
            audit_log(
                user_id=session_id,
                module="chat",
                action="send_user_message",
                status="ERROR",
                details=str(e)
            )
            logger.exception(f"Error in send_user_message for session '{session_id}': {e}")
            raise
