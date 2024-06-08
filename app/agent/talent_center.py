import os

import Agently

center = Agently.AgentFactory()
center \
    .set_settings("current_model", "OpenAI") \
    .set_settings("model.OpenAI.auth", {"api_key": os.environ["API_KEY"]}) \
    .set_settings("model.OpenAI.url", os.environ["API_URL"]) \
    .set_settings("model.OpenAI.options", {"model": os.environ["MODEL"]})
