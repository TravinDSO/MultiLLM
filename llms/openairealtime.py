import openai
import json
import asyncio
import websockets
import ssl
import base64
import os
import logging
from llms.tools.image_gen import OpenAI_ImageGen

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenaiRealtime:
    def __init__(self, api_key, model='gpt-4o-realtime-preview-2024-12-17',
                 info_link='', wait_limit=300, type='chat', voice="alloy"):
        self.api_key = api_key
        self.model = model
        self.info_link = info_link
        self.wait_limit = int(wait_limit)
        self.type = type
        self.voice = voice
        self.ws = None
        self.conversation_history = {}
        self.extra_messages = {}
        self.current_response = ""
        self.current_user = None
        self.last_activity_time = None
        self.SESSION_TIMEOUT = 55  # Set timeout to 55 seconds to be safe
        
        # WebSocket Configuration
        self.url = "wss://api.openai.com/v1/realtime"
        
        # SSL Configuration
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # Initialize image generation tool
        self.image_gen_tool = OpenAI_ImageGen(api_key)
        
        # Session configuration
        self.session_config = {
            "modalities": ["text"],  # Only using text modality for now
            "model": self.model,
            "voice": self.voice,
            "instructions": "You are a helpful AI assistant.",
            "tools": [
                {
                    "type": "function",
                    "name": "generate_image",
                    "description": "Generate an image based on the prompt",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "Generate an image based on the prompt. Format the response in HTML to display the image."
                            }
                        },
                        "required": ["prompt"]
                    }
                }
            ],
            "tool_choice": "auto",
            "temperature": 0.7
        }

    async def check_session(self):
        """Check if the session needs to be refreshed."""
        if not self.ws:
            return await self.connect()
            
        try:
            # Test if connection is still alive
            pong_waiter = await self.ws.ping()
            await asyncio.wait_for(pong_waiter, timeout=5)
            return
        except Exception:
            logger.info("Session disconnected, reconnecting...")
            await self.cleanup()
            return await self.connect()

    async def connect(self):
        """Connect to the WebSocket server."""
        logger.info(f"Connecting to WebSocket: {self.url}")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        try:
            # Use wait_for instead of timeout for better compatibility
            self.ws = await asyncio.wait_for(
                websockets.connect(
                    f"{self.url}?model={self.model}",
                    extra_headers=headers,
                    ssl=self.ssl_context
                ),
                timeout=30
            )
            logger.info("Successfully connected to WebSocket")
            
            # Configure session
            await self.send_event({
                "type": "session.update",
                "session": self.session_config
            })
            logger.info("Session configuration sent")
            self.last_activity_time = asyncio.get_event_loop().time()
            
            # Restore conversation if there is one
            if self.current_user:
                await self.restore_conversation(self.current_user)
                
        except asyncio.TimeoutError:
            logger.error("Connection timed out after 30 seconds")
            raise Exception("WebSocket connection timed out")
        except websockets.WebSocketException as e:
            logger.error(f"WebSocket error: {str(e)}")
            if "401" in str(e):
                raise Exception("Authentication failed - check your API key")
            elif "404" in str(e):
                raise Exception("Invalid endpoint or model not found")
            else:
                raise Exception(f"Connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            raise

    async def send_event(self, event):
        """Send an event to the WebSocket server."""
        if not self.ws:
            await self.connect()
        try:
            await self.ws.send(json.dumps(event))
            logger.debug(f"Event sent - type: {event['type']}")
        except websockets.ConnectionClosed:
            logger.info("Connection closed, reconnecting...")
            await self.connect()
            await self.ws.send(json.dumps(event))
            logger.debug(f"Event resent - type: {event['type']}")
        except Exception as e:
            logger.error(f"Error sending event: {e}")
            raise

    async def handle_event(self, event):
        """Handle incoming events from the WebSocket server."""
        event_type = event.get("type")
        
        if event_type == "error":
            logger.error(f"Error event received: {event['error']['message']}")
            raise Exception(event['error']['message'])
            
        elif event_type == "session.created":
            logger.info(f"Session created: {event.get('session', {}).get('id')}")
            
        elif event_type == "session.updated":
            logger.info("Session configuration updated")
            
        elif event_type == "conversation.created":
            logger.info(f"Conversation created: {event.get('conversation', {}).get('id')}")
            
        elif event_type == "conversation.item.created":
            logger.info(f"Conversation item created: {event.get('item', {}).get('id')}")
            
        elif event_type == "conversation.item.input_audio_transcription.completed":
            transcript = event.get("transcript")
            logger.info(f"Audio transcription completed: {transcript}")
            
        elif event_type == "response.text.delta":
            self.current_response += event["delta"]
            
        elif event_type == "response.done":
            logger.info("Response generation completed")
            if "usage" in event:
                usage = event["usage"]
                logger.info(f"Token usage - Total: {usage.get('total_tokens')}, "
                          f"Input: {usage.get('input_tokens')}, "
                          f"Output: {usage.get('output_tokens')}")
                
        elif event_type == "rate_limits.updated":
            for limit in event.get("rate_limits", []):
                if limit["remaining"] < limit["limit"] * 0.2:  # Warning at 20% remaining
                    logger.warning(f"Rate limit '{limit['name']}' low: {limit['remaining']}/{limit['limit']} "
                                 f"(resets in {limit['reset_seconds']} seconds)")
                    
        elif event_type == "response.function_call_arguments.done":
            # Handle function call
            #tool_args = json.loads(event["arguments"])
            #if event.get("name") == "generate_image":
            #    response = self.image_gen_tool.image_generate(prompt=tool_args["prompt"])
            #    self.extra_messages[self.current_user].append(
            #        f'<HR><i>Generating image using this prompt: {tool_args["prompt"]}</i>'
            #     )
            response = await self.handle_tool(self.current_user, event)
            self.current_response += response
        else:
            logger.debug(f"Unhandled event type: {event_type}")

    async def handle_tool(self, user, tool):
        """Handle tool calls asynchronously."""
        tool_name = tool.get("name")
        debug = True  # Set to True to print debug information
        args = json.loads(tool["arguments"])

        if tool_name == "generate_image":
            self.extra_messages[user].append(f'<HR><i>Generating image using this prompt: {args["prompt"]}</i>')
            results = self.image_gen_tool.image_generate(prompt=args['prompt'])
        else:
            results = "Tool not supported"

        return results

    async def generate(self, user, prompt):
        """Generate a response using the Realtime API."""
        self.current_user = user
        self.current_response = ""
        
        if user not in self.conversation_history:
            self.conversation_history[user] = []
        if user not in self.extra_messages:
            self.extra_messages[user] = []
        
        # Create message object
        message = {
            "type": "message",
            "role": "user",
            "content": [{
                "type": "input_text",
                "text": prompt
            }]
        }
        
        # Add to history
        self.conversation_history[user].append(message)
        
        try:
            await self.check_session()
            
            # Create a conversation item with the user's prompt
            await self.send_event({
                "type": "conversation.item.create",
                "item": message
            })
            logger.info("User message created")
            
            # Request a response
            await self.send_event({"type": "response.create"})
            logger.info("Response requested")
            
            # Wait for and process the response
            try:
                async for message in self.ws:
                    event = json.loads(message)
                    await self.handle_event(event)
                    
                    # If we've received a response.done event, we can stop listening
                    if event.get("type") == "response.done":
                        # Store assistant's response in history
                        if self.current_response:
                            self.conversation_history[user].append({
                                "type": "message",
                                "role": "assistant",
                                "content": [{
                                    "type": "text",
                                    "text": self.current_response
                                }]
                            })
                        break
                        
            except websockets.ConnectionClosed:
                logger.error("WebSocket connection closed")
                # Try to reconnect and resend the prompt
                await self.check_session()
                return await self.generate(user, prompt)
            
            return self.current_response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {e}"

    async def clear_conversation(self, user):
        """Clear the conversation history for a user."""
        if self.type == 'chat':
            self.conversation_history[user] = []
            # Reconnect to start a fresh session
            if self.ws:
                await self.ws.close()
                self.ws = None
            return "Conversation cleared."
        else:
            return "Not supported"

    async def summarize_conversation(self, user):
        """Summarize the current conversation."""
        if self.type in ['chat']:
            prompt = 'Summarize the current conversation. If code was generated, preserve it, presenting the most complete version to the user.'
            return await self.generate(user, prompt)
        else:
            return "Not supported"

    def check_for_previous_conversation(self, user):
        """Check if there is a previous conversation for the user."""
        return user in self.conversation_history and len(self.conversation_history[user]) > 1

    def get_extra_messages(self, user):
        """Get and clear extra messages for a user."""
        if user not in self.extra_messages:
            self.extra_messages[user] = []
        messages = self.extra_messages[user]
        self.extra_messages[user] = []
        return messages

    async def cleanup(self):
        """Clean up resources by closing the WebSocket connection."""
        if self.ws:
            try:
                await self.ws.close()
                logger.info("WebSocket connection closed")
            except Exception as e:
                logger.error(f"Error closing WebSocket connection: {e}")
            finally:
                self.ws = None
                self.current_response = ""
                logger.info("Cleanup completed")

    async def restore_conversation(self, user):
        """Restore conversation history for a user after reconnecting."""
        if user not in self.conversation_history:
            return
            
        for message in self.conversation_history[user]:
            await self.send_event({
                "type": "conversation.item.create",
                "item": message
            })
            logger.debug(f"Restored message: {message['role']}")