"""Blog generation nodes for LangGraph workflow with multilingual support."""

import logging
from typing import Dict, Any
from src.states.blogstate import BlogState, Blog

logger = logging.getLogger(__name__)


class BlogNode:
    """Blog generation node with multilingual support and improved prompts."""

    # Language-specific instructions
    LANGUAGE_INSTRUCTIONS = {
        "English": "Write in clear, professional English.",
        "Spanish": "Escribe en español claro y profesional. Usa un tono accesible pero informativo.",
        "French": "Écrivez en français clair et professionnel. Utilisez un ton accessible mais informatif.",
        "German": "Schreiben Sie in klarem, professionellem Deutsch. Verwenden Sie einen zugänglichen, aber informativen Ton.",
        "Italian": "Scrivi in italiano chiaro e professionale. Usa un tono accessibile ma informativo.",
        "Portuguese": "Escreva em português claro e profissional. Use um tom acessível, mas informativo.",
        "Chinese": "用清晰、专业的中文写作。使用通俗易懂但信息丰富的语气。",
        "Japanese": "明確でプロフェッショナルな日本語で書いてください。わかりやすく、情報量の多い口調を使用してください。",
        "Korean": "명확하고 전문적인 한국어로 작성하세요. 접근하기 쉽지만 유익한 어조를 사용하세요.",
        "Arabic": "اكتب بلغة عربية واضحة واحترافية. استخدم نبرة سهلة المنال ولكن غنية بالمعلومات.",
        "Hindi": "स्पष्ट, पेशेवर हिंदी में लिखें। सुलभ लेकिन जानकारीपूर्ण लहजे का उपयोग करें।",
        "Russian": "Пишите на ясном, профессиональном русском языке. Используйте доступный, но информативный тон.",
        "Dutch": "Schrijf in duidelijk, professioneel Nederlands. Gebruik een toegankelijke maar informatieve toon.",
        "Turkish": "Açık, profesyonel Türkçe yazın. Erişilebilir ama bilgilendirici bir ton kullanın.",
        "Polish": "Pisz w jasnym, profesjonalnym języku polskim. Używaj przystępnego, ale pouczającego tonu.",
    }

    def __init__(self, llm):
        """
        Initialize BlogNode with LLM instance.

        Args:
            llm: LangChain LLM instance for content generation
        """
        self.llm = llm

    def _get_language_instruction(self, language: str) -> str:
        """
        Get language-specific instruction.

        Args:
            language: Target language

        Returns:
            Language instruction string
        """
        return self.LANGUAGE_INSTRUCTIONS.get(
            language,
            f"Write in clear, professional {language}."
        )

    def title_creation(self, state: BlogState) -> Dict[str, Any]:
        """
        Generate an SEO-friendly blog title for the given topic in the specified language.

        Args:
            state: Current blog state containing the topic and language

        Returns:
            Updated state with generated title
        """
        try:
            if "topic" not in state or not state["topic"]:
                return {"error": "No topic provided for title generation"}

            topic = state["topic"]
            language = state.get("language", "English")
            language_instruction = self._get_language_instruction(language)

            prompt = f"""You are an expert blog content writer and SEO specialist.

Topic: {topic}
Target Language: {language}

Generate a compelling, SEO-friendly blog title IN {language.upper()} that:
1. Captures attention and encourages clicks
2. Is between 50-60 characters for optimal SEO
3. Includes relevant keywords naturally
4. Is clear and describes the content accurately
5. {language_instruction}

IMPORTANT: The title MUST be written in {language}, not English.

Return ONLY the title text in {language}, without quotes or additional formatting."""

            logger.info(f"Generating {language} title for topic: {topic}")
            response = self.llm.invoke(prompt)

            title = response.content.strip().strip('"').strip("'")

            return {"blog": {"title": title, "content": "", "language": language}}

        except Exception as e:
            logger.error(f"Error in title_creation: {str(e)}")
            return {"error": f"Failed to generate title: {str(e)}"}

    def content_generation(self, state: BlogState) -> Dict[str, Any]:
        """
        Generate detailed blog content based on the topic and title in the specified language.

        Args:
            state: Current blog state with topic, title, and language

        Returns:
            Updated state with generated content
        """
        try:
            if "topic" not in state or not state["topic"]:
                return {"error": "No topic provided for content generation"}

            if "blog" not in state or not state["blog"].get("title"):
                return {"error": "No title found in state for content generation"}

            title = state["blog"]["title"]
            topic = state["topic"]
            language = state.get("language", "English")
            language_instruction = self._get_language_instruction(language)

            prompt = f"""You are an expert blog writer specializing in creating engaging, informative content.

Title: {title}
Topic: {topic}
Target Language: {language}

Write a comprehensive, well-structured blog post IN {language.upper()} that:
1. Uses proper Markdown formatting (headings, lists, bold, italics)
2. Includes an engaging introduction that hooks the reader
3. Covers the topic in depth with clear sections and subheadings
4. Provides actionable insights and practical examples
5. Concludes with key takeaways or a call-to-action
6. Is approximately 800-1200 words
7. Uses a professional yet conversational tone
8. {language_instruction}

Format the content with:
- ## for main sections
- ### for subsections
- **bold** for emphasis
- * for bullet points
- > for important quotes or notes

CRITICAL: Write the ENTIRE blog post in {language}, not English. All headings, content, and examples must be in {language}.

Generate the complete blog content in {language} now:"""

            logger.info(f"Generating {language} content for: {title}")
            response = self.llm.invoke(prompt)

            content = response.content.strip()

            return {
                "blog": {
                    "title": title,
                    "content": content,
                    "language": language
                }
            }

        except Exception as e:
            logger.error(f"Error in content_generation: {str(e)}")
            return {"error": f"Failed to generate content: {str(e)}"}