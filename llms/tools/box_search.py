import os
from dotenv import load_dotenv
from box_sdk_gen import BoxCCGAuth, BoxClient, SearchManager, BoxDeveloperTokenAuth, CCGConfig


class BoxSearch:
    def __init__(self, client_id=None, client_secret=None, enterprise_id=None, user_id=None, developer_token=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.enterprise_id = enterprise_id
        self.user_id = user_id
        self.developer_token = developer_token
        self.client: BoxClient = BoxClient(auth=self.box_auth())
        #self.search = SearchManager(auth=self.box_auth())


    def box_auth(self):

        auth_obj = None

        if self.developer_token:
            box_auth: BoxDeveloperTokenAuth = BoxDeveloperTokenAuth(token=self.developer_token)
        else:
            if self.enterprise_id:
                box_oauth_config = CCGConfig(
                    client_id=os.getenv(self.client_id),
                    client_secret=os.getenv(self.client_secret),
                    enterprise_id=os.getenv(self.enterprise_id)
                )
            else:
                box_oauth_config = CCGConfig(
                    client_id=os.getenv(self.client_id),
                    client_secret=os.getenv(self.client_secret),
                    user_id=os.getenv(self.user_id)
                )

            auth_obj = BoxCCGAuth(config=box_oauth_config)

        return auth_obj


    def box_search(self, query):
        items = self.client.search.search_for_content(query=query)
        print(items)

# Test Cell
# Please do not modify
if __name__ == '__main__':
    try:
        # Load the env file
        load_dotenv('environment.env', override=True)

        box_search = BoxSearch(
            developer_token=os.getenv('BOX_DEVELOPER_TOKEN')
        )

        #box_search = BoxSearch(
        #    client_id=os.getenv('BOX_CLIENT_ID'),
        #    client_secret=os.getenv('BOX_CLIENT_SECRET'),
        #    enterprise_id=os.getenv('BOX_ENTERPRISE_ID'),
        #)

        box_search.box_search('mescas')

    except Exception as e:
        print(f"An error occurred: {str(e)}")