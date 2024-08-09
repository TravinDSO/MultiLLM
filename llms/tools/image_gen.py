import openai


class OpenAI_ImageGen:
    def __init__(self, api_key):
        self.client = openai.Client(api_key=api_key)

    def image_generate(self, prompt, model='dall-e-3'):
        try:
            image = self.client.images.generate(
                    model=model,
                    prompt=prompt,
                    n=1,
                    size="1024x1024"
            )                
            # Return the image in a HTML tag
            return f'<img src="{image.data[0].url}" alt={prompt} style="max-width: 100%;">'
        except Exception as e:
            print(f'Could not process image prompt to OpenAI: {e}')
            return f'Could not process image: {e}'
        
class Azure_OpenAI_ImageGen:
    def __init__(self, api_key, api_version, azure_endpoint):
        try:
            self.client = openai.AzureOpenAI(
                api_key=api_key,
                api_version=api_version,
                azure_endpoint=azure_endpoint
            )
        except Exception as e:
            print(f'Error creating Azure OpenAI client: {e}')

    def image_generate(self, prompt, model='dall-e-3'):
        try:
            image = self.client.images.generate(
                    model=model,
                    prompt=prompt,
                    n=1,
                    size="1024x1024"
            )                
            # Return the image in a HTML tag
            return f'<img src="{image.data[0].url}" alt={prompt} style="max-width: 100%;">'
        except Exception as e:
            print(f'Could not process image prompt to Azure: {e}')
            return f'Could not process image: {e}'